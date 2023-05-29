from struct import unpack
from pyblinx.address import get_raw_address
from pyblinx.helpers import validate_file_handle


class Node:
    def __init__(
        self, xbe, entry_offset, section, material_list=None, parent_coords=None
    ):
        self.xbe = validate_file_handle(xbe)
        self.section = section
        self.offset = get_raw_address(entry_offset, self.section)
        self.material_list = material_list

        header = self.parse_header()

        # TODO: what the heck is "entry"??
        self.entry = header["entry"]
        self.geometry_header = header["geometry_header"]
        self.world_coords = header["world_coords"]
        self.left_child_offset = header["left"]
        self.right_child_offset = header["right"]

        # fmt: off
        self.parent_coords = parent_coords or (0, 0, 0, 0, 0, 0, 0, 0, 0,)
        # fmt: on

        self.left_child = None
        self.right_child = None

    def parse_header(self):
        """
        Parse header stub and store its data.
        """
        f = self.xbe
        f.seek(self.offset)
        entry = unpack("i", f.read(4))[0]

        geometry_header = unpack("i", f.read(4))[0]
        if geometry_header == 0:
            geometry_header = None

        world = []
        for _ in range(9):
            world.append(unpack("f", f.read(4))[0])

        left = unpack("i", f.read(4))[0]
        if left == 0:
            left = None

        right = unpack("i", f.read(4))[0]
        if right == 0:
            right = None

        return {
            "entry": entry,
            "geometry_header": geometry_header,
            "world_coords": world,
            "left": left,
            "right": right,
        }
