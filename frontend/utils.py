import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional


def check_netlist_filetype(filepath: str) -> bool:
    """Checks if the selected file has a valid netlist extension."""
    valid_extensions = (".cir", ".net", ".sp", ".txt")
    return filepath.lower().endswith(valid_extensions)


def open_file_dialog() -> Optional[str]:
    """Opens a file dialog for the user to select a netlist."""
    file_path = filedialog.askopenfilename(
        title="Select a Netlist File",
        filetypes=[
            (
                "Netlist Files",
                ("*.cir", "*.net", "*.sp", "*.txt"),
            ),  # Corrected filetypes
            ("All Files", "*.*"),
        ],
    )
    if file_path and not check_netlist_filetype(file_path):
        messagebox.showerror(
            "Error", "Invalid file type. Please select a .cir, .net, .sp, or .txt file."
        )
        return None
    return file_path
