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

init(autoreset=True)

# ============================================================
# Interim Evaluation 3 (Robustness)
# - Runs each threshold configuration (C1-C5) on robustness dataset
# - Exports Stage 3 predictions
# - Evaluates predictions against robustness reference labels
# - Prints report-style detection/cost tables
# - Writes logs, reports, predictions and summary CSVs
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
DEDUPE_PY_DIR = REPO_ROOT / "services" / "dedupe-py"
PYTHON_EXE = str(Path(sys.executable).resolve())

DATASET_DIR = "robustness"

REFERENCE_LABELS_SOURCE = (
    REPO_ROOT / "data" / "labels" / "reference_labels_eval_v2_robustness.csv"
).resolve()

CONFIGS = [
    ("C1", 5, 0.85, "eval3-robustness-c1"),
    ("C2", 4, 0.85, "eval3-robustness-c2"),
    ("C3", 5, 0.90, "eval3-robustness-c3"),
    ("C4", 6, 0.85, "eval3-robustness-c4"),
    ("C5", 6, 0.90, "eval3-robustness-c5"),
]

# ============================================================
# Final result locations
# ============================================================

OUT_ROOT = (REPO_ROOT / "results" / "interim" / "eval3").resolve()

METRICS_DIR = OUT_ROOT / "metrics"
LOGS_DIR = OUT_ROOT / "logs"
PREDICTIONS_DIR = OUT_ROOT / "predictions"
REPORTS_DIR = OUT_ROOT / "reports"

DETECTION_SUMMARY_CSV = METRICS_DIR / "table_eval3_detection_summary.csv"
COST_SUMMARY_CSV = METRICS_DIR / "table_eval3_cost_summary.csv"

# ============================================================
# Staging locations for current path-safety rules
# ============================================================

BENCHMARK_STAGING_DIR = (
    REPO_ROOT / "benchmarks" / "results" / "interim" / "eval3"
).resolve()

REVIEW_STAGING_DIR = (REPO_ROOT / "data" / "reviews" / "interim" / "eval3").resolve()

REFERENCE_LABELS_STAGED = (
    REVIEW_STAGING_DIR / "reference_labels_eval_v2_robustness.csv"
).resolve()

# ============================================================
# Table: detection quality
# ============================================================

DETECTION_TABLE_COLUMNS = [
    ("ConfigID", "Config ID", 13, "left"),
    ("pHashThreshold", "pHash", 7, "center"),
    ("SSIMThreshold", "SSIM", 7, "center"),
    ("TP", "TP", 4, "center"),
    ("FP", "FP", 4, "center"),
    ("FN", "FN", 4, "center"),
    ("TN", "TN", 4, "center"),
    ("Precision", "Precision", 10, "center"),
    ("Recall", "Recall", 8, "center"),
    ("F1Score", "F1 Score", 9, "center"),
    ("Accuracy", "Accuracy", 10, "center"),
]

# ============================================================
# Table: computational cost
# ============================================================

COST_TABLE_COLUMNS = [
    ("ConfigID", "Config ID", 13, "left"),
    ("Stage1Time", "Stage 1 Time", 18, "center"),
    ("Stage2Time", "Stage 2 Time", 18, "center"),
    ("Stage3Time", "Stage 3 Time", 20, "center"),
    ("TotalTime", "Total Time", 19, "center"),
    ("PipelinePeakMemMB", "Peak RAM", 10, "center"),
    ("Stage2CandidatePairs", "S2 Pairs", 9, "center"),
    ("Stage3VerifiedPairs", "S3 Pairs", 9, "center"),
]


def build_environment() -> dict:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")

    if existing_pythonpath:
        env["PYTHONPATH"] = str(DEDUPE_PY_DIR) + os.pathsep + existing_pythonpath
    else:
        env["PYTHONPATH"] = str(DEDUPE_PY_DIR)

    return env


def run_cmd(cmd: list[str], log_file: Path) -> str:
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
    ansi_pattern = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
    return ansi_pattern.sub("", text)


def parse_eval_metrics(text: str) -> dict:
    clean_text = strip_ansi(text)

    patterns = {
        "PairsEvaluated": (r"\bPairs\s+evaluated\b\s*[:=]\s*(\d+)"),
        "TP": r"\bTP\b\s*[:=]\s*(\d+)",
        "FP": r"\bFP\b\s*[:=]\s*(\d+)",
        "FN": r"\bFN\b\s*[:=]\s*(\d+)",
        "TN": r"\bTN\b\s*[:=]\s*(\d+)",
        "Precision": (r"\bPrecision\b\s*[:=]\s*([0-9]*\.?[0-9]+)"),
        "Recall": (r"\bRecall\b\s*[:=]\s*([0-9]*\.?[0-9]+)"),
        "F1Score": (r"\bF1(?:\s*Score)?\b\s*[:=]\s*([0-9]*\.?[0-9]+)"),
        "Accuracy": (r"\bAccuracy\b\s*[:=]\s*([0-9]*\.?[0-9]+)"),
    }

    metrics = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, clean_text, flags=re.IGNORECASE)
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


def parse_benchmark_cost(json_path: Path) -> dict:
    if not json_path.exists():
        raise FileNotFoundError(f"Benchmark JSON was not created: {json_path}")

    data = json.loads(json_path.read_text(encoding="utf-8"))

    def get_value(*keys, default=""):
        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current

    def number(value, decimal_places=2) -> str:
        try:
            return f"{float(value):.{decimal_places}f}"
        except (TypeError, ValueError):
            return ""

    def stage_metric(stage: str, metric: str, statistic: str):
        return get_value("stages", stage, metric, statistic)

    return {
        "Stage1TimeMsMean": number(stage_metric("stage1_sha256", "time_ms", "mean")),
        "Stage1TimeMsStd": number(stage_metric("stage1_sha256", "time_ms", "std_dev")),
        "Stage2TimeMsMean": number(stage_metric("stage2_phash", "time_ms", "mean")),
        "Stage2TimeMsStd": number(stage_metric("stage2_phash", "time_ms", "std_dev")),
        "Stage3TimeMsMean": number(stage_metric("stage3_ssim", "time_ms", "mean")),
        "Stage3TimeMsStd": number(stage_metric("stage3_ssim", "time_ms", "std_dev")),
        "TotalTimeMsMean": number(get_value("total_pipeline_time_ms", "mean")),
        "TotalTimeMsStd": number(get_value("total_pipeline_time_ms", "std_dev")),
        "PipelinePeakMemMB": number(get_value("total_pipeline_peak_ram_mb")),
        "Stage2CandidatePairs": get_value("detections", "stage2_candidate_pairs"),
        "Stage3VerifiedPairs": get_value("detections", "stage3_verified_pairs"),
    }


def validate_inputs() -> None:
    dataset_path = REPO_ROOT / "data" / DATASET_DIR
    if not dataset_path.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_path}")

    if not REFERENCE_LABELS_SOURCE.is_file():
        raise FileNotFoundError(
            f"Reference labels file does not exist: {REFERENCE_LABELS_SOURCE}"
        )


def prepare_directories() -> None:
    directories = [
        METRICS_DIR,
        LOGS_DIR,
        PREDICTIONS_DIR,
        REPORTS_DIR,
        BENCHMARK_STAGING_DIR,
        REVIEW_STAGING_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def prepare_reference_labels() -> None:
    shutil.copy2(REFERENCE_LABELS_SOURCE, REFERENCE_LABELS_STAGED)


def format_table_cell(value, width: int, alignment: str) -> str:
    text = str(value)
    if alignment == "left":
        return text.ljust(width)
    if alignment == "right":
        return text.rjust(width)
    return text.center(width)


def build_table_separator(columns: list[tuple]) -> str:
    return "+" + "+".join("-" * (width + 2) for _, _, width, _ in columns) + "+"


def print_table_header(title: str, columns: list[tuple]) -> None:
    header = (
        "| "
        + " | ".join(
            format_table_cell(label, width, alignment)
            for _, label, width, alignment in columns
        )
        + " |"
    )
    separator = build_table_separator(columns)

    print(f"\n{Fore.GREEN}{title}")
    print(f"{Fore.BLUE}{separator}")
    print(f"{Fore.CYAN}{header}")
    print(f"{Fore.BLUE}{separator}")


def print_table_row(row: dict, row_index: int, columns: list[tuple]) -> None:
    display_row = dict(row)
    if row["ConfigID"] == "C1":
        display_row["ConfigID"] = "C1 (baseline)"

    line = (
        "| "
        + " | ".join(
            format_table_cell(display_row[key], width, alignment)
            for key, _, width, alignment in columns
        )
        + " |"
    )

    if row["ConfigID"] == "C1":
        row_colour = Fore.GREEN
    elif row_index % 2 == 0:
        row_colour = Fore.CYAN
    else:
        row_colour = Fore.WHITE

    print(f"{row_colour}{line}", flush=True)


def print_table_footer(columns: list[tuple]) -> None:
    print(f"{Fore.BLUE}{build_table_separator(columns)}")


def write_detection_summary(rows: list[dict]) -> None:
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
        "BenchmarkJSON",
        "PredictionsCSV",
    ]

    with DETECTION_SUMMARY_CSV.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_cost_summary(rows: list[dict]) -> None:
    fieldnames = [
        "ConfigID",
        "RunTag",
        "pHashThreshold",
        "SSIMThreshold",
        "Stage1TimeMsMean",
        "Stage1TimeMsStd",
        "Stage2TimeMsMean",
        "Stage2TimeMsStd",
        "Stage3TimeMsMean",
        "Stage3TimeMsStd",
        "TotalTimeMsMean",
        "TotalTimeMsStd",
        "PipelinePeakMemMB",
        "Stage2CandidatePairs",
        "Stage3VerifiedPairs",
        "BenchmarkJSON",
    ]

    csv_rows = [{field: row.get(field, "") for field in fieldnames} for row in rows]

    with COST_SUMMARY_CSV.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)


def main() -> None:
    validate_inputs()
    prepare_directories()
    prepare_reference_labels()

    print(f"{Fore.GREEN}=== Running Interim Evaluation 3: Robustness ===")
    print(f"{Fore.YELLOW}Dataset:          {Fore.CYAN}data/{DATASET_DIR}")
    print(f"{Fore.YELLOW}Reference labels: {Fore.CYAN}{REFERENCE_LABELS_SOURCE}")

    detection_rows = []
    cost_rows = []

    print_table_header(
        "Table A - Detection Performance Across Threshold Configurations (Eval 3)",
        DETECTION_TABLE_COLUMNS,
    )

    for row_index, (config_id, phash, ssim, run_tag) in enumerate(CONFIGS):
        staged_benchmark_json = (BENCHMARK_STAGING_DIR / f"{run_tag}.json").resolve()
        final_benchmark_json = (REPORTS_DIR / f"{run_tag}.json").resolve()

        staged_predictions_csv = (
            REVIEW_STAGING_DIR / f"{run_tag}-stage3.csv"
        ).resolve()
        final_predictions_csv = (PREDICTIONS_DIR / f"{run_tag}-stage3.csv").resolve()

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
            "5000",
            "--phash-threshold",
            str(phash),
            "--ssim-threshold",
            str(ssim),
            "--run-tag",
            run_tag,
            "--no-timestamp",
        ]

        run_cmd(benchmark_command, LOGS_DIR / f"{config_id}_01_benchmark.log")
        shutil.copy2(staged_benchmark_json, final_benchmark_json)

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

        run_cmd(export_command, LOGS_DIR / f"{config_id}_02_export.log")
        shutil.copy2(staged_predictions_csv, final_predictions_csv)

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
            evaluation_command, LOGS_DIR / f"{config_id}_03_evaluate.log"
        )

        quality = parse_eval_metrics(evaluation_output)
        cost = parse_benchmark_cost(staged_benchmark_json)

        detection_row = {
            "ConfigID": config_id,
            "RunTag": run_tag,
            "pHashThreshold": phash,
            "SSIMThreshold": ssim,
            "PairsEvaluated": quality["PairsEvaluated"],
            "TP": quality["TP"],
            "FP": quality["FP"],
            "FN": quality["FN"],
            "TN": quality["TN"],
            "Precision": quality["Precision"],
            "Recall": quality["Recall"],
            "F1Score": quality["F1Score"],
            "Accuracy": quality["Accuracy"],
            "BenchmarkJSON": final_benchmark_json.as_posix(),
            "PredictionsCSV": final_predictions_csv.as_posix(),
        }

        detection_rows.append(detection_row)
        print_table_row(detection_row, row_index, DETECTION_TABLE_COLUMNS)

        cost_row = {
            "ConfigID": config_id,
            "RunTag": run_tag,
            "pHashThreshold": phash,
            "SSIMThreshold": ssim,
            **cost,
            "BenchmarkJSON": final_benchmark_json.as_posix(),
        }

        cost_rows.append(cost_row)

    print_table_footer(DETECTION_TABLE_COLUMNS)

    print_table_header(
        "Table B - Computational Cost by Configuration (Eval 3)",
        COST_TABLE_COLUMNS,
    )

    for row_index, row in enumerate(cost_rows):
        display_row = {
            **row,
            "Stage1Time": f"{row['Stage1TimeMsMean']} +/- {row['Stage1TimeMsStd']}",
            "Stage2Time": f"{row['Stage2TimeMsMean']} +/- {row['Stage2TimeMsStd']}",
            "Stage3Time": f"{row['Stage3TimeMsMean']} +/- {row['Stage3TimeMsStd']}",
            "TotalTime": f"{row['TotalTimeMsMean']} +/- {row['TotalTimeMsStd']}",
        }

        print_table_row(display_row, row_index, COST_TABLE_COLUMNS)

    print_table_footer(COST_TABLE_COLUMNS)

    write_detection_summary(detection_rows)
    write_cost_summary(cost_rows)

    print(f"\n{Fore.GREEN}Done.")
    print(f"{Fore.YELLOW}Detection summary: {Fore.CYAN}{DETECTION_SUMMARY_CSV}")
    print(f"{Fore.YELLOW}Cost summary:      {Fore.CYAN}{COST_SUMMARY_CSV}")
    print(f"{Fore.YELLOW}Logs:              {Fore.CYAN}{LOGS_DIR}")
    print(f"{Fore.YELLOW}Reports:           {Fore.CYAN}{REPORTS_DIR}")
    print(f"{Fore.YELLOW}Predictions:       {Fore.CYAN}{PREDICTIONS_DIR}")


if __name__ == "__main__":
    main()
