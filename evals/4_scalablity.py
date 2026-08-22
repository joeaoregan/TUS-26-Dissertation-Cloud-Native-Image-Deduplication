#!/usr/bin/env python3

import argparse
import csv
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from colorama import Fore, init

init(autoreset=True)

# ============================================================
# Final Evaluation 4 (Scalability)
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = str(Path(sys.executable).resolve())
DEDUPE_PY_DIR = REPO_ROOT / "services" / "dedupe-py"

MASTER_DIR = REPO_ROOT / "data" / "base"
SCALABILITY_ROOT = REPO_ROOT / "data" / "scalability"
LABELS_ROOT = REPO_ROOT / "data" / "labels"
TRANSFORM_MANIFEST = SCALABILITY_ROOT / "transform_manifest.csv"
IMAGE_EXTENSIONS = {".jpeg", ".jpg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
LABEL_FIELDNAMES = ["img_a", "img_b", "label", "type", "notes"]
FILE_LIST_FIELDNAMES = ["path"]
SEED = 42

SIZE_TO_COUNT = {
    "t5": 5,
    "t10": 10,
    "s": 500,
    "m": 1000,
    "l": 2000,
    "xl": 5000,
}

SIZE_TO_LABELS = {
    "t5": "reference_labels_eval_v3_scalability_t5.csv",
    "t10": "reference_labels_eval_v3_scalability_t10.csv",
    "s": "reference_labels_eval_v3_scalability_s.csv",
    "m": "reference_labels_eval_v3_scalability_m.csv",
    "l": "reference_labels_eval_v3_scalability_l.csv",
    "xl": "reference_labels_eval_v3_scalability_xl.csv",
}

DETECTION_COLUMNS = [
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
    ("RunTime", "Run Time", 9, "center"),
]

COST_COLUMNS = [
    ("ConfigID", "Config ID", 13, "left"),
    ("Stage1Time", "Stage 1 Time", 18, "center"),
    ("Stage2Time", "Stage 2 Time", 18, "center"),
    ("Stage3Time", "Stage 3 Time", 18, "center"),
    ("TotalTime", "Total Time", 18, "center"),
    ("PipelinePeakMemMB", "Peak RAM", 10, "center"),
    ("Stage2CandidatePairs", "S2 Pairs", 9, "center"),
    ("Stage3VerifiedPairs", "S3 Pairs", 9, "center"),
]


def load_common_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "common_config.json"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Missing config file: {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def build_configs_from_common_config(cfg: dict) -> list[tuple]:
    configs_raw = cfg.get("threshold_configs", [])
    enabled = [c for c in configs_raw if c.get("enabled", True)]
    if not enabled:
        raise ValueError("No enabled threshold_configs in common_config.json")

    configs = []
    for c in enabled:
        for key in ("id", "phash", "ssim", "tag"):
            if key not in c:
                raise ValueError(f"Missing '{key}' in threshold config: {c}")
        configs.append((c["id"], int(c["phash"]), float(c["ssim"]), c["tag"]))
    return configs


def parse_args():
    p = argparse.ArgumentParser(description="Run final Eval 4 (scalability)")
    p.add_argument(
        "--sizes",
        nargs="+",
        required=True,
        choices=["t5", "t10", "s", "m", "l", "xl"],
        help="One or more sizes to run back-to-back, e.g. --sizes s m l",
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
    return p.parse_args()


def env_with_pythonpath():
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(DEDUPE_PY_DIR) + (os.pathsep + existing if existing else "")
    return env


def run_cmd(cmd, log_file: Path):
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        env=env_with_pythonpath(),
    )
    log_file.parent.mkdir(parents=True, exist_ok=True)
    shown = subprocess.list2cmdline(cmd)
    log_file.write_text(
        f"$ {shown}\n\n[STDOUT]\n{proc.stdout}\n\n[STDERR]\n{proc.stderr}\n",
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}):\n{shown}\n\n"
            f"See log: {log_file}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)


def parse_eval_metrics(text: str) -> dict:
    clean = strip_ansi(text)
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
    out = {}
    for k, p in patterns.items():
        m = re.search(p, clean, flags=re.IGNORECASE)
        out[k] = m.group(1) if m else ""
    missing = [k for k, v in out.items() if v == ""]
    if missing:
        raise ValueError(f"Missing metrics in evaluate output: {', '.join(missing)}")
    return out


def parse_benchmark_cost(json_path: Path) -> dict:
    data = json.loads(json_path.read_text(encoding="utf-8"))

    def getv(*keys, default=""):
        cur = data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def fnum(v, dp=2):
        try:
            return f"{float(v):.{dp}f}"
        except (TypeError, ValueError):
            return ""

    def stage(stage_name, metric, stat):
        return getv("stages", stage_name, metric, stat)

    return {
        "Stage1TimeMsMean": fnum(stage("stage1_sha256", "time_ms", "mean")),
        "Stage1TimeMsStd": fnum(stage("stage1_sha256", "time_ms", "std_dev")),
        "Stage2TimeMsMean": fnum(stage("stage2_phash", "time_ms", "mean")),
        "Stage2TimeMsStd": fnum(stage("stage2_phash", "time_ms", "std_dev")),
        "Stage3TimeMsMean": fnum(stage("stage3_ssim", "time_ms", "mean")),
        "Stage3TimeMsStd": fnum(stage("stage3_ssim", "time_ms", "std_dev")),
        "TotalTimeMsMean": fnum(getv("total_pipeline_time_ms", "mean")),
        "TotalTimeMsStd": fnum(getv("total_pipeline_time_ms", "std_dev")),
        "PipelinePeakMemMB": fnum(getv("total_pipeline_peak_ram_mb")),
        "Stage2CandidatePairs": getv("detections", "stage2_candidate_pairs"),
        "Stage3VerifiedPairs": getv("detections", "stage3_verified_pairs"),
    }


def fmt_cell(value, width, align):
    txt = str(value)
    if align == "left":
        return txt.ljust(width)
    if align == "right":
        return txt.rjust(width)
    return txt.center(width)


def sep(cols):
    return "+" + "+".join("-" * (w + 2) for _, _, w, _ in cols) + "+"


def print_table_header(title, cols):
    s = sep(cols)
    hdr = "| " + " | ".join(fmt_cell(lbl, w, a) for _, lbl, w, a in cols) + " |"
    print(f"\n{Fore.GREEN}{title}")
    print(f"{Fore.BLUE}{s}")
    print(f"{Fore.CYAN}{hdr}")
    print(f"{Fore.BLUE}{s}")


def print_table_row(row: dict, idx: int, cols):
    d = dict(row)
    if d.get("ConfigID") == "C1":
        d["ConfigID"] = "C1 (baseline)"
    line = "| " + " | ".join(fmt_cell(d.get(k, ""), w, a) for k, _, w, a in cols) + " |"
    color = (
        Fore.GREEN
        if row.get("ConfigID") == "C1"
        else (Fore.CYAN if idx % 2 == 0 else Fore.WHITE)
    )
    print(f"{color}{line}", flush=True)


def write_csv(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def select_sources(size_key: str) -> list[Path]:
    count = SIZE_TO_COUNT[size_key]
    subset_dir = SCALABILITY_ROOT / size_key
    source_dir = subset_dir if subset_dir.is_dir() else MASTER_DIR

    if not source_dir.is_dir():
        raise FileNotFoundError(f"Missing source dir: {source_dir}")

    files = sorted(
        p
        for p in source_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if len(files) < count:
        raise ValueError(
            f"Need {count} files for size '{size_key}', found {len(files)} in {source_dir}"
        )

    selected = files[:count]
    return selected


def manifest_name(path_text: str) -> str:
    return path_text.replace("\\", "/").split("/")[-1]


def data_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT / "data").as_posix()


def load_transform_manifest() -> list[dict[str, str]]:
    if not TRANSFORM_MANIFEST.is_file():
        raise FileNotFoundError(f"Missing transform manifest: {TRANSFORM_MANIFEST}")

    with TRANSFORM_MANIFEST.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {
            "source_file",
            "variant_file",
            "transform_family",
            "transform_name",
            "parameter",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Transform manifest missing columns: {sorted(missing)}")
        return list(reader)


def build_file_list_for_subset(
    size_key: str, sources: list[Path], manifest_rows: list[dict[str, str]]
) -> Path:
    source_names = {p.name for p in sources}
    out_csv = LABELS_ROOT / f"reference_images_eval_v3_scalability_{size_key}.csv"

    rows = [{"path": data_relative(p)} for p in sources]
    seen = {r["path"] for r in rows}

    for row in manifest_rows:
        if manifest_name(row["source_file"]) not in source_names:
            continue
        variant_path = SCALABILITY_ROOT / Path(row["variant_file"].replace("\\", "/"))
        if not variant_path.is_file():
            continue
        rel = data_relative(variant_path)
        if rel not in seen:
            rows.append({"path": rel})
            seen.add(rel)

    write_csv(out_csv, FILE_LIST_FIELDNAMES, rows)
    return out_csv


def build_labels_for_subset(
    size_key: str, sources: list[Path], manifest_rows: list[dict[str, str]]
) -> Path:
    out_csv = LABELS_ROOT / SIZE_TO_LABELS[size_key]
    source_names = {p.name for p in sources}
    source_by_name = {p.name: p for p in sources}
    by_source: dict[str, list[dict[str, str]]] = {}
    positives: list[dict[str, str]] = []

    for row in manifest_rows:
        source_name = manifest_name(row["source_file"])
        if source_name not in source_names:
            continue

        source_path = source_by_name[source_name]
        variant_path = SCALABILITY_ROOT / Path(row["variant_file"].replace("\\", "/"))
        if not source_path.is_file() or not variant_path.is_file():
            continue

        label_row = {
            "img_a": data_relative(source_path),
            "img_b": data_relative(variant_path),
            "label": "1",
            "type": "near",
            "notes": (
                f"transform={row['transform_name']};"
                f"parameter={row['parameter']};"
                f"family={row['transform_family']}"
            ),
        }
        positives.append(label_row)
        by_source.setdefault(source_name, []).append(label_row)

    if not positives:
        raise ValueError(f"No usable transform pairs found for size '{size_key}'")

    random.seed(SEED)
    source_list = sorted(by_source)
    negatives: list[dict[str, str]] = []
    seen_negative_pairs: set[tuple[str, str]] = set()

    attempts = 0
    max_attempts = len(positives) * 80
    while len(negatives) < len(positives) and attempts < max_attempts:
        attempts += 1
        source_name = source_list[attempts % len(source_list)]
        other_sources = [s for s in source_list if s != source_name]
        if not other_sources:
            break

        other_source = random.choice(other_sources)
        variant_row = random.choice(by_source[other_source])
        source_path = source_by_name[source_name]
        pair = tuple(sorted((data_relative(source_path), variant_row["img_b"])))
        if pair in seen_negative_pairs:
            continue
        seen_negative_pairs.add(pair)

        negatives.append(
            {
                "img_a": data_relative(source_path),
                "img_b": variant_row["img_b"],
                "label": "0",
                "type": "non",
                "notes": "non-duplicate:different_source",
            }
        )

    if len(negatives) < len(positives):
        raise RuntimeError(
            f"Could not generate enough negatives for {size_key} "
            f"({len(negatives)}/{len(positives)})."
        )

    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LABEL_FIELDNAMES)
        writer.writeheader()
        writer.writerows(positives + negatives)

    return out_csv


def run_for_size(
    size_key: str, pair_limit: str, rebuild_subsets: bool, configs: list[tuple]
):
    size_start = time.perf_counter()
    if rebuild_subsets:
        print(
            f"{Fore.YELLOW}Note: --rebuild-subsets is ignored for manifest-based Eval 4 inputs."
        )
    sources = select_sources(size_key)
    manifest_rows = load_transform_manifest()
    file_list_src = build_file_list_for_subset(size_key, sources, manifest_rows)
    labels_src = build_labels_for_subset(size_key, sources, manifest_rows).resolve()
    labels_file = labels_src.name
    if not labels_src.is_file():
        raise FileNotFoundError(
            f"Missing labels file for size '{size_key}': {labels_src}"
        )

    out_root = (REPO_ROOT / "results" / "final" / f"eval4_{size_key}").resolve()
    logs_dir = out_root / "logs"
    metrics_dir = out_root / "metrics"
    reports_dir = out_root / "reports"
    preds_dir = out_root / "predictions"

    bench_stage_dir = (
        REPO_ROOT / "benchmarks" / "results" / "final" / f"eval4_{size_key}"
    ).resolve()
    review_stage_dir = (
        REPO_ROOT / "data" / "reviews" / "final" / f"eval4_{size_key}"
    ).resolve()

    for d in [
        logs_dir,
        metrics_dir,
        reports_dir,
        preds_dir,
        bench_stage_dir,
        review_stage_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    labels_staged = review_stage_dir / labels_file
    shutil.copy2(labels_src, labels_staged)

    print(f"\n{Fore.GREEN}=== Eval 4 ({size_key.upper()}) ===")
    print(f"{Fore.YELLOW}Dataset root:     {Fore.CYAN}data")
    print(f"{Fore.YELLOW}Image file list:  {Fore.CYAN}{file_list_src}")
    print(f"{Fore.YELLOW}Reference labels: {Fore.CYAN}{labels_src}")

    detection_rows = []
    cost_rows = []

    print_table_header(
        f"Table A - Detection Performance (Eval 4, {size_key.upper()})",
        DETECTION_COLUMNS,
    )

    for idx, (cfg, phash, ssim, tag_base) in enumerate(configs):
        cfg_start = time.perf_counter()
        run_tag = f"eval4-{size_key}-{cfg.lower()}-{tag_base}"

        staged_json = bench_stage_dir / f"{run_tag}.json"
        final_json = reports_dir / f"{run_tag}.json"
        staged_pred = review_stage_dir / f"{run_tag}-stage3.csv"
        final_pred = preds_dir / f"{run_tag}-stage3.csv"

        cmd_bench = [
            PYTHON_EXE,
            "-m",
            "benchmarks.benchmark_pipeline",
            "--dir",
            ".",
            "--file-list",
            file_list_src.relative_to(REPO_ROOT / "data").as_posix(),
            "--output",
            str(staged_json),
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
        run_cmd(cmd_bench, logs_dir / f"{cfg}_01_benchmark.log")
        shutil.copy2(staged_json, final_json)

        cmd_export = [
            PYTHON_EXE,
            "-m",
            "benchmarks.tools.export_predictions",
            "--input",
            str(staged_json),
            "--output",
            str(staged_pred),
            "--source",
            "stage3",
        ]
        run_cmd(cmd_export, logs_dir / f"{cfg}_02_export.log")
        shutil.copy2(staged_pred, final_pred)

        cmd_eval = [
            PYTHON_EXE,
            "-m",
            "benchmarks.tools.evaluate_predictions",
            "--reference-labels",
            str(labels_staged),
            "--predictions",
            str(staged_pred),
        ]
        eval_out = run_cmd(cmd_eval, logs_dir / f"{cfg}_03_evaluate.log")

        q = parse_eval_metrics(eval_out)
        c = parse_benchmark_cost(staged_json)
        cfg_elapsed = time.perf_counter() - cfg_start

        drow = {
            "ConfigID": cfg,
            "RunTag": run_tag,
            "pHashThreshold": phash,
            "SSIMThreshold": ssim,
            "PairsEvaluated": q["PairsEvaluated"],
            "TP": q["TP"],
            "FP": q["FP"],
            "FN": q["FN"],
            "TN": q["TN"],
            "Precision": q["Precision"],
            "Recall": q["Recall"],
            "F1Score": q["F1Score"],
            "Accuracy": q["Accuracy"],
            "RunTime": f"{cfg_elapsed:.1f}s",
            "BenchmarkJSON": final_json.as_posix(),
            "PredictionsCSV": final_pred.as_posix(),
        }
        detection_rows.append(drow)
        print_table_row(drow, idx, DETECTION_COLUMNS)

        crow = {
            "ConfigID": cfg,
            "RunTag": run_tag,
            "pHashThreshold": phash,
            "SSIMThreshold": ssim,
            **c,
            "BenchmarkJSON": final_json.as_posix(),
        }
        cost_rows.append(crow)

    print(f"{Fore.BLUE}{sep(DETECTION_COLUMNS)}")

    print_table_header(
        f"Table B - Computational Cost (Eval 4, {size_key.upper()})", COST_COLUMNS
    )
    for idx, row in enumerate(cost_rows):
        show = {
            **row,
            "Stage1Time": f"{row['Stage1TimeMsMean']} +/- {row['Stage1TimeMsStd']}",
            "Stage2Time": f"{row['Stage2TimeMsMean']} +/- {row['Stage2TimeMsStd']}",
            "Stage3Time": f"{row['Stage3TimeMsMean']} +/- {row['Stage3TimeMsStd']}",
            "TotalTime": f"{row['TotalTimeMsMean']} +/- {row['TotalTimeMsStd']}",
        }
        print_table_row(show, idx, COST_COLUMNS)
    print(f"{Fore.BLUE}{sep(COST_COLUMNS)}")

    detection_csv = metrics_dir / f"table_eval4_{size_key}_detection_summary.csv"
    cost_csv = metrics_dir / f"table_eval4_{size_key}_cost_summary.csv"

    write_csv(
        detection_csv,
        [
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
            "RunTime",
            "BenchmarkJSON",
            "PredictionsCSV",
        ],
        detection_rows,
    )

    write_csv(
        cost_csv,
        [
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
        ],
        [
            {
                "ConfigID": r["ConfigID"],
                "RunTag": r["RunTag"],
                "pHashThreshold": r["pHashThreshold"],
                "SSIMThreshold": r["SSIMThreshold"],
                "Stage1TimeMsMean": r["Stage1TimeMsMean"],
                "Stage1TimeMsStd": r["Stage1TimeMsStd"],
                "Stage2TimeMsMean": r["Stage2TimeMsMean"],
                "Stage2TimeMsStd": r["Stage2TimeMsStd"],
                "Stage3TimeMsMean": r["Stage3TimeMsMean"],
                "Stage3TimeMsStd": r["Stage3TimeMsStd"],
                "TotalTimeMsMean": r["TotalTimeMsMean"],
                "TotalTimeMsStd": r["TotalTimeMsStd"],
                "PipelinePeakMemMB": r["PipelinePeakMemMB"],
                "Stage2CandidatePairs": r["Stage2CandidatePairs"],
                "Stage3VerifiedPairs": r["Stage3VerifiedPairs"],
                "BenchmarkJSON": r["BenchmarkJSON"],
            }
            for r in cost_rows
        ],
    )

    print(
        f"\n{Fore.GREEN}Completed size {size_key.upper()} in {(time.perf_counter() - size_start) / 60:.2f} min"
    )
    print(f"{Fore.YELLOW}Detection CSV: {Fore.CYAN}{detection_csv}")
    print(f"{Fore.YELLOW}Cost CSV:      {Fore.CYAN}{cost_csv}")
    print(f"{Fore.YELLOW}Logs:          {Fore.CYAN}{logs_dir}")


def main():
    cfg = load_common_config()
    args = parse_args()
    configs = build_configs_from_common_config(cfg)
    pair_limits = cfg.get("pair_limits", {})
    effective_pair_limit = (
        str(args.pair_limit)
        if args.pair_limit is not None
        else str(pair_limits.get("eval4", 5000))
    )
    overall_start = time.perf_counter()

    print(f"{Fore.GREEN}=== Running Final Evaluation 4: Scalability ===")
    print(f"{Fore.YELLOW}Master dataset: {Fore.CYAN}{MASTER_DIR}")
    print(
        f"{Fore.YELLOW}Sizes to run:   {Fore.CYAN}{', '.join(s.upper() for s in args.sizes)}"
    )
    print(f"{Fore.YELLOW}Pair limit:     {Fore.CYAN}{effective_pair_limit}")
    print(f"{Fore.YELLOW}Configs:        {Fore.CYAN}{', '.join(c[0] for c in configs)}")

    for size_key in args.sizes:
        run_for_size(
            size_key=size_key,
            pair_limit=effective_pair_limit,
            rebuild_subsets=args.rebuild_subsets,
            configs=configs,
        )

    print(f"\n{Fore.GREEN}All requested sizes complete.")
    print(
        f"{Fore.YELLOW}Total runtime: {Fore.CYAN}{(time.perf_counter() - overall_start) / 60:.2f} min"
    )


if __name__ == "__main__":
    main()
