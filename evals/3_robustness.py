#!/usr/bin/env python3

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from colorama import Fore, init

init(autoreset=True)

# ============================================================
# Interim Evaluation 3 (Robustness)
# - Runs threshold configs from evals/common_config.json
# - Supports multiple subset sizes (e.g. t5 t10) in one run
# - Materialises subsets from data/base into data/robustness/<size>
# - DEFAULT: cleans up materialised subsets after each size run
# - Exports Stage 3 predictions
# - Evaluates predictions against robustness reference labels
# - Prints report-style detection/cost tables
# - Writes logs, reports, predictions and summary CSVs per size
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
DEDUPE_PY_DIR = REPO_ROOT / "services" / "dedupe-py"
PYTHON_EXE = str(Path(sys.executable).resolve())

MASTER_DIR = REPO_ROOT / "data" / "base"
ROBUSTNESS_ROOT = REPO_ROOT / "data" / "robustness"

# Default (fallback) robustness labels (full set)
REFERENCE_LABELS_SOURCE = (
    REPO_ROOT / "data" / "labels" / "reference_labels_eval_v2_robustness.csv"
).resolve()

# Optional size-specific labels (recommended for tiny subsets)
# If a size key exists here and file exists, it will be used instead of full labels.
SIZE_LABELS = {
    "t5": REPO_ROOT / "data" / "labels" / "reference_labels_eval_v2_robustness_t5.csv",
    "t10": REPO_ROOT
    / "data"
    / "labels"
    / "reference_labels_eval_v2_robustness_t10.csv",
}

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


def load_common_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "common_config.json"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Missing config file: {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Interim Eval 3 (robustness)")
    p.add_argument(
        "--sizes",
        nargs="+",
        required=True,
        help="Subset size keys from common_config.json (e.g. --sizes t5 t10)",
    )
    p.add_argument(
        "--pair-limit",
        default=None,
        help="Override pair-limit from common_config.json",
    )
    p.add_argument(
        "--rebuild-subsets",
        action="store_true",
        help="Force rebuild subset folders even if they already exist",
    )
    p.add_argument(
        "--keep-subsets",
        action="store_true",
        help="Keep materialised subset folders (default is cleanup after each size run)",
    )
    return p.parse_args()


def build_configs(cfg: dict) -> list[tuple]:
    threshold_configs = cfg.get("threshold_configs", [])
    enabled = [c for c in threshold_configs if c.get("enabled", True)]
    if not enabled:
        raise ValueError("No enabled threshold_configs in common_config.json")

    configs = []
    for c in enabled:
        for required in ("id", "phash", "ssim", "tag"):
            if required not in c:
                raise ValueError(f"Missing '{required}' in threshold config: {c}")
        configs.append((c["id"], int(c["phash"]), float(c["ssim"]), c["tag"]))
    return configs


def build_environment() -> dict:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(DEDUPE_PY_DIR) + (
        os.pathsep + existing_pythonpath if existing_pythonpath else ""
    )
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
        check=False,
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
        "PairsEvaluated": r"\bPairs\s+evaluated\b\s*[:=]\s*(\d+)",
        "TP": r"\bTP\b\s*[:=]\s*(\d+)",
        "FP": r"\bFP\b\s*[:=]\s*(\d+)",
        "FN": r"\bFN\b\s*[:=]\s*(\d+)",
        "TN": r"\bTN\b\s*[:=]\s*(\d+)",
        "Precision": r"\bPrecision\b\s*[:=]\s*([0-9]*\.?[0-9]+)",
        "Recall": r"\bRecall\b\s*[:=]\s*([0-9]*\.?[0-9]+)",
        "F1Score": r"\bF1(?:\s*Score)?\b\s*[:=]\s*([0-9]*\.?[0-9]+)",
        "Accuracy": r"\bAccuracy\b\s*[:=]\s*([0-9]*\.?[0-9]+)",
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
            format_table_cell(display_row.get(key, ""), width, alignment)
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


def materialise_subset(size_key: str, subset_sizes: dict, rebuild: bool) -> str:
    if size_key not in subset_sizes:
        valid = ", ".join(subset_sizes.keys())
        raise ValueError(f"Unknown size '{size_key}'. Valid sizes: {valid}")

    count = int(subset_sizes[size_key])
    target_dir = ROBUSTNESS_ROOT / size_key

    if not MASTER_DIR.is_dir():
        raise FileNotFoundError(f"Missing master directory: {MASTER_DIR}")

    files = sorted(
        p
        for p in MASTER_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpeg", ".jpg", ".png"}
    )

    if len(files) < count:
        raise ValueError(
            f"Need {count} files for size '{size_key}', found {len(files)} in {MASTER_DIR}"
        )

    if target_dir.exists() and not rebuild:
        existing = sorted(
            p
            for p in target_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpeg", ".jpg", ".png"}
        )
        if len(existing) == count:
            return f"robustness/{size_key}"

    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    for p in files[:count]:
        shutil.copy2(p, target_dir / p.name)

    return f"robustness/{size_key}"


def cleanup_subset(size_key: str) -> None:
    target_dir = ROBUSTNESS_ROOT / size_key
    if target_dir.exists():
        shutil.rmtree(target_dir)


def resolve_labels_for_size(size_key: str) -> Path:
    candidate = SIZE_LABELS.get(size_key)
    if candidate and candidate.is_file():
        return candidate.resolve()
    return REFERENCE_LABELS_SOURCE


def write_detection_summary(path: Path, rows: list[dict]) -> None:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_cost_summary(path: Path, rows: list[dict]) -> None:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)


def run_for_size(
    size_key: str, dataset_dir: str, configs: list[tuple], pair_limit: str
) -> None:
    size_start = time.perf_counter()

    out_root = (REPO_ROOT / "results" / "interim" / f"eval3_{size_key}").resolve()
    metrics_dir = out_root / "metrics"
    logs_dir = out_root / "logs"
    predictions_dir = out_root / "predictions"
    reports_dir = out_root / "reports"

    detection_summary_csv = (
        metrics_dir / f"table_eval3_{size_key}_detection_summary.csv"
    )
    cost_summary_csv = metrics_dir / f"table_eval3_{size_key}_cost_summary.csv"

    benchmark_staging_dir = (
        REPO_ROOT / "benchmarks" / "results" / "interim" / f"eval3_{size_key}"
    ).resolve()
    review_staging_dir = (
        REPO_ROOT / "data" / "reviews" / "interim" / f"eval3_{size_key}"
    ).resolve()

    labels_source = resolve_labels_for_size(size_key)
    reference_labels_staged = review_staging_dir / labels_source.name

    for d in [
        metrics_dir,
        logs_dir,
        predictions_dir,
        reports_dir,
        benchmark_staging_dir,
        review_staging_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    if not labels_source.is_file():
        raise FileNotFoundError(
            f"Reference labels file does not exist: {labels_source}"
        )
    shutil.copy2(labels_source, reference_labels_staged)

    print(
        f"\n{Fore.GREEN}=== Running Interim Evaluation 3: Robustness ({size_key.upper()}) ==="
    )
    print(f"{Fore.YELLOW}Dataset:          {Fore.CYAN}data/{dataset_dir}")
    print(f"{Fore.YELLOW}Reference labels: {Fore.CYAN}{labels_source}")
    print(f"{Fore.YELLOW}Pair limit:       {Fore.CYAN}{pair_limit}")

    detection_rows = []
    cost_rows = []

    print_table_header(
        f"Table A - Detection Performance Across Threshold Configurations (Eval 3, {size_key.upper()})",
        DETECTION_TABLE_COLUMNS,
    )

    for row_index, (config_id, phash, ssim, tag) in enumerate(configs):
        run_tag = f"eval3-{size_key}-{config_id.lower()}-{tag}"

        staged_benchmark_json = benchmark_staging_dir / f"{run_tag}.json"
        final_benchmark_json = reports_dir / f"{run_tag}.json"

        staged_predictions_csv = review_staging_dir / f"{run_tag}-stage3.csv"
        final_predictions_csv = predictions_dir / f"{run_tag}-stage3.csv"

        benchmark_command = [
            PYTHON_EXE,
            "-m",
            "benchmarks.benchmark_pipeline",
            "--dir",
            dataset_dir,
            "--output",
            str(staged_benchmark_json),
            "--export-pairs",
            "--pair-limit",
            str(pair_limit),
            "--phash-threshold",
            str(phash),
            "--ssim-threshold",
            str(ssim),
            "--run-tag",
            run_tag,
            "--no-timestamp",
        ]
        run_cmd(benchmark_command, logs_dir / f"{config_id}_01_benchmark.log")
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
        run_cmd(export_command, logs_dir / f"{config_id}_02_export.log")
        shutil.copy2(staged_predictions_csv, final_predictions_csv)

        evaluation_command = [
            PYTHON_EXE,
            "-m",
            "benchmarks.tools.evaluate_predictions",
            "--reference-labels",
            str(reference_labels_staged),
            "--predictions",
            str(staged_predictions_csv),
        ]
        evaluation_output = run_cmd(
            evaluation_command, logs_dir / f"{config_id}_03_evaluate.log"
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
        f"Table B - Computational Cost by Configuration (Eval 3, {size_key.upper()})",
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

    write_detection_summary(detection_summary_csv, detection_rows)
    write_cost_summary(cost_summary_csv, cost_rows)

    print(
        f"\n{Fore.GREEN}Completed size {size_key.upper()} in {(time.perf_counter() - size_start) / 60:.2f} min"
    )
    print(f"{Fore.YELLOW}Detection summary: {Fore.CYAN}{detection_summary_csv}")
    print(f"{Fore.YELLOW}Cost summary:      {Fore.CYAN}{cost_summary_csv}")
    print(f"{Fore.YELLOW}Logs:              {Fore.CYAN}{logs_dir}")
    print(f"{Fore.YELLOW}Reports:           {Fore.CYAN}{reports_dir}")
    print(f"{Fore.YELLOW}Predictions:       {Fore.CYAN}{predictions_dir}")


def main() -> None:
    cfg = load_common_config()
    args = parse_args()

    subset_sizes = cfg.get("subset_sizes", {})
    if not subset_sizes:
        raise ValueError("Missing subset_sizes in common_config.json")

    for s in args.sizes:
        if s not in subset_sizes:
            raise ValueError(
                f"Unknown size '{s}'. Valid sizes: {', '.join(subset_sizes.keys())}"
            )

    configs = build_configs(cfg)
    pair_limits = cfg.get("pair_limits", {})
    effective_pair_limit = (
        str(args.pair_limit)
        if args.pair_limit is not None
        else str(pair_limits.get("eval3", 5000))
    )

    overall_start = time.perf_counter()

    print(f"{Fore.GREEN}=== Running Interim Evaluation 3: Robustness ===")
    print(f"{Fore.YELLOW}Master dataset: {Fore.CYAN}{MASTER_DIR}")
    print(
        f"{Fore.YELLOW}Sizes to run:   {Fore.CYAN}{', '.join(s.upper() for s in args.sizes)}"
    )
    print(f"{Fore.YELLOW}Pair limit:     {Fore.CYAN}{effective_pair_limit}")
    print(f"{Fore.YELLOW}Configs:        {Fore.CYAN}{', '.join(c[0] for c in configs)}")
    print(
        f"{Fore.YELLOW}Subset cleanup: {Fore.CYAN}"
        + ("OFF (--keep-subsets)" if args.keep_subsets else "ON (default)")
    )

    for size_key in args.sizes:
        dataset_dir = materialise_subset(size_key, subset_sizes, args.rebuild_subsets)
        try:
            run_for_size(
                size_key=size_key,
                dataset_dir=dataset_dir,
                configs=configs,
                pair_limit=effective_pair_limit,
            )
        finally:
            if not args.keep_subsets:
                cleanup_subset(size_key)

    print(f"\n{Fore.GREEN}All requested sizes complete.")
    print(
        f"{Fore.YELLOW}Total runtime: {Fore.CYAN}{(time.perf_counter() - overall_start) / 60:.2f} min"
    )


if __name__ == "__main__":
    main()
