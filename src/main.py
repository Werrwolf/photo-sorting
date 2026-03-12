from pathlib import Path

from core.cache import HashCache
from core.duplicates import find_duplicates
from core.scanner import scan_images


def main() -> None:
    folder = Path(input("Enter folder path: ").strip())

    images = scan_images(folder)
    print(f"Found {len(images)} images")

    cache = HashCache(Path("hash_cache.db"))

    try:
        duplicates = find_duplicates(images, cache, max_workers=8, batch_size=200)

        print(f"\nDuplicate groups: {len(duplicates)}\n")

        for files in list(duplicates.values())[:5]:
            print("----")
            for file_path in files:
                print(file_path)
    finally:
        cache.close()


if __name__ == "__main__":
    main()