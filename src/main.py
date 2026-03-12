from pathlib import Path

from core.scanner import scan_images


def main() -> None:
    folder = Path(input("Enter folder path: ").strip())
    image_files = scan_images(folder)

    print(f"Found {len(image_files)} image(s).")

    for path in image_files[:10]:
        print(path)


if __name__ == "__main__":
    main()