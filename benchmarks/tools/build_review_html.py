import argparse
import csv
import json
from html import escape
from pathlib import Path

from colorama import Fore, init

init(autoreset=True)


def norm_pair(a: str, b: str) -> tuple[str, str]:
    a = a.replace("\\", "/").strip()
    b = b.replace("\\", "/").strip()
    return tuple(sorted((a, b)))


def load_reference_labels(path: Path):
    labels = {}
    if not path or not path.exists():
        return labels
    allowed_input_base = (
        Path.cwd() / "data" / "reviews"
    ).resolve()  # choose strict base
    safe_path = resolve_within(allowed_input_base, str(path))

    with safe_path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            k = norm_pair(row["img_a"], row["img_b"])
            labels[k] = {
                "label": row["label"].strip(),
                "type": row["type"].strip(),
                "notes": row["notes"].strip(),
            }
    return labels


def resolve_within(base_dir: Path, user_input: str) -> Path:
    base = base_dir.resolve()
    target = Path(user_input)
    if not target.is_absolute():
        target = (base / target).resolve()
    else:
        target = target.resolve()
    if target != base and base not in target.parents:
        raise ValueError(f"Path escapes allowed directory: {user_input}")
    return target


def main():
    parser = argparse.ArgumentParser(
        description="Build side-by-side HTML pair reviewer"
    )
    parser.add_argument(
        "--input", required=True, type=Path, help="Benchmark JSON with pair_details"
    )
    parser.add_argument(
        "--output", default=Path("benchmarks/review_pairs.html"), type=Path
    )
    parser.add_argument("--source", choices=["stage2", "stage3"], default="stage3")
    parser.add_argument("--reference-labels", type=Path, default=None)
    args = parser.parse_args()
    allowed_input_base = (Path.cwd() / "benchmarks").resolve()  # adjust if needed
    safe_input = resolve_within(allowed_input_base, str(args.input))

    data = json.loads(safe_input.read_text(encoding="utf-8"))
    pd = data.get("pair_details", {})
    pairs = (
        pd.get("stage3_verified_sample", [])
        if args.source == "stage3"
        else pd.get("stage2_candidates_sample", [])
    )

    if not pairs:
        print(
            f"{Fore.RED}No pairs found. Re-run benchmark with --export-pairs and suitable --pair-limit."
        )
        raise SystemExit(1)

    ref = load_reference_labels(args.reference_labels)

    rows_html = []
    for i, p in enumerate(pairs, start=1):
        a = str(p["file_a"]).replace("\\", "/")
        b = str(p["file_b"]).replace("\\", "/")
        k = norm_pair(a, b)

        ref_label = ref.get(k, {}).get("label", "")
        ref_type = ref.get(k, {}).get("type", "")
        ref_notes = ref.get(k, {}).get("notes", "")

        metric = ""
        if "ssim_score" in p:
            metric = f"SSIM: {p['ssim_score']}"
        elif "phash_distance" in p:
            metric = f"pHash distance: {p['phash_distance']}"

        rows_html.append(
            f"""
<tr>
  <td>{i}</td>
  <td><div class="path">{escape(a)}</div><img src="../{escape(a)}" loading="lazy"></td>
  <td><div class="path">{escape(b)}</div><img src="../{escape(b)}" loading="lazy"></td>
  <td>{escape(metric)}</td>
  <td>
    <select>
      <option value="">-- choose --</option>
      <option value="1" {"selected" if ref_label == "1" else ""}>duplicate (1)</option>
      <option value="0" {"selected" if ref_label == "0" else ""}>non-duplicate (0)</option>
      <option value="u">unsure</option>
    </select>
    <div class="small">type: {escape(ref_type)}</div>
    <input type="text" value="{escape(ref_notes)}" placeholder="notes...">
  </td>
</tr>
"""
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pair Reviewer ({args.source})</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 16px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
th {{ background: #f4f4f4; }}
img {{ max-width: 320px; max-height: 220px; display: block; border: 1px solid #ccc; margin-top: 6px; }}
.path {{ font-family: Consolas, monospace; font-size: 12px; color: #333; word-break: break-all; }}
.small {{ font-size: 12px; color: #666; margin-top: 6px; }}
input[type=text] {{ width: 96%; margin-top: 6px; }}
button {{ margin-right: 8px; }}
</style>
</head>
<body>
<h2>Side-by-side Pair Reviewer ({escape(args.source)})</h2>
<p>Tip: after reviewing labels, click "Export CSV" and save output as <code>benchmarks/reference_labels_eval_v2.csv</code>.</p>
<button onclick="exportCsv()">Export CSV (from table)</button>
<label for="out" class="sr-only">CSV output</label>
<textarea id="out" rows="10" style="width:100%;margin-top:10px;" placeholder="CSV output appears here..."></textarea>
<table>
<thead>
<tr><th>#</th><th>Image A</th><th>Image B</th><th>Metric</th><th>Review</th></tr>
</thead>
<tbody>
{"".join(rows_html)}
</tbody>
</table>

<script>
function exportCsv() {{
  const rows = [];
  rows.push("img_a,img_b,label,type,notes");
  const trs = document.querySelectorAll("tbody tr");
  trs.forEach(tr => {{
    const tds = tr.querySelectorAll("td");
    const a = tds[1].querySelector(".path").textContent.trim();
    const b = tds[2].querySelector(".path").textContent.trim();
    const sel = tds[4].querySelector("select").value;
    const note = tds[4].querySelector("input").value.trim();
    let type = "near";
    if (a.includes(" - Copy.") || b.includes(" - Copy.")) type = "exact";
    if (sel === "1" || sel === "0") {{
      const safe = (s) => '"' + String(s).replaceAll('"', '""') + '"';
      rows.push([safe(a), safe(b), sel, type, safe(note)].join(","));
    }}
  }});
  document.getElementById("out").value = rows.join("\\n");
}}
</script>
</body>
</html>
"""

    allowed_output_base = (
        Path.cwd() / "data" / "reviews"
    ).resolve()  # choose strict base
    safe_output = resolve_within(allowed_output_base, str(args.output))
    safe_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"{Fore.YELLOW}Review HTML written to: {Fore.CYAN}{args.output}")


if __name__ == "__main__":
    main()
