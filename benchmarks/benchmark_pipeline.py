import json
import time
import tracemalloc
from pathlib import Path
from statistics import mean, stdev
from core_engine.utils.dedupe_exact import file_hash
from core_engine.utils.dedupe_perceptual import compare_perceptual_hashes, IMAGE_EXTENSIONS
from core_engine.utils.dedupe_ssim import calculate_ssim
from PIL import Image
import imagehash
from datetime import datetime
from colorama import Fore, Style, init
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


def run_repeated(func, warmup_runs=WARMUP_RUNS, measured_runs=MEASURED_RUNS, *args, **kwargs):
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
    return {
        "mean": round(mean(values), 2),
        "std_dev": round(stdev(values), 2)
    }


def run_benchmark(dataset_dir: Path, output_json: Path = Path("benchmarks/results.json"), timestamp_output: bool = True):
    print(f"\n{Fore.GREEN}--- Running Benchmark on: {Fore.CYAN}{dataset_dir}{Fore.GREEN} ---")

    images = [p for p in dataset_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    print(f"{Fore.YELLOW}Total target images found: {Fore.CYAN}{len(images)}")

    metrics = {
        "dataset": str(dataset_dir),
        "total_images": len(images),
        "runs": {
            "warmup_discarded": WARMUP_RUNS,
            "measured_iterations": MEASURED_RUNS
        },
        "stages": {}
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
        "time_ms": {
            "raw": [round(x, 2) for x in s1_times],
            **summarise(s1_times)
        },
        "peak_ram_mb": {
            "raw": [round(x, 4) for x in s1_peaks],
            **summarise(s1_peaks)
        }
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
        "time_ms": {
            "raw": [round(x, 2) for x in s2_times],
            **summarise(s2_times)
        },
        "peak_ram_mb": {
            "raw": [round(x, 4) for x in s2_peaks],
            **summarise(s2_peaks)
        },
        "candidate_pairs": len(candidates)
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
        "time_ms": {
            "raw": [round(x, 2) for x in s3_times],
            **summarise(s3_times)
        },
        "peak_ram_mb": {
            "raw": [round(x, 4) for x in s3_peaks],
            **summarise(s3_peaks)
        },
        "verified_pairs": len(verified)
    }

    # Total pipeline timing estimate from per-iteration sums
    total_times = [a + b + c for a, b, c in zip(s1_times, s2_times, s3_times)]
    metrics["total_pipeline_time_ms"] = {
        "raw": [round(x, 2) for x in total_times],
        **summarise(total_times)
    }

    print(f"\n{Fore.GREEN}--- Summary (mean ± std dev, ms) ---")
    print(f"{Fore.YELLOW}Stage 1 (SHA-256): {Fore.CYAN}{metrics['stages']['stage1_sha256']['time_ms']['mean']} ± {metrics['stages']['stage1_sha256']['time_ms']['std_dev']}")
    print(f"{Fore.YELLOW}Stage 2 (pHash):   {Fore.CYAN}{metrics['stages']['stage2_phash']['time_ms']['mean']} ± {metrics['stages']['stage2_phash']['time_ms']['std_dev']}")
    print(f"{Fore.YELLOW}Stage 3 (SSIM):    {Fore.CYAN}{metrics['stages']['stage3_ssim']['time_ms']['mean']} ± {metrics['stages']['stage3_ssim']['time_ms']['std_dev']}")
    print(f"{Fore.MAGENTA}Total Pipeline:    {Fore.CYAN}{metrics['total_pipeline_time_ms']['mean']} ± {metrics['total_pipeline_time_ms']['std_dev']}")
    
    print(f"\n{Fore.GREEN}--- Peak RAM (MB, mean ± std dev) ---")
    print(f"{Fore.YELLOW}Stage 1 (SHA-256): {Fore.CYAN}{metrics['stages']['stage1_sha256']['peak_ram_mb']['mean']} ± {metrics['stages']['stage1_sha256']['peak_ram_mb']['std_dev']}")
    print(f"{Fore.YELLOW}Stage 2 (pHash):   {Fore.CYAN}{metrics['stages']['stage2_phash']['peak_ram_mb']['mean']} ± {metrics['stages']['stage2_phash']['peak_ram_mb']['std_dev']}")
    print(f"{Fore.YELLOW}Stage 3 (SSIM):    {Fore.CYAN}{metrics['stages']['stage3_ssim']['peak_ram_mb']['mean']} ± {metrics['stages']['stage3_ssim']['peak_ram_mb']['std_dev']}")

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
    target = Path("dedupe_test")
    if target.exists():
        run_benchmark(target)
    else:
        print(f"{Fore.RED}Directory '{target}' not found.")