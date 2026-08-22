#!/usr/bin/env python3
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FULL = ROOT / "data" / "labels" / "reference_labels_eval_v2_robustness.csv"

OUTS = {
    "t5": (
        ROOT / "data" / "labels" / "reference_labels_eval_v2_robustness_t5.csv",
        5,
    ),
    "t10": (
        ROOT / "data" / "labels" / "reference_labels_eval_v2_robustness_t10.csv",
        10,
    ),
}


def main() -> None:
    print("ROOT:", ROOT)
    print("FULL:", FULL, "exists=", FULL.exists())

    if not FULL.is_file():
        raise FileNotFoundError(f"Full labels file not found: {FULL}")

    with FULL.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not rows:
        raise RuntimeError("Full labels file is empty")
    if not fieldnames:
        raise RuntimeError("Could not read header from full labels file")

    for key, (out_path, n_rows) in OUTS.items():
        subset = rows[:n_rows]
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(subset)

        print(f"{key}: wrote {len(subset)} rows -> {out_path}")


if __name__ == "__main__":
    main()
