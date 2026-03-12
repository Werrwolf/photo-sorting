from pathlib import Path

from core.cache import HashCache
from core.duplicates import find_exact_duplicates, find_visual_duplicates
from core.scanner import scan_images


def print_groups(title: str, groups: dict[str, list[Path]], limit: int = 5) -> None:
    print(f"\n{title}: {len(groups)}\n")

    for files in list(groups.values())[:limit]:
        print("----")
        for file_path in files:
            print(file_path)


def main() -> None:
    folder = Path(input("Enter folder path: ").strip())

    images = scan_images(folder)
    print(f"Found {len(images)} images")

    cache = HashCache(Path("hash_cache.db"))

    try:
        exact_duplicates = find_exact_duplicates(images, cache, max_workers=8, batch_size=200)
        visual_duplicates = find_visual_duplicates(
            images,
            cache,
            exact_duplicates=exact_duplicates,
            max_workers=8,
            batch_size=200,
        )

        print_groups("Exact duplicate groups", exact_duplicates)
        print_groups("Visual duplicate groups", visual_duplicates)

    finally:
        cache.close()


if __name__ == "__main__":
    main()