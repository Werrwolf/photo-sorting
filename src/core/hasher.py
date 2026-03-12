from PIL import Image
import imagehash


def compute_hash(path):
    with Image.open(path) as img:
        return imagehash.phash(img)