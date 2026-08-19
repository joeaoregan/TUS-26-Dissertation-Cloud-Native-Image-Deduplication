import os


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_int(value: str, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _as_float(value: str, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


def load_runtime_config() -> dict:
    """
    Environment-driven runtime config for benchmark execution.
    CLI args should still override these values where applicable.
    """
    return {
        "dataset_dir": os.getenv("DATASET_DIR", "data/dedupe_test_100"),
        "output_json": os.getenv("OUTPUT_JSON", "logs/results.json"),
        "export_pairs": _as_bool(os.getenv("EXPORT_PAIRS"), default=False),
        "pair_limit": _as_int(os.getenv("PAIR_LIMIT"), default=500),
        "phash_threshold": _as_int(os.getenv("PHASH_THRESHOLD"), default=5),
        "ssim_threshold": _as_float(os.getenv("SSIM_THRESHOLD"), default=0.85),
        "run_tag": os.getenv("RUN_TAG", "").strip() or None,
    }
