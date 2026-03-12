import os
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from core.service import run_duplicate_scan


class PhotoSortingApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Photo Sorting")
        self.root.geometry("1300x900")

        self.selected_folder = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")

        self.exact_duplicates: dict[str, list[Path]] = {}
        self.visual_duplicates: dict[str, list[Path]] = {}
        self.current_groups: list[list[Path]] = []

        self.current_preview_image = None
        self.thumbnail_images = []

        self._build_ui()

    def _build_ui(self) -> None:
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="Folder:").pack(side="left")

        folder_entry = ttk.Entry(
            top_frame,
            textvariable=self.selected_folder,
            width=80,
        )
        folder_entry.pack(side="left", padx=5, fill="x", expand=True)

        ttk.Button(
            top_frame,
            text="Choose Folder",
            command=self.choose_folder,
        ).pack(side="left", padx=5)

        ttk.Button(
            top_frame,
            text="Start Scan",
            command=self.start_scan,
        ).pack(side="left", padx=5)

        status_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        status_frame.pack(fill="x")

        ttk.Label(status_frame, textvariable=self.status_text).pack(anchor="w")

        content = ttk.PanedWindow(self.root, orient="horizontal")
        content.pack(fill="both", expand=True, padx=10, pady=10)

        left_panel = ttk.Frame(content)
        right_panel = ttk.Frame(content)

        content.add(left_panel, weight=1)
        content.add(right_panel, weight=2)

        ttk.Label(left_panel, text="Result Type").pack(anchor="w")

        self.result_type = ttk.Combobox(
            left_panel,
            values=["Exact duplicates", "Visual duplicates"],
            state="readonly",
        )
        self.result_type.current(0)
        self.result_type.pack(fill="x", pady=(0, 10))
        self.result_type.bind("<<ComboboxSelected>>", self.refresh_group_list)

        ttk.Label(left_panel, text="Duplicate Groups").pack(anchor="w")

        self.group_listbox = tk.Listbox(left_panel, exportselection=False)
        self.group_listbox.pack(fill="both", expand=True)
        self.group_listbox.bind("<<ListboxSelect>>", self.show_selected_group)

        ttk.Label(right_panel, text="Files in Selected Group").pack(anchor="w")

        self.file_listbox = tk.Listbox(right_panel, exportselection=False)
        self.file_listbox.pack(fill="both", expand=True)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_selected)
        self.file_listbox.bind("<Double-Button-1>", self.open_selected_file_location)

        thumbnail_frame = ttk.Frame(right_panel)
        thumbnail_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.thumb_canvas = tk.Canvas(thumbnail_frame)
        self.thumb_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            thumbnail_frame,
            orient="vertical",
            command=self.thumb_canvas.yview,
        )
        scrollbar.pack(side="right", fill="y")

        self.thumb_canvas.configure(yscrollcommand=scrollbar.set)

        self.thumb_container = ttk.Frame(self.thumb_canvas)
        self.thumb_canvas.create_window((0, 0), window=self.thumb_container, anchor="nw")

        self.thumb_container.bind(
            "<Configure>",
            lambda e: self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all")),
        )

        preview_container = ttk.Frame(right_panel)
        preview_container.pack(fill="x")

        self.preview_label = ttk.Label(preview_container)
        self.preview_label.pack()

        self.metadata_text = tk.Text(
            preview_container,
            height=6,
            state="disabled",
        )
        self.metadata_text.pack(fill="x", pady=(10, 0))

        button_row = ttk.Frame(right_panel)
        button_row.pack(fill="x", pady=(10, 0))

        ttk.Button(
            button_row,
            text="Open Selected Location",
            command=self.open_selected_file_location,
        ).pack(side="left", padx=5)

        ttk.Button(
            button_row,
            text="Open All Locations",
            command=self.open_all_file_locations,
        ).pack(side="left", padx=5)

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder.set(folder)

    def start_scan(self) -> None:
        folder_text = self.selected_folder.get().strip()
        if not folder_text:
            messagebox.showerror("Missing folder", "Please choose a folder first.")
            return

        folder = Path(folder_text)
        if not folder.exists() or not folder.is_dir():
            messagebox.showerror("Invalid folder", "Selected folder does not exist.")
            return

        self.status_text.set("Starting scan...")
        self.group_listbox.delete(0, tk.END)
        self.file_listbox.delete(0, tk.END)
        self.preview_label.configure(image="")
        self.current_preview_image = None
        self._set_metadata_text("")
        self.current_groups.clear()

        thread = threading.Thread(
            target=self._run_scan_thread,
            args=(folder,),
            daemon=True,
        )
        thread.start()

    def _run_scan_thread(self, folder: Path) -> None:
        try:
            exact_duplicates, visual_duplicates = run_duplicate_scan(
                folder=folder,
                cache_path=Path("hash_cache.db"),
                progress_callback=self._threadsafe_status_update,
            )

            self.exact_duplicates = exact_duplicates
            self.visual_duplicates = visual_duplicates

            self.root.after(0, self.refresh_group_list)
            self._threadsafe_status_update("Scan finished.")
        except Exception as exc:
            self.root.after(
                0,
                lambda: messagebox.showerror("Scan failed", str(exc)),
            )
            self._threadsafe_status_update("Scan failed.")

    def _threadsafe_status_update(self, message: str) -> None:
        self.root.after(0, lambda: self.status_text.set(message))

    def refresh_group_list(self, event=None) -> None:
        selection = self.result_type.get()

        if selection == "Exact duplicates":
            groups = list(self.exact_duplicates.values())
        else:
            groups = list(self.visual_duplicates.values())

        self.current_groups = groups
        self.group_listbox.delete(0, tk.END)
        self.file_listbox.delete(0, tk.END)
        self.preview_label.configure(image="")
        self.current_preview_image = None
        self._set_metadata_text("")

        for index, group in enumerate(groups, start=1):
            self.group_listbox.insert(
                tk.END,
                f"Group {index} ({len(group)} files)",
            )

    def show_selected_group(self, event=None) -> None:
        selection = self.group_listbox.curselection()
        if not selection:
            return

        group_index = selection[0]
        group = self.current_groups[group_index]

        self.file_listbox.delete(0, tk.END)

        for path in group:
            self.file_listbox.insert(tk.END, str(path))

        self.display_thumbnails(group)

    def display_thumbnails(self, paths: list[Path]) -> None:
        for widget in self.thumb_container.winfo_children():
            widget.destroy()

        self.thumbnail_images.clear()

        thumb_size = (120, 120)
        columns = 5

        for index, path in enumerate(paths):
            try:
                img = Image.open(path)
                img.thumbnail(thumb_size)

                tk_img = ImageTk.PhotoImage(img)

                label = ttk.Label(self.thumb_container, image=tk_img)
                label.grid(row=index // columns, column=index % columns, padx=5, pady=5)

                label.bind(
                    "<Button-1>",
                    lambda e, p=path: self.select_thumbnail_file(p),
                )

                self.thumbnail_images.append(tk_img)

            except Exception:
                continue

    def select_thumbnail_file(self, path: Path) -> None:
        for i in range(self.file_listbox.size()):
            if Path(self.file_listbox.get(i)) == path:
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(i)
                self.file_listbox.see(i)
                break

        self.display_image_preview(path)
        self.display_metadata(path)

    def on_file_selected(self, event=None) -> None:
        selection = self.file_listbox.curselection()
        if not selection:
            return

        path = Path(self.file_listbox.get(selection[0]))

        self.display_image_preview(path)
        self.display_metadata(path)

    def display_image_preview(self, path: Path) -> None:
        try:
            with Image.open(path) as img:
                max_size = (500, 400)
                img.thumbnail(max_size)

                tk_img = ImageTk.PhotoImage(img.copy())

            self.preview_label.configure(image=tk_img)
            self.current_preview_image = tk_img

        except Exception:
            self.preview_label.configure(image="")
            self.current_preview_image = None

    def display_metadata(self, path: Path) -> None:
        try:
            stat = path.stat()

            info = [
                f"Path: {path}",
                f"Size: {stat.st_size / (1024 * 1024):.2f} MB",
                f"Modified: {stat.st_mtime}",
            ]

            try:
                with Image.open(path) as img:
                    info.append(f"Resolution: {img.width} x {img.height}")
                    info.append(f"Format: {img.format}")
            except Exception:
                pass

            text = "\n".join(info)

        except Exception as exc:
            text = f"Metadata unavailable\n{exc}"

        self._set_metadata_text(text)

    def _set_metadata_text(self, text: str) -> None:
        self.metadata_text.configure(state="normal")
        self.metadata_text.delete("1.0", tk.END)
        self.metadata_text.insert(tk.END, text)
        self.metadata_text.configure(state="disabled")

    def  open_selected_file_location(self, event=None) -> None:
        selection = self.file_listbox.curselection()
        if not selection:
            return

        selected_path = Path(self.file_listbox.get(selection[0]))

        if not selected_path.exists():
            messagebox.showerror("Missing file", "Selected file no longer exists.")
            return

        self._open_in_file_manager(selected_path)

    def open_all_file_locations(self) -> None:
        selection = self.group_listbox.curselection()
        if not selection:
            return

        group = self.current_groups[selection[0]]

        existing_paths = [path for path in group if path.exists()]

        if not existing_paths:
            messagebox.showerror(
                "Missing files",
                "None of the files in the selected group exist anymore.",
            )
            return

        for path in existing_paths:
            self._open_in_file_manager(path)

    @staticmethod
    def _open_in_file_manager(path: Path) -> None:
        if os.name == "nt":
            subprocess.run(["explorer", "/select,", str(path)])
        else:
            subprocess.run(["xdg-open", str(path.parent)])