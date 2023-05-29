from struct import unpack
from pyblinx.address import get_raw_address
from pyblinx.helpers import validate_file_handle

TEXTURE_NAME_LIST_ITEM_SIZE = 32


class MaterialList:
    def __init__(self, xbe, entry_offset, section):
        self.xbe = validate_file_handle(xbe)
        self.offset = get_raw_address(entry_offset, section)
        self.section = section

        self.name = "tl_" + self.section + "_" + hex(self.offset)

        self._texture_names = None
        self._material_names = None

    def __str__(self):
        return self.name

    @property
    def is_parsed(self):
        return bool(self._texture_names)

    @property
    def texture_names(self):
        if self._texture_names:
            return self._texture_names
        return self.parse_texture_names()
    
    @property
    def material_names(self):
        if self._material_names:
            return self._material_names
        return self._get_material_names()

    def parse_texture_names(self):
        """
        Parse texture names for a MaterialList.
        """
        header = self._parse_texture_names_header()
        texture_names_offset = get_raw_address(
            header["texture_names_offset"], self.section
        )
        texture_names_length = header["texture_names_length"]

        self.xbe.seek(texture_names_offset)

        texture_names = []
        for _ in range(texture_names_length):
            chars = unpack(
                f"<{TEXTURE_NAME_LIST_ITEM_SIZE}c",
                self.xbe.read(TEXTURE_NAME_LIST_ITEM_SIZE),
            )
            texture_name = ""
            for c in chars:
                if c != b"\x00":
                    texture_name += c.decode("latin-1")

            texture_names.append(texture_name)

        self._texture_names = texture_names
        return texture_names

    # TODO: parse and write game-defined materials
    def write_material_library(self, out_file, media_path):
        """
        Create a .mat material library with dummy Kd and Ks values.
        """
        f = validate_file_handle(out_file, usage="a+")
        paths = [media_path + "/" + string + ".dds" for string in self.texture_names]
        material_names = self.material_names

        for i in range(len(paths)):
            f.write(f"newmtl {material_names[i]}\n")
            f.write("Kd 0.8 0.8 0.8\n")
            f.write("Ks 0.0 0.0 0.0\n")
            f.write(f"map_Kd {paths[i]}\n\n")

    def _parse_texture_names_header(self):
        """
        Read header and return its data.
        """
        self.xbe.seek(self.offset)

        texture_names_offset_pointer = unpack("i", self.xbe.read(4))[0]
        texture_names_length = unpack("i", self.xbe.read(4))[0]

        return {
            "texture_names_offset": texture_names_offset_pointer,
            "texture_names_length": texture_names_length,
        }

    def _get_material_names(self):
        return [hex(self.offset) + string for string in self.texture_names]
