#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="tus26-image-dedupe"
IMAGE_TAG="${1:-v0.4.0}"
RUN_TAG="${2:-phase04-docker-${IMAGE_TAG}}"

# Resolve repo root from script location and run from there
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "$REPO_ROOT"

# Ensure logs directory exists
mkdir -p logs

# Build
docker build \
  -t "${IMAGE_NAME}:${IMAGE_TAG}" \
  -f services/dedupe-py/Dockerfile \
  .

# Run (Git Bash on Windows: disable path conversion)
MSYS_NO_PATHCONV=1 docker run --rm \
  -e DATASET_DIR=dedupe_test_100 \
  -e OUTPUT_JSON=logs/results-docker-${IMAGE_TAG}.json \
  -e EXPORT_PAIRS=true \
  -e PAIR_LIMIT=500 \
  -e PHASH_THRESHOLD=5 \
  -e SSIM_THRESHOLD=0.85 \
  -e RUN_TAG="${RUN_TAG}" \
  -v "${REPO_ROOT}/data:/app/data" \
  -v "${REPO_ROOT}/logs:/app/logs" \
  "${IMAGE_NAME}:${IMAGE_TAG}"