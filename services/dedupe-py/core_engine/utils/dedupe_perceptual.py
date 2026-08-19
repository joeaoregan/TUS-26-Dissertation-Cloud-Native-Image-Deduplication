from pathlib import Path
import sys
from PIL import Image
import imagehash
from colorama import Fore, init

init(autoreset=True) # colorama: auto clear colours after printing

# Supported cloud-native media file extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def compare_perceptual_hashes(hashes: dict, threshold: int = 5) -> list:
    """
    Compares a dictionary of {Path: imagehash} values using bitwise Hamming Distance
    to identify visually similar image pairs below the specified threshold.
    """
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

    # Shared comparison helper function to identify visually similar pairs
    return compare_perceptual_hashes(hashes, threshold)


def print_perceptual_summary(similar_images: list):
    """Prints a styled, coloured summary of visually similar image groups."""
    print(f"{Fore.GREEN}Found {len(similar_images)} pairs of visually similar images:\n")
    
    unique_duplicates = set()
    total_wasted_bytes = 0

    for p1, p2, distance in similar_images:
        print(f"Hamming Distance: {Fore.CYAN}{distance}")
        print(f"  - {Fore.GREEN}{p1}")
        print(f"  - {Fore.GREEN}{p2}")
        print()
        
        # Track unique duplicate files (assuming the second file is the redundant copy)
        if p2 not in unique_duplicates:
            unique_duplicates.add(p2)
            total_wasted_bytes += p2.stat().st_size

    # Convert bytes to megabytes and kilobytes
    wasted_kb = total_wasted_bytes / 1024
    wasted_mb = wasted_kb / 1024

    print(f"{Fore.YELLOW}Summary of Wasted Storage:")
    print(f"  - Redundant Files Identified: {Fore.CYAN}{len(unique_duplicates)}")
    print(f"  - Estimated Wasted Space:     {Fore.CYAN}{wasted_mb:.2f} MB ({wasted_kb:.1f} KB)\n")


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

    print_perceptual_summary(similar_images)


if __name__ == "__main__":
    main()