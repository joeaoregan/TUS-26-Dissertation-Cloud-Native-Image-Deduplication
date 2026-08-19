# RUNBOOK — Reproducibility Guide

This runbook provides the exact steps to reproduce the final benchmark and evaluation results for the cloud-native perceptual image deduplication pipeline.

---

## 1) Environment Setup

### Prerequisites
- Windows 11 (tested)
- Git Bash terminal
- Python 3.13.x (tested on 3.13.15)

### Create and activate virtual environment
```bash
py -3.13 -m venv venv
source venv/Scripts/activate
```

### Install dependencies
```bash
pip install -r services/dedupe-py/core_engine/requirements.txt
```

---

## 2) Verify Project Structure (required paths)

Ensure these paths exist before running:
- `data/dedupe_test_100`
- `data/labels/reference_labels_eval_v1.csv`
- `services/dedupe-py/benchmarks/tools/`

---

## 3) Final Baseline Reproduction Commands

Run from repository root:

```bash
export PYTHONPATH=services/dedupe-py
python -m benchmarks.benchmark_pipeline --dir data/dedupe_test_100 --output logs/final-baseline-phash5-ssim085.json --export-pairs --pair-limit 500 --phash-threshold 5 --ssim-threshold 0.85 --run-tag final-baseline
python -m benchmarks.tools.export_predictions --input logs/final-baseline-phash5-ssim085.json --output data/predictions/final-baseline-phash5-ssim085-stage3.csv --source stage3
python -m benchmarks.tools.evaluate_predictions --reference-labels data/labels/reference_labels_eval_v1.csv --predictions data/predictions/final-baseline-phash5-ssim085-stage3.csv
```

---

## 4) Docker Reproduction Commands

Run from repository root:

### PowerShell
```powershell
powershell -ExecutionPolicy Bypass -File .\services\dedupe-py\scripts\run_docker_benchmark.ps1
```

### Git Bash
```bash
bash services/dedupe-py/scripts/run_docker_benchmark.sh
```

Notes:
- Dockerfile used: `services/dedupe-py/Dockerfile`
- Output artifacts are written to repository root `logs/`

---

## 5) Expected Final Metrics

From the final baseline run (`pHash=5`, `SSIM=0.85`), expected evaluation output is:

- **Pairs evaluated:** 59  
- **TP:** 48  
- **FP:** 0  
- **FN:** 3  
- **TN:** 8  

- **Precision:** 1.0000  
- **Recall:** 0.9412  
- **F1 Score:** 0.9697  
- **Accuracy:** 0.9492  

Known false negatives:
- `ILSVRC2012_val_00000139.JPEG` ↔ `ILSVRC2012_val_00000139_brightness_up.jpg`
- `ILSVRC2012_val_00000141.JPEG` ↔ `ILSVRC2012_val_00000141_brightness_up.jpg`
- `ILSVRC2012_val_00000126.JPEG` ↔ `ILSVRC2012_val_00000126_green.jpg`

Note:
- One predicted pair may be reported as not present in reference labels and is ignored in confusion-matrix scoring.

---

## 6) Output Artifacts

Expected generated files:

- Benchmark JSON:
  - `logs/final-baseline-phash5-ssim085.json`
  - `logs/final-baseline-phash5-ssim085-YYYYMMDD-HHMMSS.json` (timestamped snapshot)

- Predictions CSV:
  - `data/predictions/final-baseline-phash5-ssim085-stage3.csv`

---

## 7) Troubleshooting

### Python version mismatch
If dependency install fails, confirm Python 3.13 is active:
```bash
python --version
```

### Missing dataset/labels
Check paths and filenames exactly:
- `data/dedupe_test_100`
- `data/labels/reference_labels_eval_v1.csv`

### No Stage 3 output
If Stage 2 candidate pairs are zero, Stage 3 may report near-zero work; this is expected when no candidates pass Stage 2.

---

## 8) Optional Validation Commands

Validate label file before evaluation:
```bash
export PYTHONPATH=services/dedupe-py
python -m benchmarks.tools.validate_reference_labels --csv data/labels/reference_labels_eval_v1.csv
```

Run full tests:
```bash
pytest -v
```