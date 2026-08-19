# Phase 04: Containerisation and Runtime Configuration

## Objective

Package the local deduplication pipeline as a portable service and externalise runtime configuration to support cloud-native execution patterns.

## Scope

This phase focuses on:

- Containerising the pipeline runtime
- Removing hard-coded runtime assumptions
- Supporting environment-based configuration
- Keeping algorithmic logic unchanged

## Planned Deliverables

- [x] `Dockerfile` for pipeline service
- [x] `.dockerignore` to minimise image size
- [x] Runtime config module (env var driven)
- [x] Updated CLI/API entrypoint using external config
- [x] Documentation for local container run commands
- [x] Test path stabilisation for consistent local execution
- [x] SonarCloud quality baseline validation

## Configuration Variables Implemented

- `PHASH_THRESHOLD` (default: `5`)
- `SSIM_THRESHOLD` (default: `0.85`)
- `DATASET_DIR` (default: `data/dedupe_test_100`)
- `OUTPUT_JSON` (default: `logs/results.json`)
- `EXPORT_PAIRS` (default: `false`, overrideable)
- `PAIR_LIMIT` (default: `500`)
- `RUN_TAG` (default: empty string)

## Acceptance Criteria

- [x] Container builds successfully on Windows 11 (Docker Desktop)
- [x] Pipeline runs in container and writes output artifact(s)
- [x] Threshold values can be overridden at runtime without code changes
- [x] Baseline metrics remain consistent with local execution (within expected variance)
- [x] Full test suite passes locally after path corrections (`16 passed`)
- [x] SonarCloud Quality Gate and project badges operational
- [x] SonarCloud duplication metric reduced to `0.0%` after excluding generated review HTML artifacts

## Evidence

### Build Command

```bash
docker build -t tus26-image-dedupe:v0.4.0 .
```

### Run Commands

PowerShell:

```powershell
.\scripts\run_docker_benchmark.ps1
```

Git Bash:

```bash
bash scripts/run_docker_benchmark.sh
```

Manual container run (explicit CLI args):

```bash
MSYS_NO_PATHCONV=1 docker run --rm \
  -v "$PWD/data:/app/data" \
  -v "$PWD/logs:/app/logs" \
  tus26-image-dedupe:v0.4.0 \
  python -m benchmarks.benchmark_pipeline \
    --dir dedupe_test_100 \
    --output /app/logs/results-docker-v0.4.0.json \
    --export-pairs \
    --pair-limit 500 \
    --phash-threshold 5 \
    --ssim-threshold 0.85 \
    --run-tag phase04-docker-v0.4.0
```

### Output Artifacts

- `logs/results-docker-v0.4.0.json`
- `logs/results-docker-v0.4.0-<timestamp>.json`

### Validation Summary

- Stage 1 exact duplicate groups: **10**
- Stage 2 candidate pairs: **53**
- Stage 3 verified pairs: **49**
- Detection parity with host execution: **maintained**
- Runtime differs between host and container: **expected** (container overhead and environment variance)
- Test suite status: **16 passed**
- SonarCloud status: **badges active, duplication 0.0%, warnings cleared**

### SonarCloud Configuration Notes

To prevent non-source generated artifacts from distorting quality metrics, the following exclusions are applied:

```properties
sonar.cpd.exclusions=**/data/reviews/review_pairs_stage*.html,**/submission/data/reviews/review_pairs_stage*.html
sonar.exclusions=**/data/reviews/review_pairs_stage*.html,**/submission/data/reviews/review_pairs_stage*.html
```

### Docker Hub (Versioned Image)

Target repository:

- `joe0regan/tus26-image-dedupe`

Tag/push commands used:

```bash
docker login
docker tag tus26-image-dedupe:v0.4.0 joe0regan/tus26-image-dedupe:v0.4.0
docker tag tus26-image-dedupe:v0.4.0 joe0regan/tus26-image-dedupe:phase04
docker push joe0regan/tus26-image-dedupe:v0.4.0
docker push joe0regan/tus26-image-dedupe:phase04
```

## Risks / Notes

- Python wheel/runtime differences can affect timings across environments.
- Git Bash path conversion on Windows can corrupt `-v` mounts unless handled (used `MSYS_NO_PATHCONV=1` where needed).
- Memory/CPU scheduling differences between host and container affect absolute timings but not detection outcomes.
- Generated review HTML can inflate duplication metrics if not excluded from static analysis scope.
- `logs/` is runtime-output only and is intentionally not committed by default.

## Exit Status

**Phase 04 Complete** — containerisation, runtime externalisation, baseline parity, and quality controls are validated.  
Next phase: **Phase 05 – Async Job Orchestration and Worker Model**.