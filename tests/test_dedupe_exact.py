from pathlib import Path

import pytest

from core_engine.utils.dedupe_exact import file_hash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = PROJECT_ROOT / "data" / "dedupe_test"


@pytest.fixture
def image_assets():
    """Fixture providing paths to actual test images in dedupe_test/."""
    me_original = TEST_DIR / "me.jpg"
    me_copy = TEST_DIR / "me - Copy.jpg"
    crop_img = TEST_DIR / "crop.jpg"

    return me_original, me_copy, crop_img


def test_file_hash_identical_byte_images(image_assets):
    """Verify exact copy (me.jpg vs me - Copy.jpg) generates matching SHA-256 hashes."""
    me_original, me_copy, _ = image_assets

    assert me_original.exists(), f"Missing test file: {me_original}"
    assert me_copy.exists(), f"Missing test file: {me_copy}"

    hash_original = file_hash(me_original)
    hash_copy = file_hash(me_copy)

    assert hash_original == hash_copy
    assert len(hash_original) == 64  # Valid 64-character SHA-256 hex string


def test_file_hash_distinct_images(image_assets):
    """Verify different images (me.jpg vs crop.jpg) generate distinct SHA-256 hashes."""
    me_original, _, crop_img = image_assets

    assert me_original.exists(), f"Missing test file: {me_original}"
    assert crop_img.exists(), f"Missing test file: {crop_img}"

    hash_original = file_hash(me_original)
    hash_crop = file_hash(crop_img)

    assert hash_original != hash_crop


def test_file_hash_nonexistent_file():
    """Verify file_hash raises FileNotFoundError/OSError for missing files."""
    missing_file = TEST_DIR / "non_existent_image.jpg"
    with pytest.raises((FileNotFoundError, OSError)):
        file_hash(missing_file)
