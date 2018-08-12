from struct import unpack
from node import Node
from address import rawaddress

class Chunk(Node) :
    def __init__(self, xbe, entry_offset, section, texlist=None, full=True) :
        Node.__init__(self, xbe, entry_offset, section, texlist)
    
        block = self.parse_block()
        self.voffset = block['voffset']
        self.toffset = block['toffset']


    def parse_block(self) :
        f = self.xbe
        offset = rawaddress(self.block, self.section, Node.section_table)
        f.seek(offset)
        vdata_offset = unpack('i', f.read(4))[0]
        tdata_offset = unpack('i', f.read(4))[0]

        float_array_0 = []
        for _ in range(6) : float_array_0.append(unpack('f', f.read(4))[0])
        
        return {
            'voffset': vdata_offset,
            'toffset': tdata_offset,
            'farray': float_array_0
        }