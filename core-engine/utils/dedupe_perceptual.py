from pathlib import Path
import sys
from PIL import Image
import imagehash
from colorama import Fore, init

init(autoreset=True) # colorama: auto clear colours after printing

# Supported cloud-native media file extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def find_perceptual_duplicates(folder: Path, threshold: int = 5):
    """
    Scans a folder structure to identify visually similar or near-duplicate
    images using Perceptual Hashing (pHash). It handles compression variations
    and format shifts that traditional byte-level hashing misses.
    """
    hashes = {}

    # Scan directories recursively using pathlib rglob
    for path in folder.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            try:
                # Open image block and calculate structural pHash
                with Image.open(path) as img:
                    phash_value = imagehash.phash(img)
                    hashes[path] = phash_value
            except Exception as e:
                print(f"{Fore.RED}Could not process image {path}: {e}")

    duplicates_found = []
    processed_paths = list(hashes.keys())

    # Compare calculated hashes using bitwise Hamming Distance
    for i in range(len(processed_paths)):
        for j in range(i + 1, len(processed_paths)):
            path1 = processed_paths[i]
            path2 = processed_paths[j]
            
            # Subtracting imagehashes calculates the visual distance matrix
            distance = hashes[path1] - hashes[path2]
            
            # A threshold between 5 and 10 catches resized and compressed versions
            if distance <= threshold:
                duplicates_found.append((path1, path2, distance))

    return duplicates_found

def main():
    if len(sys.argv) != 2:
        print(f"{Fore.YELLOW}Usage: python dedupe_perceptual.py <folder>")
        sys.exit(1)

    folder = Path(sys.argv[1])

    if not folder.exists() or not folder.is_dir():
        print(f"{Fore.RED}Invalid folder: {folder}")
        sys.exit(1)

    print(f"{Fore.GREEN}Scanning folder for perceptual/compressed duplicates...")
    similar_images = find_perceptual_duplicates(folder)

    if not similar_images:
        print(f"{Fore.RED}No visually similar images found.")
        return

    print(f"\n{Fore.GREEN}Found {len(similar_images)} pairs of visually similar images:\n")
    for p1, p2, dist in similar_images:
        print(f"{Fore.YELLOW}Hamming Distance: {dist}")
        print(f"  - {Fore.GREEN}{p1}")
        print(f"  - {Fore.GREEN}{p2}")
        print()

if __name__ == "__main__":
    main()