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

        self.voffset = rawaddress(self.header['voffset'], section, Chunk.section_table)
        self.vertices = None

        self.toffset = rawaddress(self.header['toffset'], section, Chunk.section_table)
        self.triangles = None

    def parse_header(self) :
        '''
        Reads chunk metadata contained in the header and returns a dictionary. Chunklist pointers are None
        if they do not exist.
        '''
        f = self.xbe
        f.seek(self.offset)

        entry = unpack('i', f.read(4))[0]

        chunk_offset = unpack('i', f.read(4))[0]
        f.seek(-40, 1)

        vdata_offset = unpack('i', f.read(4))[0]
        tdata_offset = unpack('i', f.read(4))[0]

        float_array_0 = []
        for _ in range(6) : float_array_0.append(unpack('f', f.read(4))[0])
        
        f.seek(8, 1)

        world = []
        for _ in range(9) : world.append(unpack('f', f.read(4))[0])

        clist_ptr_0 = unpack('i', f.read(4))[0]
        if clist_ptr_0 == 0 : clist_ptr_0 = None

        clist_ptr_1 = unpack('i', f.read(4))[0]
        if clist_ptr_1 == 0 : clist_ptr_1 = None

        return {
            'entry' : entry,
            'virtual_offset' : chunk_offset,
            'voffset' : vdata_offset,
            'toffset' : tdata_offset,
            'f_array_0' : float_array_0,
            'world_coords' : world,
            'clist_ptr_0' : clist_ptr_0,
            'clist_ptr_1' : clist_ptr_1
        }

    def parse_vertices(self) :
        '''
        Reads vertex list from xbe. Returns a list[count], where each element is a tuple[3] denoting xyz.
        '''
        f = self.xbe
        f.seek(self.voffset + 6)
        
        count = unpack('h', f.read(2))[0]
        f.seek(8, 1)

        v = []
        for _ in range(count) :
            word = unpack('fff', f.read(12))
            v.append(word)
            f.seek(4, 1)
        
        self.vertices = v
        return v

    def parse_triangles(self, part_count) :
        f = self.xbe
        f.seek(self.toffset)

        # TODO: Research header types and usage.
        flavor = unpack('h', f.read(2))
        header_size = unpack('h', f.read(2))
        f.seek(header_size, 1)

        t = []

        while(True) :
            tripart = self.parse_tripart()
            t.append((tripart[0], tripart[1]))
            if tripart[2] : break

        


    def parse_tripart(self) :
        '''
        Reads tripart. Returns tuple (tripart, texlist index, last) where tripart is a list of tuples (vertex index, tex_x, tex_y),
        texlist index assigns the texture, and last is an escape flag.
        '''
        f = self.xbe

        t = []
        escape = False
        f.seek(2, 1)        
        texlist_index = unpack('h', f.read(2))[0] ^ 0x4000     
        f.seek(2, 1)
        
        # Check if last tripart 
        tripart_size = unpack('h', f.read(2))[0] * 2
        f.seek(tripart_size, 1) 
        if f.read(4) is b'\xff\x00\x00\x00' :  escape = True # Escape symbol
        f.read(-(tripart_size + 4), 1)

        #TODO finish

        return (None, texlist_index, escape)

def verify_file_arg_b(fileobj) :
    '''
    Type-check file-like argument. If it's a string, assume it's a path and open file at that path (binary mode). Otherwise return 
    open file handle.
    TODO: Handle invalid file paths. 
    '''
    if isinstance(fileobj, str) :
        with open(fileobj, 'rb') as f :
            return f

    else : return fileobj