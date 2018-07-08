from enum import Enum
from tkinter import filedialog
from tkinter import Tk
import struct
import argparse
import os
import time

class SectionAddress :
    DATA    =     0x002D0660
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
    def __init__(self, mode=0, chunk_path=None, vert_path=None, tri_path=None, obj_path=None, bin_dir=None) :
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
            self.chunk_path = chunk_path if chunk_path is not None else self.__tk_load_bin('chunk')
        
        else :
            self.vert_path = vert_path if vert_path is not None else self.__tk_load_bin('vert')
            self.tri_path = tri_path if tri_path is not None else self.__tk_load_bin('tri')
        
        self.obj_path = obj_path if obj_path is not None else ''        # Do not use tk to create obj path until file is verified to work



        self.verts = []  
        self.triparts = []

        # Depricated:
        self.tris = []   
        self.tristrips = []

    def read_verts(self, start_off=0x0000, file = None) :
        '''
        Parses the list of raw floats delimited by some unknown value.
        Args:
            param1: self instance reference
        '''

        v = []
        if file is None :    
            path = self.vert_path if self.mode is True else self.chunk_path
            f = open(path, 'rb')   

        else : f = file


        f.seek(start_off + 6)
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

    def parse_chunk_header(self, start_off=0x0000, file=None, chunk_style='short') :
        '''
        Reads the header for standard complex trilist chunk
        Returns dict with all objects in chunk header.
        TODO: adapt for more types of chunks and figure out mystery values
        '''
        if file is None :    
            path = self.chunk_path
            f = open(path, 'rb')   
        else : f = file
        
        f.seek(start_off + 8, 1)        # seek past first two dwords

        h_float_array_0 = []            # store first set of floats
        for _ in range(6) : h_float_array_0.append(struct.unpack('f', f.read(4))[0])
        
        mystery_short_0 = struct.unpack('h', f.read(2))[0]   #hold onto short, not sure what it is
        f.seek(2,1)
        
        h_sect_offset = hex(struct.unpack('i', f.read(4))[0])    # store offset of chunk (virtual address)

        h_float_array_1 = []            # store second set of floats
        for _ in range(9) : h_float_array_1.append(struct.unpack('f', f.read(4))[0])
        f.seek(4, 1)          # maybe another float? 

        mystery_short_0_prev_offset = hex(struct.unpack('i', f.read(4))[0])   #store offset to prev chunk mystery short 0

        if chunk_style == 'long' :
            mystery_short_1 = struct.unpack('h', f.read(2))   #store another mystery short
            f.seek(2, 1)

            h_float_array_2 = []            # store third set of floats
            for _ in range(10) : h_float_array_2.append(struct.unpack('f', f.read(4))[0])

            mystery_short_0_offset = hex(struct.unpack('i', f.read(4))[0])  # store offset to cur chunk mystery short 0

            f.seek(8, 1)

        if file is None : f.close()

        return {'float array 0': h_float_array_0, 
                'mystery short 0': mystery_short_0,
                'chunk offset' : h_sect_offset,
                'float array 1' : h_float_array_1,
                'mystery short 0 prev offset' : mystery_short_0_prev_offset,
                'mystery short 1' : None,
                'float array 2' : None,
                'mystery short 0 offset' : None}
        
    def read_chunk(self, section, tpart_flavor='standard', start_off=0x0000, file=None, nc_pointers = False, voffset=0x0000, toffset=0x0000, head=True) :
        if file is None :    
            path = self.chunk_path
            f = open(path, 'rb')

        else : f = file
        
        # Hacky, make more flexible
        if nc_pointers is True:
            f.seek(36)
            if head : chunk_offset = struct.unpack('i', f.read(4))[0]  - section
            else : chunk_offset = 0x4c8

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

        vertlist = self.read_verts(start_off=voff, file=f)
       

        self.verts = vertlist
        self.triparts = triset

        if file is None : f.close()
        
    def read_tripart_set(self, flavor='standard', start_off=0x0000, header=True, part_count=10, file=None) :
        '''
        12 byte header, usually: 1325 0400 b2b2 b2ff 7f7f 7fff
        '''
        if file is None :    
            path = self.tri_path if self.mode is True else self.chunk_path
            f = open(path, 'rb')
        
        else : f = file
        t = [] # is this really neccisary?
        
        # TODO research header types, usage, etc
        if header is True : 
            f.seek(start_off + 0x000c)


        else : f.seek(start_off, 1)

        print('Reading tripart set')
        print('Trying to read {x} triparts...'.format(x=part_count))

        for i in range(part_count) :
            print('Tripart {x}:'.format(x=i+1))
            tripart_t = self.read_tristrip_set(file=f, tpart_flavor=flavor)
            t.append(tripart_t[0])
            if tripart_t[1] :
                print('Exit from tristrip set reader after tripart {x}'.format(x=i+1))
                return t

            padding = struct.unpack('h', f.read(2))[0]
 #           if len(bytes(padding)) < 2 :
 #               print('Reached EOF after tripart {x}'.format(x=i+1))
 #               return t

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

    def read_tristrip_set(self, file, style='complex', tpart_flavor='standard', start_off=0x0000) :
        f = file
        t = []
        last = False

        if tpart_flavor is 'fxx' :
            print('\t Tpart flavor fxx')
            f.seek(4, 1)

        #TODO: Research and handle 0x0, 0x2, and 0x4
        f.seek(6, 1)
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
            for j in range(length) :
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
            
            print('\t\t' + str(strip))

            t.append(strip)  

        return (t, last)          


    def write_verts(self) :
        verts = self.verts
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

    def write_triparts(self) :
        if not self.obj_path : self.obj_path = self.__tk_save_obj()
        with open(self.obj_path, 'a+') as f :
            i = 0
            for t in self.triparts :
                f.write('#tripart {x}\n'.format(x=i))
                self.write_tristrips(cur_tristrips=t, file=f, i=i)
                i += 1

    def write_tristrips(self, cur_tristrips=None, file=None, i=0) :
        
        tristrips = cur_tristrips if cur_tristrips is not None else self.tristrips

        if file is None :
            if not self.obj_path : self.obj_path = self.__tk_save_obj()
            f = open(self.obj_path, 'a+')
        else :
            f = file

        print('Writing tristrips in part {x}... '.format(x=i), end='')
        for t in tristrips :
            for j in range(len(t)-2) :
                ln = 'f {v0} {v1} {v2}\n'.format(v0=t[j][0], v1=t[j+1][0], v2=t[j+2][0])
                f.write(ln)

        print('Done')

        if file is None : f.close()

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
        
        if filetype == 'chunk' :
            in_path = filedialog.askopenfilename(initialdir=self.bin_dir, title="Select Chunk file")

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
    def read_triparts_stageobj(self, start_off=0x0000, header=False, part_count_in=1) :
        '''
        0x14 (20) byte header. Does not know tripart count.
        '''
        t = []
        path = self.tri_path if self.mode is True else self.chunk_path
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
        path = self.tri_path if self.mode is True else self.chunk_path
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
            path = self.tri_path if self.mode is True else self.chunk_path
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

        #self.tristrips = t
        return t
    def write_obj(self) :
        """
        Creates a Wavefront obj file that contains the vertex and triangle list.
        """

        verts = self.verts
        tris = self.tris

        if not self.obj_path : self.obj_path = self.__tk_save_obj()


            
        if self.obj_path == '' :
            print('Invalid save path')
            return

        with open(self.obj_path, 'w+') as f :
            
            if not verts :
                print('No verts to write!')
            
            else :
                print('Extracting verts...')
                for v in verts :
                    ln = 'v {x} {y} {z}\n'.format(x=v[0], y=v[1], z=v[2])
                    f.write(ln, end='')
                print('Done')
            
            if not tris :
                print('No tris to write!')

            else :
                print('Extracting tris...')
                for t in tris :
                    ln = 'f {i0} {i1} {i2}\n'.format(i0=t[0], i1=t[1], i2=t[2])
                    f.write(ln)
                print('Done')
    def old_read_verts(self) :
        #TODO: implement starting offset
        """
        Parses the list of raw floats delimited by some unknown value.
        Args:
            param1: self instance reference

        Returns: 
            A list of lists containing local x y z cords
        """
        v = []

        with open(self.vert_path, 'rb') as f :
           while True :
                word = f.read(16)
                if len(word) < 4 :
                    break

                word = struct.unpack('fffi', word)
                word = list(word)
                v.append(word)

        self.verts = v
    def read_tris_slide(self, start_off=0x0000) :
        """
        Parses a triangle array into a list. Strips invalid and incorrect triangles.

        Args:
            param1: self instance reference
            param2: starting offset for triangle array, after 0xffffff05

        Returns:
            A list containing tuples of vertex indices
        """

        data = ''
        t = []
        with open(self.tri_path, 'rb') as f :
            f.seek(start_off + 0x0002)          # accounts for first unknown short
            size = struct.unpack('h', f.read(2))[0]
            data = f.read(size * 2)

        if data == '' :
            print('Could not parse tris - empty data string!')
            return
        

        #TODO: Clean up loop. This is bad since i is immutable. Use iterator or something
        window = data[0: 6]
        i = 2   
        while i + 6 <= len(data) :
            window = data[i: i+6]
            word_t = struct.unpack('hhh', window)
            word_l = list(word_t)
            word = [w+1 for w in word_l]
            t.append(word)
            i += 2
            # TODO: Handle invalid and incorrect tris 

        self.tris = t


def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', help='Mode of operation - chunk=0, vert/tri=1', type=int)
    parser.add_argument('-c', '--chunk', help='Path to chunk file', type=str)
    parser.add_argument('-p', '--pointers', help='Chunk file contains pointers to next chunk', type=bool)
    parser.add_argument('-vo', '--voffset', help='Vertex offset in chunk file (in hex)', type=int) #type=lambda x: int(x,0)
    parser.add_argument('-to', '--toffset', help='Triangle offset in chunk file (in hex)', type=int)
    parser.add_argument('-v', '--vert', help='Path to vertex list file', type=str)
    parser.add_argument('-t', '--tri', help='Path to triangle list file', type=str)
    parser.add_argument('-o', '--obj', help='Path to output obj file', type=str)
    parser.add_argument('-b', '--bin', help='Path to binary directory', type=str)
    parser.add_argument('-tpi', '--tripartcount', help='Custom number of triparts', type=int)
    args = parser.parse_args()

    extract = Extractor(mode=args.mode, chunk_path=args.chunk, vert_path=args.vert, tri_path=args.tri, obj_path=args.obj, bin_dir=args.bin)

    v_offset = args.voffset if args.voffset is not None else 0x0000
    t_offset = args.toffset if args.toffset is not None else 0x0000

    print(str(hex(v_offset)) + ' ' + str(hex(t_offset)))

    #extract.read_verts(start_off=voffset)
    #extract.read_triparts_prop(start_off=toffset, part_count_in=args.tripartcount)
    #extract.read_triparts_stageobj(start_off=toffset, header=True, part_count_in=args.tripartcount)
    extract.read_chunk(voffset=v_offset, nc_pointers=args.pointers, toffset=t_offset, section=SectionAddress.MAP11, head=True)
    extract.write_verts()
    extract.write_triparts()


if __name__ == '__main__' :
    main()