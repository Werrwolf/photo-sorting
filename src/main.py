from pathlib import Path

from core.scanner import scan_images
from core.duplicates import find_duplicates


def main():

    folder = Path(input("Enter folder path: ").strip())

    images = scan_images(folder)

    print(f"Found {len(images)} images")

    duplicates = find_duplicates(images)

    print(f"\nDuplicate groups: {len(duplicates)}\n")

    for h, files in list(duplicates.items())[:5]:

        print("----")
        for f in files:
            print(f)


if __name__ == "__main__":
    main()