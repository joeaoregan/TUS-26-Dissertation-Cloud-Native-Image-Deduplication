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
# - Runs benchmark for each threshold configuration
# - Exports Stage 3 predicted duplicate pairs
# - Evaluates predictions against reference labels
# - Writes evaluation logs and summary CSV
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

# Final Eval 2 results
OUT_ROOT = (REPO_ROOT / "results" / "interim" / "eval2").resolve()

METRICS_DIR = OUT_ROOT / "metrics"
LOGS_DIR = OUT_ROOT / "logs"
PREDICTIONS_DIR = OUT_ROOT / "predictions"
REPORTS_DIR = OUT_ROOT / "reports"

SUMMARY_CSV = METRICS_DIR / "table_eval2_summary.csv"

# ------------------------------------------------------------
# Tool staging directories
#
# export_predictions requires its JSON input under:
#   <repo>/benchmarks/
#
# export_predictions and evaluate_predictions require CSV files
# under:
#   <repo>/data/reviews/
# ------------------------------------------------------------

BENCHMARK_STAGING_DIR = (
    REPO_ROOT / "benchmarks" / "results" / "interim" / "eval2"
).resolve()

REVIEW_STAGING_DIR = (REPO_ROOT / "data" / "reviews" / "interim" / "eval2").resolve()

REFERENCE_LABELS_STAGED = (
    REVIEW_STAGING_DIR / "reference_labels_eval_v1.csv"
).resolve()


def build_environment() -> dict:
    """Create a subprocess environment that can import benchmarks."""
    env = os.environ.copy()

    existing_pythonpath = env.get("PYTHONPATH")

    if existing_pythonpath:
        env["PYTHONPATH"] = str(DEDUPE_PY_DIR) + os.pathsep + existing_pythonpath
    else:
        env["PYTHONPATH"] = str(DEDUPE_PY_DIR)

    return env


def run_cmd(cmd: list[str], log_file: Path) -> str:
    """Run a command from the repository root and capture its output."""
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        env=build_environment(),
    )

    log_file.parent.mkdir(parents=True, exist_ok=True)

    displayed_command = subprocess.list2cmdline(cmd)

    log_file.write_text(
        f"$ {displayed_command}\n\n"
        f"[STDOUT]\n{proc.stdout}\n\n"
        f"[STDERR]\n{proc.stderr}\n",
        encoding="utf-8",
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {proc.returncode}:\n"
            f"{displayed_command}\n\n"
            f"STDOUT:\n{proc.stdout}\n\n"
            f"STDERR:\n{proc.stderr}\n\n"
            f"See log: {log_file}"
        )

    return proc.stdout


def strip_ansi(text: str) -> str:
    """Remove ANSI colour codes before parsing captured output."""
    ansi_pattern = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
    return ansi_pattern.sub("", text)


def parse_eval_metrics(text: str) -> dict:
    """Extract quality metrics printed by evaluate_predictions."""
    clean_text = strip_ansi(text)

    patterns = {
        "PairsEvaluated": (r"\bPairs\s+evaluated\b\s*[:=]\s*(\d+)"),
        "TP": r"\bTP\b\s*[:=]\s*(\d+)",
        "FP": r"\bFP\b\s*[:=]\s*(\d+)",
        "FN": r"\bFN\b\s*[:=]\s*(\d+)",
        "TN": r"\bTN\b\s*[:=]\s*(\d+)",
        "Precision": (r"\bPrecision\b\s*[:=]\s*([0-9]*\.?[0-9]+)"),
        "Recall": (r"\bRecall\b\s*[:=]\s*([0-9]*\.?[0-9]+)"),
        "F1Score": (
            r"\bF1(?:\s*Score)?\b\s*[:=]\s*"
            r"([0-9]*\.?[0-9]+)"
        ),
        "Accuracy": (r"\bAccuracy\b\s*[:=]\s*([0-9]*\.?[0-9]+)"),
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
            "Could not extract the following evaluation metrics: "
            + ", ".join(missing)
            + "\n\nEvaluation output:\n"
            + clean_text
        )

    return metrics


def read_benchmark_counts(json_path: Path) -> dict:
    """Read detection counts from the current benchmark JSON schema."""
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
    """Check that required inputs exist before running benchmarks."""
    dataset_path = REPO_ROOT / "data" / DATASET_DIR

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_path}")

    if not REFERENCE_LABELS_SOURCE.exists():
        raise FileNotFoundError(
            f"Reference labels file does not exist: {REFERENCE_LABELS_SOURCE}"
        )


def prepare_directories() -> None:
    """Create result and staging directories."""
    for directory in [
        METRICS_DIR,
        LOGS_DIR,
        PREDICTIONS_DIR,
        REPORTS_DIR,
        BENCHMARK_STAGING_DIR,
        REVIEW_STAGING_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def prepare_reference_labels() -> None:
    """
    Copy reference labels into data/reviews so that the evaluation
    tool's path-safety policy accepts them.
    """
    shutil.copy2(
        REFERENCE_LABELS_SOURCE,
        REFERENCE_LABELS_STAGED,
    )


def print_evaluation(
    config_id: str,
    phash: int,
    ssim: float,
    metrics: dict,
    counts: dict,
) -> None:
    """Print a compact result for one configuration."""
    print(
        f"{config_id}: "
        f"pHash={phash}, "
        f"SSIM={ssim}, "
        f"TP={metrics['TP']}, "
        f"FP={metrics['FP']}, "
        f"FN={metrics['FN']}, "
        f"TN={metrics['TN']}, "
        f"Precision={metrics['Precision']}, "
        f"Recall={metrics['Recall']}, "
        f"F1={metrics['F1Score']}, "
        f"Accuracy={metrics['Accuracy']}, "
        f"S2 candidates={counts['Stage2Candidates']}, "
        f"S3 verified={counts['Stage3Verified']}"
    )


def main() -> None:
    validate_inputs()
    prepare_directories()
    prepare_reference_labels()

    print(
        f"{Fore.GREEN}=== Running Interim Evaluation 2: Threshold Sensitivity / Error Analysis ==="
    )
    print(f"Dataset:          data/{DATASET_DIR}")
    print(f"Reference labels: {REFERENCE_LABELS_SOURCE}")

    rows = []

    for config_id, phash, ssim, run_tag in CONFIGS:
        print(f"\n=== {config_id}: pHash={phash}, SSIM={ssim} ===")

        # The exporter only accepts JSON input from benchmarks/.
        staged_benchmark_json = (BENCHMARK_STAGING_DIR / f"{run_tag}.json").resolve()

        # Final copy retained with the Eval 2 results.
        final_benchmark_json = (REPORTS_DIR / f"{run_tag}.json").resolve()

        # The exporter/evaluator only accepts CSVs under data/reviews/.
        staged_predictions_csv = (
            REVIEW_STAGING_DIR / f"{run_tag}-stage3.csv"
        ).resolve()

        # Final copy retained with the Eval 2 results.
        final_predictions_csv = (PREDICTIONS_DIR / f"{run_tag}-stage3.csv").resolve()

        # ----------------------------------------------------
        # 1. Run benchmark and export pair details to JSON
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
        # 2. Export Stage 3 verified pairs to predictions CSV
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
        # 3. Evaluate predictions against reference labels
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

        print_evaluation(
            config_id,
            phash,
            ssim,
            metrics,
            counts,
        )

        rows.append(
            {
                "ConfigID": config_id,
                "RunTag": run_tag,
                "pHashThreshold": phash,
                "SSIMThreshold": ssim,
                "PairsEvaluated": metrics["PairsEvaluated"],
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
        )

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

    print("\nDone.")
    print(f"Summary CSV: {SUMMARY_CSV}")
    print(f"Logs:        {LOGS_DIR}")
    print(f"Reports:     {REPORTS_DIR}")
    print(f"Predictions: {PREDICTIONS_DIR}")


if __name__ == "__main__":
    main()
