# Submission Pack — Cloud-Native Perceptual Image Deduplication Platform

## Purpose
This folder contains the final reproducibility and evidence pack for dissertation review.

## Included Contents

- `RUNBOOK.md`  
  Step-by-step commands to reproduce the final baseline benchmark and evaluation.

- `artifacts/logs/final-baseline-phash5-ssim085.json`  
  Final benchmark output (timings, memory, detections, config, dataset profile).

- `artifacts/predictions/final-baseline-phash5-ssim085-stage3.csv`  
  Exported Stage 3 predicted duplicate pairs used for evaluation.

- `checksums/SHA256SUMS.txt`  
  SHA-256 hashes for submitted artifacts to verify file integrity.

---

## Final Baseline Configuration

- **pHash threshold:** `5`
- **SSIM threshold:** `0.85`
- **Run tag:** `final-baseline`

---

## Final Baseline Evaluation Metrics

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

---

## Quick Reproduction

Run from repository root (full steps in `RUNBOOK.md`):

```bash
python -m benchmarks.benchmark_pipeline --dir data/dedupe_test_100 --output logs/final-baseline-phash5-ssim085.json --export-pairs --pair-limit 500 --phash-threshold 5 --ssim-threshold 0.85 --run-tag final-baseline
python -m benchmarks.tools.export_predictions --input logs/final-baseline-phash5-ssim085.json --output data/predictions/final-baseline-phash5-ssim085-stage3.csv --source stage3
python -m benchmarks.tools.evaluate_predictions --reference-labels data/labels/reference_labels_eval_v1.csv --predictions data/predictions/final-baseline-phash5-ssim085-stage3.csv
```

## Notes

- Results are based on the controlled data/dedupe_test_100 evaluation set.
- Timing and memory metrics are environment-dependent.
- Thresholds were selected through documented tuning experiments (see main project README.md).