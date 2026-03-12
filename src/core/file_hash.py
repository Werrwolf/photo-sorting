import hashlib
from pathlib import Path


def compute_file_hash(path: Path, chunk_size: int = 1024 * 1024) -> str | None:
    """
    Compute a cryptographic hash (SHA-256) of a file.

    This hash identifies *exact duplicates*, meaning files that are
    byte-for-byte identical. If two files produce the same SHA-256 hash,
    they contain exactly the same binary data.

    Used for detecting:
        - copied files
        - duplicated backups
        - identical images in different folders

    Parameters
    ----------
    path : Path
        File path to hash.
    chunk_size : int
        Size of chunks read from the file to avoid loading the entire file
        into memory.

    Returns
    -------
    str | None
        Hexadecimal SHA-256 hash of the file or None if the file could not
        be processed.
    """
    try:
        hasher = hashlib.sha256()

        with path.open("rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)

        return hasher.hexdigest()
    except Exception:
        return None