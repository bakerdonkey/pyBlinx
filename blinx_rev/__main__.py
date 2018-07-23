from extract import Extractor
from chunk import Chunk
from texlist import Texlist
from address import section_addresses
import argparse


def main() :
    #TODO: Restructure, clean up extra arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('xbe', help='Path to xbe', type=str)

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

    with open(args.xbe, 'rb') as xbe :
        texlist = Texlist(xbe, 0xDAE6A8, 'MDLB1')
        texlist.parse_strlist()

        with open('../Desktop/outie.mtl', 'w+') as m :
            texlist.write_mtl(m, 'C:/Users/Sam/blinx/media')

        chunk = Chunk(xbe, 0xDE019C, 'MDLB1')
        chunk.parse_vertices()
        chunk.parse_triangles()

        with open('../Desktop/outie.obj', 'w+') as f :
            f.write('mtllib outie.mtl\n')
            f.write('o im_outie\n')
            chunk.write_vertices(f)
            chunk.write_texcoords(f)
            chunk.write_triangles(f, matlist=texlist.matlist)

        


    #extract = Extractor(section_path=args.section, media_path=args.mediapath, vert_path=args.vert, tri_path=args.tri, obj_path=args.obj, bin_dir=args.bin)
    #sl = extract.parse_stringlist(start_off=args.soffset, section=sections.get('data')[0])
    #chunk = extract.read_chunk(usage='vt', section=sections.get('data')[0], start_off=args.coffset)
    #extract.create_texture_coordinates(triset=chunk[1], stringlist=sl)
    #extract.write_verts(chunk[0])
    #extract.write_vt(extract.texpart_list)
    #extract.write_triparts_texture(chunk[1])



if __name__ == '__main__' :
    main()