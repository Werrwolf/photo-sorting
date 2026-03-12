from collections import defaultdict
from pathlib import Path

from core.hasher import compute_hash


def find_duplicates(paths: list[Path]):
    hash_map = defaultdict(list)

    for path in paths:
        h = compute_hash(path)

        if h is None:
            continue

        hash_map[str(h)].append(path)

    duplicates = {
        hash_value: files
        for hash_value, files in hash_map.items()
        if len(files) > 1
    }

    return duplicates