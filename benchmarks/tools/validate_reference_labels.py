import argparse
import csv
from pathlib import Path

from colorama import Fore, init

from benchmarks.tools.path_safety import resolve_within

VALID_LABELS = {"0", "1"}
VALID_TYPES = {"exact", "near", "non"}

init(autoreset=True)


def normalise_pair(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a.strip(), b.strip())))


def main():
    print(f"{Fore.GREEN}Validate Reference Labels CSV")

    parser = argparse.ArgumentParser(description="Validate reference labels CSV")
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()

    allowed_input_base = (Path.cwd() / "data" / "reviews").resolve()

    try:
        safe_csv = resolve_within(allowed_input_base, str(args.csv))
    except ValueError as e:
        print(f"{Fore.RED}ERROR: {Fore.RESET}{e}")
        raise SystemExit(2)

    if not safe_csv.exists():
        print(f"{Fore.RED}ERROR: CSV not found: {safe_csv}")
        raise SystemExit(2)

    required = {"img_a", "img_b", "label", "type", "notes"}
    seen = set()
    errors = 0
    rows = 0

    with safe_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if set(reader.fieldnames or []) != required:
            print(f"{Fore.RED}ERROR: headers must be exactly: {sorted(required)}")
            raise SystemExit(2)

        for line_no, row in enumerate(reader, start=2):
            rows += 1
            a = row["img_a"].strip()
            b = row["img_b"].strip()
            label = row["label"].strip()
            typ = row["type"].strip().lower()

            if not a or not b:
                print(f"{Fore.RED}Line {line_no}: ERROR empty image path")
                errors += 1
                continue

            if a == b:
                print(f"{Fore.RED}Line {line_no}: ERROR same file on both sides: {a}")
                errors += 1

            if label not in VALID_LABELS:
                print(f"{Fore.RED}Line {line_no}: ERROR invalid label '{label}'")
                errors += 1

            if typ not in VALID_TYPES:
                print(f"{Fore.RED}Line {line_no}: ERROR invalid type '{typ}'")
                errors += 1

            if not Path(a).exists():
                print(f"{Fore.RED}Line {line_no}: ERROR missing file: {a}")
                errors += 1
            if not Path(b).exists():
                print(f"{Fore.RED}Line {line_no}: ERROR missing file: {b}")
                errors += 1

            k = normalise_pair(a, b)
            if k in seen:
                print(
                    f"{Fore.RED}Line {line_no}: ERROR duplicate pair (order-insensitive): {a} <-> {b}"
                )
                errors += 1
            seen.add(k)

    print(f"\n{Fore.YELLOW}Rows checked: {Fore.CYAN}{rows}")
    print(f"{Fore.RED}Errors: {Fore.CYAN}{errors}")
    if errors:
        raise SystemExit(1)

    print(f"{Fore.GREEN}Reference labels CSV is valid.")


if __name__ == "__main__":
    main()
