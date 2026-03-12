from collections.abc import Callable
from pathlib import Path

from core.cache import HashCache
from core.duplicates import find_exact_duplicates, find_visual_duplicates
from core.scanner import scan_images

ProgressCallback = Callable[[str], None]


def run_duplicate_scan(
    folder: Path,
    cache_path: Path,
    progress_callback: ProgressCallback | None = None,
) -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    """
    Run the full duplicate detection pipeline.

    The scan performs:
    1. recursive image discovery
    2. exact duplicate detection using SHA-256
    3. visual duplicate detection using perceptual hashes

    Parameters
    ----------
    folder : Path
        Root folder containing images to scan.
    cache_path : Path
        SQLite cache database path.
    progress_callback : ProgressCallback | None
        Optional callback receiving human-readable progress messages.

    Returns
    -------
    tuple[dict[str, list[Path]], dict[str, list[Path]]]
        exact duplicate groups, visual duplicate groups
    """
    def report(message: str) -> None:
        if progress_callback is not None:
            progress_callback(message)

    report("Scanning folders for images...")
    images = scan_images(folder)
    report(f"Found {len(images)} image(s).")

    cache = HashCache(cache_path)

    try:
        report("Finding exact duplicates...")
        exact_duplicates = find_exact_duplicates(images, cache)

        report("Finding visual duplicates...")
        visual_duplicates = find_visual_duplicates(
            images,
            cache,
            exact_duplicates=exact_duplicates,
        )

        report(
            f"Done. Exact groups: {len(exact_duplicates)} | "
            f"Visual groups: {len(visual_duplicates)}"
        )

        return exact_duplicates, visual_duplicates
    finally:
        cache.close()