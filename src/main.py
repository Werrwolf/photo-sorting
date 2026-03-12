import tkinter as tk

from gui.app import PhotoSortingApp


def main() -> None:
    root = tk.Tk()
    PhotoSortingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()