#!/usr/bin/env python3
"""
Build Eval 4 scalability inputs without copying transformed images.

Inputs:
  data/base/
  data/scalability/transform_manifest.csv
  data/scalability/<transform_bucket>/

Outputs:
  data/labels/reference_images_eval_v3_scalability_<size>.csv
  data/labels/reference_labels_eval_v3_scalability_<size>.csv
  data/labels/reference_labels_eval_v3_scalability.csv

The image-list CSVs are passed to benchmarks.benchmark_pipeline via --file-list.
That lets Eval 4 benchmark one logical dataset made from base originals plus
their transformed variants, while the files stay in their canonical folders.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

from colorama import Fore, init

init(autoreset=True)

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
BASE_DIR = DATA_DIR / "base"
SCALABILITY_DIR = DATA_DIR / "scalability"
MANIFEST_CSV = SCALABILITY_DIR / "transform_manifest.csv"
OUT_DIR = DATA_DIR / "labels"
LABEL_PREFIX = "reference_labels_eval_v3_scalability_"
IMAGE_PREFIX = "reference_images_eval_v3_scalability_"
COMBINED_LABELS_CSV = OUT_DIR / "reference_labels_eval_v3_scalability.csv"

VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
SIZE_TO_COUNT = {
    "t5": 5,
    "t10": 10,
    "s": 500,
    "m": 1000,
    "l": 2000,
    "xl": 5000,
}
LABEL_FIELDNAMES = ["img_a", "img_b", "label", "type", "notes"]
IMAGE_FIELDNAMES = ["path"]
SEED = 42


def data_relative(path: Path) -> str:
    return path.relative_to(DATA_DIR).as_posix()


def manifest_name(path_text: str) -> str:
    return path_text.replace("\\", "/").split("/")[-1]


def load_transform_manifest() -> list[dict[str, str]]:
    if not MANIFEST_CSV.is_file():
        raise FileNotFoundError(f"Missing transform manifest: {MANIFEST_CSV}")

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
            raise ValueError(f"Transform manifest missing columns: {sorted(missing)}")
        return list(reader)


def select_sources(size_key: str) -> list[Path]:
    count = SIZE_TO_COUNT[size_key]
    subset_dir = SCALABILITY_DIR / size_key
    source_dir = subset_dir if subset_dir.is_dir() else BASE_DIR
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Missing source directory: {source_dir}")

    sources = sorted(
        p
        for p in source_dir.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXTS
    )
    if len(sources) < count:
        raise ValueError(
            f"Need {count} source images for size '{size_key}', found {len(sources)} in {source_dir}"
        )
    return sources[:count]


def variant_path(row: dict[str, str]) -> Path:
    return SCALABILITY_DIR / Path(row["variant_file"].replace("\\", "/"))


def build_positive_rows(
    sources: list[Path], manifest_rows: list[dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]]]:
    source_names = {p.name for p in sources}
    source_by_name = {p.name: p for p in sources}
    positives: list[dict[str, str]] = []
    by_source: dict[str, list[dict[str, str]]] = {}

    for row in manifest_rows:
        source_name = manifest_name(row["source_file"])
        if source_name not in source_names:
            continue

        source_path = source_by_name[source_name]
        var_path = variant_path(row)
        if not source_path.is_file() or not var_path.is_file():
            continue

        label_row = {
            "img_a": data_relative(source_path),
            "img_b": data_relative(var_path),
            "label": "1",
            "type": "near",
            "notes": (
                f"transform={row['transform_name']};"
                f"parameter={row['parameter']};"
                f"family={row['transform_family']}"
            ),
        }
        positives.append(label_row)
        by_source.setdefault(source_name, []).append(label_row)

    return positives, by_source


def build_negative_rows(
    sources: list[Path],
    positives_by_source: dict[str, list[dict[str, str]]],
    target_count: int,
) -> list[dict[str, str]]:
    random.seed(SEED)
    source_by_name = {p.name: p for p in sources}
    source_names = sorted(positives_by_source)

    negatives: list[dict[str, str]] = []
    seen_negative_pairs: set[tuple[str, str]] = set()
    attempts = 0
    max_attempts = target_count * 80

    while len(negatives) < target_count and attempts < max_attempts:
        attempts += 1
        source_name = source_names[attempts % len(source_names)]
        other_sources = [s for s in source_names if s != source_name]
        if not other_sources:
            break

        other_source = random.choice(other_sources)
        variant_row = random.choice(positives_by_source[other_source])
        source_rel = data_relative(source_by_name[source_name])
        pair = tuple(sorted((source_rel, variant_row["img_b"])))
        if pair in seen_negative_pairs:
            continue
        seen_negative_pairs.add(pair)

        negatives.append(
            {
                "img_a": source_rel,
                "img_b": variant_row["img_b"],
                "label": "0",
                "type": "non",
                "notes": "non-duplicate:different_source",
            }
        )

    if len(negatives) < target_count:
        raise RuntimeError(
            f"Could not generate enough negatives ({len(negatives)}/{target_count})."
        )

    return negatives


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_size_inputs(
    size_key: str, manifest_rows: list[dict[str, str]]
) -> tuple[Path, Path, int, int, int]:
    sources = select_sources(size_key)
    positives, positives_by_source = build_positive_rows(sources, manifest_rows)
    if not positives:
        raise ValueError(f"No usable transform pairs found for size '{size_key}'")

    negatives = build_negative_rows(
        sources, positives_by_source, target_count=len(positives)
    )
    label_rows = positives + negatives

    image_rows = [{"path": data_relative(p)} for p in sources]
    seen_images = {row["path"] for row in image_rows}
    for row in positives:
        if row["img_b"] not in seen_images:
            image_rows.append({"path": row["img_b"]})
            seen_images.add(row["img_b"])

    image_csv = OUT_DIR / f"{IMAGE_PREFIX}{size_key}.csv"
    labels_csv = OUT_DIR / f"{LABEL_PREFIX}{size_key}.csv"
    write_csv(image_csv, IMAGE_FIELDNAMES, image_rows)
    write_csv(labels_csv, LABEL_FIELDNAMES, label_rows)

    return image_csv, labels_csv, len(image_rows), len(positives), len(negatives)


def write_combined_labels(size_csvs: list[Path]) -> int:
    total_rows = 0
    COMBINED_LABELS_CSV.parent.mkdir(parents=True, exist_ok=True)

    with COMBINED_LABELS_CSV.open("w", encoding="utf-8", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=LABEL_FIELDNAMES)
        writer.writeheader()

        for size_csv in size_csvs:
            with size_csv.open("r", encoding="utf-8", newline="") as in_f:
                reader = csv.DictReader(in_f)
                for row in reader:
                    writer.writerow(row)
                    total_rows += 1

    return total_rows


def main() -> None:
    manifest_rows = load_transform_manifest()
    label_csvs: list[Path] = []
    summaries: list[tuple[str, int, int, int, Path, Path]] = []

    for size_key in SIZE_TO_COUNT:
        image_csv, labels_csv, image_count, positives, negatives = write_size_inputs(
            size_key, manifest_rows
        )
        label_csvs.append(labels_csv)
        summaries.append(
            (size_key, image_count, positives, negatives, image_csv, labels_csv)
        )

    total_rows = write_combined_labels(label_csvs)

    print(f"\n{Fore.GREEN}=== EVAL 4 SCALABILITY INPUT BUILD ===")
    for size_key, image_count, positives, negatives, image_csv, labels_csv in summaries:
        print(
            f"{Fore.YELLOW}{size_key:>4}: "
            f"{Fore.CYAN}{image_count} images, "
            f"{positives} positives, {negatives} negatives "
            f"{Fore.YELLOW}-> {Fore.CYAN}{labels_csv}"
        )
        print(f"{Fore.YELLOW}      file list -> {Fore.CYAN}{image_csv}")
    print(f"{Fore.YELLOW}Combined label rows: {Fore.CYAN}{total_rows}")
    print(f"{Fore.YELLOW}Combined labels CSV: {Fore.CYAN}{COMBINED_LABELS_CSV}")


if __name__ == "__main__":
    main()
