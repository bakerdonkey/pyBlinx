from pathlib import Path
from tkinter import Tk, filedialog


def tk_load_dir(dir_type):
    Tk().withdraw()
    if dir_type == "base":
        titlestr = "Select game folder"
    elif dir_type == "out":
        titlestr = "Select output folder"
    else:
        return None

    in_path = filedialog.askdirectory(title=titlestr)
    if not in_path:
        print("You must select a folder or provide a path via CLI args")
        exit(1)
    return Path(in_path)
