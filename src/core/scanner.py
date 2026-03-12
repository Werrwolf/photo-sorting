from pathlib import Path

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def scan_images(root_path: Path):
    files = []

    for path in root_path.rglob("*"):
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)

    return files