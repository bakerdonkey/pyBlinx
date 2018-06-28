from tkinter import filedialog
from tkinter import Tk
import struct
import argparse

class Extractor:
    def __init__(self, vert_path=None, tri_path=None, obj_path=None, bin_dir='./') :
        """
        Construct extractor. If paths to verts and tris are passed in, it use them. Otherwise
        loads from Tkinter filedialog.

        Args:
            param1: self instance reference
            param2: path to vert file
            param3: path to tri file
            param4: path to proposed obj output
            param5: path to binary directory
        """
        #TODO: The methodology behind this may be a no-no in python, look into alternatives
        self.bin_dir = bin_dir
        self.verts = []
        self.tris = []

        if vert_path is None :
            self.vert_path = self.__tk_load_bin('vert')
        else :
            self.vert_path = vert_path

        if tri_path is None :
            self.tri_path = self.__tk_load_bin('tri')
        else :
            self.tri_path = tri_path

        if obj_path is None :
            print('here')
            self.obj_path = ''
        else :
            self.obj_path = obj_path


    def read_verts(self, start_off=0x0000) :
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
            f.seek(start_off)
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
#           print(str(i) + ' ' + str(window))
            window = data[i: i+6]
            word_t = struct.unpack('hhh', window)
            word_l = list(word_t)
            word = [w+1 for w in word_l]
            t.append(word)
            i += 2
            # TODO: Handle invalid and incorrect tris 

        self.tris = t



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
                    f.write(ln)
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
        if filetype == 'vert' :
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
    parser.add_argument('-b', '--bin', help='Provide binary directory', type=str)
    parser.add_argument('-v', '--vert', help='Provide vert list binary', type=str)
    parser.add_argument('-t', '--tri', help='Provide triangle array binary', type=str)
    parser.add_argument('-o', '--obj', help='Provide output path', type=str)
    args = parser.parse_args()

    extract = Extractor(vert_path=args.vert, tri_path=args.tri, obj_path=args.obj, bin_dir=args.bin)

    extract.read_verts()
    #extract.read_tris_slide()
    extract.write_obj()


if __name__ == '__main__' :
    main()