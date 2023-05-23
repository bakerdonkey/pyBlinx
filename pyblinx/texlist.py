from struct import unpack
from pyblinx.address import get_section_address_mapping, get_raw_address
from pyblinx.helpers import verify_file_arg_o, verify_file_arg_b


class Texlist:
    section_address_mapping = get_section_address_mapping()

    def __init__(self, xbe, entry_offset, section):
        self.xbe = verify_file_arg_b(xbe)

        self.offset = get_raw_address(entry_offset, section, Texlist.section_address_mapping)
        self.section = section
        self.header = self.parse_header()
        self.top = get_raw_address(
            self.header["top_adr"], self.section, Texlist.section_address_mapping
        )
        self.length = self.header["size"]

        self.strlist = None
        self.matlist = None
        self.pathlist = None

        self.name = "tl_" + section + "_" + hex(self.offset)

    def __str__(self):
        return self.name

    def parse_header(self):
        """
        Read header stub and return its data.
        """
        f = self.xbe
        f.seek(self.offset)

        top_ptr = unpack("i", f.read(4))[0]
        length = unpack("i", f.read(4))[0]

        return {"top_adr": top_ptr, "size": length}

    def parse_strlist(self):
        """
        Parse texture names and store in self.strlist.
        """
        f = self.xbe
        s = []

        f.seek(self.top)
        for _ in range(self.length):
            chars = unpack("<32c", f.read(32))
            string = ""
            for c in chars:
                if c != b"\x00":
                    string += c.decode("latin-1")

            s.append(string)

        self.strlist = s
        return s

    # TODO: implement game-defined materials
    def write_mtl(self, file, mediapath):
        """
        Create a .mat material library from the texlist with dummy Kd and Ks values.
        """
        f = verify_file_arg_o(file)
        pathlist = self.strlist_to_pathlist(mediapath)
        matlist = self.strlist_to_matlist()

        i = 0
        for mat in matlist:
            path = pathlist[i]
            f.write("newmtl {}\n".format(mat))
            f.write("Kd 0.8 0.8 0.8\n")
            f.write("Ks 0.0 0.0 0.0\n")
            f.write("map_Kd {}\n\n".format(path))
            i += 1

    def strlist_to_pathlist(self, mediapath):
        """
        Create a pathlist from self.strlist and a provided path to media folder.
        """
        if self.strlist is None:
            print("Stringlist not parsed, can not convert to pathlist")
            return None

        strlist = self.strlist
        pathlist = []
        for s in strlist:
            p = mediapath + "/" + s + ".dds"
            pathlist.append(p)

        self.pathlist = pathlist
        return pathlist

    def strlist_to_matlist(self):
        """
        Create a matlist from self.strlist
        """
        if self.strlist is None:
            print("Stringlist not parsed, can not convert to material list")
            return None

        strlist = self.strlist
        matlist = []
        for s in strlist:
            m = hex(self.offset) + s
            matlist.append(m)

        self.matlist = matlist
        return matlist
