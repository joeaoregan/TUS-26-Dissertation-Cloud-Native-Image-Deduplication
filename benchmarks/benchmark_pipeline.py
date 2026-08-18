import argparse
import json
import platform
from datetime import datetime
from pathlib import Path

import imagehash
import psutil
from colorama import Fore, init
from PIL import Image

from benchmarks.constants import (
    DEFAULT_PAIR_LIMIT,
    MEASURED_RUNS,
    PHASH_THRESHOLD,
    SSIM_THRESHOLD,
    WARMUP_RUNS,
)
from benchmarks.exports import (
    export_stage1_groups,
    export_stage2_candidates,
    export_stage3_verified,
)
from benchmarks.measurement import run_repeated, summarise
from benchmarks.profile import build_dataset_profile
from benchmarks.runtime_config import load_runtime_config
from core_engine.utils.dedupe_exact import file_hash
from core_engine.utils.dedupe_perceptual import (
    IMAGE_EXTENSIONS,
    compare_perceptual_hashes,
)
from core_engine.utils.dedupe_ssim import calculate_ssim

init(autoreset=True)


def run_benchmark(
    dataset_dir: Path,
    output_json: Path = Path("benchmarks/results.json"),
    timestamp_output: bool = True,
    export_pairs: bool = False,
    pair_limit: int = DEFAULT_PAIR_LIMIT,
    phash_threshold: int = PHASH_THRESHOLD,
    ssim_threshold: float = SSIM_THRESHOLD,
    run_tag: str = "",
):
    print(
        f"\n{Fore.GREEN}--- Running Benchmark on: {Fore.CYAN}{dataset_dir}{Fore.GREEN} ---"
    )

    images = sorted(
        [
            p
            for p in dataset_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ],
        key=lambda p: str(p).lower(),
    )
    print(f"{Fore.YELLOW}Total target images found: {Fore.CYAN}{len(images)}")
    if not images:
        print(f"{Fore.RED}No valid images found in {dataset_dir}")
        return None

    dataset_profile = build_dataset_profile(images)

    if dataset_profile["profile_read_errors"] > 0:
        print(
            f"{Fore.RED}Resolution profiling warnings: "
            f"{dataset_profile['profile_read_errors']} file(s) could not be read."
        )

    print(
        f"{Fore.YELLOW}Dataset size: {Fore.CYAN}{dataset_profile['total_size_mb']} MB "
        f"({dataset_profile['total_size_bytes']} bytes)"
    )
    print(f"{Fore.YELLOW}Formats: {Fore.CYAN}{dataset_profile['format_counts']}")
    if dataset_profile["resolution_range"]:
        print(
            f"{Fore.YELLOW}Resolution range: {Fore.CYAN}"
            f"{dataset_profile['resolution_range']['min']} -> "
            f"{dataset_profile['resolution_range']['max']}"
        )

    metrics = {
        "dataset": str(dataset_dir),
        "total_images": len(images),
        "runs": {"warmup_discarded": WARMUP_RUNS, "measured_iterations": MEASURED_RUNS},
        "stages": {},
        "environment": {
            "os": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        },
        "dataset_profile": dataset_profile,
        "config": {
            "phash_threshold": phash_threshold,
            "ssim_threshold": ssim_threshold,
            "export_pairs": export_pairs,
            "pair_limit": pair_limit,
            "run_tag": run_tag,
        },
    }

    # Stage 1
    def stage1_work():
        hashes = {}
        for img in images:
            h = file_hash(img)
            hashes.setdefault(h, []).append(img)
        return hashes

    stage1_result, s1_times, s1_peaks = run_repeated(stage1_work)
    metrics["stages"]["stage1_sha256"] = {
        "time_ms": {"raw": [round(x, 2) for x in s1_times], **summarise(s1_times)},
        "peak_ram_mb": {"raw": [round(x, 4) for x in s1_peaks], **summarise(s1_peaks)},
    }

    # Stage 2
    def stage2_work():
        phash_dict = {}
        for img in images:
            with Image.open(img) as im:
                phash_dict[img] = imagehash.phash(im)
        return compare_perceptual_hashes(phash_dict, threshold=phash_threshold)

    candidates, s2_times, s2_peaks = run_repeated(stage2_work)
    metrics["stages"]["stage2_phash"] = {
        "time_ms": {"raw": [round(x, 2) for x in s2_times], **summarise(s2_times)},
        "peak_ram_mb": {"raw": [round(x, 4) for x in s2_peaks], **summarise(s2_peaks)},
        "candidate_pairs": len(candidates),
    }

    # Stage 3
    def stage3_work():
        ssim_results = []
        for p1, p2, _ in candidates:
            score = calculate_ssim(p1, p2)
            if score >= ssim_threshold:
                ssim_results.append((p1, p2, score))
        return ssim_results

    verified, s3_times, s3_peaks = run_repeated(stage3_work)
    metrics["stages"]["stage3_ssim"] = {
        "time_ms": {"raw": [round(x, 2) for x in s3_times], **summarise(s3_times)},
        "peak_ram_mb": {"raw": [round(x, 4) for x in s3_peaks], **summarise(s3_peaks)},
        "verified_pairs": len(verified),
    }

    # Totals
    total_times = [a + b + c for a, b, c in zip(s1_times, s2_times, s3_times)]
    metrics["total_pipeline_time_ms"] = {
        "raw": [round(x, 2) for x in total_times],
        **summarise(total_times),
    }

    pipeline_peak_mb = max(
        metrics["stages"]["stage1_sha256"]["peak_ram_mb"]["mean"],
        metrics["stages"]["stage2_phash"]["peak_ram_mb"]["mean"],
        metrics["stages"]["stage3_ssim"]["peak_ram_mb"]["mean"],
    )
    metrics["total_pipeline_peak_ram_mb"] = round(pipeline_peak_mb, 2)

    exact_duplicate_groups = sum(
        1 for paths in stage1_result.values() if len(paths) > 1
    )
    exact_redundant_files = sum(
        len(paths) - 1 for paths in stage1_result.values() if len(paths) > 1
    )

    metrics["detections"] = {
        "stage1_exact_duplicate_groups": exact_duplicate_groups,
        "stage1_redundant_files": exact_redundant_files,
        "stage2_candidate_pairs": len(candidates),
        "stage3_verified_pairs": len(verified),
    }

    if export_pairs:
        metrics["pair_details"] = {
            "sample_limit": pair_limit,
            "stage1_exact_groups_sample": export_stage1_groups(
                stage1_result, pair_limit
            ),
            "stage2_candidates_sample": export_stage2_candidates(
                candidates, pair_limit
            ),
            "stage3_verified_sample": export_stage3_verified(verified, pair_limit),
            "stage1_exact_groups_total": exact_duplicate_groups,
            "stage2_candidates_total": len(candidates),
            "stage3_verified_total": len(verified),
        }

    print_benchmark_summary(
        metrics=metrics,
        exact_duplicate_groups=exact_duplicate_groups,
        exact_redundant_files=exact_redundant_files,
        candidates_count=len(candidates),
        verified_count=len(verified),
        export_pairs=export_pairs,
        pair_limit=pair_limit,
    )

    if export_pairs:
        print(
            f"{Fore.GREEN}Pair export enabled: {Fore.CYAN}"
            f"up to {pair_limit} entries per section in 'pair_details'"
        )

    allowed_base = Path.cwd()
    # allowed_base = (Path.cwd() / "data").resolve() # stricter control if needed
    output_json = resolve_within(allowed_base, str(output_json))
    output_json.parent.mkdir(parents=True, exist_ok=True)

    # Always write/update canonical latest file
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)
    print(f"\n{Fore.GREEN}Benchmark report exported to: {Fore.CYAN}{output_json}")

    # Optionally write immutable timestamped snapshot
    if timestamp_output:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        stamped = output_json.with_name(f"{output_json.stem}-{ts}{output_json.suffix}")
        with open(stamped, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=4)
        print(f"{Fore.GREEN}Timestamped snapshot exported to: {Fore.CYAN}{stamped}")

    return metrics


def print_benchmark_summary(
    metrics: dict,
    exact_duplicate_groups: int,
    exact_redundant_files: int,
    candidates_count: int,
    verified_count: int,
    export_pairs: bool,
    pair_limit: int,
) -> None:
    print(f"{Fore.GREEN}\n--- Detection Counts ---")
    print(
        f"{Fore.YELLOW}Stage 1 exact duplicate groups: {Fore.CYAN}{exact_duplicate_groups}"
    )
    print(
        f"{Fore.YELLOW}Stage 1 redundant files:        {Fore.CYAN}{exact_redundant_files}"
    )
    print(f"{Fore.YELLOW}Stage 2 candidate pairs:        {Fore.CYAN}{candidates_count}")
    print(f"{Fore.YELLOW}Stage 3 verified pairs:         {Fore.CYAN}{verified_count}")

    print(f"\n{Fore.GREEN}--- Summary (mean ± std dev, ms) ---")
    print(
        f"{Fore.YELLOW}Stage 1 (SHA-256): {Fore.CYAN}"
        f"{metrics['stages']['stage1_sha256']['time_ms']['mean']} ± "
        f"{metrics['stages']['stage1_sha256']['time_ms']['std_dev']}"
    )
    print(
        f"{Fore.YELLOW}Stage 2 (pHash):   {Fore.CYAN}"
        f"{metrics['stages']['stage2_phash']['time_ms']['mean']} ± "
        f"{metrics['stages']['stage2_phash']['time_ms']['std_dev']}"
    )
    print(
        f"{Fore.YELLOW}Stage 3 (SSIM):    {Fore.CYAN}"
        f"{metrics['stages']['stage3_ssim']['time_ms']['mean']} ± "
        f"{metrics['stages']['stage3_ssim']['time_ms']['std_dev']}"
    )
    print(
        f"{Fore.MAGENTA}Total Pipeline:    {Fore.CYAN}"
        f"{metrics['total_pipeline_time_ms']['mean']} ± "
        f"{metrics['total_pipeline_time_ms']['std_dev']}"
    )

    print(f"\n{Fore.GREEN}--- Peak RAM (MB, mean ± std dev) ---")
    print(
        f"{Fore.YELLOW}Stage 1 (SHA-256): {Fore.CYAN}"
        f"{metrics['stages']['stage1_sha256']['peak_ram_mb']['mean']} ± "
        f"{metrics['stages']['stage1_sha256']['peak_ram_mb']['std_dev']}"
    )
    print(
        f"{Fore.YELLOW}Stage 2 (pHash):   {Fore.CYAN}"
        f"{metrics['stages']['stage2_phash']['peak_ram_mb']['mean']} ± "
        f"{metrics['stages']['stage2_phash']['peak_ram_mb']['std_dev']}"
    )
    print(
        f"{Fore.YELLOW}Stage 3 (SSIM):    {Fore.CYAN}"
        f"{metrics['stages']['stage3_ssim']['peak_ram_mb']['mean']} ± "
        f"{metrics['stages']['stage3_ssim']['peak_ram_mb']['std_dev']}"
    )
    print(
        f"{Fore.MAGENTA}Pipeline Peak RAM: {Fore.CYAN}"
        f"{metrics['total_pipeline_peak_ram_mb']} MB"
    )

    if export_pairs:
        print(
            f"{Fore.GREEN}Pair export enabled: {Fore.CYAN}"
            f"up to {pair_limit} entries per section in 'pair_details'"
        )


from pathlib import Path


def resolve_within(base_dir: Path, user_input: str) -> Path:
    base = base_dir.resolve()
    target = Path(user_input)
    if not target.is_absolute():
        target = (base / target).resolve()
    else:
        target = target.resolve()

    if target != base and base not in target.parents:
        raise ValueError(f"Path escapes allowed directory: {user_input}")
    return target


if __name__ == "__main__":
    runtime_cfg = load_runtime_config()

    parser = argparse.ArgumentParser(
        description="Run cascading deduplication benchmark."
    )
    parser.add_argument(
        "--dir",
        dest="dataset_dir",
        type=Path,
        default=Path(runtime_cfg["dataset_dir"]),
        help=f"Dataset directory to benchmark (default: {runtime_cfg['dataset_dir']})",
    )
    parser.add_argument(
        "--output",
        dest="output_json",
        type=Path,
        default=Path(runtime_cfg["output_json"]),
        help=f"Output JSON path (default: {runtime_cfg['output_json']})",
    )
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="Disable timestamped snapshot output",
    )
    parser.add_argument(
        "--export-pairs",
        action="store_true",
        help="Include sample duplicate/candidate pair details in JSON output "
        "(can also be enabled via EXPORT_PAIRS=true)",
    )
    parser.add_argument(
        "--pair-limit",
        type=int,
        default=runtime_cfg["pair_limit"],
        help=f"Max entries per pair_details section (default: {runtime_cfg['pair_limit']})",
    )
    parser.add_argument(
        "--phash-threshold",
        type=int,
        default=runtime_cfg["phash_threshold"],
        help="Stage 2 pHash Hamming distance threshold "
        f"(default: {runtime_cfg['phash_threshold']})",
    )
    parser.add_argument(
        "--ssim-threshold",
        type=float,
        default=runtime_cfg["ssim_threshold"],
        help=f"Stage 3 SSIM acceptance threshold (default: {runtime_cfg['ssim_threshold']})",
    )
    parser.add_argument(
        "--run-tag",
        type=str,
        default=runtime_cfg["run_tag"] or "",
        help="Optional run tag to store in output JSON config",
    )

    args = parser.parse_args()

    # CLI flag wins, but env can enable by default when flag is absent
    effective_export_pairs = args.export_pairs or runtime_cfg["export_pairs"]

    if args.pair_limit < 1:
        print(f"{Fore.RED}Error: --pair-limit must be >= 1")
        raise SystemExit(2)

    if args.phash_threshold < 0:
        print(f"{Fore.RED}Error: --phash-threshold must be >= 0")
        raise SystemExit(2)

    if not (0.0 <= args.ssim_threshold <= 1.0):
        print(f"{Fore.RED}Error: --ssim-threshold must be between 0.0 and 1.0")
        raise SystemExit(2)

    repo_root = Path.cwd().resolve()

    try:
        safe_dataset_dir = resolve_within(repo_root, str(args.dataset_dir))
        safe_output_json = resolve_within(repo_root, str(args.output_json))
    except ValueError as e:
        print(f"{Fore.RED}Error: {Fore.RESET}{e}")
        raise SystemExit(2)

    if safe_dataset_dir.exists() and safe_dataset_dir.is_dir():
        run_benchmark(
            dataset_dir=safe_dataset_dir,
            output_json=safe_output_json,
            timestamp_output=not args.no_timestamp,
            export_pairs=effective_export_pairs,
            pair_limit=args.pair_limit,
            phash_threshold=args.phash_threshold,
            ssim_threshold=args.ssim_threshold,
            run_tag=args.run_tag,
        )
    else:
        print(f"{Fore.RED}Directory '{safe_dataset_dir}' not found or is not a folder.")
