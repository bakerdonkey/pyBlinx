from struct import unpack
from address import section_addresses
from address import rawaddress


class Chunk :
    #TODO: reference a global, not the function to improve clearity.
    section_table = section_addresses()


    def __init__(self, xbe, entry_offset, section, texarray=None) :
        self.xbe = verify_file_arg_b(xbe)
        
        self.offset = rawaddress(entry_offset, section, Chunk.section_table)
        
        self.texarray = texarray

        self.section = section

        self.header = self.parse_header() #TODO: parse header

    def parse_header(self) :
        f = self.xbe
        f.seek(self.offset)
        entry = unpack('i', f.read(4))[0]

        return {
            'entry' : entry
        }


def verify_file_arg_b(fileobj) :
    '''
    Type-check file-like argument. If it's a string, assume it's a path and open file at that path (binary mode). Otherwise return open file handle.
    TODO: Handle invalid file paths. 
    '''
    if isinstance(fileobj, str) :
        with open(fileobj, 'rb') as f :
            return f
    else : return fileobj