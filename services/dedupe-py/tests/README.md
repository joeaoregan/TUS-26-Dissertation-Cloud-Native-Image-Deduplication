# Tests (services/dedupe-py/tests)

Run from repository root.

## Prerequisites
- Python virtual environment activated
- Dependencies installed

## Run all tests
```bash
pytest -q
```

## Run service tests only
```bash
pytest -q services/dedupe-py/tests
```

## Run specific test modules
```bash
pytest -q services/dedupe-py/tests/test_dedupe_exact.py
pytest -q services/dedupe-py/tests/test_dedupe_perceptual.py
pytest -q services/dedupe-py/tests/test_dedupe_ssim.py
pytest -q services/dedupe-py/tests/test_pipeline.py
pytest -q services/dedupe-py/tests/test_path_validation.py
```

## Test data location
Tests resolve data directory automatically using shared path helpers.

Default expected location:
- `<repo-root>/data`

Optional override (if needed):
- `TEST_DATA_DIR` environment variable

Example (Git Bash):
```bash
TEST_DATA_DIR="$(pwd)/data" pytest -q services/dedupe-py/tests
```