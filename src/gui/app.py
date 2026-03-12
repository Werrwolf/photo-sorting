import os
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core.service import run_duplicate_scan


class PhotoSortingApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Photo Sorting")
        self.root.geometry("1100x700")

        self.selected_folder = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")

        self.exact_duplicates: dict[str, list[Path]] = {}
        self.visual_duplicates: dict[str, list[Path]] = {}
        self.current_groups: list[list[Path]] = []

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

        ttk.Button(top_frame, text="Choose Folder", command=self.choose_folder).pack(
            side="left",
            padx=5,
        )
        ttk.Button(top_frame, text="Start Scan", command=self.start_scan).pack(
            side="left",
            padx=5,
        )

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
        self.file_listbox.bind("<Double-Button-1>", self.open_selected_file_location)

        button_row = ttk.Frame(right_panel)
        button_row.pack(fill="x", pady=(10, 0))

        ttk.Button(
            button_row,
            text="Open Selected File Location",
            command=self.open_selected_file_location,
        ).pack(side="left")

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

    def open_selected_file_location(self, event=None) -> None:
        selection = self.file_listbox.curselection()
        if not selection:
            return

        selected_path = Path(self.file_listbox.get(selection[0]))

        if not selected_path.exists():
            messagebox.showerror("Missing file", "Selected file no longer exists.")
            return

        self._open_in_file_manager(selected_path)

    @staticmethod
    def _open_in_file_manager(path: Path) -> None:
        if os.name == "nt":
            subprocess.run(["explorer", "/select,", str(path)])
        else:
            subprocess.run(["xdg-open", str(path.parent)])