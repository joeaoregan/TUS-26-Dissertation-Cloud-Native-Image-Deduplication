# Features Checklist

Legend:

- [x] done
- [ ] not done

---

## Core Pipeline

- [x] Stage 1 exact duplicate detection (SHA-256)
- [x] Stage 2 perceptual candidate generation (pHash)
- [x] Stage 3 candidate verification (SSIM)
- [x] Cascading pipeline execution flow
- [x] Stage-wise duplicate/candidate/verified outputs

## Benchmarking and Profiling

- [x] Benchmark runner for staged execution
- [x] Stage timing metrics (mean ± standard deviation)
- [x] Stage peak memory metrics (mean ± standard deviation)
- [x] Dataset profile summary (count, size, formats, resolution range)
- [x] Detection counts per stage
- [x] JSON benchmark report export
- [x] Timestamped benchmark snapshots
- [x] Optional pair export with configurable limit

## Correctness Evaluation

- [x] Reference label CSV validation
- [x] Prediction export from benchmark JSON
- [x] Evaluation against reference labels (TP/FP/FN/TN)
- [x] Precision/Recall/F1/Accuracy computation
- [x] Reporting of ignored predicted pairs not in labels
- [x] Optional HTML side-by-side review builder

## Threshold Tuning and Reproducibility

- [x] Runtime-configurable pHash threshold
- [x] Runtime-configurable SSIM threshold
- [x] Run tagging for experiment tracking
- [x] Threshold sweep comparison table
- [x] Final baseline selection documented
- [x] Reproducibility command block documented
- [x] Submission pack (runbook, artifacts, checksums)

## Testing and Quality

- [x] Unit tests for Stage 1
- [x] Unit tests for Stage 2
- [x] Unit tests for Stage 3
- [x] Integration tests for end-to-end pipeline

## Cloud-Native Readiness (Planned / In Progress)

- [ ] Container image for pipeline service (Dockerfile)
- [ ] Externalised runtime configuration via environment variables
- [ ] Minimal API wrapper for job submission
- [ ] Async queue-based processing flow (API -> queue -> worker)
- [ ] Worker job status tracking (pending/running/completed/failed)
- [ ] Idempotent job handling and retry safety
- [ ] Structured logging with correlation/job IDs
- [ ] Health/readiness endpoints
- [ ] Docker Compose local orchestration
- [ ] Kubernetes deployment manifests
- [ ] Object storage integration (cloud/local-compatible)
- [ ] Persistent metadata/result storage integration
- [ ] Horizontal worker scaling demonstration
- [ ] Cloud-native non-functional evaluation (scalability/resilience/observability)

## Documentation

- [x] Main README with setup, run, benchmark, and evaluation guidance
- [x] Threshold tuning results documented
- [x] Final baseline metrics documented
- [x] Threats to validity documented
- [x] Submission README and runbook
- [x] Phase notes (completed phases documented)
- [ ] Phase notes (cloud-native phases completed and evidenced)