#!/usr/bin/env python3
import csv
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

# ============================================================
# Repro script for Interim Eval 2
# - Runs benchmark for each threshold config
# - Exports stage3 predictions CSV
# - Evaluates predictions vs reference labels
# - Writes logs + summary table
# ============================================================

# Resolve repo root robustly from this file path:
# repo/services/dedupe-py/run_interim_eval2.py  -> parents[2] = repo root
REPO_ROOT = Path(__file__).resolve().parents[2]

# Core paths (ABSOLUTE to avoid relative-path bugs)
REFERENCE_LABELS = (REPO_ROOT / "data/labels/reference_labels_eval_v1.csv").resolve()
DATASET_DIR = "dedupe_test_100"  # benchmark tool expects this logical folder name

CONFIGS = [
    ("C1", 5, 0.85, "threshold-tuning-baseline-phash5-ssim085"),
    ("C2", 4, 0.85, "threshold-tuning-phash4-ssim085"),
    ("C3", 5, 0.90, "threshold-tuning-phash5-ssim090"),
    ("C4", 6, 0.85, "threshold-tuning-phash6-ssim085"),
    ("C5", 6, 0.90, "threshold-tuning-phash6-ssim090"),
]

OUT_ROOT = (REPO_ROOT / "results/interim/eval2").resolve()
METRICS_DIR = OUT_ROOT / "metrics"
PREDICTIONS_DIR = OUT_ROOT / "predictions"
SUMMARY_CSV = METRICS_DIR / "table_x_summary.csv"

# IMPORTANT: always use the SAME python interpreter as this script
PYTHON_EXE = str(Path(sys.executable).resolve())


def run_cmd(cmd: str, log_file: Path) -> str:
    proc = subprocess.run(
        shlex.split(cmd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),  # enforce repo-root execution
    )
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(
        f"$ {cmd}\n\n[STDOUT]\n{proc.stdout}\n\n[STDERR]\n{proc.stderr}\n",
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {cmd}\nSee: {log_file}"
        )
    return proc.stdout


def parse_eval_metrics(text: str) -> dict:
    patterns = {
        "TP": r"\bTP\b\s*[:=]\s*(\d+)",
        "FP": r"\bFP\b\s*[:=]\s*(\d+)",
        "FN": r"\bFN\b\s*[:=]\s*(\d+)",
        "TN": r"\bTN\b\s*[:=]\s*(\d+)",
        "Precision": r"\bPrecision\b\s*[:=]\s*([0-9]*\.?[0-9]+)",
        "Recall": r"\bRecall\b\s*[:=]\s*([0-9]*\.?[0-9]+)",
        "F1Score": r"\bF1(?:\s*Score)?\b\s*[:=]\s*([0-9]*\.?[0-9]+)",
        "Accuracy": r"\bAccuracy\b\s*[:=]\s*([0-9]*\.?[0-9]+)",
        "PairsEvaluated": r"\bPairs\s+evaluated\b\s*[:=]\s*(\d+)",
    }
    out = {}
    for key, pattern in patterns.items():
        m = re.search(pattern, text, flags=re.IGNORECASE)
        out[key] = m.group(1) if m else ""
    return out


def read_benchmark_counts(json_path: Path) -> dict:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    counts = data.get("detection_counts", {})
    return {
        "Stage2Candidates": counts.get("stage2_candidate_pairs", ""),
        "Stage3Verified": counts.get("stage3_verified_pairs", ""),
    }


def main():
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Using Python: {PYTHON_EXE}")
    print(f"Repo root:    {REPO_ROOT}")

    rows = []

    for cfg_id, phash, ssim, run_tag in CONFIGS:
        print(f"\n=== {cfg_id}: pHash={phash}, SSIM={ssim} ===")

        # Keep benchmark JSON in repo root /logs (as your project already does)
        bench_json = (REPO_ROOT / "logs" / f"{run_tag}.json").resolve()

        # Exported predictions go to requested interim path
        pred_csv = (PREDICTIONS_DIR / f"{run_tag}-stage3.csv").resolve()

        # 1) Benchmark pipeline
        bench_cmd = (
            f'"{PYTHON_EXE}" -m benchmarks.benchmark_pipeline '
            f"--dir {DATASET_DIR} "
            f'--output "{bench_json.as_posix()}" '
            f"--export-pairs --pair-limit 500 "
            f"--phash-threshold {phash} "
            f"--ssim-threshold {ssim} "
            f"--run-tag {run_tag} "
            f"--no-timestamp"
        )
        run_cmd(bench_cmd, METRICS_DIR / f"{cfg_id}_01_benchmark.log")

        # 2) Export stage3 predictions (valid source choices: stage2|stage3)
        export_cmd = (
            f'"{PYTHON_EXE}" -m benchmarks.tools.export_predictions '
            f'--input "{bench_json.as_posix()}" '
            f'--output "{pred_csv.as_posix()}" '
            f"--source stage3"
        )
        run_cmd(export_cmd, METRICS_DIR / f"{cfg_id}_02_export.log")

        # 3) Evaluate predictions
        eval_cmd = (
            f'"{PYTHON_EXE}" -m benchmarks.tools.evaluate_predictions '
            f'--reference-labels "{REFERENCE_LABELS.as_posix()}" '
            f'--predictions "{pred_csv.as_posix()}"'
        )
        eval_out = run_cmd(eval_cmd, METRICS_DIR / f"{cfg_id}_03_evaluate.log")

        metrics = parse_eval_metrics(eval_out)
        counts = read_benchmark_counts(bench_json)

        rows.append(
            {
                "ConfigID": cfg_id,
                "pHashThreshold": phash,
                "SSIMThreshold": ssim,
                "PairsEvaluated": metrics.get("PairsEvaluated", ""),
                "TP": metrics.get("TP", ""),
                "FP": metrics.get("FP", ""),
                "FN": metrics.get("FN", ""),
                "TN": metrics.get("TN", ""),
                "Precision": metrics.get("Precision", ""),
                "Recall": metrics.get("Recall", ""),
                "F1Score": metrics.get("F1Score", ""),
                "Accuracy": metrics.get("Accuracy", ""),
                "Stage2Candidates": counts.get("Stage2Candidates", ""),
                "Stage3Verified": counts.get("Stage3Verified", ""),
                "BenchmarkJSON": bench_json.as_posix(),
                "PredictionsCSV": pred_csv.as_posix(),
            }
        )

    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ConfigID",
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
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nDone.")
    print(f"Summary CSV:  {SUMMARY_CSV}")
    print(f"Metrics logs: {METRICS_DIR}")
    print(f"Predictions:  {PREDICTIONS_DIR}")


if __name__ == "__main__":
    main()
