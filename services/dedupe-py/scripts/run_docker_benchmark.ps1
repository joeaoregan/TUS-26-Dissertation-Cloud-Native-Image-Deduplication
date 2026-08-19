$ErrorActionPreference = "Stop"

# Build image
docker build -t tus26-image-dedupe:v0.4.0 -f services/dedupe-py/Dockerfile .

# Resolve absolute host paths
$RepoRoot = (Get-Location).Path
$DataPath = Join-Path $RepoRoot "data"
$LogsPath = Join-Path $RepoRoot "logs"

# Ensure logs folder exists
if (-not (Test-Path $LogsPath)) {
    New-Item -ItemType Directory -Path $LogsPath | Out-Null
}

# Run benchmark
docker run --rm `
  -e DATASET_DIR=dedupe_test_100 `
  -e OUTPUT_JSON=logs/results-docker-v0.4.0.json `
  -e EXPORT_PAIRS=true `
  -e PAIR_LIMIT=500 `
  -e PHASH_THRESHOLD=5 `
  -e SSIM_THRESHOLD=0.85 `
  -e RUN_TAG=phase04-docker-v0.4.0 `
  -v "${DataPath}:/app/data" `
  -v "${LogsPath}:/app/logs" `
  tus26-image-dedupe:v0.4.0