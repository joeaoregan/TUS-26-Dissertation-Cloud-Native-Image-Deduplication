# Cloud-Native Perceptual Image Deduplication Platform

![TUS](https://img.shields.io/badge/TUS-2026-black?style=flat-square&logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjwhLS0gQ3JlYXRlZCB3aXRoIElua3NjYXBlIChodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy8pIC0tPgoKPHN2ZwogICB3aWR0aD0iMTU3LjU1OTM2bW0iCiAgIGhlaWdodD0iMjA1LjE3MTE2bW0iCiAgIHZpZXdCb3g9IjAgMCAxNTcuNTU5MzYgMjA1LjE3MTE2IgogICB2ZXJzaW9uPSIxLjEiCiAgIGlkPSJzdmcxIgogICB4bWw6c3BhY2U9InByZXNlcnZlIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxzb2RpcG9kaTpuYW1lZHZpZXcKICAgICBpZD0ibmFtZWR2aWV3MSIKICAgICBwYWdlY29sb3I9IiNmZmZmZmYiCiAgICAgYm9yZGVyY29sb3I9IiMwMDAwMDAiCiAgICAgYm9yZGVyb3BhY2l0eT0iMC4yNSIKICAgICBpbmtzY2FwZTpzaG93cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTpwYWdlb3BhY2l0eT0iMC4wIgogICAgIGlua3NjYXBlOnBhZ2VjaGVja2VyYm9hcmQ9IjAiCiAgICAgaW5rc2NhcGU6ZGVza2NvbG9yPSIjZDFkMWQxIgogICAgIGlua3NjYXBlOmRvY3VtZW50LXVuaXRzPSJtbSI+PGlua3NjYXBlOnBhZ2UKICAgICAgIHg9IjAiCiAgICAgICB5PSIwIgogICAgICAgd2lkdGg9IjE1Ny41NTkzNiIKICAgICAgIGhlaWdodD0iMjA1LjE3MTE2IgogICAgICAgaWQ9InBhZ2UyIgogICAgICAgbWFyZ2luPSIwIgogICAgICAgYmxlZWQ9IjAiIC8+PC9zb2RpcG9kaTpuYW1lZHZpZXc+PGRlZnMKICAgICBpZD0iZGVmczEiPjxzdHlsZQogICAgICAgaWQ9InN0eWxlMSI+LmNscy0xe2ZpbGw6I2EzOTQ2MTt9PC9zdHlsZT48c3R5bGUKICAgICAgIGlkPSJzdHlsZTEtNCI+LmNscy0xe2ZpbGw6I2EzOTQ2MTt9PC9zdHlsZT48L2RlZnM+PGcKICAgICBpbmtzY2FwZTpsYWJlbD0iTGF5ZXIgMSIKICAgICBpbmtzY2FwZTpncm91cG1vZGU9ImxheWVyIgogICAgIGlkPSJsYXllcjEiCiAgICAgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjA4LjE2MDkzLDQ4Ljg3NTE2MikiPjxnCiAgICAgICBpZD0iQXJ0d29yayIKICAgICAgIHRyYW5zZm9ybT0ibWF0cml4KDAuMjY0NTgzMzMsMCwwLDAuMjY0NTgzMzMsLTIwOC4xNjA5NCwtNDguODc1MTU4KSI+PHBhdGgKICAgICAgICAgY2xhc3M9ImNscy0xIgogICAgICAgICBkPSJNIDU5NS40OCwwIEggNDc2LjM4IFYgNTguNTIgSCAzNTcuMyBWIDAgSCAyMzguMiBWIDU4LjUyIEggMTE5LjEgViAwIEggMCB2IDM1Ny4yOSBoIDExOS4xIGEgMTc4LjY0LDE3OC42NCAwIDEgMSAzNTcuMjgsMCBoIDExOS4wNiB6IgogICAgICAgICBpZD0icGF0aDEiIC8+PHJlY3QKICAgICAgICAgY2xhc3M9ImNscy0xIgogICAgICAgICB4PSI0NzYuMzgiCiAgICAgICAgIHk9IjcxNS45MDAwMiIKICAgICAgICAgd2lkdGg9IjExOS4xIgogICAgICAgICBoZWlnaHQ9IjU5LjU0OTk5OSIKICAgICAgICAgaWQ9InJlY3QxIiAvPjxyZWN0CiAgICAgICAgIGNsYXNzPSJjbHMtMSIKICAgICAgICAgeT0iNzE1LjkwMDAyIgogICAgICAgICB3aWR0aD0iMTE5LjEiCiAgICAgICAgIGhlaWdodD0iNTkuNTQ5OTk5IgogICAgICAgICBpZD0icmVjdDIiCiAgICAgICAgIHg9IjAiIC8+PHJlY3QKICAgICAgICAgY2xhc3M9ImNscy0xIgogICAgICAgICB5PSI1OTYuNzk5OTkiCiAgICAgICAgIHdpZHRoPSIxMTkuMSIKICAgICAgICAgaGVpZ2h0PSI1OS41NDk5OTkiCiAgICAgICAgIGlkPSJyZWN0MyIKICAgICAgICAgeD0iMCIgLz48cmVjdAogICAgICAgICBjbGFzcz0iY2xzLTEiCiAgICAgICAgIHg9IjQ3Ni4zOTk5OSIKICAgICAgICAgeT0iNTk2Ljc5OTk5IgogICAgICAgICB3aWR0aD0iMTE5LjEiCiAgICAgICAgIGhlaWdodD0iNTkuNTQ5OTk5IgogICAgICAgICBpZD0icmVjdDQiIC8+PHJlY3QKICAgICAgICAgY2xhc3M9ImNscy0xIgogICAgICAgICB4PSIxMTkuMSIKICAgICAgICAgeT0iNTM3LjI1IgogICAgICAgICB3aWR0aD0iMzU3LjI5OTk5IgogICAgICAgICBoZWlnaHQ9IjU5LjU0OTk5OSIKICAgICAgICAgaWQ9InJlY3Q1IiAvPjxwb2x5Z29uCiAgICAgICAgIGNsYXNzPSJjbHMtMSIKICAgICAgICAgcG9pbnRzPSI0NzYuMzksNjU2LjM1IDExOS4xLDY1Ni4zNSAxMTkuMSw3MTUuOSAyMzguMiw3MTUuOSAyMzguMiw3NzUuNDUgMzU3LjI5LDc3NS40NSAzNTcuMjksNzE1LjkgNDc2LjM5LDcxNS45ICIKICAgICAgICAgaWQ9InBvbHlnb241IiAvPjxyZWN0CiAgICAgICAgIGNsYXNzPSJjbHMtMSIKICAgICAgICAgeD0iNDc2LjM5OTk5IgogICAgICAgICB5PSI0MTguMTYiCiAgICAgICAgIHdpZHRoPSIxMTkuMSIKICAgICAgICAgaGVpZ2h0PSIxMTkuMSIKICAgICAgICAgaWQ9InJlY3Q2IiAvPjxyZWN0CiAgICAgICAgIGNsYXNzPSJjbHMtMSIKICAgICAgICAgeT0iNDE4LjE2IgogICAgICAgICB3aWR0aD0iMTE5LjEiCiAgICAgICAgIGhlaWdodD0iMTE5LjEiCiAgICAgICAgIGlkPSJyZWN0NyIKICAgICAgICAgeD0iMCIgLz48L2c+PC9nPjwvc3ZnPgo=)
![Module](https://img.shields.io/badge/Module-Dissertation-blue?style=flat-square)
![Topic](https://img.shields.io/badge/Topic-Perceptual%20Image%20Deduplication-yellow?style=flat-square)

![testing](https://img.shields.io/badge/testing-pytest-blue?style=flat-square&logo=pytest)
![benchmarks](https://img.shields.io/badge/benchmarks-included-blue?style=flat-square&logo=speedtest)

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
├── core_engine/
│   ├── pipeline.py              # Cascading Hybrid Entry Point
│   ├── requirements.txt         # Python dependencies (Pillow, ImageHash, colorama)
│   └── utils/
│       ├── __init__.py          # Python package marker file
│       ├── dedupe_exact.py      # Stage 1: Cryptographic byte-level verification
│       └── dedupe_perceptual.py # Stage 2: Perceptual structural matching
│       └── dedupe_ssim.py       # Stage 3: Fine Structural Similarity (SSIM) verification
└── dedupe_test/                 # Evaluation testing dataset
```

## Setup

1. Initialise and Active Virtual Environment

```bash
# Create the virtual environment (run once)
python -m venv venv

# Activate the environment (Windows Git Bash)
source venv/Scripts/activate
```

## Requirements

```bash
# Install core dependencies (Pillow, ImageHash, and colorama)
pip install -r core_engine/requirements.txt
```

## Run Stage Execution

1. Exact Byte-Level Deduplication (SHA-256)
This script performs rapid cryptographic verification at the binary level. It catches exact copies but misses modified file formats or compressed streams due to the avalanche effect.

```bash
python core_engine/utils/dedupe_exact.py dedupe_test
```
2. Perceptual Image Hashing (pHash)
This script calculates structural visual fingerprints to identify near-duplicates (e.g., format shifts, resizing, compression noise) by computing bitwise Hamming Distances.

```bash
python core_engine/utils/dedupe_perceptual.py dedupe_test
```

3. Structural Similarity Index Measure (SSIM) Verification
This script performs fine-grained structural comparison between two candidate image paths to output a similarity score (-1.0 to 1.0).

```bash
python -m core_engine.utils.dedupe_ssim "dedupe_test/me.jpg" "dedupe_test/me - Copy.jpg"
```

## Running the Hybrid Cascading Pipeline

The unified hybrid execution combines all three modules to optimize compute performance. It runs SHA-256 byte-matching first, evaluates pHash visual candidates on unique media, and applies an SSIM verification gate to confirm high-confidence visual matches.

You can execute the entire pipeline directly from your main project root directory:

```bash
python -m core_engine.pipeline dedupe_test
```

## Testing

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
To run the performance benchmark and generate a metric report:

* Execute script: `python -m benchmarks.benchmark_pipeline`

### Output Metrics
Results are automatically exported to `benchmarks/results.json` containing:
* Execution duration (in milliseconds) per stage.
* Peak memory allocation (in MB) tracked via `tracemalloc`.
* Total cascading pipeline elapsed time.

### Benchmark Baseline (`dedupe_test`)

| Stage | Algorithm | Execution Time | Peak Memory | Output |
| :--- | :--- | :---: | :---: | :---: |
| **Stage 1** | SHA-256 Hashing | 2.22 ms | 1.75 MB | Filtered exact copies |
| **Stage 2** | Perceptual Hash (pHash) | 103.18 ms | 1.49 MB | 4 candidate pairs |
| **Stage 3** | SSIM Verification | 83.16 ms | 11.86 MB | 2 verified duplicates |
| **Total** | **Cascading Pipeline** | **188.56 ms** | — | — |