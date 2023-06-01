from pathlib import Path
from struct import unpack
from typing import BinaryIO, TextIO
from pyblinx.address import get_raw_address

TEXTURE_NAME_LIST_ITEM_SIZE = 32


class MaterialList:
    def __init__(self, xbe: BinaryIO, entry_offset: int, section: str):
        self.xbe = xbe
        self.offset = get_raw_address(entry_offset, section)
        self.section = section

        self.name = "mtl_" + self.section + "_" + hex(self.offset)

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

    def parse_texture_names(self) -> list:
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
    def write_material_library(self, file: TextIO, media_path: Path):
        """
        Create a .mat material library with dummy Kd and Ks values.
        """
        paths = [media_path / f"{string}.dds" for string in self.texture_names]
        materials = zip(self.material_names, paths)

        for material in materials:
            absolute_path = str(material[1].resolve())
            file.write(f"newmtl {material[0]}\n")
            file.write("Kd 0.8 0.8 0.8\n")
            file.write("Ks 0.0 0.0 0.0\n")
            file.write(f"map_Kd {absolute_path}\n\n")

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
