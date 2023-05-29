from pathlib import Path
from tkinter import Tk, filedialog


# TODO: remove this. rely on duck-typing!!
def validate_file_handle(file, usage="rb"):
    """
    Type-check output file-like argument. If string, assume path and open file at that path (text append mode). Otherwise return
    open file handle.
    """
    if isinstance(file, str):
        # TODO: Handle invalid file paths.
        with open(file, usage) as f:
            return f

    return file


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
