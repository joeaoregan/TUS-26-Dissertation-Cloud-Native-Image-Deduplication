import argparse
import csv
import json
from pathlib import Path

from colorama import Fore, init

from benchmarks.tools.path_safety import resolve_within

init(autoreset=True)


def norm_pair(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


def main():
    parser = argparse.ArgumentParser(
        description="Export predicted duplicate pairs from benchmark JSON"
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Benchmark JSON (must include pair_details)",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output CSV path")
    parser.add_argument(
        "--source",
        choices=["stage2", "stage3"],
        default="stage3",
        help="Use stage2 candidates or stage3 verified pairs",
    )
    args = parser.parse_args()

    allowed_input_base = (Path.cwd() / "benchmarks").resolve()
    safe_input = resolve_within(allowed_input_base, str(args.input))

    data = json.loads(safe_input.read_text(encoding="utf-8"))
    pair_details = data.get("pair_details")
    if not pair_details:
        print(
            f"{Fore.RED}ERROR: pair_details not found. Re-run benchmark with --export-pairs"
        )
        raise SystemExit(2)

    if args.source == "stage3":
        pairs = pair_details.get("stage3_verified_sample", [])
    else:
        pairs = pair_details.get("stage2_candidates_sample", [])

    seen = set()
    rows = []
    for item in pairs:
        a = item["file_a"]
        b = item["file_b"]
        k = norm_pair(a, b)
        if k in seen:
            continue
        seen.add(k)
        rows.append({"img_a": k[0], "img_b": k[1], "predicted_label": 1})

    allowed_output_base = (Path.cwd() / "data" / "reviews").resolve()
    safe_output = resolve_within(allowed_output_base, str(args.output))

    safe_output.parent.mkdir(parents=True, exist_ok=True)
    with safe_output.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["img_a", "img_b", "predicted_label"])
        w.writeheader()
        w.writerows(rows)

    print(
        f"{Fore.YELLOW}Exported {len(rows)} predicted pairs to {safe_output} (source={args.source})"
    )


if __name__ == "__main__":
    main()
