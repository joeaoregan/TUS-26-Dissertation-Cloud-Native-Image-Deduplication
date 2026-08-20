#!/usr/bin/env python3

import csv
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from colorama import Fore, init

init(autoreset=True)  # colorama: auto clear colours after printing

# ============================================================
# Interim Evaluation 2 (Detection Quality)
# - Runs each threshold configuration
# - Exports Stage 3 predictions
# - Evaluates predictions against reference labels
# - Prints results progressively as a report-style table
# - Writes logs, reports, predictions and summary CSV
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
DEDUPE_PY_DIR = REPO_ROOT / "services" / "dedupe-py"
PYTHON_EXE = str(Path(sys.executable).resolve())

DATASET_DIR = "dedupe_test_100"

REFERENCE_LABELS_SOURCE = (
    REPO_ROOT / "data" / "labels" / "reference_labels_eval_v1.csv"
).resolve()

CONFIGS = [
    ("C1", 5, 0.85, "threshold-tuning-baseline-phash5-ssim085"),
    ("C2", 4, 0.85, "threshold-tuning-phash4-ssim085"),
    ("C3", 5, 0.90, "threshold-tuning-phash5-ssim090"),
    ("C4", 6, 0.85, "threshold-tuning-phash6-ssim085"),
    ("C5", 6, 0.90, "threshold-tuning-phash6-ssim090"),
]


# ============================================================
# Final result locations
# ============================================================

OUT_ROOT = (REPO_ROOT / "results" / "interim" / "eval2").resolve()

METRICS_DIR = OUT_ROOT / "metrics"
LOGS_DIR = OUT_ROOT / "logs"
PREDICTIONS_DIR = OUT_ROOT / "predictions"
REPORTS_DIR = OUT_ROOT / "reports"

SUMMARY_CSV = METRICS_DIR / "table_eval2_summary.csv"


# ============================================================
# Staging locations required by path-safety rules
#
# export_predictions requires JSON input under benchmarks/.
# export_predictions and evaluate_predictions require CSV
# inputs/outputs under data/reviews/.
# ============================================================

BENCHMARK_STAGING_DIR = (
    REPO_ROOT / "benchmarks" / "results" / "interim" / "eval2"
).resolve()

REVIEW_STAGING_DIR = (REPO_ROOT / "data" / "reviews" / "interim" / "eval2").resolve()

REFERENCE_LABELS_STAGED = (
    REVIEW_STAGING_DIR / "reference_labels_eval_v1.csv"
).resolve()


# ============================================================
# Console table layout
# ============================================================

TABLE_COLUMNS = [
    ("ConfigID", "Config ID", 13, "left"),
    ("pHashThreshold", "pHash Threshold", 15, "center"),
    ("SSIMThreshold", "SSIM Threshold", 14, "center"),
    ("TP", "TP", 4, "center"),
    ("FP", "FP", 4, "center"),
    ("FN", "FN", 4, "center"),
    ("TN", "TN", 4, "center"),
    ("Precision", "Precision", 10, "center"),
    ("Recall", "Recall", 8, "center"),
    ("F1Score", "F1 Score", 9, "center"),
    ("Accuracy", "Accuracy", 10, "center"),
]


def build_environment() -> dict:
    """
    Create an environment in which Python can import the
    benchmarks package without requiring the user to export
    PYTHONPATH manually.
    """
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")

    if existing_pythonpath:
        env["PYTHONPATH"] = str(DEDUPE_PY_DIR) + os.pathsep + existing_pythonpath
    else:
        env["PYTHONPATH"] = str(DEDUPE_PY_DIR)

    return env


def run_cmd(
    cmd: list[str],
    log_file: Path,
) -> str:
    """Run one command and write its stdout and stderr to a log."""
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        env=build_environment(),
    )

    log_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    displayed_command = subprocess.list2cmdline(cmd)

    log_file.write_text(
        f"$ {displayed_command}\n\n"
        f"[STDOUT]\n{proc.stdout}\n\n"
        f"[STDERR]\n{proc.stderr}\n",
        encoding="utf-8",
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code "
            f"{proc.returncode}:\n"
            f"{displayed_command}\n\n"
            f"STDOUT:\n{proc.stdout}\n\n"
            f"STDERR:\n{proc.stderr}\n\n"
            f"See log: {log_file}"
        )

    return proc.stdout


def strip_ansi(text: str) -> str:
    """Remove ANSI colour sequences before parsing output."""
    ansi_pattern = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
    return ansi_pattern.sub("", text)


def parse_eval_metrics(text: str) -> dict:
    """Extract quality metrics from evaluate_predictions output."""
    clean_text = strip_ansi(text)

    patterns = {
        "PairsEvaluated": (r"\bPairs\s+evaluated\b\s*[:=]\s*(\d+)"),
        "TP": r"\bTP\b\s*[:=]\s*(\d+)",
        "FP": r"\bFP\b\s*[:=]\s*(\d+)",
        "FN": r"\bFN\b\s*[:=]\s*(\d+)",
        "TN": r"\bTN\b\s*[:=]\s*(\d+)",
        "Precision": (
            r"\bPrecision\b\s*[:=]\s*"
            r"([0-9]*\.?[0-9]+)"
        ),
        "Recall": (
            r"\bRecall\b\s*[:=]\s*"
            r"([0-9]*\.?[0-9]+)"
        ),
        "F1Score": (
            r"\bF1(?:\s*Score)?\b\s*[:=]\s*"
            r"([0-9]*\.?[0-9]+)"
        ),
        "Accuracy": (
            r"\bAccuracy\b\s*[:=]\s*"
            r"([0-9]*\.?[0-9]+)"
        ),
    }

    metrics = {}

    for name, pattern in patterns.items():
        match = re.search(
            pattern,
            clean_text,
            flags=re.IGNORECASE,
        )

        metrics[name] = match.group(1) if match else ""

    missing = [name for name, value in metrics.items() if value == ""]

    if missing:
        raise ValueError(
            "Could not extract the following metrics: "
            + ", ".join(missing)
            + "\n\nEvaluation output:\n"
            + clean_text
        )

    return metrics


def read_benchmark_counts(
    json_path: Path,
) -> dict:
    """Read Stage 2 and Stage 3 counts from benchmark JSON."""
    if not json_path.exists():
        raise FileNotFoundError(f"Benchmark JSON was not created: {json_path}")

    data = json.loads(json_path.read_text(encoding="utf-8"))

    detections = data.get("detections", {})

    return {
        "Stage2Candidates": detections.get(
            "stage2_candidate_pairs",
            "",
        ),
        "Stage3Verified": detections.get(
            "stage3_verified_pairs",
            "",
        ),
    }


def validate_inputs() -> None:
    """Validate the dataset and reference labels."""
    dataset_path = REPO_ROOT / "data" / DATASET_DIR

    if not dataset_path.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_path}")

    if not REFERENCE_LABELS_SOURCE.is_file():
        raise FileNotFoundError(
            f"Reference labels file does not exist: {REFERENCE_LABELS_SOURCE}"
        )


def prepare_directories() -> None:
    """Create final result and staging directories."""
    directories = [
        METRICS_DIR,
        LOGS_DIR,
        PREDICTIONS_DIR,
        REPORTS_DIR,
        BENCHMARK_STAGING_DIR,
        REVIEW_STAGING_DIR,
    ]

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


def prepare_reference_labels() -> None:
    """Copy labels into the path accepted by the evaluator."""
    shutil.copy2(
        REFERENCE_LABELS_SOURCE,
        REFERENCE_LABELS_STAGED,
    )


def format_table_cell(
    value,
    width: int,
    alignment: str,
) -> str:
    """Format one table cell without ANSI colour codes."""
    text = str(value)

    if alignment == "left":
        return text.ljust(width)

    if alignment == "right":
        return text.rjust(width)

    return text.center(width)


def table_separator() -> str:
    """Build the table's horizontal border."""
    return "+" + "+".join("-" * (width + 2) for _, _, width, _ in TABLE_COLUMNS) + "+"


def print_evaluation_table_header() -> None:
    """Print the title, top border and column headings."""
    header = (
        "| "
        + " | ".join(
            format_table_cell(
                label,
                width,
                alignment,
            )
            for _, label, width, alignment in TABLE_COLUMNS
        )
        + " |"
    )

    print(f"\n{Fore.GREEN}=== Interim Evaluation 2 Results ===")
    print(f"{Fore.BLUE}{table_separator()}")
    print(f"{Fore.CYAN}{header}")
    print(f"{Fore.BLUE}{table_separator()}")


def print_evaluation_table_row(
    row: dict,
    row_index: int,
) -> None:
    """
    Print one table row immediately after its configuration
    finishes.
    """
    display_row = dict(row)

    if row["ConfigID"] == "C1":
        display_row["ConfigID"] = "C1 (baseline)"

    line = (
        "| "
        + " | ".join(
            format_table_cell(
                display_row[key],
                width,
                alignment,
            )
            for key, _, width, alignment in TABLE_COLUMNS
        )
        + " |"
    )

    if row["ConfigID"] == "C1":
        row_colour = Fore.GREEN
    elif row_index % 2 == 0:
        row_colour = Fore.CYAN
    else:
        row_colour = Fore.WHITE

    print(
        f"{row_colour}{line}",
        flush=True,
    )


def print_evaluation_table_footer() -> None:
    """Print the table's closing border."""
    print(f"{Fore.BLUE}{table_separator()}")


def main() -> None:
    validate_inputs()
    prepare_directories()
    prepare_reference_labels()

    print(
        f"{Fore.GREEN}"
        "=== Running Interim Evaluation 2: "
        "Threshold Sensitivity / Error Analysis ==="
    )
    print(f"{Fore.YELLOW}Dataset:          {Fore.CYAN}data/{DATASET_DIR}")
    print(f"{Fore.YELLOW}Reference labels: {Fore.CYAN}{REFERENCE_LABELS_SOURCE}")

    rows = []

    # Print the table headings before any configurations run.
    print_evaluation_table_header()

    for row_index, (
        config_id,
        phash,
        ssim,
        run_tag,
    ) in enumerate(CONFIGS):
        # ----------------------------------------------------
        # Paths for this configuration
        # ----------------------------------------------------

        staged_benchmark_json = (BENCHMARK_STAGING_DIR / f"{run_tag}.json").resolve()

        final_benchmark_json = (REPORTS_DIR / f"{run_tag}.json").resolve()

        staged_predictions_csv = (
            REVIEW_STAGING_DIR / f"{run_tag}-stage3.csv"
        ).resolve()

        final_predictions_csv = (PREDICTIONS_DIR / f"{run_tag}-stage3.csv").resolve()

        # ----------------------------------------------------
        # 1. Run benchmark
        # ----------------------------------------------------

        benchmark_command = [
            PYTHON_EXE,
            "-m",
            "benchmarks.benchmark_pipeline",
            "--dir",
            DATASET_DIR,
            "--output",
            str(staged_benchmark_json),
            "--export-pairs",
            "--pair-limit",
            "500",
            "--phash-threshold",
            str(phash),
            "--ssim-threshold",
            str(ssim),
            "--run-tag",
            run_tag,
            "--no-timestamp",
        ]

        run_cmd(
            benchmark_command,
            LOGS_DIR / f"{config_id}_01_benchmark.log",
        )

        shutil.copy2(
            staged_benchmark_json,
            final_benchmark_json,
        )

        # ----------------------------------------------------
        # 2. Export Stage 3 predictions
        # ----------------------------------------------------

        export_command = [
            PYTHON_EXE,
            "-m",
            "benchmarks.tools.export_predictions",
            "--input",
            str(staged_benchmark_json),
            "--output",
            str(staged_predictions_csv),
            "--source",
            "stage3",
        ]

        run_cmd(
            export_command,
            LOGS_DIR / f"{config_id}_02_export.log",
        )

        shutil.copy2(
            staged_predictions_csv,
            final_predictions_csv,
        )

        # ----------------------------------------------------
        # 3. Evaluate predictions
        # ----------------------------------------------------

        evaluation_command = [
            PYTHON_EXE,
            "-m",
            "benchmarks.tools.evaluate_predictions",
            "--reference-labels",
            str(REFERENCE_LABELS_STAGED),
            "--predictions",
            str(staged_predictions_csv),
        ]

        evaluation_output = run_cmd(
            evaluation_command,
            LOGS_DIR / f"{config_id}_03_evaluate.log",
        )

        metrics = parse_eval_metrics(evaluation_output)

        counts = read_benchmark_counts(staged_benchmark_json)

        row = {
            "ConfigID": config_id,
            "RunTag": run_tag,
            "pHashThreshold": phash,
            "SSIMThreshold": ssim,
            "PairsEvaluated": (metrics["PairsEvaluated"]),
            "TP": metrics["TP"],
            "FP": metrics["FP"],
            "FN": metrics["FN"],
            "TN": metrics["TN"],
            "Precision": metrics["Precision"],
            "Recall": metrics["Recall"],
            "F1Score": metrics["F1Score"],
            "Accuracy": metrics["Accuracy"],
            "Stage2Candidates": (counts["Stage2Candidates"]),
            "Stage3Verified": (counts["Stage3Verified"]),
            "BenchmarkJSON": (final_benchmark_json.as_posix()),
            "PredictionsCSV": (final_predictions_csv.as_posix()),
        }

        rows.append(row)

        # Print this row immediately. The script does not wait
        # for all five configurations to finish.
        print_evaluation_table_row(
            row,
            row_index,
        )

    print_evaluation_table_footer()

    # ========================================================
    # Write summary CSV
    # ========================================================

    fieldnames = [
        "ConfigID",
        "RunTag",
        "pHashThreshold",
        "SSIMThreshold",
        "PairsEvaluated",
        "TP",
        "FP",
        "FN",
        "TN",
        "Precision",
        "Recall",
        "F1Score",
        "Accuracy",
        "Stage2Candidates",
        "Stage3Verified",
        "BenchmarkJSON",
        "PredictionsCSV",
    ]

    with SUMMARY_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{Fore.GREEN}Done.")
    print(f"{Fore.YELLOW}Summary CSV: {Fore.CYAN}{SUMMARY_CSV}")
    print(f"{Fore.YELLOW}Logs:        {Fore.CYAN}{LOGS_DIR}")
    print(f"{Fore.YELLOW}Reports:     {Fore.CYAN}{REPORTS_DIR}")
    print(f"{Fore.YELLOW}Predictions: {Fore.CYAN}{PREDICTIONS_DIR}")


if __name__ == "__main__":
    main()
