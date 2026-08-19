# Phase 02: Benchmarking and Evaluation Framework

## Objective

Add measurable performance and correctness evaluation to the local pipeline.

## Implemented Benchmarking

### Benchmark runner
- `benchmarks/benchmark_pipeline.py`

### Metrics captured
- Stage timing (mean ± standard deviation)
- Peak RAM usage (mean ± standard deviation)
- Detection counts by stage
- Dataset profile (count, size, formats, resolution range)
- Environment metadata
- Run metadata timestamps (start/end UTC, run duration ms)

### Output
- Canonical JSON output (e.g., `logs/smoke.json`)
- Optional timestamped snapshot JSON (disabled with `--no-timestamp`)
- Optional pair exports in JSON (`--export-pairs`, `--pair-limit`)

### Path resolution notes
- `--dir` is resolved under `<repo-root>/data`  
  (use `dedupe_test_100`, not `data/dedupe_test_100`)
- `--output` is resolved from `<repo-root>`  
  (e.g., `logs/smoke.json`)
- `benchmarks/tools/validate_reference_labels.py --csv` is constrained to `<repo-root>/data/labels`

## Implemented Correctness Evaluation

### Tools
- `benchmarks/tools/validate_reference_labels.py`
- `benchmarks/tools/export_predictions.py`
- `benchmarks/tools/evaluate_predictions.py`
- `benchmarks/tools/build_review_html.py` (optional reviewer support)

### Evaluation workflow
1. Run benchmark with pair export
2. Validate reference labels CSV
3. Export predictions to CSV
4. Compare predictions vs labels to compute:
   - TP, FP, FN, TN
   - Precision, Recall, F1, Accuracy

## Result

The project moved from "works functionally" to "works and can be measured/reproduced with standard metrics."