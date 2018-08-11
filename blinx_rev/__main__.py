from chunk import Chunk
from chunklist import Chunklist
from texlist import Texlist
from address import section_addresses
from argparse import ArgumentParser
from tkinter import filedialog
from tkinter import Tk
import os

def main() :
    #TODO: Restructure, clean up extra arguments
    parser = ArgumentParser()
    parser.add_argument('-d', '--directory', help='Path to Blinx directory', type=str)
    parser.add_argument('-o', '--out', help='Path to output directory', type=str)
    parser.add_argument('-s', '--section', help='Section containing chunk', type=str)
    parser.add_argument('-co', '--coffset', help='Chunk entry offset (virtual address)', type=lambda x: int(x,16))
    parser.add_argument('-so', '--soffset', help='Stringlist file entry offset (virtual address)', type=lambda x: int(x,16))


#    parser.add_argument('-me', '--mediapath', help='Path to media directory', type=str)
#    parser.add_argument('-m', '--mode', help='Mode of operation - chunk=0, vert/tri=1', type=int)
#    parser.add_argument('-s', '--section', help='Path to section file', type=str)
#    parser.add_argument('-so', '--soffset', help='Stringlist file entry offset', type=lambda x: int(x,0))
#    parser.add_argument('-co', '--coffset', help='Chunk file entry offset', type=lambda x: int(x,0))
#    parser.add_argument('-o', '--obj', help='Path to output obj file (vert/tri)', type=str)
#    parser.add_argument('-b', '--bin', help='Path to binary directory (vert/tri)', type=str)

#    parser.add_argument('-c', '--chunk', help='(DEPRICATED) Path to chunk file', type=str)
#    parser.add_argument('-p', '--pointers', help='(DEPRICATED) Chunk file contains pointers to next chunk', type=bool)
#    parser.add_argument('-vo', '--voffset', help='(DEPRICATED) Vertex offset in chunk file (in hex)', type=int)
#    parser.add_argument('-to', '--toffset', help='(DEPRICATED) Triangle offset in chunk file (in hex)', type=int)
#    parser.add_argument('-v', '--vert', help='(DEPRICATED) Path to vertex list file', type=str)
#    parser.add_argument('-t', '--tri', help='(DEPRICATED) Path to triangle list file', type=str)
    args = parser.parse_args()

    in_directory = os.path.abspath(args.directory) if args.directory is not None else __tk_load_dir('base')
    out_directory = os.path.abspath(args.out) if args.out is not None else __tk_load_dir('out')

    sect = 'MAP11' if args.section is None else args.section

    coffset = 0xDE9464 if args.coffset is None else args.coffset
    soffset = 0xD80280 if args.soffset is None else args.soffset

    with open(in_directory + '/default.xbe', 'rb') as xbe :
        texlist = Texlist(xbe, soffset, sect)
        texlist.parse_strlist()

        with open('{}/{}.mtl'.format(out_directory, texlist.name), 'w+') as m :
            texlist.write_mtl(m, in_directory +'/media')


  #      chunklist = Chunklist(xbe, coffset, sect, texlist)
 #       chunklist.discover_local_chunks()
#        chunklist.parse_all_chunks()
#        with open('{}/{}.obj'.format(out_directory, chunklist.name), 'w+') as f :
#            chunklist.write(f, texlist=texlist, outdir=out_directory)

        chunk = Chunk(xbe, coffset, sect)
        with open('{}/{}.obj'.format(out_directory, chunk.name), 'w+') as f :
           chunk.write(f, texlist)



##        chunk.parse_vertices()
##        chunk.parse_triangles()
##        chunk.parse()

##            f.write('mtllib outie.mtl\n')
##            f.write('o im_outie\n')
##            chunk.write_vertices(f)
##            chunk.write_texcoords(f)
##            chunk.write_triangles(f, matlist=texlist.matlist)

def __tk_load_dir(dir_type) :
    Tk().withdraw()
    if dir_type is 'base' : titlestr = 'Select game folder' 
    elif dir_type is 'out' : titlestr = 'Select output folder'
    else : return False

    in_path = filedialog.askdirectory(title=titlestr)

    return in_path 

if __name__ == '__main__' :
    main()