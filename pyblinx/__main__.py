from tree import Tree
from chunk import Chunk
from chunklist import Chunklist
from texlist import Texlist
from address import section_addresses
from argparse import ArgumentParser
from tkinter import filedialog
from tkinter import Tk
from struct import unpack
from pathlib import Path
from address import find_section
import os


def main() :
    #TODO: Restructure, clean up extra arguments
    parser = ArgumentParser()
    parser.add_argument('-d', '--directory', help='Path to Blinx directory', type=str)
    parser.add_argument('-o', '--out', help='Path to output directory', type=str)
    parser.add_argument('-s', '--section', help='Section containing chunk', type=str)
    parser.add_argument('-co', '--coffset', help='Chunk entry offset (virtual address)', type=lambda x: int(x,16))
    parser.add_argument('-so', '--soffset', help='Stringlist file entry offset (virtual address)', type=lambda x: int(x,16))
    parser.add_argument('-to', '--toffset', help='Pointer table offset', type=str)
    parser.add_argument('-mi', '--modelindex', help='Index of model to select from pointer table', type=int)
    parser.add_argument('-c', help='Node at root is a chunk', action='store_true')

    args = parser.parse_args()

    in_directory = os.path.abspath(args.directory) if args.directory is not None else __tk_load_dir('base')
    out_directory = os.path.abspath(args.out) if args.out is not None else __tk_load_dir('out')

    sect = 'MAP11' if args.section is None else args.section

    coffset = 0xDE9464 if args.coffset is None else args.coffset
    soffset = 0xD80280 if args.soffset is None else args.soffset
    models = [(coffset, soffset, sect)]

    with open(in_directory + '/default.xbe', 'rb') as xbe :
        #m = parse_map_table(xbe, selection=args.modelindex)
        #for mod in m: print(f'{hex(mod[0])} {hex(mod[1])} {mod[2]}')

        #m = models
        m = parse_prop_table(xbe)
        run(m, xbe, in_directory, out_directory, root_is_chunk=args.c)

def parse_prop_table(xbe, toffset=(0x159da0 + 0x001C1000), count=116) :
    f = xbe
    f.seek(toffset)
    models = []
    section = 'DATA'
    for _ in range(count) :
        m = list(unpack('II', f.read(8)))
        section = find_section(m[0])
        m.append(section)
        m = tuple(m)
        if m[0] != 0 and m[1] != 0 and m[2] == 'DATA':
            models.append(m)
        f.seek(72, 1)
        print(m)
    return models

def parse_map_table(xbe, toffset=(0xe7f0 + 0x001C1000), selection=None) :
        f = xbe
        f.seek(toffset)
        models = []
        sections =  [
                        ['MAP11','MAP12','MAP13','MDLB1'],
                        ['MAP21','MAP22','MAP23','MDLB2'],
                        ['MAP31','MAP32','MAP33','MDLB3'],
                        ['MAP41','MAP42','MAP43','MDLB4'],
                        ['MAP51','MAP52','MAP53','MDLB5'],
                        ['MAP61','MAP62','MAP63','MDLB6'],
                        ['MAP11','MAP11','MAP11','MAP11'],
                        ['MAP81','MAP82','MAP83','MDLB8'],
                        ['MAP91','MAP92','MAP93','MDLB9'],
                        ['MDLB10','MDLB102','MAP11','MDLB10'],
                    ]
        for stage in sections :
            for section in stage :
                map_pointers = unpack('III', f.read(12))
                m = (map_pointers[1], map_pointers[2], section)
                models.append(m)

        if selection is not None :
            models = (models[selection],)
        return models

def run(models, xbe, in_directory, out_directory, root_is_chunk=False) :
    for model in models :
        print(f'Model {model[2]}: {hex(model[0])}, {hex(model[1])}')
        geo_offset = model[0]
        texlist_offset = model[1]
        section = model[2]

        outpath = Path(f'{out_directory}/{section}').mkdir(parents=True, exist_ok=True)

        texlist = Texlist(xbe, texlist_offset, section)
        texlist.parse_strlist()
        with open(f'{out_directory}/{section}/{texlist.name}.mtl', 'w+') as m :
            texlist.write_mtl(m, in_directory +'/media')

        tree = Tree(xbe, geo_offset, section, texlist, is_chunk=root_is_chunk)
        tree.build_tree_rec(tree.root)
        tree.parse_chunks(verts=True, tris=True)
        tree.write(f'{out_directory}/{section}')
        
#        chunklist = Chunklist(xbe, coffset, sect, texlist)
#        chunklist.discover_local_chunks()
#        chunklist.parse_all_chunks()
#        with open('{}/{}.obj'.format(out_directory, chunklist.name), 'w+') as f :
#            chunklist.write(f, texlist=texlist, outdir=out_directory)

#        chunk = Chunk(xbe, coffset, sect, full=False)
#        chunk.parse_triangles()
#        with open('{}/{}.obj'.format(out_directory, chunk.name), 'w+') as f :
#            chunk.write_texcoords(f)


def __tk_load_dir(dir_type) :
    Tk().withdraw()
    if dir_type is 'base' : titlestr = 'Select game folder' 
    elif dir_type is 'out' : titlestr = 'Select output folder'
    else : return False

    in_path = filedialog.askdirectory(title=titlestr)

    return in_path 

if __name__ == '__main__' :
    main()
