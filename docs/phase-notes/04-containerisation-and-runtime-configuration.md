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

- [ ] `Dockerfile` for pipeline service
- [ ] `.dockerignore` to minimise image size
- [ ] Runtime config module (env var driven)
- [ ] Updated CLI/API entrypoint using external config
- [ ] Documentation for local container run commands

## Proposed Configuration Variables

- `PHASH_THRESHOLD` (default: `5`)
- `SSIM_THRESHOLD` (default: `0.85`)
- `DATASET_DIR` (default: `data/dedupe_test_100`)
- `OUTPUT_JSON` (default: `logs/results.json`)
- `EXPORT_PAIRS` (default: `true/false`)
- `PAIR_LIMIT` (default: `500`)

## Acceptance Criteria

- [ ] Container builds successfully on Windows 11 (Docker Desktop)
- [ ] Pipeline runs in container and writes output artifact(s)
- [ ] Threshold values can be overridden at runtime without code changes
- [ ] Baseline metrics remain consistent with local execution (within expected variance)

## Evidence to Capture

- Docker build command and image tag
- Docker run command(s)
- Output JSON path and sample output summary
- Any observed runtime/performance differences vs host execution

## Risks / Notes

- Python package wheel compatibility in container image
- Path handling differences between host and container mounts
- Memory/CPU limits affecting timing results