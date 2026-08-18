import argparse
import csv
from pathlib import Path

from colorama import Fore, init

from benchmarks.tools.path_safety import resolve_within

init(autoreset=True)


def pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a.strip(), b.strip())))


def load_reference_labels(path: Path) -> dict[tuple[str, str], int]:
    labels = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"img_a", "img_b", "label", "type", "notes"}
        if set(reader.fieldnames or []) != required:
            raise ValueError(
                f"Reference labels headers must be exactly: {sorted(required)}"
            )

        for row in reader:
            k = pair_key(row["img_a"], row["img_b"])
            labels[k] = int(row["label"])
    return labels


def load_predictions(path: Path) -> set[tuple[str, str]]:
    preds = set()
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"img_a", "img_b", "predicted_label"}
        if set(reader.fieldnames or []) != required:
            raise ValueError(f"Predictions headers must be exactly: {sorted(required)}")

        for row in reader:
            if int(row["predicted_label"]) == 1:
                preds.add(pair_key(row["img_a"], row["img_b"]))
    return preds


def safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate predictions against reference labels"
    )
    parser.add_argument("--reference-labels", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    args = parser.parse_args()

    allowed_input_base = (Path.cwd() / "data" / "reviews").resolve()

    try:
        safe_reference_labels = resolve_within(
            allowed_input_base, str(args.reference_labels)
        )
        safe_predictions = resolve_within(allowed_input_base, str(args.predictions))
    except ValueError as e:
        print(f"{Fore.RED}ERROR: {Fore.RESET}{e}")
        raise SystemExit(2)

    if not safe_reference_labels.exists():
        print(
            f"{Fore.RED}ERROR: Missing reference labels file: {safe_reference_labels}"
        )
        raise SystemExit(2)

    if not safe_predictions.exists():
        print(f"{Fore.RED}ERROR: Missing predictions file: {safe_predictions}")
        raise SystemExit(2)

    labels = load_reference_labels(safe_reference_labels)
    preds = load_predictions(safe_predictions)

    tp = fp = fn = tn = 0

    for pair, true_label in labels.items():
        predicted = 1 if pair in preds else 0
        if true_label == 1 and predicted == 1:
            tp += 1
        elif true_label == 0 and predicted == 1:
            fp += 1
        elif true_label == 1 and predicted == 0:
            fn += 1
        else:
            tn += 1

    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall)
    accuracy = safe_div(tp + tn, tp + tn + fp + fn)

    print(f"\n{Fore.GREEN}--- Evaluation (Reference Labels) ---")
    print(f"{Fore.YELLOW}Pairs evaluated: {Fore.CYAN}{len(labels)}")
    print(
        f"{Fore.YELLOW}TP={Fore.CYAN}{tp}  {Fore.YELLOW}FP={Fore.CYAN}{fp}  {Fore.YELLOW}FN={Fore.CYAN}{fn}  {Fore.YELLOW}TN={Fore.CYAN}{tn}"
    )
    print(f"{Fore.YELLOW}Precision: {Fore.CYAN}{precision:.4f}")
    print(f"{Fore.YELLOW}Recall:    {Fore.CYAN}{recall:.4f}")
    print(f"{Fore.YELLOW}F1 Score:  {Fore.CYAN}{f1:.4f}")
    print(f"{Fore.YELLOW}Accuracy:  {Fore.CYAN}{accuracy:.4f}")

    fn_pairs = [
        pair
        for pair, true_label in labels.items()
        if true_label == 1 and pair not in preds
    ]
    if fn_pairs:
        print(f"\n{Fore.RED}False Negatives (label=1 but not predicted):")
        for a, b in fn_pairs:
            print(f"- {a}  <->  {b}")

    extra_preds = [p for p in preds if p not in labels]
    if extra_preds:
        print(
            f"\n{Fore.BLUE}Note: {Fore.RESET}{len(extra_preds)} predicted pair(s) were not present in reference labels."
        )
        print("They were ignored for confusion-matrix scoring.")
        print("Tip: add them to reference labels for full coverage.")


if __name__ == "__main__":
    main()
