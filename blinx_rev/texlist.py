from struct import unpack
from address import section_addresses
from address import rawaddress
from chunk import verify_file_arg_b
from chunk import verify_file_arg_o

class Texlist :
    section_table = section_addresses()

    def __init__(self, xbe, entry_offset, section) :
        self.xbe = verify_file_arg_b(xbe)

        self.offset = rawaddress(entry_offset, section, Texlist.section_table)

        self.section = section

        self.header = self.parse_header()

        self.top = rawaddress(self.header['top_adr'], self.section, Texlist.section_table)

        self.length = self.header['size']

        self.strlist = None


    def parse_header(self) :
        f = self.xbe
        f.seek(self.offset)

        top_ptr = unpack('i', f.read(4))[0]
        length = unpack('i', f.read(4))[0]

        return {
            'top_adr': top_ptr,
            'size': length
        }

    def parse_strlist(self) :
        f = self.xbe
        s = []

        f.seek(self.top)
        for _ in range(self.length) :
            chars = unpack('<32c', f.read(32))
            string = ''
            for c in chars :
                if c != b'\x00' :
                    string += c.decode('latin-1')
            
            print('{}\t{}'.format(_, string))
            s.append(string)

        self.strlist = s
        return s

    def strlist_to_path(self, mediapath) :
        if self.strlist is None : print('Stringlist not parsed, can not convert to pathlist')
        strlist = self.strlist
        pathlist = []
        for s in strlist :
            s = mediapath + '/' + s + '.dds'
            pathlist.append(s)
        return pathlist