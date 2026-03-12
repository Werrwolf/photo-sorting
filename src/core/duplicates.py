from collections import defaultdict


def group_by_hash(paths, hash_func):
    groups = defaultdict(list)

    for p in paths:
        h = hash_func(p)
        groups[h].append(p)

    return {h: g for h, g in groups.items() if len(g) > 1}