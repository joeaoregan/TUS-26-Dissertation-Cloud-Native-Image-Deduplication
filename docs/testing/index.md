# Testing Guide

This page documents the project testing strategy, execution commands, and reproducibility expectations.

## Scope

Testing currently covers:

!!! info "Stage 1"
    Exact duplicate detection (SHA-256)

!!! info "Stage 2"
    Perceptual hashing behaviour (pHash)

!!! info "Stage 3"
    Structural similarity scoring (SSIM)

!!! info "Pipeline"
    End-to-end pipeline execution

!!! info "Path Safety"
    Safe path resolution and traversal protection

## Test Structure

Primary service test modules:

- `services/dedupe-py/tests/test_dedupe_exact.py`
- `services/dedupe-py/tests/test_dedupe_perceptual.py`
- `services/dedupe-py/tests/test_dedupe_ssim.py`
- `services/dedupe-py/tests/test_pipeline.py`
- `services/dedupe-py/tests/test_path_validation.py`

Primary local dataset used by tests:

- `data/dedupe_test`

## Preconditions (Windows 11 + Git Bash)

1. Open Git Bash in repository root.
2. Activate virtual environment:
   - `source venv/Scripts/activate`
   - or `source .venv/Scripts/activate`
3. Install dependencies:
   - `python -m pip install --upgrade pip`
   - `pip install -r requirements.txt`
4. Confirm dataset exists:
   - `ls -la data/dedupe_test`

## Run Tests

Quick run (entire suite):

```bash
pytest -q
```

Verbose run:

```bash
pytest -v
```

Run service tests only:

```bash
pytest -q services/dedupe-py/tests
```

Run a single module:

```bash
pytest -q services/dedupe-py/tests/test_dedupe_ssim.py
```

Fallback if `pytest` is not on PATH:

```bash
python -m pytest -q
```

## Current Baseline Result

- **Full suite:** 17 passed
- **Command:** `pytest -q`
- **Status:** pass

## Data Path Configuration

Tests use shared path resolution with sensible defaults for portability.

Default expected location:

- `<repo-root>/data`

Optional override (only when needed):

- `TEST_DATA_DIR`

Example override (Git Bash):

```bash
TEST_DATA_DIR="$(pwd)/data" pytest -q services/dedupe-py/tests
```

## Quality Gate and Static Analysis

SonarCloud is used for continuous static analysis and quality monitoring.

Expected quality baseline:

- Quality Gate: passing
- Duplicated Lines (%): 0.0%
- Generated review HTML excluded from duplication scope

Exclusion configuration:

```properties
sonar.cpd.exclusions=**/data/reviews/review_pairs_stage*.html,**/submission/data/reviews/review_pairs_stage*.html
sonar.exclusions=**/data/reviews/review_pairs_stage*.html,**/submission/data/reviews/review_pairs_stage*.html
```

## Troubleshooting

!!! failure "Missing test file / Test path does not exist"
    **Cause:** incorrect dataset path assumptions.  
    **Resolution:** ensure `data/dedupe_test` exists at repository root, or set `TEST_DATA_DIR` override.

!!! failure "pytest: command not found"
    Use module execution form:
    `python -m pytest -q`

!!! failure "SonarCloud badge shows Quality Gate not computed"
    - Ensure analysis has run on default branch after latest push.
    - Check SonarCloud Background Tasks for successful completion.