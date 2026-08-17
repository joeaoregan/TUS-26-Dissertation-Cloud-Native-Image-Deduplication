from collections import Counter
from pathlib import Path

from colorama import Fore
from PIL import Image


def build_dataset_profile(images: list[Path]) -> dict:
    """
    Build reproducible dataset metadata:
    - total size (bytes/MB)
    - format counts by file extension
    - resolution min/max (width x height)
    """
    if not images:
        return {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0.0,
            "format_counts": {},
            "resolution_range": None,
            "width_range": None,
            "height_range": None,
            "profile_read_errors": 0,
        }

    format_counts = Counter(p.suffix.lower() for p in images)

    total_size_bytes = 0
    widths = []
    heights = []
    resolution_read_errors = 0

    for p in images:
        total_size_bytes += p.stat().st_size
        try:
            with Image.open(p) as im:
                w, h = im.size
                widths.append(w)
                heights.append(h)
        except Exception as e:
            resolution_read_errors += 1
            print(f"{Fore.RED}Warning: could not read resolution for {p}: {e}")

    total_size_mb = round(total_size_bytes / (1024 * 1024), 2)

    profile = {
        "total_files": len(images),
        "total_size_bytes": total_size_bytes,
        "total_size_mb": total_size_mb,
        "format_counts": dict(sorted(format_counts.items())),
        "resolution_range": None,
        "width_range": None,
        "height_range": None,
        "profile_read_errors": resolution_read_errors,
    }

    if widths and heights:
        profile["width_range"] = {"min": min(widths), "max": max(widths)}
        profile["height_range"] = {"min": min(heights), "max": max(heights)}
        profile["resolution_range"] = {
            "min": f"{min(widths)}x{min(heights)}",
            "max": f"{max(widths)}x{max(heights)}",
        }

    return profile
