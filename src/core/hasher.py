from pathlib import Path
from PIL import Image
import imagehash


def compute_hash(path: Path):
    try:
        with Image.open(path) as img:
            return imagehash.phash(img)
    except Exception:
        return None