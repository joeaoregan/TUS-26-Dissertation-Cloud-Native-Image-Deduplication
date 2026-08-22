#!/usr/bin/env python3

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check that dataset files are consecutively numbered."
    )
    parser.add_argument(
        "--dir",
        default="data/base",
        help="Dataset directory to scan (default: data/base)",
    )
    parser.add_argument(
        "--prefix",
        default="ILSVRC2012_val_",
        help="Filename prefix before the numeric part",
    )
    parser.add_argument(
        "--ext",
        default=".JPEG",
        help="Filename extension (case-sensitive by default)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Expected starting index (default: 1)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=8,
        help="Zero-padding width of numeric part (default: 8)",
    )
    parser.add_argument(
        "--case-insensitive-ext",
        action="store_true",
        help="Treat extension match as case-insensitive",
    )
    return parser.parse_args()


def build_pattern(
    prefix: str, ext: str, width: int, case_insensitive_ext: bool
) -> re.Pattern:
    prefix_esc = re.escape(prefix)
    ext_esc = re.escape(ext)
    flags = re.IGNORECASE if case_insensitive_ext else 0
    return re.compile(rf"^{prefix_esc}(\d{{{width}}}){ext_esc}$", flags=flags)


def main() -> int:
    args = parse_args()
    dataset_dir = Path(args.dir).resolve()

    if not dataset_dir.is_dir():
        print(f"ERROR: Directory not found: {dataset_dir}")
        return 2

    pattern = build_pattern(
        prefix=args.prefix,
        ext=args.ext,
        width=args.width,
        case_insensitive_ext=args.case_insensitive_ext,
    )

    numbered = []
    non_matching = []

    for p in sorted(dataset_dir.iterdir()):
        if not p.is_file():
            continue
        m = pattern.match(p.name)
        if m:
            numbered.append((int(m.group(1)), p.name))
        else:
            non_matching.append(p.name)

    if not numbered:
        print("ERROR: No files matched the configured pattern.")
        print(
            f"Pattern: {args.prefix}" + "N" * args.width + f"{args.ext} "
            f"(case_insensitive_ext={args.case_insensitive_ext})"
        )
        return 3

    numbers = sorted(n for n, _ in numbered)
    expected_min = args.start
    expected_max = args.start + len(numbers) - 1
    expected = list(range(expected_min, expected_max + 1))

    missing = sorted(set(expected) - set(numbers))
    duplicates = sorted({n for n in numbers if numbers.count(n) > 1})

    # Also check for out-of-range relative to expected contiguous block
    out_of_range = sorted([n for n in numbers if n < expected_min or n > expected_max])

    print(f"Directory: {dataset_dir}")
    print(f"Matched files: {len(numbered)}")
    print(f"Start expected: {args.start}")
    print(f"Detected min/max: {numbers[0]}..{numbers[-1]}")

    if non_matching:
        print(f"Non-matching files: {len(non_matching)} (showing up to 10)")
        for name in non_matching[:10]:
            print(f"  - {name}")

    ok = True

    if missing:
        ok = False
        print(f"Missing numbers ({len(missing)}):")
        print("  " + ", ".join(str(x) for x in missing[:50]))
        if len(missing) > 50:
            print(f"  ... and {len(missing) - 50} more")

    if duplicates:
        ok = False
        print(f"Duplicate numbers ({len(duplicates)}):")
        print("  " + ", ".join(str(x) for x in duplicates))

    if out_of_range:
        ok = False
        print(f"Out-of-range numbers ({len(out_of_range)}):")
        print("  " + ", ".join(str(x) for x in out_of_range[:50]))
        if len(out_of_range) > 50:
            print(f"  ... and {len(out_of_range) - 50} more")

    if ok:
        print("OK: Numbering is consecutive for matched files.")
        return 0

    print("FAIL: Numbering issues detected.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
