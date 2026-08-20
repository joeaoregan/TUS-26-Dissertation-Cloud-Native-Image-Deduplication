#!/usr/bin/env python3

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from colorama import Fore, init

init(autoreset=True)  # colorama: auto clear colours after printing

# ============================================================
# Interim Evaluation 1 (Performance/Efficiency)
# - Runs benchmark pipeline for selected threshold configs
# - Captures benchmark logs
# - Writes compact metrics summary CSV
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
DEDUPE_PY_DIR = REPO_ROOT / "services" / "dedupe-py"
PYTHON_EXE = str(Path(sys.executable).resolve())

DATASET_DIR = "dedupe_test_100"

# Keep configurations aligned with Eval 2 table labels.
CONFIGS = [
    ("C1", 5, 0.85, "threshold-tuning-baseline-phash5-ssim085"),
    ("C2", 4, 0.85, "threshold-tuning-phash4-ssim085"),
    ("C3", 5, 0.90, "threshold-tuning-phash5-ssim090"),
    ("C4", 6, 0.85, "threshold-tuning-phash6-ssim085"),
    ("C5", 6, 0.90, "threshold-tuning-phash6-ssim090"),
]

OUT_ROOT = (REPO_ROOT / "results" / "interim" / "eval1").resolve()
METRICS_DIR = OUT_ROOT / "metrics"
LOGS_DIR = OUT_ROOT / "logs"
REPORTS_DIR = OUT_ROOT / "reports"

SUMMARY_CSV = METRICS_DIR / "table_eval1_summary.csv"


def run_cmd(cmd: list[str], log_file: Path) -> str:
    """
    Run a command from the repository root and capture its output.

    services/dedupe-py is added to PYTHONPATH so that
    `python -m benchmarks.benchmark_pipeline` works without requiring
    the caller to export PYTHONPATH manually.
    """
    env = os.environ.copy()

    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        env["PYTHONPATH"] = str(DEDUPE_PY_DIR) + os.pathsep + existing_pythonpath
    else:
        env["PYTHONPATH"] = str(DEDUPE_PY_DIR)

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        env=env,
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
            f"STDERR:\n{proc.stderr}\n"
            f"See log: {log_file}"
        )

    return proc.stdout


def parse_benchmark_json(json_path: Path) -> dict:
    """Extract the Eval 1 summary fields from a benchmark JSON report."""
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

    def number(value, decimal_places=2):
        try:
            return f"{float(value):.{decimal_places}f}"
        except (TypeError, ValueError):
            return ""

    def stage_metric(stage, metric, statistic):
        return get_value("stages", stage, metric, statistic)

    resolution_min = get_value(
        "dataset_profile",
        "resolution_range",
        "min",
    )
    resolution_max = get_value(
        "dataset_profile",
        "resolution_range",
        "max",
    )

    if resolution_min and resolution_max:
        resolution_range = f"{resolution_min}->{resolution_max}"
    else:
        resolution_range = ""

    return {
        "Stage1TimeMsMean": number(stage_metric("stage1_sha256", "time_ms", "mean")),
        "Stage1TimeMsStd": number(stage_metric("stage1_sha256", "time_ms", "std_dev")),
        "Stage2TimeMsMean": number(stage_metric("stage2_phash", "time_ms", "mean")),
        "Stage2TimeMsStd": number(stage_metric("stage2_phash", "time_ms", "std_dev")),
        "Stage3TimeMsMean": number(stage_metric("stage3_ssim", "time_ms", "mean")),
        "Stage3TimeMsStd": number(stage_metric("stage3_ssim", "time_ms", "std_dev")),
        "TotalTimeMsMean": number(get_value("total_pipeline_time_ms", "mean")),
        "TotalTimeMsStd": number(get_value("total_pipeline_time_ms", "std_dev")),
        "Stage1MemMBMean": number(stage_metric("stage1_sha256", "peak_ram_mb", "mean")),
        "Stage1MemMBStd": number(
            stage_metric("stage1_sha256", "peak_ram_mb", "std_dev")
        ),
        "Stage2MemMBMean": number(stage_metric("stage2_phash", "peak_ram_mb", "mean")),
        "Stage2MemMBStd": number(
            stage_metric("stage2_phash", "peak_ram_mb", "std_dev")
        ),
        "Stage3MemMBMean": number(stage_metric("stage3_ssim", "peak_ram_mb", "mean")),
        "Stage3MemMBStd": number(stage_metric("stage3_ssim", "peak_ram_mb", "std_dev")),
        "PipelinePeakMemMB": number(get_value("total_pipeline_peak_ram_mb")),
        "Stage1ExactGroups": get_value(
            "detections",
            "stage1_exact_duplicate_groups",
        ),
        "Stage1RedundantFiles": get_value(
            "detections",
            "stage1_redundant_files",
        ),
        "Stage2CandidatePairs": get_value(
            "detections",
            "stage2_candidate_pairs",
        ),
        "Stage3VerifiedPairs": get_value(
            "detections",
            "stage3_verified_pairs",
        ),
        "DatasetTotalFiles": get_value(
            "dataset_profile",
            "total_files",
        ),
        "DatasetTotalSizeMB": number(get_value("dataset_profile", "total_size_mb")),
        "DatasetResolutionRange": resolution_range,
    }


def main():
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"{Fore.YELLOW}Using Python: {Fore.CYAN}{PYTHON_EXE}")
    print(f"{Fore.YELLOW}Repository:   {Fore.CYAN}{REPO_ROOT}")
    print(f"{Fore.YELLOW}Dataset:      {Fore.CYAN}data/{DATASET_DIR}")

    rows = []

    for config_id, phash, ssim, run_tag in CONFIGS:
        print(f"\n{Fore.GREEN}=== {config_id}: pHash={phash}, SSIM={ssim} ===")

        # benchmark_json = (REPO_ROOT / "logs" / f"{run_tag}.json").resolve()
        benchmark_json = (REPORTS_DIR / f"{run_tag}.json").resolve()

        benchmark_command = [
            PYTHON_EXE,
            "-m",
            "benchmarks.benchmark_pipeline",
            "--dir",
            DATASET_DIR,
            "--output",
            str(benchmark_json),
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
            LOGS_DIR / f"{config_id}_benchmark.log",
        )

        parsed = parse_benchmark_json(benchmark_json)

        rows.append(
            {
                "ConfigID": config_id,
                "RunTag": run_tag,
                "pHashThreshold": phash,
                "SSIMThreshold": ssim,
                **parsed,
                "BenchmarkJSON": benchmark_json.as_posix(),
            }
        )

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
        "Stage1MemMBMean",
        "Stage1MemMBStd",
        "Stage2MemMBMean",
        "Stage2MemMBStd",
        "Stage3MemMBMean",
        "Stage3MemMBStd",
        "PipelinePeakMemMB",
        "Stage1ExactGroups",
        "Stage1RedundantFiles",
        "Stage2CandidatePairs",
        "Stage3VerifiedPairs",
        "DatasetTotalFiles",
        "DatasetTotalSizeMB",
        "DatasetResolutionRange",
        "BenchmarkJSON",
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
    print(f"{Fore.YELLOW}Summary CSV: {Fore.CYAN}{SUMMARY_CSV}")
    print(f"{Fore.YELLOW}Logs:        {Fore.CYAN}{LOGS_DIR}")
    print(f"{Fore.YELLOW}JSON reports: {Fore.CYAN}{REPORTS_DIR}")


if __name__ == "__main__":
    main()
