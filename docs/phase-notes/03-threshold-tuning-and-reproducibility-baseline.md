# Phase 03: Threshold Tuning and Reproducibility Baseline

## Objective

Tune similarity thresholds and establish a reproducible final local baseline.

## Changes Introduced

Runtime-configurable benchmark arguments:
- `--phash-threshold`
- `--ssim-threshold`
- `--run-tag`

This removed the need to edit source code between experimental runs.

## Tuning Sweep

Tested combinations:
- **pHash**: 4, 5, 6, 7
- **SSIM**: 0.85, 0.90

Observed behaviour:
- pHash changes (4–7) did not alter results on the evaluation dataset.
- SSIM 0.90 reduced recall without improving precision.

## Selected Operating Point

- **pHash=5**
- **SSIM=0.85**

## Final Baseline Metrics

- TP=48, FP=0, FN=3, TN=8
- Precision=1.0000
- Recall=0.9412
- F1=0.9697
- Accuracy=0.9492

Known misses:
- `ILSVRC2012_val_00000139` (brightness_up)
- `ILSVRC2012_val_00000141` (brightness_up)
- `ILSVRC2012_val_00000126` (green variant)

Observed tendency:
- Misses often involve low-colour/near-grayscale imagery with subtle brightness/colour shifts.

## Reproducibility Assets Added

- `submission/RUNBOOK.md`
- `submission/README_SUBMISSION.md`
- final baseline JSON/CSV artifacts
- SHA-256 checksum manifest
- Benchmark JSON includes internal UTC timestamps (`run_started_at_utc`, `run_completed_at_utc`) and `run_duration_ms`

## Result

A stable, reproducible, and defensible local baseline was established for dissertation submission and cloud-native extension.