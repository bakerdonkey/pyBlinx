from struct import unpack
from .address import get_section_address_mapping, get_raw_address
from .helpers import verify_file_arg_o, verify_file_arg_b


class Node:
    section_table = get_section_address_mapping()

    def __init__(self, xbe, entry_offset, section, texlist=None, parent_coords=None):
        self.xbe = verify_file_arg_b(xbe)
        self.section = section
        self.offset = get_raw_address(entry_offset, self.section, Node.section_table)
        self.texlist = texlist

        header = self.parse_header()

        # TODO: rename left_node/right_node and left/right for readability
        self.entry = header["entry"]
        self.block = header["block_ptr"]
        self.world_coords = header["world_coords"]
        self.left = header["left_ptr"]
        self.right = header["right_ptr"]

        self.parent_coords = (
            parent_coords
            if parent_coords is not None
            else (
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            )
        )
        self.left_node = None
        self.right_node = None

    def parse_header(self):
        """
        Parse header stub and store its data.
        """
        f = self.xbe
        f.seek(self.offset)
        entry = unpack("i", f.read(4))[0]

        block = unpack("i", f.read(4))[0]
        if block == 0:
            block = None

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
            "block_ptr": block,
            "world_coords": world,
            "left_ptr": left,
            "right_ptr": right,
        }
