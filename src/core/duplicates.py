from collections import defaultdict
from pathlib import Path

from core.hasher import compute_hash
from core.cache import HashCache


def find_duplicates(paths: list[Path], cache: HashCache):

    hash_map = defaultdict(list)

    for path in paths:

        h = cache.get(path)

        if h is None:
            ph = compute_hash(path)

            if ph is None:
                continue

            h = str(ph)
            cache.set(path, h)

        hash_map[h].append(path)

    return {h: files for h, files in hash_map.items() if len(files) > 1}