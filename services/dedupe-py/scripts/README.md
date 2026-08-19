# Docker Benchmark Scripts

These scripts build and run the dedupe service container benchmark.

## Location

- `services/dedupe-py/scripts/run_docker_benchmark.sh`
- `services/dedupe-py/scripts/run_docker_benchmark.ps1`

## Run from repository root (recommended)

### Git Bash (Windows)

```bash
bash services/dedupe-py/scripts/run_docker_benchmark.sh
```

Optional arguments:

```bash
bash services/dedupe-py/scripts/run_docker_benchmark.sh v0.4.0 phase04-docker-v0.4.0
```

- Arg 1 = image tag (default: `v0.4.0`)
- Arg 2 = run tag (default: `phase04-docker-<image_tag>`)

### PowerShell (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File .\services\dedupe-py\scripts\run_docker_benchmark.ps1
```

## What the scripts do

1. Build Docker image:
   - Dockerfile: `services/dedupe-py/Dockerfile`
   - Build context: repository root (`.`)

2. Run container with benchmark settings:
   - Dataset in container: `data/dedupe_test_100`
   - Output JSON: `/app/logs/results-docker-v0.4.0.json` (or tag-based for `.sh`)
   - Host mounts:
     - `./data -> /app/data`
     - `./logs -> /app/logs`

## Prerequisites

- Docker Desktop running
- Execute from repository root
- Local folders available:
  - `data/` (with benchmark dataset)
  - `logs/` (created automatically by PowerShell script if missing)

## Notes

- Git Bash script sets `MSYS_NO_PATHCONV=1` to avoid path conversion issues on Windows.
- If image/tag changes, update script args (or script defaults) consistently.