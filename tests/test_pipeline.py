from pathlib import Path

from core_engine.pipeline import run_pipeline

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = PROJECT_ROOT / "data" / "dedupe_test"


def test_pipeline_execution():
    """Verify the full 3-stage cascading pipeline executes cleanly on dedupe_test/."""
    assert TEST_DIR.exists(), f"Test path does not exist: {TEST_DIR}"
    assert TEST_DIR.is_dir(), f"Test path is not a directory: {TEST_DIR}"

    # Run full pipeline against dedupe_test
    # (Any unexpected exception will fail the test naturally.)
    run_pipeline(TEST_DIR)
