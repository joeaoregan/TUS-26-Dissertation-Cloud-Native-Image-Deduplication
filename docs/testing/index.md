# Testing Guide

This page documents the project testing strategy, execution commands, and evidence expectations for reproducibility and assessment.

## Scope

Testing currently covers:

!!! info "Stage 1"

    Exact duplicate logic (SHA-256)

!!! info "Stage 2"

    Perceptual hashing behaviour (pHash)
    
!!! info "Stage 3"

    Structural similarity scoring (SSIM)
    
!!! info "Pipeline"

    End-to-end pipeline execution
    


## Test Structure

- `tests/test_dedupe_exact.py`
- `tests/test_dedupe_perceptual.py`
- `tests/test_dedupe_ssim.py`
- `tests/test_pipeline.py`

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

Quick run:

```bash
pytest -q
```

### Verbose run:

`pytest -v`

### Run a single test module:

`pytest -q tests/test_dedupe_ssim.py`

## Current Baseline Result

- **Full suite:** 16 passed
- **Commands:** pytest -q
- **Status:** pass

## Quality Gate and Static Analysis

SonarCloud is used for continuous static analysis and quality monitoring.

Expected project quality baseline:

- Quality Gate: computed and passing
- Duplicated Lines (%): 0.0%
- Generated review HTML excluded from duplication scope

Exclusion configuration used:

```properties
sonar.cpd.exclusions=**/data/reviews/review_pairs_stage*.html,**/submission/data/reviews/review_pairs_stage*.html
sonar.exclusions=**/data/reviews/review_pairs_stage*.html,**/submission/data/reviews/review_pairs_stage*.html
```

## Troubleshooting

!!! Failure "Missing test file / Test path does not exist"

    **Cause**: incorrect dataset path assumptions.  
    **Resolution**: ensure tests reference: `PROJECT_ROOT / "data" / "dedupe_test"`  
    and verify folder contents exist locally.
    
!!! Failure "pytest: command not found"

    **Use module execution form:**: `python -m pytest -q`  
    
!!! Failure "SonarCloud badge shows Quality gate not computed"

    - Ensure analysis has run on main branch after latest push.  
    - Check SonarCloud Background Tasks for successful analysis completion.