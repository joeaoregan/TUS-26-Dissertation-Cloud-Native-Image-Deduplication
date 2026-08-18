from pathlib import Path

import imagehash
import pytest
from PIL import Image

from core_engine.utils.dedupe_perceptual import (
    IMAGE_EXTENSIONS,
    compare_perceptual_hashes,
)

TEST_DIR = Path("dedupe_test")


@pytest.fixture
def image_paths():
    """Fixture providing paths to actual test images in dedupe_test/."""
    me_original = TEST_DIR / "me.jpg"
    me_copy = TEST_DIR / "me - Copy.jpg"
    crop_img = TEST_DIR / "crop.jpg"

    return me_original, me_copy, crop_img


def test_image_extensions_constant():
    """Verify supported image extensions list includes common formats."""
    assert ".jpg" in IMAGE_EXTENSIONS
    assert ".jpeg" in IMAGE_EXTENSIONS
    assert ".png" in IMAGE_EXTENSIONS


def test_phash_generation_valid_image(image_paths):
    """Verify imagehash.phash returns a valid ImageHash object for existing images."""
    me_original, _, _ = image_paths
    assert me_original.exists(), f"Missing test file: {me_original}"

    with Image.open(me_original) as img:
        hash_val = imagehash.phash(img)

    assert hash_val is not None
    assert isinstance(hash_val, imagehash.ImageHash)


def test_phash_identical_visuals(image_paths):
    """Verify identical/copied images yield a Hamming distance of 0."""
    me_original, me_copy, _ = image_paths
    assert me_original.exists(), f"Missing test file: {me_original}"
    assert me_copy.exists(), f"Missing test file: {me_copy}"

    with Image.open(me_original) as img1, Image.open(me_copy) as img2:
        hash1 = imagehash.phash(img1)
        hash2 = imagehash.phash(img2)

    hamming_distance = hash1 - hash2
    assert hamming_distance == 0


def test_compare_perceptual_hashes_threshold(image_paths):
    """Verify compare_perceptual_hashes returns candidate pairs within specified threshold."""
    me_original, me_copy, crop_img = image_paths

    hashes = {}
    for path in (me_original, me_copy, crop_img):
        if path.exists():
            with Image.open(path) as img:
                hashes[path] = imagehash.phash(img)

    # Compare with strict threshold = 5
    pairs = compare_perceptual_hashes(hashes, threshold=5)

    assert len(pairs) >= 1
    # Check that pair tuple contains (Path, Path, int_distance)
    p1, p2, dist = pairs[0]
    assert isinstance(dist, int)
    assert dist <= 5
