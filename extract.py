from enum import Enum
from tkinter import filedialog
from tkinter import Tk
import struct
import argparse
import os
import time

class SectionAddress :
    DATA    =     0x001D0660
    MDLPL   =     0x00AAFF40
    MDLB1   =     0x00D80280
    MDLB10  =     0x00E56C60
    MDLB2   =     0x00F90AA0
    MDLB3   =     0x01080A20
    MDLB4   =     0x0115EE60
    MDLB5   =     0x011CA300
    MDLB6   =     0x012BF680
    MDLB8   =     0x01355AE0
    MDLB9   =     0x01413B80
    MDLEN   =     0x01485A40
    MDLB102 =     0x018C1960
    MAP13   =     0x0191EFE0
    MAP12   =     0x01AD72C0
    MAP11   =     0x01C58640
    MDLR2   =     0x01DD52E0
    
    MDLR5   =     0x026C5660
    #TODO: Finish filling out

    
class Extractor :
    def __init__(self, mode=0, section_path=None, media_path=None, vert_path=None, tri_path=None, obj_path=None, bin_dir=None) :
        '''
        Construct extractor. Handle mode assignment. Assign chunk, vert, tri files from args or tkinter load helpers. 
        Args:
            param1: self instance reference
            param2: mode of operation
            param3: path to chunk file
            param4: path to vert file
            param5: path to tri file
            param6: path to proposed obj output
            param7: path to binary directory
        '''
        self.mode = mode

        self.bin_dir = bin_dir if bin_dir is not None else './'

        if mode == 0 :
            self.section_path = section_path if section_path is not None else self.__tk_load_bin('section')
            self.media_path = media_path if media_path is not None else self.__tk_load_dir()

        else :
            self.vert_path = vert_path if vert_path is not None else self.__tk_load_bin('vert')
            self.tri_path = tri_path if tri_path is not None else self.__tk_load_bin('tri')
        
        self.obj_path = obj_path if obj_path is not None else ''        # Do not use tk to create obj path until file is verified to work
        
        self.stringlist_list = []

        self.texpart_list = []

        self.verts = []  
        self.triparts = []


    def parse_stringlist(self, start_off=0x0000, file=None, section=SectionAddress.MAP11) :
        '''
        Read a stringlist at a specified offset, store each member in a list. This is very slow, can be improved.
        '''
        if file is None : 
            f = open(self.section_path, 'rb')

        else : f = file       

        f.seek(start_off) 

        s = []

        print('Parsing stringlist...')

        head_offset = struct.unpack('i', f.read(4))[0]
        size = struct.unpack('i', f.read(4))[0]

        f.seek(head_offset - section)

        for i in range(size) :
            
            charlist = struct.unpack('<32c', f.read(32))
            string = ''
            for c in charlist :
                if c != b'\x00' :
                    string = string + c.decode('latin-1')

                   
            mediapath = self.media_path if self.media_path is not None else ''
                
            string = mediapath + '/' + string + '.dds'

            print('{x}\t{s}'.format(x=i, s=string))
            s.append(string)
            
        print()

        self.stringlist_list.append(s)


        return s

    def parse_chunk_header(self, start_off=0x0000, file=None, chunk_style='single') :
        '''
        Reads the header for standard complex trilist chunk
        Returns dict with all objects in chunk header.
        TODO: adapt for more types of chunks and figure out mystery values
        '''
        if file is None : 
            f = open(self.section_path, 'rb')   
        else : f = file
        f.seek(start_off)

        entry_short = struct.unpack('h', f.read(2))[0]   #hold onto short, not sure what it is
        f.seek(2,1)

        h_sect_offset = struct.unpack('i', f.read(4))[0]    # store offset of chunk (virtual address)

        f.seek(-40, 1)      # Go to top of header

        vertlist_offset = struct.unpack('i', f.read(4))[0]
        triset_offset = struct.unpack('i', f.read(4))[0]

        float_array_0 = []            # store first set of floats
        for _ in range(6) : float_array_0.append(struct.unpack('f', f.read(4))[0])
        
        f.seek(8, 1)       
        
        h_float_array_1 = []            # store second set of floats
        for _ in range(9) : h_float_array_1.append(struct.unpack('f', f.read(4))[0])

        if chunk_style == 'list' :
            if struct.unpack('i', f.read(4))[0] != 0 :
                f.seek(-4, 1)

            next_chunk_offset = struct.unpack('i', f.read(4))[0]   #store offset to prev chunk mystery short 0
        else :
            next_chunk_offset = None

        if file is None : f.close()

        return {'vertlist offset' : vertlist_offset,
                'triset offset' : triset_offset,
                'float array 0': float_array_0, 
                'entry short' : entry_short,
                'chunk offset' : h_sect_offset,
                'float array 1' : h_float_array_1,
                'next chunk offset' : next_chunk_offset }

    #TODO: make file objects class variables -- data AND section

    def read_chunk(self, section, usage='vt', start_off=0x0000, file=None) :
        if file is None : 
            f = open(self.section_path, 'rb')
            
        else : f = file
            
        f.seek(start_off + 4)


        output = []

        header = self.parse_chunk_header(start_off=start_off, file=f)
        print('Chunk info :')
        for k, v in header.items() :
            print('{x} : {y}'.format(x=k, y=v))
        print()

        if usage.find('v') > -1 : 
            vertlist_offset = header['vertlist offset'] - section
            output.append(self.read_vertlist(start_off=vertlist_offset, file=f))
            self.verts = output[-1]

        if usage.find('t') > -1 : 
            triset_offset = header['triset offset'] - section
            triset_flavor = self.get_triset_flavor(file=f, start_off=triset_offset)
            output.append(self.read_tripart_set(start_off=triset_offset, flavor=triset_flavor, file=f))
            self.verts = output[-1]

            

        if file is None : f.close()

        return output

    def get_triset_flavor(self, file, start_off=0x0000) :
        if file is None : 
            f = open(self.section_path, 'rb')
        else : f = file        

        f.seek(start_off)
        f.seek(12, 1)

        candidate = struct.unpack('i', f.read(4))

        if candidate == 0x5FFFFFF :
            if file is None : f.close()
            return 'fxx'

        elif candidate == 0xBFFFFFF :
            if file is None : f.close()
            return 'fxx'

        elif candidate == 0xFFFFFFFF :
            if file is None : f.close()
            return 'fxx'

        else :
            if file is None : f.close()
            return 'standard'

    def read_tripart_set(self, flavor='standard', start_off=0x0000, header=True, part_count=10, file=None) :
        '''
        12 byte header, usually: 1325 0400 b2b2 b2ff 7f7f 7fff
        '''

        #TODO: Fully implement tripart flavors
        if flavor is not 'standard' :
            print('Non-standard tripart flavors are currently not supported. Returning')
            return None



        if file is None :    
            path = self.tri_path if self.mode is True else self.section_path
            f = open(path, 'rb')
        
        else : f = file

        t = [] # is this really neccisary?

        f.seek(start_off)
        
        # TODO research header types, usage, etc
        if header is True : 
            f.seek(start_off + 0x000c)


        else : f.seek(start_off, 1)

        print('Reading tripart set')
        print('Trying to read {x} triparts...'.format(x=part_count))

        for i in range(part_count) :
            print('Tripart {x}:'.format(x=i+1))
            tripart_t = self.read_tristrip_set(file=f)
            t.append((tripart_t[0], tripart_t[1]))
            if tripart_t[2] :
                print('Exit from tristrip set reader after tripart {x}'.format(x=i+1))
                return t

            padding = struct.unpack('h', f.read(2))[0]

            # May be redundant
            if padding == 255 :
                if struct.unpack('h', f.read(2))[0] == 0 :
                    print('Reached escape symbol ff000000 after tripart {x}'.format(x=i+1))
                    return t
                else :
                    f.seek(-2, 1)

            if padding is not 0 :
                f.seek(-2,1)

        if file is None : f.close()
        return t

    def create_texture_coordinates(self, triset=None, stringlist=None) :
        '''
        All tristrips must exist and be complex. 
        '''
        print('Creating texture coordinates... ')
        
        # TODO: handle invalid trisets
        if triset == None :
            tripart_set = self.triparts

        else : tripart_set = triset

        if stringlist == None :
            print('Stringlist not expressly declaired, using first stringlist in section')
            if self.stringlist_list is not None : 
                texture_list = self.stringlist_list[0]

            else : 
                print('Stringlistlist is None. Exiting')
                return None

        else : texture_list = stringlist

        texpart_set = []
        for tripart in tripart_set :
            print('Tripart texture: ' + str(tripart[1]) + '\t'+ str(texture_list[tripart[1]]))

            texpart = []
            for tristrip in tripart[0] :
                texstrip = []
                for c in tristrip :
                    tex = list(c[1:])
                    tex[0] /= 255
                    tex[1] /= -255
                    tex[1] += 1
                    tex = tuple(tex)
                    texstrip.append(tex)

                texpart.append(texstrip)
            texpart_set.append(texpart)
        
        self.texpart_list = tuple(texpart_set)

        return tuple(texpart_set)
                
    def read_tristrip_set(self, file, style='complex', start_off=0x0000) :
        f = file
        t = []
        last = False

        #TODO: Research and handle 0x0, 0x2, and 0x4
        f.seek(2, 1)
        stringlist_index_raw = struct.unpack('h', f.read(2))[0]
        stringlist_index = stringlist_index_raw - 0x4000 # FIXME: use bitwise for readability
        print('\t\tStringlist index : {x}'.format(x=stringlist_index))
    
        f.seek(2, 1)
        size = struct.unpack('h', f.read(2))[0] * 2
        print('\tTripart size : {x}'.format(x=size))
        f.seek(size, 1)

        escape = struct.unpack('h', f.read(2))[0] 
        if escape == 255 :
            nex = struct.unpack('h', f.read(2))[0]
            if nex == 0 :
                last = True
            
            f.seek(-4, 1)
            f.seek(-size, 1)   

        else :
            f.seek(-2, 1)
            f.seek(-size, 1)     

        count = struct.unpack('h', f.read(2))[0]
        print('\tNumber of tristrips: {x}'.format(x=count))
        for i in range(count) :
            strip = []
            length = abs(struct.unpack('h', f.read(2))[0])

            print('\tTristrip {i}, length {l}'.format(i=i+1, l=length))
            for _ in range(length) :
                if style == 'complex' :
                    data = list(struct.unpack('hhh', f.read(6)))
                    data = tuple([w+1 for w in data])
                    strip.append(data)
                
                elif style == 'simple' :
                    data = list(struct.unpack('h', f.read(2))[0])
                    data += 1
                    strip.append(data)
                
                else :
                    print('\tIncorrect tripart style argument, exiting....')
                    return (t, True)

            t.append(strip)  

        return (t, stringlist_index, last)          

    def read_vertlist(self, start_off=0x0000, file=None) :
        '''
        Parses the list of raw floats delimited by some unknown value.
        Args:
            param1: self instance reference
        '''
        v = []
        if file is None :    
            path = self.vert_path
            f = open(path, 'rb') 
        else : f = file

        f.seek(start_off)

        f.seek(6, 1)
        count = struct.unpack('h', f.read(2))[0]
        print('Reading {x} verts'.format(x=count))
        f.seek(8, 1)
        for _ in range(count) :
            raw_word = f.read(12)
            if len(raw_word) < 12 :
                break

            elif raw_word[:4] ==  b'\xff\x00\x00\x00' :
                break

            word = struct.unpack('fff', raw_word)
            v.append(word)

            f.seek(4, 1)
        
        if file is None : f.close()
        
        return v

    def write_triparts(self, in_triparts=None, world_coordinates=None) :
        triparts = self.triparts if in_triparts is None else in_triparts
        if not self.obj_path : self.obj_path = self.__tk_save_obj()
        with open(self.obj_path, 'a+') as f :
            i = 0
            for t in triparts :
                f.write('#tripart {x}\n'.format(x=i))
                self.write_tristrips(cur_tristrips=t, file=f, i=i)
                i += 1

    def write_tristrips(self, cur_tristrips, file=None, mode=None, i=0) :
        
        tristrips = cur_tristrips[0]

        if file is None :
            if not self.obj_path : self.obj_path = self.__tk_save_obj()
            f = open(self.obj_path, 'a+')
        else :
            f = file

        # TODO: verify normal bug is fixed, make code more readable!
        print('Writing tristrips in part {x}... '.format(x=i), end='')

        for t in tristrips :
            for j in range(len(t)-2) :
                if j % 2 == 0 : 
                    ln = 'f {v0} {v1} {v2}\n'.format(v0=t[j][0], v1=t[j+1][0], v2=t[j+2][0])
                
                else :  
                    ln = 'f {v1} {v0} {v2}\n'.format(v0=t[j][0], v1=t[j+1][0], v2=t[j+2][0])

                f.write(ln)


        print('Done')

        if file is None : f.close()

    def write_triparts_texture(self, triparts, file=None, mode=None, i=0) :

        if file is None :
            if not self.obj_path : self.obj_path = self.__tk_save_obj()
            f = open(self.obj_path, 'a+')
        else :
            f = file

        # TODO: verify normal bug is fixed, make code more readable!
        print('Writing tristrips (texture) in part {x}... '.format(x=i), end='')

        vt = 1
        
        for tp in triparts :
            for ts in tp[0] :
                for j in range(len(ts)-2) :
                    if j % 2 == 0 : 
                        ln = 'f {v0}/{vt0} {v1}/{vt1} {v2}/{vt2}\n'.format(v0=ts[j][0], vt0=vt, v1=ts[j+1][0], vt1=vt+1, v2=ts[j+2][0], vt2=vt+2)
                        vt += 1
                    else :  
                        ln = 'f {v1}/{vt1} {v0}/{vt0} {v2}/{vt2}\n'.format(v0=ts[j][0], vt0=vt, v1=ts[j+1][0], vt1=vt+1, v2=ts[j+2][0], vt2=vt+2)
                        vt += 1

                    f.write(ln)
                vt += 2
            
            

        print('Done')

        if file is None : f.close()
        return vt

    def write_verts(self, in_vertlist=None) :
        verts = self.verts if in_vertlist is None else in_vertlist
        if not self.obj_path : self.obj_path = self.__tk_save_obj()
        with open(self.obj_path, 'w+') as f :
            if not verts :
                print('No verts to write')
            else :
                print('Writing verts...', end='')
                for v in verts :
                    ln = 'v {x} {y} {z}\n'.format(x=v[0], y=v[1], z=v[2])
                    f.write(ln)
                print('Done')

    def write_vt(self, texpart_list) :
        # TODO implement texpart class variables
        if not self.obj_path : self.obj_path = self.__tk_save_obj()
        with open(self.obj_path, 'a+') as f :
            for texpart in texpart_list :
                for texlist in texpart :
                    for tex in texlist :
                        ln = 'vt {u} {v}\n'.format(u=str(tex[0]), v=str(tex[1]))
                        f.write(ln)

    def __tk_load_dir(self, filetype=None) :
        Tk().withdraw()
        in_path = ''

        if filetype == None :
            in_path = filedialog.askdirectory(title="Select Media directory")

        else :
            print('Invalid filetype')
        
        return in_path

    def __tk_load_bin(self, filetype) :
        """
        Open a file dialog with Tkinter for loading a binary file, handling the file type.

        Args:
            param1: self instance reference
            param2: a string that denotes the type open request

        Returns:
            A string containing the absolute path to the appropriate binary or an empty string 
            on user termination of the file dialog.
        """

        Tk().withdraw()
        in_path = ''

        # TODO: handle invalid path assignment
        
        if filetype == 'section' :
            in_path = filedialog.askopenfilename(initialdir=self.bin_dir, title="Select Section file")

        elif filetype == 'vert' :
            in_path = filedialog.askopenfilename(initialdir=self.bin_dir, title="Select Vert file")

        elif filetype == 'tri' :
            in_path = filedialog.askopenfilename(initialdir=self.bin_dir, title="Select Tri file")
        
        else:
            print('Incorrect filetype')

        return in_path
    
    def __tk_save_obj(self) :
        """
        Open a file dialog with Tkinter for saving an obj file.

        Args:
            param1: self instance reference

        Returns:
            A string with the absolute path to where the file should be saved, or an empty string
            on user termination of the file dialog.
        """

        Tk().withdraw()

        # TODO: handle invalid path assignment
        out_path = filedialog.asksaveasfilename(initialdir=self.bin_dir, defaultextension='.obj', title="Save as obj")
        return out_path

    # Depricated: 

    def read_chunk_old(self, section, tpart_flavor='standard', start_off=0x0000, file=None, nc_pointers=False, voffset=0x0000, toffset=0x0000, head=True) :
        if file is None :    
            path = self.section_path
            f = open(path, 'rb')

        else : f = file
        
        # Hacky, make more flexible. FIX CHUNK OFFSET
        if nc_pointers is True:
            f.seek(36)
            if head : chunk_offset = struct.unpack('i', f.read(4))[0]  - section
            else : chunk_offset = 0xad8

            f.seek(-8, 2)
            voff = struct.unpack('i', f.read(4))[0] - (section + chunk_offset)
            print('Vertlist offset: {x}'.format(x=hex(voff)))
            toff = struct.unpack('i', f.read(4))[0] - (section + chunk_offset)
            print('Trilist offset: {x}'.format(x=hex(toff)))
            f.seek(0)

        else :
            print('**Offsets set by user**')
            voff = voffset
            print('Vertlist offset: {x}'.format(x=hex(voff)))
            toff = toffset
            print('Trilist offset: {x}'.format(x=hex(toff)))
        
        print('Reading chunk...')
        if head :
            header = self.parse_chunk_header(file=f)
            print('\nHeader info')
            for k, v in header.items() :
                print('{x} : {y}'.format(x=k, y=v))
            print()

        triset = self.read_tripart_set(start_off=toff, flavor=tpart_flavor, part_count=10, file=f)

        vertlist = self.read_vertlist(start_off=voff, file=f)
       

        self.verts = vertlist
        self.triparts = triset

        if file is None : f.close()
    def read_triparts_stageobj(self, start_off=0x0000, header=False, part_count_in=1) :
        '''
        0x14 (20) byte header. Does not know tripart count.
        '''
        t = []
        path = self.tri_path if self.mode is True else self.section_path
        with open(path, 'rb') as f :

            if header == True: f.seek(start_off + 0x0004)
            else : f.seek(start_off)
            
            #TODO: Find actual part count           
            part_count = part_count_in           
            print('Total triparts: {x}'.format(x=part_count))


            for _ in range(part_count) :
                print('Reading tripart {x}'.format(x=_))
                cur_tripart = self.read_tristrips_complex(file=f)
                t.append(cur_tripart)

                next_short = f.read(2)
                if len(next_short) < 2 :            # Break if EOF TODO: look for escape char
                    print('There are only {x} triparts in the chunk!'.format(x=_+1))
                    break
                pad = struct.unpack('h', next_short)[0]
                if pad is not 0 : f.seek(-2, 1)
                
                

        self.triparts = t
    def read_triparts_prop(self, start_off=0x0000, part_count_in=1) :
        '''
        Starting offset 0x14 (20) bytes before 7f7f7fff
        '''
        t = []
        path = self.tri_path if self.mode is True else self.section_path
        part_count = part_count_in
        with open(path, 'rb') as f :
            f.seek(start_off + 0x0014)
            for _ in range(part_count) :

                print('Reading tripart {x}'.format(x=_))
                cur_tripart = self.read_tristrips_complex(file=f)
                t.append(cur_tripart)
                
                #TODO: clean up 
                pad = struct.unpack('h', f.read(2))[0]                  # handle potential padding
                if pad < 2 :
                    print('There are only {x} triparts in the chunk!'.format(x=_+1))
                    break
                
                print('pad is {x}'.format(x=pad))

                if pad is 0 :
                    if struct.unpack('f', f.read(4))[0] < 1.5:          # hacky but probably works since
                        print('End of complex triparts')                # first 8 bytes (float) =~ 2.1
                        break
                    else :
                        f.seek(-4, 1)
                elif pad is -1 :
                    if struct.unpack('h', f.read(2))[0] is 0 :
                        break
                    else :
                        print('Escape symbol encountered.')
                        f.seek(-2, 1)
                else : f.seek(-2, 1)

        self.triparts = t
    def read_tristrips_complex(self, start_off=0x0000, file=None) :
        size_buff = ''
        data_buff = ''
        t = []

        if file is None :    
            path = self.tri_path if self.mode is True else self.section_path
            f = open(path, 'rb')
        else :
            f = file
        
        f.seek(start_off + 0x0008, 1)
        tristrip_count = struct.unpack('h', f.read(2))[0]
        print('Number of tristrips: {x}'.format(x=tristrip_count))
        for i in range(tristrip_count) :
            size_buff = f.read(2)
            if len(size_buff) < 2 :
                break
                
            size = abs(struct.unpack('h', size_buff)[0])
            points = []
            for j in range(size) :
                data_buff = f.read(6)
                data = list(struct.unpack('hhh', data_buff))
                data = [w+1 for w in data]
                point = tuple(data)
                points.append(point)

            t.append(points)
            if size == 255 :
                if struct.unpack('h', f.read(2))[0] == 0 :
                    break

                else :
                    f.seek(-2, 1)

            print('Tristrip {i} size {s}: \n{x}\n'.format(i=i, s=size, x=points))

        if file is None : f.close()

        return t

def main() :
    #TODO: handle invalid arguments, update vert/tri mode
    parser = argparse.ArgumentParser()
    parser.add_argument('-me', '--mediapath', help='Path to media directory', type=str)
    parser.add_argument('-m', '--mode', help='Mode of operation - chunk=0, vert/tri=1', type=int)
    parser.add_argument('-s', '--section', help='Path to section file', type=str)
    parser.add_argument('-so', '--soffset', help='Stringlist file entry offset', type=lambda x: int(x,0))
    parser.add_argument('-co', '--coffset', help='Chunk file entry offset', type=lambda x: int(x,0))
    parser.add_argument('-o', '--obj', help='Path to output obj file (vert/tri)', type=str)
    parser.add_argument('-b', '--bin', help='Path to binary directory (vert/tri)', type=str)

    parser.add_argument('-c', '--chunk', help='(DEPRICATED) Path to chunk file', type=str)
    parser.add_argument('-p', '--pointers', help='(DEPRICATED) Chunk file contains pointers to next chunk', type=bool)
    parser.add_argument('-vo', '--voffset', help='(DEPRICATED) Vertex offset in chunk file (in hex)', type=int)
    parser.add_argument('-to', '--toffset', help='(DEPRICATED) Triangle offset in chunk file (in hex)', type=int)
    parser.add_argument('-v', '--vert', help='(DEPRICATED) Path to vertex list file', type=str)
    parser.add_argument('-t', '--tri', help='(DEPRICATED) Path to triangle list file', type=str)
    args = parser.parse_args()


    extract = Extractor(section_path=args.section, media_path=args.mediapath, vert_path=args.vert, tri_path=args.tri, obj_path=args.obj, bin_dir=args.bin)

    sl = extract.parse_stringlist(start_off=args.soffset, section=SectionAddress.DATA)

    chunk = extract.read_chunk(usage='vt', section=SectionAddress.DATA, start_off=args.coffset)
    
    extract.create_texture_coordinates(triset=chunk[1], stringlist=sl)



    extract.write_verts(chunk[0])
    extract.write_vt(extract.texpart_list)
    extract.write_triparts_texture(chunk[1])

    

if __name__ == '__main__' :
    main()