from pathlib import Path

import pytest

from core_engine.utils.dedupe_ssim import calculate_ssim

TEST_DIR = Path("dedupe_test")


@pytest.fixture
def ssim_image_assets():
    """Fixture providing paths to actual test images for SSIM comparison."""
    me_original = TEST_DIR / "me.jpg"
    me_copy = TEST_DIR / "me - Copy.jpg"
    crop_blur_jpg = TEST_DIR / "crop_blur.jpg"
    crop_blur_png = TEST_DIR / "crop_blur.png"

    return me_original, me_copy, crop_blur_jpg, crop_blur_png


def test_calculate_ssim_identical_images(ssim_image_assets):
    """Verify identical/copied images yield an SSIM score of 1.0 (or extremely close to 1.0)."""
    me_original, me_copy, _, _ = ssim_image_assets
    assert me_original.exists(), f"Missing test file: {me_original}"
    assert me_copy.exists(), f"Missing test file: {me_copy}"

    score = calculate_ssim(me_original, me_copy)

    assert isinstance(score, float)
    assert pytest.approx(score, abs=1e-3) == 1.0


def test_calculate_ssim_format_shifted_candidates(ssim_image_assets):
    """Verify crop_blur.jpg vs crop_blur.png yields high SSIM score (>= 0.80)."""
    _, _, crop_blur_jpg, crop_blur_png = ssim_image_assets
    assert crop_blur_jpg.exists(), f"Missing test file: {crop_blur_jpg}"
    assert crop_blur_png.exists(), f"Missing test file: {crop_blur_png}"

    score = calculate_ssim(crop_blur_jpg, crop_blur_png)

    assert isinstance(score, float)
    assert score >= 0.80


def test_calculate_ssim_nonexistent_file():
    """Verify calculate_ssim catches missing file errors gracefully and returns a fallback score of -1.0."""
    missing_file = TEST_DIR / "missing.jpg"
    existing_file = TEST_DIR / "me.jpg"

    score = calculate_ssim(missing_file, existing_file)

    assert score == -1.0
