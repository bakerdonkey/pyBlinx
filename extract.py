from tkinter import filedialog
from tkinter import Tk
import struct
import argparse

import time


class Extractor:
    def __init__(self, mode=False, chunk_path=None, vert_path=None, tri_path=None, obj_path=None, bin_dir=None) :
        """
        Construct extractor. Handle mode assignment. Assign chunk, vert, tri files from args or tkinter load helpers. 
        Args:
            param1: self instance reference
            param2: mode of operation
            param3: path to chunk file
            param4: path to vert file
            param5: path to tri file
            param6: path to proposed obj output
            param7: path to binary directory
        """
        self.mode = mode

        self.bin_dir = bin_dir if bin_dir is not None else './'

        if not mode :
            self.chunk_path = chunk_path if chunk_path is not None else self.__tk_load_bin('chunk')
        
        else :
            self.vert_path = vert_path if vert_path is not None else self.__tk_load_bin('vert')
            self.tri_path = tri_path if tri_path is not None else self.__tk_load_bin('tri')
        
        self.obj_path = obj_path if obj_path is not None else ''        # Do not use tk to create obj path until file is verified to work



        self.verts = []
        self.tristrips = []

        # Depricated:
        self.tris = []   

    def read_verts(self, start_off=0x0000) :
        """
        Parses the list of raw floats delimited by some unknown value.

        Args:
            param1: self instance reference

        Returns: 
            A list of lists containing local x y z cords
        """

        v = []

        path = self.vert_path if self.mode is True else self.chunk_path
        raw_word = b''
        with open(path, 'rb') as f :
            f.seek(start_off)
            while True :
                raw_word = f.read(12)
                if raw_word[:4] ==  b'\xff\x00\x00\x00' :                 # Check for escape symbol or EOF TODO: verify and debug
#                    print('Found vert escape symbol')
                    break

                elif len(raw_word) < 12 :
#                    print('Found vert EOF')
                    break
                    
                f.seek(4, 1)                                             # Seek relative to current iterator
                word = list(struct.unpack('fff', raw_word))
                v.append(word)
        self.verts = v


    def read_tristrips_complex(self, start_off=0x0000) :
        '''
        Starting offset after 0x7f7fffff
        '''
        size_buff = ''
        data_buff = ''
        t = []
        path = self.tri_path if self.mode is True else self.chunk_path
        with open(path, 'rb') as f :
            f.seek(start_off + 0x0008)
            tristrip_count = struct.unpack('h', f.read(2))[0]
            for i in range(tristrip_count) :
                print()
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
                        print('here')
                        break

                    else :
                        f.seek(-2)
                
        self.tristrips = t

    # Depricated
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

    # Depricated!
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
#           print(str(i) + ' ' + str(window))
            window = data[i: i+6]
            word_t = struct.unpack('hhh', window)
            word_l = list(word_t)
            word = [w+1 for w in word_l]
            t.append(word)
            i += 2
            # TODO: Handle invalid and incorrect tris 

        self.tris = t

    def write_verts(self) :
        verts = self.verts
        if not self.obj_path : self.obj_path = self.__tk_save_obj()

        with open(self.obj_path, 'w+') as f :
            if not verts :
                print('No verts to write')
            else :
                print('Extracting verts...', end='')
                for v in verts :
                    ln = 'v {x} {y} {z}\n'.format(x=v[0], y=v[1], z=v[2])
                    f.write(ln)
                print('Done')



    def write_tristrips(self) :
        tristrips = self.tristrips
        if not self.obj_path : self.obj_path = self.__tk_save_obj()

        with open(self.obj_path, 'a+') as f :
            if not tristrips :
                print ('No tristrips to write!')

            else :
                print('Extracting tristrips...', end='')
                for t in tristrips :
                    for i in range(len(t)-2) :
                        ln = 'f {v0} {v1} {v2}\n'.format(v0=t[i][0], v1=t[i+1][0], v2=t[i+2][0])
                        f.write(ln)

                print('Done')

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

def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', help='Mode of operation - chunk=0 (DO NOT USE!), vert/tri=1', type=bool)
    parser.add_argument('-c', '--chunk', help='Path to chunk file', type=str)
    parser.add_argument('-vo', '--voffset', help='Vertex offset in chunk file (in hex)', type=lambda x: int(x,0))
    parser.add_argument('-to', '--toffset', help='Triangle offset in chunk file (in hex)', type=lambda x: int(x,0))
    parser.add_argument('-v', '--vert', help='Path to vertex list file', type=str)
    parser.add_argument('-t', '--tri', help='Path to triangle list file', type=str)
    parser.add_argument('-o', '--obj', help='Path to output obj file', type=str)
    parser.add_argument('-b', '--bin', help='Path to binary directory', type=str)
    args = parser.parse_args()

    extract = Extractor(mode=args.mode, chunk_path=args.chunk, vert_path=args.vert, tri_path=args.tri, obj_path=args.obj, bin_dir=args.bin)

    voffset = args.voffset if args.voffset is not None else 0x0000
    toffset = args.toffset if args.toffset is not None else 0x0000



    extract.read_verts(start_off=voffset)
    extract.read_tristrips_complex(start_off=toffset)
    extract.write_verts()
    extract.write_tristrips()


if __name__ == '__main__' :
    main()