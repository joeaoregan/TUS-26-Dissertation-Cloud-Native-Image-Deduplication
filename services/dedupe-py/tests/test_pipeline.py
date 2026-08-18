from core_engine.pipeline import run_pipeline

from .conftest import TEST_DATA_DIR

TEST_DIR = TEST_DATA_DIR / "dedupe_test"


def test_pipeline_execution():
    """Verify the full 3-stage cascading pipeline executes cleanly on dedupe_test/."""
    assert TEST_DIR.exists(), f"Test path does not exist: {TEST_DIR}"
    assert TEST_DIR.is_dir(), f"Test path is not a directory: {TEST_DIR}"

    # Run full pipeline against dedupe_test
    # (Any unexpected exception will fail the test naturally.)
    run_pipeline(TEST_DIR)
