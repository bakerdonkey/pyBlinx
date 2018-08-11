from chunk import Chunk
from texlist import Texlist
from struct import unpack
from address import section_addresses
from address import rawaddress
from address import virtaddress
from helpers import verify_file_arg_b
from helpers import verify_file_arg_o

class Chunklist :
    section_table = section_addresses()

    def __init__(self, xbe, entry_offset, section, texlist=None) :
        self.xbe = verify_file_arg_b(xbe)
        
        self.offset = rawaddress(entry_offset, section, Chunklist.section_table)
        
        self.texlist = texlist

        self.section = section

        self.chunks = []

        self.next = None

        self.header = self.parse_header()

        self.name = 'cl_' + self.section + '_' + hex(self.offset)

        for k,v in self.header.items() :
            if isinstance(v, int) :
               v = hex(v)
            print(k,v)

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

    def discover_local_chunks(self) :
        print('Start parsing...')
        next_entry = self.entry_type(rawaddress(self.header['left_ptr'], self.section, Chunklist.section_table)) 
        if next_entry is None:
            print('Chunklist {}: next left pointer is None'.format(self.offset))
            return None
        elif next_entry is 0xf:
            print('Chunklist {}: left pointer to chunklist not yet supported'.format(self.offset))
            return None
        else : pass

        i = 0
        print(self.header['left_ptr'])
        cur = self.next_chunk(self.header['left_ptr'])
        while True :
            print('Chunk {}'.format(i))

            #?????
 #           if self.entry_type(cur.header['clist_ptr_1']) is 0xf:
 #               print('Chunk {} ({}): next chunk does not support chunklist parsing yet'.format(i, cur.offset))
 #               break            
            self.chunks.append(cur)

            if cur.header['clist_ptr_1'] is None:
                print('Last chunk on chunklist is {}'.format(i))
                break

            cur = self.next_chunk(cur.header['clist_ptr_1'])

            i += 1

    def parse_all_chunks(self) :
        if self.chunks is None :
            print('No chunks to parse')
            return
        for c in self.chunks :
            if c.header['entry'] is not 0xe:
                c.parse()

    def write(self, file, texlist=None, outdir='') :
        f = verify_file_arg_o(file, usage='w+')
        if self.chunks is None :
            print('No chunks to write')
            return
        if texlist is not None :
            f.write('mtllib {}.mtl\n'.format(texlist.name))

        for c in self.chunks :
            with open('{}/{}.obj'.format(outdir, c.name), 'w+') as f :
                c.write(f, texlist=texlist, clist=False)

    def next_chunk(self, entry_offset) :
        '''
        Returns unparsed chunk at specified offset.
        '''
        f = self.xbe
        return Chunk(f, entry_offset, self.section, texlist=self.texlist, full=False)

    def next_chunklist(self, entry_offset) :
        '''
        Returns chunklist at specified offset
        '''
        f = self.xbe
        return Chunk(f, entry_offset, self.section, texlist=self.texlist, full=False)


    def entry_type(self, offset) :
        f = self.xbe
        f.seek(offset)
        i = unpack('i', f.read(4))[0]
        entry = i if i is not 0 else None
        return entry 