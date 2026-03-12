from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from core.cache import HashCache
from core.hasher import compute_hash


def _hash_single(path: Path) -> tuple[Path, str | None]:
    ph = compute_hash(path)
    if ph is None:
        return path, None
    return path, str(ph)


def find_duplicates(
    paths: list[Path],
    cache: HashCache,
    max_workers: int = 8,
    batch_size: int = 200,
):
    hash_map = defaultdict(list)

    cached_paths: list[tuple[Path, str]] = []
    paths_to_hash: list[Path] = []

    for path in paths:
        cached_hash = cache.get(path)

        if cached_hash is None:
            paths_to_hash.append(path)
        else:
            cached_paths.append((path, cached_hash))

    for path, cached_hash in cached_paths:
        hash_map[cached_hash].append(path)

    total_to_hash = len(paths_to_hash)
    pending_cache_writes: list[tuple[Path, str]] = []

    if total_to_hash > 0:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_hash_single, path) for path in paths_to_hash]

            for i, future in enumerate(as_completed(futures), start=1):
                path, hash_value = future.result()

                if i % 100 == 0 or i == total_to_hash:
                    print(f"Hashing {i}/{total_to_hash}", end="\r")

                if hash_value is None:
                    continue

                hash_map[hash_value].append(path)
                pending_cache_writes.append((path, hash_value))

                if len(pending_cache_writes) >= batch_size:
                    cache.set_many(pending_cache_writes)
                    pending_cache_writes.clear()

        if pending_cache_writes:
            cache.set_many(pending_cache_writes)

        print()

    return {h: files for h, files in hash_map.items() if len(files) > 1}