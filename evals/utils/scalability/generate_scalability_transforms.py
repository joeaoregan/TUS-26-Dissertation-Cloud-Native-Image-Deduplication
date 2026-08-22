#!/usr/bin/env python3
"""
Generate scalability transform variants from base images.

Input:
  data/scalability/base/

Output:
  data/scalability/<transform_bucket>/
  data/scalability/transform_manifest.csv

Notes:
- This mirrors robustness transform generation for reproducibility.
- If you do not need transformed scalability data for a specific run,
  you can skip executing this script.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from colorama import Fore, init
from PIL import Image, ImageEnhance

init(autoreset=True)

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT = REPO_ROOT / "data" / "scalability"
BASE_DIR = REPO_ROOT / "data" / "base"  # changed
MANIFEST_CSV = ROOT / "transform_manifest.csv"

VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


@dataclass(frozen=True)
class OutputRecord:
    source_file: str
    variant_file: str
    transform_family: str
    transform_name: str
    parameter: str


def iter_base_images(base_dir: Path) -> Iterable[Path]:
    for p in sorted(base_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in VALID_EXTS:
            yield p


def ensure_rgb(img: Image.Image) -> Image.Image:
    return img.convert("RGB") if img.mode != "RGB" else img


def save_jpeg(img: Image.Image, out_path: Path, quality: int = 95) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="JPEG", quality=quality, optimize=True)


def save_png(img: Image.Image, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)


def stem_safe_name(source: Path) -> str:
    rel = source.relative_to(BASE_DIR)
    return "__".join(rel.with_suffix("").parts)


def to_data_relative(manifest_rel_path: str) -> str:
    p = manifest_rel_path.replace("\\", "/").strip()
    if p.startswith("base/"):
        return p
    return f"scalability/{p}"


def generate() -> list[OutputRecord]:
    if not BASE_DIR.exists():
        raise FileNotFoundError(f"Base directory not found: {BASE_DIR}")

    records: list[OutputRecord] = []

    brightness_factors = [0.85, 1.15]
    contrast_factors = [0.85, 1.15]
    jpeg_qualities = [90, 75, 60]
    resize_factors = [0.75, 0.50]
    crop_factors = [0.90, 0.75]
    rotate_degrees = [2, -2]
    channel_shifts = [("r", 20), ("g", 20), ("b", 20)]

    print(
        f"{Fore.YELLOW}Generating transformed images from base images in {Fore.CYAN}{BASE_DIR}{Fore.RESET}..."
    )

    for src in iter_base_images(BASE_DIR):
        base_name = stem_safe_name(src)

        with Image.open(src) as im_raw:
            im = ensure_rgb(im_raw)
            print(f"{Fore.CYAN}Processing {Fore.RESET}{src.relative_to(REPO_ROOT)}...")

            for factor in brightness_factors:
                out_dir = ROOT / f"brightness_{str(factor).replace('.', 'p')}"
                out_file = out_dir / f"{base_name}__brightness_{factor:.2f}.jpg"
                out = ImageEnhance.Brightness(im).enhance(factor)
                save_jpeg(out, out_file, quality=95)
                records.append(
                    OutputRecord(
                        str(src.relative_to(REPO_ROOT / "data")),
                        str(out_file.relative_to(ROOT)),
                        "photometric",
                        "brightness",
                        f"factor={factor:.2f}",
                    )
                )

            for factor in contrast_factors:
                out_dir = ROOT / f"contrast_{str(factor).replace('.', 'p')}"
                out_file = out_dir / f"{base_name}__contrast_{factor:.2f}.jpg"
                out = ImageEnhance.Contrast(im).enhance(factor)
                save_jpeg(out, out_file, quality=95)
                records.append(
                    OutputRecord(
                        str(src.relative_to(REPO_ROOT / "data")),
                        str(out_file.relative_to(ROOT)),
                        "photometric",
                        "contrast",
                        f"factor={factor:.2f}",
                    )
                )

            for channel, delta in channel_shifts:
                out_dir = ROOT / f"colourshift_{channel}_p{delta}"
                out_file = out_dir / f"{base_name}__colourshift_{channel}_p{delta}.jpg"

                r, g, b = im.split()
                bands = {"r": r, "g": g, "b": b}
                bands[channel] = bands[channel].point(
                    lambda x, d=delta: max(0, min(255, x + d))
                )
                out = Image.merge("RGB", (bands["r"], bands["g"], bands["b"]))

                save_jpeg(out, out_file, quality=95)
                records.append(
                    OutputRecord(
                        str(src.relative_to(REPO_ROOT / "data")),
                        str(out_file.relative_to(ROOT)),
                        "photometric",
                        "colour_shift",
                        f"channel={channel},delta=+{delta}",
                    )
                )

            for q in jpeg_qualities:
                out_dir = ROOT / f"jpeg_q{q}"
                out_file = out_dir / f"{base_name}__jpeg_q{q}.jpg"
                save_jpeg(im, out_file, quality=q)
                records.append(
                    OutputRecord(
                        str(src.relative_to(REPO_ROOT / "data")),
                        str(out_file.relative_to(ROOT)),
                        "compression",
                        "jpeg_recompress",
                        f"quality={q}",
                    )
                )

            w, h = im.size
            for factor in resize_factors:
                out_dir = ROOT / f"resize_{str(factor).replace('.', 'p')}"
                out_file = out_dir / f"{base_name}__resize_{factor:.2f}.jpg"
                nw, nh = max(1, int(w * factor)), max(1, int(h * factor))
                out = im.resize((nw, nh), Image.Resampling.LANCZOS)
                save_jpeg(out, out_file, quality=95)
                records.append(
                    OutputRecord(
                        str(src.relative_to(REPO_ROOT / "data")),
                        str(out_file.relative_to(ROOT)),
                        "geometric",
                        "resize",
                        f"factor={factor:.2f}",
                    )
                )

            for frac in crop_factors:
                out_dir = ROOT / f"crop_center_{str(frac).replace('.', 'p')}"
                out_file = out_dir / f"{base_name}__crop_center_{frac:.2f}.jpg"

                cw, ch = max(1, int(w * frac)), max(1, int(h * frac))
                left = (w - cw) // 2
                top = (h - ch) // 2
                out = im.crop((left, top, left + cw, top + ch))
                save_jpeg(out, out_file, quality=95)
                records.append(
                    OutputRecord(
                        str(src.relative_to(REPO_ROOT / "data")),
                        str(out_file.relative_to(ROOT)),
                        "geometric",
                        "center_crop",
                        f"fraction={frac:.2f}",
                    )
                )

            for deg in rotate_degrees:
                out_dir = ROOT / f"rotate_{'p' if deg >= 0 else 'n'}{abs(deg)}"
                out_file = out_dir / f"{base_name}__rotate_{deg:+d}.jpg"
                out = im.rotate(deg, resample=Image.Resampling.BICUBIC, expand=False)
                save_jpeg(out, out_file, quality=95)
                records.append(
                    OutputRecord(
                        str(src.relative_to(REPO_ROOT / "data")),
                        str(out_file.relative_to(ROOT)),
                        "geometric",
                        "rotate",
                        f"degrees={deg:+d}",
                    )
                )

            out_dir = ROOT / "format_png"
            out_file = out_dir / f"{base_name}__format_png.png"
            save_png(im, out_file)
            records.append(
                OutputRecord(
                    str(src.relative_to(REPO_ROOT / "data")),
                    str(out_file.relative_to(ROOT)),
                    "format",
                    "convert_png",
                    "format=PNG",
                )
            )

    return records


def write_manifest(records: list[OutputRecord]) -> None:
    MANIFEST_CSV.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_file",
                "variant_file",
                "transform_family",
                "transform_name",
                "parameter",
            ],
        )
        writer.writeheader()
        for r in records:
            writer.writerow(
                {
                    "source_file": r.source_file,
                    "variant_file": r.variant_file,
                    "transform_family": r.transform_family,
                    "transform_name": r.transform_name,
                    "parameter": r.parameter,
                }
            )


def main() -> None:
    records = generate()
    write_manifest(records)
    print(f"{Fore.GREEN}Done. Generated {len(records)} transformed images.")
    print(f"{Fore.YELLOW}Manifest: {Fore.CYAN}{MANIFEST_CSV}")


if __name__ == "__main__":
    main()
