def verify_file_arg_b(fileobj):
    """
    Type-check file-like argument. If it's a string, assume it's a path and open file at that path (binary mode). Otherwise return
    open file handle.
    TODO: Handle invalid file paths.
    """
    if isinstance(fileobj, str):
        with open(fileobj, "rb") as f:
            return f
    else:
        return fileobj


def verify_file_arg_o(fileobj, usage="a+"):
    """
    Type-check output file-like argument. If string, assume path and open file at that path (text append mode). Otherwise return
    open file handle.
    TODO: Handle invalid file paths.
    """
    if isinstance(fileobj, str):
        with open(fileobj, usage) as f:
            return f
    else:
        return fileobj
