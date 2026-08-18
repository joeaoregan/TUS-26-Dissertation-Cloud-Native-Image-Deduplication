#!/usr/bin/env bash
set -euo pipefail

# Build
docker build -t tus26-image-dedupe:v0.4.0 .

# Run with explicit settings (Git Bash on Windows: disable path conversion)
MSYS_NO_PATHCONV=1 docker run --rm \
  -e DATASET_DIR=data/dedupe_test_100 \
  -e OUTPUT_JSON=/app/logs/results-docker-v0.4.0.json \
  -e EXPORT_PAIRS=true \
  -e PAIR_LIMIT=500 \
  -e PHASH_THRESHOLD=5 \
  -e SSIM_THRESHOLD=0.85 \
  -e RUN_TAG=phase04-docker-v0.4.0 \
  -v "$PWD/data:/app/data" \
  -v "$PWD/logs:/app/logs" \
  tus26-image-dedupe:v0.4.0