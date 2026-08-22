#!/usr/bin/env python3
"""
Build reference labels for robustness evaluation from transform_manifest.csv.

Outputs:
  data/labels/reference_labels_eval_v2_robustness.csv

Validator compatibility:
- headers: img_a,img_b,label,type,notes
- type values: exact|near|non
- paths are relative to data/ (e.g., robustness/base/..., robustness/jpeg_q90/...)
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from colorama import Fore, init

# Initialise colorama to automatically clear formatting after each print
init(autoreset=True)

SEED = 42

ROOT = Path(__file__).resolve().parents[3]  # repo root
DATA_DIR = ROOT / "data"
ROBUSTNESS_DIR = DATA_DIR / "robustness"
MANIFEST_CSV = ROBUSTNESS_DIR / "transform_manifest.csv"
OUT_CSV = DATA_DIR / "labels" / "reference_labels_eval_v2_robustness.csv"


@dataclass(frozen=True)
class PairRow:
    img_a: str
    img_b: str
    label: str
    type: str
    notes: str


def to_data_relative(manifest_rel_path: str) -> str:
    """
    Manifest paths are relative to data/robustness.
    Convert to paths relative to data/ for validator compatibility.
    Example:
      base/ILSVRC...JPEG -> robustness/base/ILSVRC...JPEG
    """
    p = manifest_rel_path.replace("\\", "/").strip()
    return f"robustness/{p}"


def file_exists_under_data(data_rel_path: str) -> bool:
    return (DATA_DIR / data_rel_path).exists()


def load_manifest() -> list[dict[str, str]]:
    if not MANIFEST_CSV.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_CSV}")

    rows: list[dict[str, str]] = []
    with MANIFEST_CSV.open("r", encoding="utf-8", newline="") as f:
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
            raise ValueError(f"Manifest missing columns: {sorted(missing)}")

        for r in reader:
            src = to_data_relative(r["source_file"])
            var = to_data_relative(r["variant_file"])

            # Keep only rows whose files exist under data/
            if file_exists_under_data(src) and file_exists_under_data(var):
                rows.append(
                    {
                        "source_file": src,
                        "variant_file": var,
                        "transform_family": r["transform_family"],
                        "transform_name": r["transform_name"],
                        "parameter": r["parameter"],
                    }
                )

    if not rows:
        raise ValueError("No usable manifest rows found (after existence checks).")
    return rows


def build_positive_pairs(rows: list[dict[str, str]]) -> list[PairRow]:
    positives: list[PairRow] = []
    seen: set[tuple[str, str, str]] = set()

    for r in rows:
        a = r["source_file"]
        b = r["variant_file"]
        key = (a, b, "1")
        if key in seen:
            continue
        seen.add(key)

        notes = (
            f"transform={r['transform_name']};"
            f"parameter={r['parameter']};"
            f"family={r['transform_family']}"
        )

        positives.append(
            PairRow(
                img_a=a,
                img_b=b,
                label="1",
                type="near",  # transformed duplicate = near duplicate
                notes=notes,
            )
        )

    return positives


def build_negative_pairs(
    rows: list[dict[str, str]], target_count: int
) -> list[PairRow]:
    """
    Build balanced negatives:
    pair source image A with a variant derived from DIFFERENT source image B.
    """
    random.seed(SEED)

    by_source: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        by_source.setdefault(r["source_file"], []).append(r)

    sources = sorted(by_source.keys())
    if len(sources) < 2:
        raise ValueError("Need at least 2 unique source images to build negatives.")

    negatives: list[PairRow] = []
    seen: set[tuple[str, str, str]] = set()

    i = 0
    attempts = 0
    max_attempts = target_count * 80

    while len(negatives) < target_count and attempts < max_attempts:
        attempts += 1

        src = sources[i % len(sources)]
        i += 1

        other_sources = [s for s in sources if s != src]
        other_src = random.choice(other_sources)
        chosen = random.choice(by_source[other_src])

        a = src
        b = chosen["variant_file"]
        key = (a, b, "0")

        if key in seen:
            continue
        seen.add(key)

        notes = (
            "non-duplicate:different_source;"
            f"variant_transform={chosen['transform_name']};"
            f"parameter={chosen['parameter']}"
        )

        negatives.append(
            PairRow(
                img_a=a,
                img_b=b,
                label="0",
                type="non",
                notes=notes,
            )
        )

    if len(negatives) < target_count:
        raise RuntimeError(
            f"Could not generate enough negatives ({len(negatives)}/{target_count})."
        )

    return negatives


def write_csv(rows: list[PairRow], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["img_a", "img_b", "label", "type", "notes"]
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "img_a": r.img_a,
                    "img_b": r.img_b,
                    "label": r.label,
                    "type": r.type,
                    "notes": r.notes,
                }
            )


def main() -> None:
    manifest_rows = load_manifest()
    positives = build_positive_pairs(manifest_rows)
    negatives = build_negative_pairs(manifest_rows, target_count=len(positives))

    all_rows = positives + negatives
    random.Random(SEED).shuffle(all_rows)

    write_csv(all_rows, OUT_CSV)

    print(f"\n{Fore.GREEN}=== STAGE 3 SSIM COMPARISON METRIC ===")
    print(f"{Fore.YELLOW}Manifest usable rows: {Fore.CYAN}{len(manifest_rows)}")
    print(f"{Fore.YELLOW}Positives:            {Fore.CYAN}{len(positives)}")
    print(f"{Fore.YELLOW}Negatives:            {Fore.CYAN}{len(negatives)}")
    print(f"{Fore.YELLOW}Total label rows:     {Fore.CYAN}{len(all_rows)}")
    print(f"{Fore.YELLOW}Output CSV:           {Fore.CYAN}{OUT_CSV}")


if __name__ == "__main__":
    main()
