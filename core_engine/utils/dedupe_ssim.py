from pathlib import Path
import sys
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity as ssim
from colorama import Fore, init

# Initialise colorama to automatically clear formatting after each print
init(autoreset=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def calculate_ssim(image_path_1: Path, image_path_2: Path, target_size: tuple = (300, 300)) -> float:
    """
    Computes the Structural Similarity Index Measure (SSIM) between two image files.
    Resizes both images to target_size and converts them to grayscale arrays before evaluation.
    Returns a float score between -1.0 and 1.0.
    """
    try:
        with Image.open(image_path_1) as img1, Image.open(image_path_2) as img2:
            # Convert images to grayscale ('L' mode) to compare structure over luminance
            img1_gray = img1.convert("L").resize(target_size)
            img2_gray = img2.convert("L").resize(target_size)

            # Convert PIL Images to NumPy numerical arrays
            arr1 = np.array(img1_gray)
            arr2 = np.array(img2_gray)

            # Compute SSIM structural metric
            score, _ = ssim(arr1, arr2, full=True)
            return float(score)

    except Exception as e:
        print(f"{Fore.RED}Error calculating SSIM between {image_path_1.name} and {image_path_2.name}: {e}")
        return -1.0


def verify_image_pair(image_path_1: Path, image_path_2: Path, threshold: float = 0.80) -> tuple[bool, float]:
    """
    Evaluates whether two candidate image paths exceed the minimum SSIM similarity threshold.
    """
    score = calculate_ssim(image_path_1, image_path_2)
    is_similar = score >= threshold
    return is_similar, score


def main():
    if len(sys.argv) != 3:
        print(f"{Fore.YELLOW}Usage: python -m core_engine.utils.dedupe_ssim <image_path_1> <image_path_2>")
        sys.exit(1)

    path1 = Path(sys.argv[1])
    path2 = Path(sys.argv[2])

    if not path1.exists() or not path2.exists():
        print(f"{Fore.RED}One or both specified image paths do not exist.")
        sys.exit(1)

    score = calculate_ssim(path1, path2)

    print(f"\n{Fore.GREEN}=== STAGE 3 SSIM COMPARISON METRIC ===")
    print(f"Image 1: {path1.name}")
    print(f"Image 2: {path2.name}")
    print(f"SSIM Score: {Fore.CYAN}{score:.4f}")

    if score >= 0.80:
        print(f"Status:     {Fore.GREEN}CONFIRMED VISUAL MATCH (>= 0.80)\n")
    else:
        print(f"Status:     {Fore.RED}DISTINCT IMAGES (< 0.80)\n")


if __name__ == "__main__":
    main()