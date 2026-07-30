from pathlib import Path
import pytest
from core_engine.pipeline import run_pipeline

TEST_DIR = Path("dedupe_test")


def test_pipeline_execution():
    """Verify the full 3-stage cascading pipeline executes cleanly on dedupe_test/."""
    assert TEST_DIR.exists() and TEST_DIR.is_dir(), f"Test directory {TEST_DIR} does not exist"

    # Run full pipeline against dedupe_test
    # (Assuming run_pipeline returns metrics dict/tuple or executes without uncaught exceptions)
    try:
        run_pipeline(TEST_DIR)
    except Exception as e:
        pytest.fail(f"run_pipeline raised an unexpected exception: {e}")