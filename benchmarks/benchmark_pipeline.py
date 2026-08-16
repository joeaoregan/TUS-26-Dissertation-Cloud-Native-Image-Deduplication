import argparse
import json
import platform
import time
import tracemalloc
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev

import imagehash
import psutil
from colorama import Fore, init
from PIL import Image

from core_engine.utils.dedupe_exact import file_hash
from core_engine.utils.dedupe_perceptual import (
    IMAGE_EXTENSIONS,
    compare_perceptual_hashes,
)
from core_engine.utils.dedupe_ssim import calculate_ssim

init(autoreset=True)


WARMUP_RUNS = 1
MEASURED_RUNS = 10


def measure_once(func, *args, **kwargs):
    """Measure execution time (ms) and peak memory (MB) for one function call."""
    tracemalloc.start()
    start_time = time.perf_counter()

    result = func(*args, **kwargs)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mem_mb = peak_mem / (1024 * 1024)
    return result, elapsed_ms, peak_mem_mb


def run_repeated(
    func, warmup_runs=WARMUP_RUNS, measured_runs=MEASURED_RUNS, *args, **kwargs
):
    """
    Execute warm-up runs (discarded), then measured runs.
    Returns:
      - last_result
      - list of execution times (ms)
      - list of peak memory values (MB)
    """
    # Warm-up (discard)
    for _ in range(warmup_runs):
        func(*args, **kwargs)

    times_ms = []
    peaks_mb = []
    last_result = None

    # Measured runs
    for _ in range(measured_runs):
        last_result, t_ms, p_mb = measure_once(func, *args, **kwargs)
        times_ms.append(t_ms)
        peaks_mb.append(p_mb)

    return last_result, times_ms, peaks_mb


def summarise(values):
    """Return mean and std-dev (0.0 std if only one sample)."""
    if not values:
        return {"mean": 0.0, "std_dev": 0.0}
    if len(values) == 1:
        return {"mean": round(values[0], 2), "std_dev": 0.0}
    return {"mean": round(mean(values), 2), "std_dev": round(stdev(values), 2)}


def build_dataset_profile(images: list[Path]) -> dict:
    """
    Build reproducible dataset metadata:
    - total size (bytes/MB)
    - format counts by file extension
    - resolution min/max (width x height)
    """
    if not images:
        return {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0.0,
            "format_counts": {},
            "resolution_range": None,
            "width_range": None,
            "height_range": None,
        }

    format_counts = Counter(p.suffix.lower() for p in images)

    total_size_bytes = 0
    widths = []
    heights = []

    resolution_read_errors = 0

    for p in images:
        total_size_bytes += p.stat().st_size
        try:
            with Image.open(p) as im:
                w, h = im.size
                widths.append(w)
                heights.append(h)
        except Exception as e:
            resolution_read_errors += 1
            print(f"{Fore.RED}Warning: could not read resolution for {p}: {e}")

    total_size_mb = round(total_size_bytes / (1024 * 1024), 2)

    profile = {
        "total_files": len(images),
        "total_size_bytes": total_size_bytes,
        "total_size_mb": total_size_mb,
        "format_counts": dict(sorted(format_counts.items())),
        "resolution_range": None,
        "width_range": None,
        "height_range": None,
        "profile_read_errors": resolution_read_errors,
    }

    if widths and heights:
        profile["width_range"] = {"min": min(widths), "max": max(widths)}
        profile["height_range"] = {"min": min(heights), "max": max(heights)}
        profile["resolution_range"] = {
            "min": f"{min(widths)}x{min(heights)}",
            "max": f"{max(widths)}x{max(heights)}",
        }

    return profile


def run_benchmark(
    dataset_dir: Path,
    output_json: Path = Path("benchmarks/results.json"),
    timestamp_output: bool = True,
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
            f"{dataset_profile['resolution_range']['min']} -> {dataset_profile['resolution_range']['max']}"
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
        return compare_perceptual_hashes(phash_dict, threshold=5)

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
            if score >= 0.85:
                ssim_results.append((p1, p2, score))
        return ssim_results

    verified, s3_times, s3_peaks = run_repeated(stage3_work)
    metrics["stages"]["stage3_ssim"] = {
        "time_ms": {"raw": [round(x, 2) for x in s3_times], **summarise(s3_times)},
        "peak_ram_mb": {"raw": [round(x, 4) for x in s3_peaks], **summarise(s3_peaks)},
        "verified_pairs": len(verified),
    }

    # Total pipeline timing estimate from per-iteration sums
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

    print(f"{Fore.GREEN}\n--- Detection Counts ---")
    print(
        f"{Fore.YELLOW}Stage 1 exact duplicate groups: {Fore.CYAN}{exact_duplicate_groups}"
    )
    print(
        f"{Fore.YELLOW}Stage 1 redundant files:        {Fore.CYAN}{exact_redundant_files}"
    )
    print(f"{Fore.YELLOW}Stage 2 candidate pairs:        {Fore.CYAN}{len(candidates)}")
    print(f"{Fore.YELLOW}Stage 3 verified pairs:         {Fore.CYAN}{len(verified)}")

    metrics["detections"] = {
        "stage1_exact_duplicate_groups": exact_duplicate_groups,
        "stage1_redundant_files": exact_redundant_files,
        "stage2_candidate_pairs": len(candidates),
        "stage3_verified_pairs": len(verified),
    }

    print(f"\n{Fore.GREEN}--- Summary (mean ± std dev, ms) ---")
    print(
        f"{Fore.YELLOW}Stage 1 (SHA-256): {Fore.CYAN}{metrics['stages']['stage1_sha256']['time_ms']['mean']} ± {metrics['stages']['stage1_sha256']['time_ms']['std_dev']}"
    )
    print(
        f"{Fore.YELLOW}Stage 2 (pHash):   {Fore.CYAN}{metrics['stages']['stage2_phash']['time_ms']['mean']} ± {metrics['stages']['stage2_phash']['time_ms']['std_dev']}"
    )
    print(
        f"{Fore.YELLOW}Stage 3 (SSIM):    {Fore.CYAN}{metrics['stages']['stage3_ssim']['time_ms']['mean']} ± {metrics['stages']['stage3_ssim']['time_ms']['std_dev']}"
    )
    print(
        f"{Fore.MAGENTA}Total Pipeline:    {Fore.CYAN}{metrics['total_pipeline_time_ms']['mean']} ± {metrics['total_pipeline_time_ms']['std_dev']}"
    )

    print(f"\n{Fore.GREEN}--- Peak RAM (MB, mean ± std dev) ---")
    print(
        f"{Fore.YELLOW}Stage 1 (SHA-256): {Fore.CYAN}{metrics['stages']['stage1_sha256']['peak_ram_mb']['mean']} ± {metrics['stages']['stage1_sha256']['peak_ram_mb']['std_dev']}"
    )
    print(
        f"{Fore.YELLOW}Stage 2 (pHash):   {Fore.CYAN}{metrics['stages']['stage2_phash']['peak_ram_mb']['mean']} ± {metrics['stages']['stage2_phash']['peak_ram_mb']['std_dev']}"
    )
    print(
        f"{Fore.YELLOW}Stage 3 (SSIM):    {Fore.CYAN}{metrics['stages']['stage3_ssim']['peak_ram_mb']['mean']} ± {metrics['stages']['stage3_ssim']['peak_ram_mb']['std_dev']}"
    )
    print(
        f"{Fore.MAGENTA}Pipeline Peak RAM: {Fore.CYAN}{metrics['total_pipeline_peak_ram_mb']} MB"
    )

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run cascading deduplication benchmark."
    )
    parser.add_argument(
        "--dir",
        dest="dataset_dir",
        type=Path,
        default=Path("dedupe_test"),
        help="Dataset directory to benchmark (default: dedupe_test)",
    )
    parser.add_argument(
        "--output",
        dest="output_json",
        type=Path,
        default=Path("benchmarks/results.json"),
        help="Output JSON path (default: benchmarks/results.json)",
    )
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="Disable timestamped snapshot output",
    )

    args = parser.parse_args()

    if args.dataset_dir.exists() and args.dataset_dir.is_dir():
        run_benchmark(
            dataset_dir=args.dataset_dir,
            output_json=args.output_json,
            timestamp_output=not args.no_timestamp,
        )
    else:
        print(f"Directory '{args.dataset_dir}' not found or is not a folder.")
