# Cloud-Native Perceptual Image Deduplication Platform

![TUS](https://img.shields.io/badge/TUS-2026-black?style=flat-square&logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjwhLS0gQ3JlYXRlZCB3aXRoIElua3NjYXBlIChodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy8pIC0tPgoKPHN2ZwogICB3aWR0aD0iMTU3LjU1OTM2bW0iCiAgIGhlaWdodD0iMjA1LjE3MTE2bW0iCiAgIHZpZXdCb3g9IjAgMCAxNTcuNTU5MzYgMjA1LjE3MTE2IgogICB2ZXJzaW9uPSIxLjEiCiAgIGlkPSJzdmcxIgogICB4bWw6c3BhY2U9InByZXNlcnZlIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxzb2RpcG9kaTpuYW1lZHZpZXcKICAgICBpZD0ibmFtZWR2aWV3MSIKICAgICBwYWdlY29sb3I9IiNmZmZmZmYiCiAgICAgYm9yZGVyY29sb3I9IiMwMDAwMDAiCiAgICAgYm9yZGVyb3BhY2l0eT0iMC4yNSIKICAgICBpbmtzY2FwZTpzaG93cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTpwYWdlb3BhY2l0eT0iMC4wIgogICAgIGlua3NjYXBlOnBhZ2VjaGVja2VyYm9hcmQ9IjAiCiAgICAgaW5rc2NhcGU6ZGVza2NvbG9yPSIjZDFkMWQxIgogICAgIGlua3NjYXBlOmRvY3VtZW50LXVuaXRzPSJtbSI+PGlua3NjYXBlOnBhZ2UKICAgICAgIHg9IjAiCiAgICAgICB5PSIwIgogICAgICAgd2lkdGg9IjE1Ny41NTkzNiIKICAgICAgIGhlaWdodD0iMjA1LjE3MTE2IgogICAgICAgaWQ9InBhZ2UyIgogICAgICAgbWFyZ2luPSIwIgogICAgICAgYmxlZWQ9IjAiIC8+PC9zb2RpcG9kaTpuYW1lZHZpZXc+PGRlZnMKICAgICBpZD0iZGVmczEiPjxzdHlsZQogICAgICAgaWQ9InN0eWxlMSI+LmNscy0xe2ZpbGw6I2EzOTQ2MTt9PC9zdHlsZT48c3R5bGUKICAgICAgIGlkPSJzdHlsZTEtNCI+LmNscy0xe2ZpbGw6I2EzOTQ2MTt9PC9zdHlsZT48L2RlZnM+PGcKICAgICBpbmtzY2FwZTpsYWJlbD0iTGF5ZXIgMSIKICAgICBpbmtzY2FwZTpncm91cG1vZGU9ImxheWVyIgogICAgIGlkPSJsYXllcjEiCiAgICAgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjA4LjE2MDkzLDQ4Ljg3NTE2MikiPjxnCiAgICAgICBpZD0iQXJ0d29yayIKICAgICAgIHRyYW5zZm9ybT0ibWF0cml4KDAuMjY0NTgzMzMsMCwwLDAuMjY0NTgzMzMsLTIwOC4xNjA5NCwtNDguODc1MTU4KSI+PHBhdGgKICAgICAgICAgY2xhc3M9ImNscy0xIgogICAgICAgICBkPSJNIDU5NS40OCwwIEggNDc2LjM4IFYgNTguNTIgSCAzNTcuMyBWIDAgSCAyMzguMiBWIDU4LjUyIEggMTE5LjEgViAwIEggMCB2IDM1Ny4yOSBoIDExOS4xIGEgMTc4LjY0LDE3OC42NCAwIDEgMSAzNTcuMjgsMCBoIDExOS4wNiB6IgogICAgICAgICBpZD0icGF0aDEiIC8+PHJlY3QKICAgICAgICAgY2xhc3M9ImNscy0xIgogICAgICAgICB4PSI0NzYuMzgiCiAgICAgICAgIHk9IjcxNS45MDAwMiIKICAgICAgICAgd2lkdGg9IjExOS4xIgogICAgICAgICBoZWlnaHQ9IjU5LjU0OTk5OSIKICAgICAgICAgaWQ9InJlY3QxIiAvPjxyZWN0CiAgICAgICAgIGNsYXNzPSJjbHMtMSIKICAgICAgICAgeT0iNzE1LjkwMDAyIgogICAgICAgICB3aWR0aD0iMTE5LjEiCiAgICAgICAgIGhlaWdodD0iNTkuNTQ5OTk5IgogICAgICAgICBpZD0icmVjdDIiCiAgICAgICAgIHg9IjAiIC8+PHJlY3QKICAgICAgICAgY2xhc3M9ImNscy0xIgogICAgICAgICB5PSI1OTYuNzk5OTkiCiAgICAgICAgIHdpZHRoPSIxMTkuMSIKICAgICAgICAgaGVpZ2h0PSI1OS41NDk5OTkiCiAgICAgICAgIGlkPSJyZWN0MyIKICAgICAgICAgeD0iMCIgLz48cmVjdAogICAgICAgICBjbGFzcz0iY2xzLTEiCiAgICAgICAgIHg9IjQ3Ni4zOTk5OSIKICAgICAgICAgeT0iNTk2Ljc5OTk5IgogICAgICAgICB3aWR0aD0iMTE5LjEiCiAgICAgICAgIGhlaWdodD0iNTkuNTQ5OTk5IgogICAgICAgICBpZD0icmVjdDQiIC8+PHJlY3QKICAgICAgICAgY2xhc3M9ImNscy0xIgogICAgICAgICB4PSIxMTkuMSIKICAgICAgICAgeT0iNTM3LjI1IgogICAgICAgICB3aWR0aD0iMzU3LjI5OTk5IgogICAgICAgICBoZWlnaHQ9IjU5LjU0OTk5OSIKICAgICAgICAgaWQ9InJlY3Q1IiAvPjxwb2x5Z29uCiAgICAgICAgIGNsYXNzPSJjbHMtMSIKICAgICAgICAgcG9pbnRzPSI0NzYuMzksNjU2LjM1IDExOS4xLDY1Ni4zNSAxMTkuMSw3MTUuOSAyMzguMiw3MTUuOSAyMzguMiw3NzUuNDUgMzU3LjI5LDc3NS40NSAzNTcuMjksNzE1LjkgNDc2LjM5LDcxNS45ICIKICAgICAgICAgaWQ9InBvbHlnb241IiAvPjxyZWN0CiAgICAgICAgIGNsYXNzPSJjbHMtMSIKICAgICAgICAgeD0iNDc2LjM5OTk5IgogICAgICAgICB5PSI0MTguMTYiCiAgICAgICAgIHdpZHRoPSIxMTkuMSIKICAgICAgICAgaGVpZ2h0PSIxMTkuMSIKICAgICAgICAgaWQ9InJlY3Q2IiAvPjxyZWN0CiAgICAgICAgIGNsYXNzPSJjbHMtMSIKICAgICAgICAgeT0iNDE4LjE2IgogICAgICAgICB3aWR0aD0iMTE5LjEiCiAgICAgICAgIGhlaWdodD0iMTE5LjEiCiAgICAgICAgIGlkPSJyZWN0NyIKICAgICAgICAgeD0iMCIgLz48L2c+PC9nPjwvc3ZnPgo=)
![Module](https://img.shields.io/badge/Module-Dissertation-blue?style=flat-square)
![Topic](https://img.shields.io/badge/Topic-Perceptual%20Image%20Deduplication-yellow?style=flat-square)

![testing](https://img.shields.io/badge/testing-pytest-blue?style=flat-square&logo=pytest)
![benchmarks](https://img.shields.io/badge/benchmarks-included-blue?style=flat-square&logo=speedtest)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=joeaoregan_TUS-26-Dissertation-Cloud-Native-Image-Deduplication&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=joeaoregan_TUS-26-Dissertation-Cloud-Native-Image-Deduplication)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=joeaoregan_TUS-26-Dissertation-Cloud-Native-Image-Deduplication&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=joeaoregan_TUS-26-Dissertation-Cloud-Native-Image-Deduplication)

[![Python Version](https://img.shields.io/badge/Python-3.13-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
![pytest](https://img.shields.io/badge/pytest-passing-brightgreen?logo=pytest)

![GitHub repo size](https://img.shields.io/github/repo-size/joeaoregan/TUS-26-Dissertation-Cloud-Native-Image-Deduplication?color=orange)
![GitHub last commit](https://img.shields.io/github/last-commit/joeaoregan/TUS-26-Dissertation-Cloud-Native-Image-Deduplication?color=blue)
![GitHub top language](https://img.shields.io/github/languages/top/joeaoregan/TUS-26-Dissertation-Cloud-Native-Image-Deduplication)
![Stars](https://img.shields.io/github/stars/joeaoregan/TUS-26-Dissertation-Cloud-Native-Image-Deduplication?style=social)

A multi-stage, cascading image deduplication pipeline designed to identify exact file duplicates alongside visually similar, compressed, or resized media variations.

---

## Structure

```text
## Structure

```text
├── services/
│   └── dedupe-py/                       # Python deduplication service
│       ├── benchmarks/                  # Benchmark runner and analysis helpers
│       │   ├── benchmark_pipeline.py    # Runs staged benchmark, timings/memory, and JSON output
│       │   ├── constants.py             # Shared benchmark defaults (runs, thresholds, pair limits)
│       │   ├── exports.py               # Formats stage outputs (groups/candidates/verified) for JSON export
│       │   ├── measurement.py           # Timing + peak-memory measurement utilities (warmup/measured runs)
│       │   ├── profile.py               # Dataset profiling (file counts, size, formats, resolution ranges)
│       │   └── tools/                   # Evaluation and review workflow scripts
│       │       ├── build_review_html.py         # Builds side-by-side HTML reviewer from exported benchmark pairs
│       │       ├── evaluate_predictions.py      # Computes TP/FP/FN/TN and Precision/Recall/F1/Accuracy from labels vs predictions
│       │       ├── export_predictions.py        # Exports stage pair predictions from benchmark JSON to CSV
│       │       └── validate_reference_labels.py # Validates reference label CSV schema, label values, and duplicate/invalid rows
│       ├── core_engine/
│       │   ├── pipeline.py              # Cascading Hybrid Entry Point
│       │   ├── requirements.txt         # Python dependencies (Pillow, ImageHash, colorama)
│       │   └── utils/
│       │       ├── __init__.py          # Python package marker file
│       │       ├── dedupe_exact.py      # Stage 1: Cryptographic byte-level verification
│       │       ├── dedupe_perceptual.py # Stage 2: Perceptual structural matching
│       │       └── dedupe_ssim.py       # Stage 3: Fine Structural Similarity (SSIM) verification
│       ├── api/                         # API wrapper (cloud-native in-progress)
│       ├── worker/                      # Background worker (cloud-native in-progress)
│       ├── jobs/                        # Job model/state handling (cloud-native in-progress)
│       └── scripts/                     # Utility scripts (docker benchmark helpers, etc.)
├── data/
│   ├── dedupe_test/                     # Evaluation testing dataset (small)
│   ├── dedupe_test_100/                 # Evaluation testing dataset (100 images)
│   ├── dedupe_test_100_clean/           # Evaluation testing dataset (100 unique, unaltered images)
│   ├── labels/                          # Reference label CSV files
│   ├── predictions/                     # Prediction stage CSV outputs
│   └── reviews/                         # Side-by-side comparison HTML review files
├── tests/                               # Test files (unit + integration)
├── logs/                                # JSON log / benchmark output files
├── docker-compose.yml                   # Local container orchestration
├── RUNBOOK.md                           # Reproducibility guide
└── README.md                            # Project overview and usage
```

## Setup

1. Initialise and Activate Virtual Environment

```bash
py -3.13 -m venv venv
source venv/Scripts/activate
```

2) Install dependencies

```bash
pip install -r services/dedupe-py/core_engine/requirements.txt
```
### Python Version

This project is tested with **Python 3.13.x** (benchmark runs validated on **3.13.15**).

> Note: Python 3.14 may fail dependency installation (notably NumPy/scikit-image wheel compatibility) unless package versions are updated.

## Run Stage Execution

Run from repository root with PYTHONPATH set:

```bash
export PYTHONPATH=services/dedupe-py
```

1. Exact Byte-Level Deduplication (SHA-256)  
  This script performs rapid cryptographic verification at the binary level. It catches exact copies but misses modified file formats or compressed streams due to the avalanche effect.
```bash
python -m core_engine.utils.dedupe_exact data/dedupe_test
```

2. Perceptual Image Hashing (pHash)  
  This script calculates structural visual fingerprints to identify near-duplicates (e.g., format shifts, resizing, compression noise) by computing bitwise Hamming distances.
```bash
python -m core_engine.utils.dedupe_perceptual data/dedupe_test
```

3. Structural Similarity Index Measure (SSIM) Verification  
  This script performs fine-grained structural comparison between two candidate image paths to output a similarity score (-1.0 to 1.0).

```bash
python -m core_engine.utils.dedupe_ssim "data/dedupe_test/me.jpg" "data/dedupe_test/me - Copy.jpg"
```

## Running the Hybrid Cascading Pipeline

The unified hybrid execution combines all three modules to optimise compute performance. It runs SHA-256 byte-matching first, evaluates pHash visual candidates on unique media, and applies an SSIM verification pass to reduce false positives.

You can execute the entire pipeline directly from your main project root directory:

```bash
export PYTHONPATH=services/dedupe-py
python -m core_engine.pipeline data/dedupe_test
```

## Testing

Run from repository root:

- pytest
- pytest -v

Test suite includes:

- tests/test_dedupe_exact.py
- tests/test_dedupe_perceptual.py
- tests/test_dedupe_ssim.py
- tests/test_pipeline.py

The project includes a `pytest` unit and integration test suite covering all deduplication stages and edge cases.

### Run All Tests
To execute the full test suite, run from the repository root:

* Run standard tests: `pytest`
* Run with verbose output: `pytest -v`

### Test Suite Structure
* **`tests/test_dedupe_exact.py`** – Stage 1 SHA-256 exact byte-hashing tests.
* **`tests/test_dedupe_perceptual.py`** – Stage 2 pHash perceptual matching tests.
* **`tests/test_dedupe_ssim.py`** – Stage 3 SSIM structural similarity tests.
* **`tests/test_pipeline.py`** – End-to-end cascading pipeline integration tests.

## Performance Benchmarking

The project includes an empirical benchmarking module to profile execution timing and peak memory usage across all three deduplication stages.

### Run Benchmarks

From repository root:

```bash
# Default dataset + default output
export PYTHONPATH=services/dedupe-py
python -m benchmarks.benchmark_pipeline

# Custom dataset directory + custom output JSON
python -m benchmarks.benchmark_pipeline --dir dedupe_test_100 --output logs/eval-100.json

# Export sample duplicate/candidate/verified pair details
python -m benchmarks.benchmark_pipeline --dir dedupe_test_100 --output logs/eval-100.json --export-pairs

# Increase export cap per pair section
python -m benchmarks.benchmark_pipeline --dir dedupe_test_100 --output logs/eval-100.json --export-pairs --pair-limit 300

# Disable timestamped snapshot
python -m benchmarks.benchmark_pipeline --dir dedupe_test_100 --output logs/eval-100.json --no-timestamp
```

### Why Stage 3 Can Be `0.0 ms`

If Stage 2 returns zero candidate pairs, Stage 3 has no work to perform and may report `0.0 ms` and `0.0 MB`.  
This is expected behaviour, not a failure.

Use **Detection Counts** in the output to interpret this:
- `stage2_candidate_pairs = 0` ⇒ Stage 3 verification loop is skipped.

### Benchmark Example (`dedupe_test_100`)

> Note: Benchmark values are hardware-, dataset-, and run-condition-dependent.

| Stage | Algorithm | Execution Time (mean ± sd) | Peak Memory (mean ± sd) | Output |
| :--- | :--- | :---: | :---: | :--- |
| **Stage 1** | SHA-256 Hashing | 10.06 ± 0.89 ms | 1.65 ± 0.00 MB | Exact duplicate groups / redundant files |
| **Stage 2** | Perceptual Hash (pHash) | 192.11 ± 3.95 ms | 0.20 ± 0.00 MB | Candidate near-duplicate pairs |
| **Stage 3** | SSIM Verification | 0.00 ± 0.00 ms | 0.00 ± 0.00 MB | Verified near-duplicate pairs |
| **Total** | **Cascading Pipeline** | **202.16 ± 3.93 ms** | **Peak: 1.65 MB** | Full pipeline |

**Dataset profile (example run):**
- Total images: 100
- Total size: 12.97 MB (13,596,493 bytes)
- Formats: `{'.jpeg': 100}`
- Resolution range: `120x90 -> 900x1000`

### Output Metrics

Benchmark results are exported to:
- Canonical latest file: `logs/results.json` (or custom `--output`)
- Timestamped snapshot: `logs/<name>-YYYYMMDD-HHMMSS.json` (unless `--no-timestamp` is used)

Each report now includes:

- **Timing metrics** (ms): raw per-iteration values, mean, standard deviation
- **Peak RAM metrics** (MB): raw per-iteration values, mean, standard deviation
- **Detection counts**:
  - Stage 1 exact duplicate groups
  - Stage 1 redundant files
  - Stage 2 candidate pairs
  - Stage 3 verified pairs
- **Dataset profile**:
  - total file count
  - total size (bytes/MB)
  - format distribution
  - width/height min/max
  - resolution range
  - profiling read warning count
- **Environment metadata**:
  - OS
  - Python version
  - processor/machine
  - total RAM
- **Benchmark config**:
  - pHash threshold
  - SSIM threshold
  - pair export enabled/disabled
  - pair export limit

When `--export-pairs` is enabled, JSON also includes `pair_details` samples:
- Stage 1 exact duplicate groups (with file lists)
- Stage 2 candidate pairs (`file_a`, `file_b`, `phash_distance`)
- Stage 3 verified pairs (`file_a`, `file_b`, `ssim_score`)

### Historical Baseline (`dedupe_test`)

> Note: Benchmark values are hardware-, dataset-, and run-condition-dependent.

Earlier small-set baseline run (for continuity with prior commits):

- Stage 1: 2.22 ms
- Stage 2: 103.18 ms
- Stage 3: 83.16 ms
- Total: 188.56 ms

## Docker Benchmark Reproduction (Verified)

Both scripts validated successfully on **2026-08-18**.

PowerShell (Windows):

```powershell
powershell -ExecutionPolicy Bypass -File .\services\dedupe-py\scripts\run_docker_benchmark.ps1
```

Git Bash:

```bash
bash services/dedupe-py/scripts/run_docker_benchmark.sh
```

Notes:

- Dockerfile: services/dedupe-py/Dockerfile
- Output artifacts are written to repository root logs/

## Correctness Evaluation with Reference Labels

To evaluate detection quality (not just performance), this project uses manually verified **Reference Labels**.

#### Files
- `data/labels/reference_labels_eval_v1.csv` — labelled image pairs (`label=1` duplicate, `label=0` non-duplicate)
- `benchmarks/tools/validate_reference_labels.py` — validates CSV schema, paths, labels, and duplicate pairs
- `benchmarks/tools/export_predictions.py` — exports predicted pairs from benchmark JSON
- `benchmarks/tools/evaluate_predictions.py` — computes TP/FP/FN/TN, Precision, Recall, F1, Accuracy
- `benchmarks/tools/build_review_html.py` — optional side-by-side HTML reviewer for pair adjudication

#### Workflow

```bash
export PYTHONPATH=services/dedupe-py
python -m benchmarks.benchmark_pipeline --dir ./data/dedupe_test_100 --output logs/eval-100-YYYYMMDD-HHMMSS.json --export-pairs --pair-limit 500
python -m benchmarks.tools.validate_reference_labels --csv reference_labels_eval_v1.csv
```

broken for now:

```bash
python -m benchmarks.tools.export_predictions --input logs/eval-100-YYYYMMDD-HHMMSS.json --output data/predictions/pred_stage3_eval100.csv --source stage3
python -m benchmarks.tools.evaluate_predictions --reference-labels data/labels/reference_labels_eval_v1.csv --predictions data/predictions/pred_stage3_eval100.csv
```

## Threshold Tuning

| Run tag | pHash | SSIM | Stage2 candidates | Stage3 verified | TP | FP | FN | TN | Precision | Recall | F1 | Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| threshold-tuning-baseline-phash5-ssim085 | 5 | 0.85 | 53 | 49 | 48 | 0 | 3 | 8 | 1.0000 | 0.9412 | 0.9697 | 0.9492 |
| threshold-tuning-phash4-ssim085 | 4 | 0.85 | 53 | 49 | 48 | 0 | 3 | 8 | 1.0000 | 0.9412 | 0.9697 | 0.9492 |
| threshold-tuning-phash4-ssim090 | 4 | 0.90 | 53 | 48 | 47 | 0 | 4 | 8 | 1.0000 | 0.9216 | 0.9592 | 0.9322 |
| threshold-tuning-phash5-ssim090 | 5 | 0.90 | 53 | 48 | 47 | 0 | 4 | 8 | 1.0000 | 0.9216 | 0.9592 | 0.9322 |
| threshold-tuning-phash6-ssim085 | 6 | 0.85 | 53 | 49 | 48 | 0 | 3 | 8 | 1.0000 | 0.9412 | 0.9697 | 0.9492 |
| threshold-tuning-phash6-ssim090 | 6 | 0.90 | 53 | 48 | 47 | 0 | 4 | 8 | 1.0000 | 0.9216 | 0.9592 | 0.9322 |
| threshold-tuning-phash7-ssim090 | 7 | 0.90 | 53 | 48 | 47 | 0 | 4 | 8 | 1.0000 | 0.9216 | 0.9592 | 0.9322 |

**Selected operating point:** `pHash=5`, `SSIM=0.85`.

Across tested values, changing pHash from 4 to 7 did not change outcomes on this dataset.  
Increasing SSIM from 0.85 to 0.90 reduced recall (0.9412 → 0.9216) with no precision gain (remained 1.0000).  
Therefore, SSIM=0.85 was retained as the better precision/recall balance.

### Threats to Validity

- **Dataset size/composition:** These results come from a controlled 100-image test set; performance may change on larger, more varied real-world image datasets.
- **Label coverage:** One predicted pair was not present in the reference labels and was excluded from confusion-matrix scoring, which may slightly understate/overstate final metrics.
- **Transformation scope:** The benchmark emphasises specific transformations (copy, format conversion, brightness/colour edits, compression). Performance may differ for other distortions (crop, heavy blur, perspective changes).
- **Threshold generalisability:** The chosen thresholds (`pHash=5`, `SSIM=0.85`) are empirically suitable for this dataset; re-tuning may be required for different domains.
- **Environment dependence:** Timing and memory figures are machine-dependent (Windows 11, Python 3.13, local hardware) and are not directly comparable across systems.

## Final Baseline

- **Config:** pHash=5, SSIM=0.85
- **Pairs evaluated**: 59
- TP / FP / FN / TN: 48 / 0 / 3 / 8
- Precision / Recall / F1 / Accuracy: 1.0000 / 0.9412 / 0.9697 / 0.9492
- **Known misses:**
  - ILSVRC2012_val_00000139.JPEG ↔ ILSVRC2012_val_00000139_brightness_up.jpg
  - ILSVRC2012_val_00000141.JPEG ↔ ILSVRC2012_val_00000141_brightness_up.jpg
  - ILSVRC2012_val_00000126.JPEG ↔ ILSVRC2012_val_00000126_green.jpg

- **Observation:** Missed pairs tend to have low-colour or near-grayscale content with subtle brightness/colour shifts, which can reduce SSIM enough to fall below the threshold.

### Reproducibility:

```bash
export PYTHONPATH=services/dedupe-py
python -m benchmarks.benchmark_pipeline --dir dedupe_test_100 --output logs/final-baseline-phash5-ssim085.json --export-pairs --pair-limit 500 --phash-threshold 5 --ssim-threshold 0.85 --run-tag final-baseline
python -m benchmarks.tools.export_predictions --input logs/final-baseline-phash5-ssim085.json --output data/predictions/final-baseline-phash5-ssim085-stage3.csv --source stage3
python -m benchmarks.tools.evaluate_predictions --reference-labels data/labels/reference_labels_eval_v1.csv --predictions data/predictions/final-baseline-phash5-ssim085-stage3.csv
```

## Related Docs

- RUNBOOK.md — reproducibility-focused execution guide
- services/dedupe-py/scripts/README.md — Docker benchmark script usage
```