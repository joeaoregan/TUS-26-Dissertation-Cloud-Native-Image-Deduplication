#!/usr/bin/env python3
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FULL = ROOT / "data" / "labels" / "reference_labels_eval_v2_robustness.csv"
CFG = ROOT / "evals" / "common_config.json"

OUT_DIR = ROOT / "data" / "labels"
OUT_PREFIX = "reference_labels_eval_v2_robustness_"


def main() -> None:
    if not FULL.is_file():
        raise FileNotFoundError(f"Missing full labels: {FULL}")
    if not CFG.is_file():
        raise FileNotFoundError(f"Missing config: {CFG}")

    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    subset_sizes = cfg.get("subset_sizes", {})
    if not subset_sizes:
        raise ValueError("No subset_sizes found in common_config.json")

    with FULL.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not rows or not fieldnames:
        raise RuntimeError("Full labels file is empty or missing header")

    # Sort by configured subset size ascending so t5/t10/xs... are deterministic
    sorted_sizes = sorted(subset_sizes.items(), key=lambda kv: int(kv[1]))

    for size_key, n in sorted_sizes:
        n = int(n)
        out_path = OUT_DIR / f"{OUT_PREFIX}{size_key}.csv"
        subset = rows[:n]

        with out_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(subset)

        print(f"{size_key:>4} ({n:>5} rows): wrote {len(subset):>5} -> {out_path}")


if __name__ == "__main__":
    main()
