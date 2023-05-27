from struct import unpack
from pyblinx.address import get_raw_address
from pyblinx.helpers import validate_file_handle

STRINGLIST_ITEM_SIZE = 32


class MaterialList:
    def __init__(self, xbe, entry_offset, section):
        self.xbe = validate_file_handle(xbe)
        self.offset = get_raw_address(entry_offset, section)
        self.section = section

        self.name = "tl_" + self.section + "_" + hex(self.offset)

        self.stringlist = None

    def __str__(self):
        return self.name

    def parse_stringlist(self):
        """
        Parse texture names and store in self.stringlist.

        """
        header = self._parse_stringlist_header()
        stringlist_offset = get_raw_address(header["stringlist_offset"], self.section)
        stringlist_length = header["stringlist_length"]

        self.xbe.seek(stringlist_offset)

        strings = []
        for _ in range(stringlist_length):
            chars = unpack(
                f"<{STRINGLIST_ITEM_SIZE}c", self.xbe.read(STRINGLIST_ITEM_SIZE)
            )
            string = ""
            for c in chars:
                if c != b"\x00":
                    string += c.decode("latin-1")

            strings.append(string)

        self.stringlist = strings
        return strings

    # TODO: parse and write game-defined materials
    def write_material_library(self, out_file, media_path):
        """
        Create a .mat material library from the texlist with dummy Kd and Ks values.
        """
        f = validate_file_handle(out_file, usage="a+")
        paths = [media_path + "/" + string + ".dds" for string in self.stringlist]
        materials = [hex(self.offset) + string for string in self.stringlist]

        for i in range(len(paths)):
            path = paths[i]
            f.write(f"newmtl {materials[i]}\n")
            f.write("Kd 0.8 0.8 0.8\n")
            f.write("Ks 0.0 0.0 0.0\n")
            f.write(f"map_Kd {path}\n\n")

    def _parse_stringlist_header(self):
        """
        Read header and return its data.
        """
        self.xbe.seek(self.offset)

        stringlist_offset_pointer = unpack("i", self.xbe.read(4))[0]
        stringlist_length = unpack("i", self.xbe.read(4))[0]

        return {
            "stringlist_offset": stringlist_offset_pointer,
            "stringlist_length": stringlist_length,
        }
