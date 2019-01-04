from node import Node
from struct import unpack
from texlist import Texlist
from address import section_addresses, rawaddress
from helpers import verify_file_arg_o, verify_file_arg_b
from world_transform import transform
import operator

class Chunk(Node) :
    section_table = section_addresses()

    def __init__(self, xbe, entry_offset, section, texlist=None, parent_coords=None, full=True) :
        Node.__init__(self, xbe, entry_offset, section, texlist, parent_coords)

        block = self.parse_block()
        self.voffset = rawaddress(block['voffset'], self.section, Chunk.section_table)
        self.toffset = rawaddress(block['toffset'], self.section, Chunk.section_table)

        self.name = 'ch_' + self.section + '_' + hex(self.offset)

        self.vertices = None
        self.triangles = None

        if full is True :
            self.vertices, self.triangles = self.parse(world=True)

    def __str__(self) :
        return self.name

    def parse_block(self) :
        '''
        Parse pointer block and return data.
        '''
        f = self.xbe
        offset = rawaddress(self.block, self.section, Chunk.section_table)
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


    def parse(self, world=True) :
        '''
        Parse vetices and triangles in chunk.
        '''
        print(f'Parsing chunk at {self.entry}')
        v = self.parse_vertices(world=world)
        t = self.parse_triangles()
        return v, t

    def write(self, file, texlist=None, clist=False) :
        '''
        Write .obj to open file handle. If texlist exists, reference material library.
        '''
        f = verify_file_arg_o(file, usage='w+')
        if texlist is not None and clist is False :
            f.write('mtllib {}.mtl\n'.format(texlist.name))

        f.write('o {}\n'.format(self.name))
        self.write_vertices(f)
        self.write_texcoords(f)
        self.write_triangles(f, texlist.matlist)

    

    def parse_vertices(self, world=True) :
        '''
        Reads vertex list from xbe. Returns a list[count], where each element is a tuple[3] denoting xyz.
        '''
        f = self.xbe
        f.seek(self.voffset + 6)
        count = unpack('h', f.read(2))[0]
        f.seek(8, 1)

        print(f'\tParsing {count} vertices at {hex(self.voffset)}... ', end='')


        v = []
        for _ in range(count) :
            word = list(unpack('fff', f.read(12)))

            if world is True :
                w = tuple(map(operator.add, self.world_coords, self.parent_coords))
                # print(str(self.world_coords[:3]) + ' + ' + str(self.parent_coords[:3]) + ' = ' + str(w[:3]))
                word = transform(word, w)

            v.append(tuple(word))
            f.seek(4, 1)

        print('\tDone')

        self.vertices = v
        return v

    def parse_triangles(self) :
        '''
        Read tripart list from xbe. Returns a list of tuples (tripart, texlist index) as defined in parse_tripart() without escape flag
        '''
        f = self.xbe
        f.seek(self.toffset)
        #print(f'{hex(self.offset)}')
        print(f'\tParsing triangles at {hex(self.toffset)}... ')

        # Hacky fix around unknown value at 0xbc58 in MDLEN. Probably others like it.
        if unpack('i', f.read(4))[0] > 50 :
            f.seek(-4, 1)

        # TODO: Research header flavors and usage.
        f.seek(2, 1)
        header_size = unpack('h', f.read(2))[0] * 2
        f.seek(header_size, 1)

        t = []

        i = 0
        while(True) :
            print(f'\tParsing triangle section {i}')
            i += 1

            j = 0
            while(True) :
                print(f'\t\tParsing tripart {j}')
                j += 1
                
                tripart = self.parse_tripart()
                if(tripart[0] is not None and tripart[1] is not None) :     #TODO: improve readability
                    t.append((tripart[0], tripart[1]))

                if tripart[2] : 
                    break

                

            if tripart[3] :
                break

        print('\tDone\n')
        self.triangles = t
        return t
        
    def parse_tripart(self, type='texture') :
        '''
        Reads tripart. Returns tuple (tripart, texlist index, last, simple) where tripart is a list of tuples (vertex index, tex_x, tex_y),
        texlist index assigns the texture, last is the escape flag, and simple flag is true if simple tripart.
        '''
        f = self.xbe

        t = []
        escape = False
        final = True
        type_spec = unpack('h', f.read(2))[0]

        # Temporary simple tristrip handling
        # TODO: reuse code to imporve readability
        texlist_index=0
        if (type_spec - 0x0408) % 0x1000 != 0 :
            print('\t\t\tNon-texture tripart.')
            type='simple'

            tripart_size = unpack('h', f.read(2))[0] * 2
            f.seek(tripart_size, 1)
            tripart_end = f.tell()
            esc_candidate = f.read(4)
            if esc_candidate == b'\xff\x00\x00\x00' :                # Escape symbol detected
                print('\t\t\t\tsimple esc found')
                return(None, None, True, True)   
            else :
                print('\t\t\t\tsimple esc not found')
                f.seek(-4, 1)
                return(None, None, False, True)
        else :
            texlist_index = unpack('h', f.read(2))[0] ^ 0x4000   
              
        f.seek(2, 1)
        

        # Check if last tripart 
        # TODO: Handle chunks with multiple triangle data regions
        # TODO: Process SIMPLE tristrips
        tripart_size = unpack('h', f.read(2))[0] * 2
        f.seek(tripart_size, 1) 
        tripart_end = f.tell()
        esc_candidate = f.read(4)

        can_float = unpack('f', esc_candidate)[0]
        can_ints = unpack('HH', esc_candidate)

        if can_float < 1.5 : 
            escape = True       # The first four bytes of tpart headers is a float ~2.0. This will break when encountering a simple tripart

        if can_ints[0] == 0x241 :
            print('\t\t\tTEXTURE MAGIC NUMBER')
            escape = False

        if esc_candidate == b'\xff\x00\x00\x00' :  
            print('\t\t\tESCAPE SYMBOL FOUND')
            escape = True     # Escape symbol

        if (can_ints[0] >> 0x8 == 0x25 and can_ints[1] < 0x20) :
            print('\t\t\tMORE TRIANGLES')
            final = False 
            escape = True

        f.seek(-(tripart_size + 4), 1)                               # Return to beginning of tripart.

        t_length = unpack('h', f.read(2))[0]
        for i in range(t_length) :
            strip = []
            s_length = abs(unpack('h', f.read(2))[0])

            for _ in range(s_length) :
                if type == 'texture' :
                    raw_point = list(unpack('hhh', f.read(6)))
                    raw_point[0] += 1               #TODO: clean up
                    raw_point[1] /= 255.0
                    raw_point[2] /= -255.0
                    raw_point[2] += 1.0
                else :
                    raw_point = [unpack('h', f.read(2))[0] + 1, 0, 0]

                data_point = tuple(raw_point)
                strip.append(data_point)

            t.append(strip)

        f.seek(tripart_end) 
        return (t, texlist_index, escape, final,)

    def write_vertices(self, file) :
        f = verify_file_arg_o(file)

        verts = self.vertices
        if not verts :
            print('\tNo vertices found!')
            return None
        else :
            print(f'Writing {len(verts)} vertices to {f.name}')
        
        for v in verts :
            ln = f'v {v[0]} {v[1]} {v[2]}\n'
            f.write(ln)

    def write_triangles(self, file, matlist=None) : 
        f = verify_file_arg_o(file)

        triangles = self.triangles
        if not triangles :
            print('\tNo triangles found!')
            return None
        else :
            print(f'Writing {len(triangles)} triparts to {f.name}')

        #TODO: write non-texture materials
        #TODO: implement material writing
        #TODO: remove redundant code
        vt = 1
        for tp in triangles :
            if matlist is not None :
                ln = f'usemtl {matlist[tp[1]]}\n'
                f.write(ln)

#            if tp[2] is False :
            for ts in tp[0] :
                for c in range(len(ts) - 2) :
                    if c % 2 == 0 : 
                        ln = f'f {ts[c][0]}/{vt} {ts[c+1][0]}/{vt+1} {ts[c+2][0]}/{vt+2}\n'
                    else :  
                        ln = f'f {ts[c+1][0]}/{vt+1} {ts[c][0]}/{vt} {ts[c+2][0]}/{vt+2}\n'

                    vt += 1
                    f.write(ln)
                vt += 2
#            else :
#                for ts in tp[0] :
#                    for c in range(len(ts) - 2) :
#                        if c % 2 == 0 : 
#                            ln = f'f {ts[c][0]} {ts[c+1][0]} {ts[c+2][0]}\n'
#                        else :  
#                            ln = f'f {ts[c+1][0]} {ts[c][0]} {ts[c+2][0]}\n'
#
#                        f.write(ln)

    def write_texcoords(self, file) :
        '''
        Given an open file discriptor or path, write texture coordinates as indexes as they appear in the triangle array
        '''
        f = verify_file_arg_o(file)
        triangles = self.triangles

        if not triangles :
            print('\tNo texcoords found!')
            return None
        
        #TODO: Clean up
        for tp in triangles :
            #if tp[2] is False :
            for ts in tp[0] :
                for c in ts :
                    vt = list(c[1:])
                    ln = f'vt {vt[0]} {vt[1]}\n'
                    f.write(ln)