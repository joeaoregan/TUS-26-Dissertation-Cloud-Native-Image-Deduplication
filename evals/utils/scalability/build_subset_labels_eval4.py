#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CFG = ROOT / "evals" / "common_config.json"
FULL = ROOT / "data" / "labels" / "reference_labels_eval_v3_scalability.csv"
OUT_DIR = ROOT / "data" / "labels"
OUT_PREFIX = "reference_labels_eval_v3_scalability_"

DEFAULT_SKIP_SIZES = {"xxl"}


def parse_args(valid_sizes: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Slice the combined Eval 4 scalability label CSV by configured sizes."
    )
    parser.add_argument(
        "--sizes",
        nargs="+",
        choices=valid_sizes,
        default=None,
        help=(
            "Subset size keys to write. Defaults to all configured sizes except "
            f"{', '.join(sorted(DEFAULT_SKIP_SIZES))}."
        ),
    )
    parser.add_argument(
        "--include-xxl",
        action="store_true",
        help="Include xxl when --sizes is not provided.",
    )
    return parser.parse_args()


def select_size_keys(
    subset_sizes: dict[str, int], requested_sizes: list[str] | None, include_xxl: bool
) -> list[str]:
    if requested_sizes:
        selected = requested_sizes
    else:
        skipped = set() if include_xxl else DEFAULT_SKIP_SIZES
        selected = [key for key in subset_sizes if key not in skipped]

    return sorted(selected, key=lambda key: subset_sizes[key])


def main() -> None:
    if not CFG.is_file():
        raise FileNotFoundError(f"Missing config: {CFG}")
    if not FULL.is_file():
        raise FileNotFoundError(f"Missing full labels: {FULL}")

    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    subset_sizes = cfg.get("subset_sizes", {})
    if not subset_sizes:
        raise ValueError("No subset_sizes found in evals/common_config.json")

    subset_sizes = {key: int(value) for key, value in subset_sizes.items()}
    args = parse_args(list(subset_sizes.keys()))
    size_keys = select_size_keys(subset_sizes, args.sizes, args.include_xxl)

    with FULL.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not rows or not fieldnames:
        raise RuntimeError("Full scalability labels file is empty or missing header")

    for size_key in size_keys:
        n = subset_sizes[size_key]
        out_path = OUT_DIR / f"{OUT_PREFIX}{size_key}.csv"
        subset = rows[:n]

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(subset)

        print(f"{size_key:>4} ({n:>5} rows): wrote {len(subset):>5} -> {out_path}")


if __name__ == "__main__":
    main()
