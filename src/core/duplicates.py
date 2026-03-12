from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from core.cache import HashCache
from core.file_hash import compute_file_hash
from core.hasher import compute_hash

ProgressCallback = Callable[[str], None]


def _compute_exact_hash(path: Path) -> tuple[Path, str | None]:
    return path, compute_file_hash(path)


def _compute_perceptual_hash(path: Path) -> tuple[Path, str | None]:
    ph = compute_hash(path)
    if ph is None:
        return path, None
    return path, str(ph)


def _group_cached_and_uncached(
    paths: list[Path],
    cache_getter,
) -> tuple[list[tuple[Path, str]], list[Path]]:
    cached: list[tuple[Path, str]] = []
    uncached: list[Path] = []

    for path in paths:
        cached_hash = cache_getter(path)
        if cached_hash is None:
            uncached.append(path)
        else:
            cached.append((path, cached_hash))

    return cached, uncached


def _resolve_hashes_parallel(
    paths: list[Path],
    worker,
    cache_setter,
    max_workers: int,
    batch_size: int,
    label: str,
    progress_callback: ProgressCallback | None = None,
) -> list[tuple[Path, str]]:
    resolved: list[tuple[Path, str]] = []
    pending_cache_writes: list[tuple[Path, str]] = []

    total = len(paths)
    if total == 0:
        if progress_callback is not None:
            progress_callback(f"{label}: nothing to hash")
        return resolved

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, path) for path in paths]

        for i, future in enumerate(as_completed(futures), start=1):
            path, hash_value = future.result()

            if i % 100 == 0 or i == total:
                message = f"{label}: {i}/{total}"
                print(message, end="\r")
                if progress_callback is not None:
                    progress_callback(message)

            if hash_value is None:
                continue

            resolved.append((path, hash_value))
            pending_cache_writes.append((path, hash_value))

            if len(pending_cache_writes) >= batch_size:
                cache_setter(pending_cache_writes)
                pending_cache_writes.clear()

    if pending_cache_writes:
        cache_setter(pending_cache_writes)

    print()
    return resolved


def _group_by_hash(entries: list[tuple[Path, str]]) -> dict[str, list[Path]]:
    grouped = defaultdict(list)

    for path, hash_value in entries:
        grouped[hash_value].append(path)

    return {hash_value: files for hash_value, files in grouped.items() if len(files) > 1}


def find_exact_duplicates(
    paths: list[Path],
    cache: HashCache,
    max_workers: int = 8,
    batch_size: int = 200,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, list[Path]]:
    """
    Find files that are exact binary duplicates.

    Exact duplicates are detected using a cryptographic SHA-256 hash.
    Files are considered duplicates only if their binary contents are
    identical.

    Example:
        photo.jpg
        copy/photo.jpg

    These files are guaranteed to contain the same data and can be safely
    deduplicated automatically.

    Parameters
    ----------
    paths : list[Path]
        Image files to analyze.
    cache : HashCache
        SQLite cache storing previously computed hashes.
    max_workers : int
        Number of worker threads used for hashing.
    batch_size : int
        Number of hashes written to the cache in one database transaction.
    progress_callback : ProgressCallback | None
        Optional callback for reporting progress updates.

    Returns
    -------
    dict[str, list[Path]]
        Mapping of hash → list of files sharing that hash.
        Only groups with more than one file are returned.
    """
    cached, uncached = _group_cached_and_uncached(paths, cache.get_file_hash)

    resolved = list(cached)
    resolved.extend(
        _resolve_hashes_parallel(
            uncached,
            worker=_compute_exact_hash,
            cache_setter=cache.set_many_file_hashes,
            max_workers=max_workers,
            batch_size=batch_size,
            label="Exact hashing",
            progress_callback=progress_callback,
        )
    )

    return _group_by_hash(resolved)


def find_visual_duplicates(
    paths: list[Path],
    cache: HashCache,
    exact_duplicates: dict[str, list[Path]] | None = None,
    max_workers: int = 8,
    batch_size: int = 200,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, list[Path]]:
    """
    Find visually similar images using perceptual hashing.

    Visual duplicates are images that look the same to a human viewer but
    may differ in binary file content. Examples include:

        - recompressed images
        - resized images
        - format conversions (PNG → JPG)
        - metadata changes
        - images downloaded from messaging apps

    Exact duplicates detected earlier are excluded to avoid duplicate
    reporting.

    Parameters
    ----------
    paths : list[Path]
        Image files to analyze.
    cache : HashCache
        SQLite cache storing perceptual hashes.
    exact_duplicates : dict[str, list[Path]] | None
        Exact duplicate groups to exclude from visual duplicate detection.
    max_workers : int
        Number of worker threads used for hashing.
    batch_size : int
        Number of hashes written to the cache per transaction.
    progress_callback : ProgressCallback | None
        Optional callback for reporting progress updates.

    Returns
    -------
    dict[str, list[Path]]
        Mapping of perceptual hash → visually similar images.
        Only groups with more than one file are returned.
    """
    exact_duplicate_paths: set[Path] = set()

    if exact_duplicates:
        for files in exact_duplicates.values():
            exact_duplicate_paths.update(files)

    remaining_paths = [path for path in paths if path not in exact_duplicate_paths]

    cached, uncached = _group_cached_and_uncached(remaining_paths, cache.get_perceptual_hash)

    resolved = list(cached)
    resolved.extend(
        _resolve_hashes_parallel(
            uncached,
            worker=_compute_perceptual_hash,
            cache_setter=cache.set_many_perceptual_hashes,
            max_workers=max_workers,
            batch_size=batch_size,
            label="Visual hashing",
            progress_callback=progress_callback,
        )
    )

    return _group_by_hash(resolved)