from struct import unpack
from texlist import Texlist
from address import section_addresses
from address import rawaddress
from helpers import verify_file_arg_o
from helpers import verify_file_arg_b

class Node :
    section_table = section_addresses()

    def __init__(self, xbe, entry_offset, section, texlist=None) :

        self.xbe = verify_file_arg_b(xbe)
        self.section = section
        self.offset = rawaddress(entry_offset, self.section, Node.section_table)

        header = self.parse_header()

        self.entry = header['entry']
        self.world_coords = header['world_coords']
        self.left = header['left_ptr']
        self.right = header['right_ptr']

    def parse_header(self) :
        f = self.xbe
        f.seek(self.offset)
        entry = unpack('i', f.read(4))[0]

        f.seek(4, 1)        #TODO: research this value. Is it always 00000000?

        world = []
        for _ in range(9) : world.append(unpack('f', f.read(4))[0])

        left = unpack('i', f.read(4))[0]
        right = unpack('i', f.read(4))[0]

        return {
            'entry': entry,
            'world_coords': world,
            'left_ptr': left,
            'right_ptr': right
        }