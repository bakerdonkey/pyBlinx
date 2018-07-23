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

        self.matlist = None


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

    #TODO: implement game-defined materials
    def write_mtl(self, file, mediapath) :
        f = verify_file_arg_o(file)
        pathlist = self.strlist_to_pathlist(mediapath)
        matlist = self.strlist_to_matlist()
        
        i = 0
        for mat in matlist :
            path = pathlist[i] 
            f.write('newmtl {}\n'.format(mat))
            f.write('Kd 0.8 0.8 0.8\n')
            f.write('map_Kd {}\n\n'.format(path))
            i += 1



    def strlist_to_pathlist(self, mediapath) :
        if self.strlist is None : 
            print('Stringlist not parsed, can not convert to pathlist')
            return None
        
        strlist = self.strlist
        pathlist = []
        for s in strlist :
            p = mediapath + '/' + s + '.dds'
            pathlist.append(p)
        return pathlist

    def strlist_to_matlist(self) :
        if self.strlist is None : 
            print('Stringlist not parsed, can not convert to material list')
            return None
        
        strlist = self.strlist
        matlist = []
        for s in strlist :
            m = hex(self.offset) + s
            matlist.append(m)

        self.matlist = matlist
        return matlist