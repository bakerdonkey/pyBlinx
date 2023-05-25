from tkinter import Tk, filedialog


def validate_file_handle(file, usage='rb'):
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
    return in_path
