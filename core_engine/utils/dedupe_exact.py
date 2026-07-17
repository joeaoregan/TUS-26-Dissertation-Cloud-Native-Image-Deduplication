from pathlib import Path
import hashlib
import sys
from colorama import Fore, init

init(autoreset=True) # colorama: auto clear colours after printing


CHUNK_SIZE = 1024 * 1024  # 1 MB


def file_hash(path: Path, algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(folder: Path):
    hashes = {}

    for path in folder.rglob("*"):
        if path.is_file():
            try:
                digest = file_hash(path)
                hashes.setdefault(digest, []).append(path)
            except OSError as e:
                print(f"{Fore.RED}Could not read {path}: {e}")

    duplicates = {digest: paths for digest, paths in hashes.items() if len(paths) > 1}
    return duplicates


def print_duplicate_summary(duplicates: dict):
    """Calculates storage metrics and prints a summary of duplicate files."""
    print(f"{Fore.GREEN}Exact duplicates found:\n")
    
    total_redundant_files = 0
    total_wasted_bytes = 0

    for digest, paths in duplicates.items():
        print(f"Hash: {Fore.CYAN}{digest}")
        
        # Calculate extra copies in this group
        extra_copies_count = len(paths) - 1
        total_redundant_files += extra_copies_count
        
        # Calculate wasted bytes (original size * extra copies)
        file_size = paths[0].stat().st_size
        total_wasted_bytes += (file_size * extra_copies_count)

        for p in paths:
            print(f"  - {Fore.GREEN}{p}")
        print()

    # Convert bytes to megabytes and kilobytes
    wasted_kb = total_wasted_bytes / 1024
    wasted_mb = wasted_kb / 1024

    print(f"{Fore.YELLOW}Summary of Wasted Storage:")
    print(f"  - Redundant Files: {Fore.CYAN}{total_redundant_files}")
    print(f"  - Wasted Space:    {Fore.CYAN}{wasted_mb:.2f} MB ({wasted_kb:.1f} KB)\n")


def main():
    if len(sys.argv) != 2:
        print(f"{Fore.YELLOW}Usage: python dedupe_exact.py <folder>")
        sys.exit(1)

    folder = Path(sys.argv[1])

    if not folder.exists() or not folder.is_dir():
        print(f"{Fore.RED}Invalid folder: {folder}")
        sys.exit(1)

    duplicates = find_duplicates(folder)

    if not duplicates:
        print(f"{Fore.RED}No exact duplicates found.")
        return

    print_duplicate_summary(duplicates)


if __name__ == "__main__":
    main()