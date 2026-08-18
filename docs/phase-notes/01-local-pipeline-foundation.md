# Phase 01: Local Pipeline Foundation

## Objective

Build a working local image deduplication engine capable of detecting both exact and near-duplicate images.

## Implemented Components

- **Stage 1:** SHA-256 exact duplicate detection
- **Stage 2:** Perceptual hash (pHash) candidate generation
- **Stage 3:** SSIM verification for candidate confirmation
- **Cascading pipeline entry point:** `core_engine/pipeline.py`

## Design Rationale

A staged cascade reduces unnecessary compute:

1. Use fast exact hashing first.
2. Apply perceptual matching only to non-exact files.
3. Use SSIM as a final verifier to reduce false positives.

## Outputs

- Exact duplicate groups and redundant file counts
- Candidate near-duplicate pairs
- Verified near-duplicate pairs

## Result

A functional local pipeline was established as the foundation for benchmarking and later cloud-native integration.