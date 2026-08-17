import time
import tracemalloc
from statistics import mean, stdev


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


def run_repeated(func, warmup_runs=1, measured_runs=10, *args, **kwargs):
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
