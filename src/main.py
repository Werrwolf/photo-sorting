from pathlib import Path

from core.scanner import scan_images
from core.duplicates import find_duplicates
from core.cache import HashCache


def main():

    folder = Path(input("Enter folder path: ").strip())

    images = scan_images(folder)

    print(f"Found {len(images)} images")

    cache = HashCache(Path("hash_cache.db"))

    duplicates = find_duplicates(images, cache)

    print(f"\nDuplicate groups: {len(duplicates)}\n")

    for files in list(duplicates.values())[:5]:

        print("----")
        for f in files:
            print(f)


if __name__ == "__main__":
    main()