from pathlib import Path
from tkinter import Tk, filedialog


def tk_load_dir(dir_type: str):
    Tk().withdraw()
    if dir_type == "base":
        title = "Select game folder"
    elif dir_type == "out":
        title = "Select output folder"
    else:
        return None

    in_path = filedialog.askdirectory(title=title)
    if not in_path:
        print("You must select a folder or provide a path via CLI args")
        exit(1)
    return Path(in_path)


def clean_out_directory(directory: Path):
    if directory.exists():
        for item in directory.iterdir():
            if item.is_dir():
                clean_out_directory(item)
            else:
                item.unlink()
        directory.rmdir()
