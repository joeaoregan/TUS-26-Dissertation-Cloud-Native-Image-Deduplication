import argparse
import csv
from pathlib import Path

from colorama import Fore, init

from benchmarks.tools.path_safety import resolve_within

VALID_LABELS = {"0", "1"}
VALID_TYPES = {"exact", "near", "non"}
REQUIRED_HEADERS = {"img_a", "img_b", "label", "type", "notes"}

init(autoreset=True)


def normalise_pair(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a.strip(), b.strip())))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate reference labels CSV")
    parser.add_argument("--csv", required=True, type=Path)
    return parser.parse_args()


def resolve_csv_path(csv_arg: Path) -> Path:
    allowed_input_base = (Path.cwd() / "data" / "reviews").resolve()
    try:
        safe_csv = resolve_within(allowed_input_base, str(csv_arg))
    except ValueError as e:
        print(f"{Fore.RED}ERROR: {Fore.RESET}{e}")
        raise SystemExit(2) from e

    if not safe_csv.exists():
        print(f"{Fore.RED}ERROR: CSV not found: {safe_csv}")
        raise SystemExit(2)

    return safe_csv


def validate_headers(fieldnames: list[str] | None) -> None:
    if set(fieldnames or []) != REQUIRED_HEADERS:
        print(f"{Fore.RED}ERROR: headers must be exactly: {sorted(REQUIRED_HEADERS)}")
        raise SystemExit(2)


def validate_row(
    line_no: int,
    row: dict[str, str],
    seen: set[tuple[str, str]],
) -> int:
    errors = 0

    a = row["img_a"].strip()
    b = row["img_b"].strip()
    label = row["label"].strip()
    typ = row["type"].strip().lower()

    if not a or not b:
        print(f"{Fore.RED}Line {line_no}: ERROR empty image path")
        return 1

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
    else:
        seen.add(k)

    return errors


def validate_csv_rows(safe_csv: Path) -> tuple[int, int]:
    seen: set[tuple[str, str]] = set()
    total_errors = 0
    total_rows = 0

    with safe_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        validate_headers(reader.fieldnames)

        for line_no, row in enumerate(reader, start=2):
            total_rows += 1
            total_errors += validate_row(line_no, row, seen)

    return total_rows, total_errors


def print_summary(rows: int, errors: int) -> None:
    print(f"\n{Fore.YELLOW}Rows checked: {Fore.CYAN}{rows}")
    print(f"{Fore.RED}Errors: {Fore.CYAN}{errors}")

    if errors:
        raise SystemExit(1)

    print(f"{Fore.GREEN}Reference labels CSV is valid.")


def main():
    print(f"{Fore.GREEN}Validate Reference Labels CSV")
    args = parse_args()
    safe_csv = resolve_csv_path(args.csv)
    rows, errors = validate_csv_rows(safe_csv)
    print_summary(rows, errors)


if __name__ == "__main__":
    main()
