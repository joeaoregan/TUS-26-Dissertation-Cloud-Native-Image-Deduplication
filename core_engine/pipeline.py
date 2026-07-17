from pathlib import Path
import sys
from PIL import Image
import imagehash
from colorama import Fore, init

# Import working utility functions relative to the core_engine package
from core_engine.utils.dedupe_exact import file_hash
from core_engine.utils.dedupe_perceptual import IMAGE_EXTENSIONS, compare_perceptual_hashes

init(autoreset=True) # colorama: auto clear colours after printing

def print_pipeline_summary(exact_groups: dict, perceptual_pairs: list):
    """Prints a styled, colourised summary of the hybrid cascading results."""
    print(f"\n{Fore.GREEN}=== CASCADING PIPELINE RESULTS ===\n")

    total_redundant_files = 0
    total_wasted_bytes = 0
    tracked_duplicates = set()

    # 1. Report Stage 1: Exact Byte Duplicates
    print(f"{Fore.YELLOW}Stage 1: Exact Byte Matches (SHA-256)")
    exact_duplicates = {h: p for h, p in exact_groups.items() if len(p) > 1}
    
    if not exact_duplicates:
        print("  No exact byte duplicates detected.")
    else:
        for sha256, paths in exact_duplicates.items():
            print(f"  Hash: {Fore.CYAN}{sha256[:16]}...")
            extra_copies = len(paths) - 1
            total_redundant_files += extra_copies
            total_wasted_bytes += (paths[0].stat().st_size * extra_copies)
            
            for p in paths:
                print(f"    - {Fore.GREEN}{p}")
                tracked_duplicates.add(p)

    print()

    # 2. Report Stage 2: Perceptual Matches
    print(f"{Fore.YELLOW}Stage 2: Visual Near-Matches (pHash)")
    if not perceptual_pairs:
        print("  No visually similar image shifts detected.")
    else:
        for p1, p2, dist in perceptual_pairs:
            print(f"  Hamming Distance: {Fore.CYAN}{dist}")
            print(f"    - {Fore.GREEN}{p1}")
            print(f"    - {Fore.GREEN}{p2}")
            
            if p2 not in tracked_duplicates:
                tracked_duplicates.add(p2)
                total_wasted_bytes += p2.stat().st_size
                total_redundant_files += 1

    print()

    # 3. Overall Savings Summary
    wasted_kb = total_wasted_bytes / 1024
    wasted_mb = wasted_kb / 1024

    print(f"{Fore.YELLOW}Total Saved Storage Metrics:")
    print(f"  - Redundant Files Identified: {Fore.CYAN}{total_redundant_files}")
    print(f"  - Estimated Wasted Space:     {Fore.CYAN}{wasted_mb:.2f} MB ({wasted_kb:.1f} KB)\n")

def run_pipeline(folder: Path, phash_threshold: int = 5):
    """Executes the cascading deduplication check."""
    print(f"Scanning '{folder}' using cascading hybrid logic...\n")
    
    # --- STAGE 1: Exact Byte-Level Check ---
    exact_groups = {}
    for path in folder.rglob("*"):
        if path.is_file():
            try:
                # Used the imported file_hash utility
                sha256_hash = file_hash(path)
                exact_groups.setdefault(sha256_hash, []).append(path)
            except OSError as e:
                print(f"{Fore.RED}Could not read file {path}: {e}")

    # Extract exactly one representative file from each byte group for visual analysis
    unique_candidates = [paths[0] for paths in exact_groups.values()]

    # --- STAGE 2: Perceptual Hashing Check ---
    perceptual_hashes = {}
    for path in unique_candidates:
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            try:
                with Image.open(path) as img:
                    perceptual_hashes[path] = imagehash.phash(img)
            except Exception as e:
                print(f"{Fore.RED}Error processing visual hash for {path}: {e}")

    # Used the imported, shared comparison helper function
    perceptual_pairs = compare_perceptual_hashes(perceptual_hashes, phash_threshold)

    # Output combined summary
    print_pipeline_summary(exact_groups, perceptual_pairs)

def main():
    if len(sys.argv) != 2:
        print(f"{Fore.YELLOW}Usage: python pipeline.py <folder>")
        sys.exit(1)

    folder = Path(sys.argv[1])
    if not folder.exists() or not folder.is_dir():
        print(f"{Fore.RED}Invalid folder directory: {folder}")
        sys.exit(1)

    run_pipeline(folder)

if __name__ == "__main__":
    main()