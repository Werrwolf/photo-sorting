from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".gif",
    ".tiff",
    ".heic",
}


def scan_images(root_path: Path) -> list[Path]:
    if not root_path.exists():
        raise FileNotFoundError(f"Path does not exist: {root_path}")

    if not root_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root_path}")

    image_files: list[Path] = []

    for path in root_path.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            image_files.append(path)

    return image_files