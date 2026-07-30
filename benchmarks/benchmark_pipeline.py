import time
import tracemalloc
from pathlib import Path
from core_engine.utils.dedupe_exact import file_hash
from core_engine.utils.dedupe_perceptual import compare_perceptual_hashes, IMAGE_EXTENSIONS
from core_engine.utils.dedupe_ssim import calculate_ssim
from PIL import Image
import imagehash


def measure_stage_execution(func, *args, **kwargs):
    """Utility to measure execution time (ms) and peak memory (MB) of a function."""
    tracemalloc.start()
    start_time = time.perf_counter()

    result = func(*args, **kwargs)

    elapsed_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mem_mb = peak_mem / (1024 * 1024)  # Convert bytes to MB

    return result, elapsed_time, peak_mem_mb


def run_benchmark(dataset_dir: Path):
    """Executes performance benchmark on standard test directory."""
    print(f"\n--- Running Benchmark on: {dataset_dir} ---")
    
    # Collect valid images
    images = [p for p in dataset_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    print(f"Total target images found: {len(images)}")

    metrics = {}

    # -------------------------------------------------------------
    # Stage 1: Exact Byte Matching (SHA-256)
    # -------------------------------------------------------------
    def stage1_work():
        hashes = {}
        for img in images:
            h = file_hash(img)
            hashes.setdefault(h, []).append(img)
        return hashes

    _, s1_time, s1_mem = measure_stage_execution(stage1_work)
    metrics["stage1_sha256"] = {"time_ms": round(s1_time, 2), "peak_ram_mb": round(s1_mem, 4)}
    print(f"Stage 1 (SHA-256): {s1_time:.2f} ms | Peak RAM: {s1_mem:.4f} MB")

    # -------------------------------------------------------------
    # Stage 2: Perceptual Hashing (pHash)
    # -------------------------------------------------------------
    def stage2_work():
        phash_dict = {}
        for img in images:
            with Image.open(img) as im:
                phash_dict[img] = imagehash.phash(im)
        return compare_perceptual_hashes(phash_dict, threshold=5)

    candidates, s2_time, s2_mem = measure_stage_execution(stage2_work)
    metrics["stage2_phash"] = {"time_ms": round(s2_time, 2), "peak_ram_mb": round(s2_mem, 4)}
    print(f"Stage 2 (pHash):  {s2_time:.2f} ms | Peak RAM: {s2_mem:.4f} MB | Candidates: {len(candidates)}")

    # -------------------------------------------------------------
    # Stage 3: SSIM Verification
    # -------------------------------------------------------------
    def stage3_work():
        ssim_results = []
        for p1, p2, _ in candidates:
            score = calculate_ssim(p1, p2)
            if score >= 0.85:
                ssim_results.append((p1, p2, score))
        return ssim_results

    verified, s3_time, s3_mem = measure_stage_execution(stage3_work)
    metrics["stage3_ssim"] = {"time_ms": round(s3_time, 2), "peak_ram_mb": round(s3_mem, 4)}
    print(f"Stage 3 (SSIM):   {s3_time:.2f} ms | Peak RAM: {s3_mem:.4f} MB | Verified Pairs: {len(verified)}")

    total_time = s1_time + s2_time + s3_time
    print(f"\nTotal Cascading Pipeline Time: {total_time:.2f} ms")
    return metrics


if __name__ == "__main__":
    target = Path("dedupe_test")
    if target.exists():
        run_benchmark(target)
    else:
        print(f"Directory '{target}' not found.")