from pathlib import Path
from PIL import Image
import imagehash


def compute_hash(path: Path):
    """
    Compute a perceptual hash (pHash) of an image.

    Perceptual hashes represent the *visual appearance* of an image rather
    than its binary file content. Two images that look the same may produce
    the same or very similar perceptual hashes even if their files differ.

    Used for detecting:
        - recompressed images
        - resized images
        - format conversions (PNG → JPG)
        - images with stripped metadata

    This is used for finding *visual duplicates*.

    Parameters
    ----------
    path : Path
        Image file path.

    Returns
    -------
    ImageHash | None
        Perceptual hash object or None if the image could not be processed.
    """
    try:
        with Image.open(path) as img:
            return imagehash.phash(img)
    except Exception:
        return None