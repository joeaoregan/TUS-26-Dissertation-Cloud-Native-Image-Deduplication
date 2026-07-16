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

    print(f"{Fore.GREEN}Exact duplicates found:\n")
    for digest, paths in duplicates.items():
        print(f"Hash: {Fore.CYAN}{digest}")
        for p in paths:
            print(f"  - {Fore.GREEN}{p}")
        print()


if __name__ == "__main__":
    main()