from struct import unpack
from argparse import ArgumentParser
from blinx_rev.helpers import verify_file_arg_b
from blinx_rev.helpers import verify_file_arg_o

def main() :
    parser = ArgumentParser()
    parser.add_argument('offset', help='Entry offset in file', type=lambda x: int(x,16))
    parser.add_argument('file', help='Path to vert file', type=str)
    parser.add_argument('out', help='Path to output file', type=str)
    parser.add_argument('-s', help='vertlist stride', type=int)

    args = parser.parse_args()

    try:
        f = open(args.file, 'rb')
    except FileNotFoundError:
        print('File not found')

    stride = args.s if args.s else 4
    v = parse_vertices(f, args.offset, stride)

    with open(args.out, 'w+') as o:
        write_vertices(o, v)

    f.close()

def parse_vertices(file, offset, stride=4) :
    '''
    Reads vertex list from xbe. Returns a list[count], where each element is a tuple[3] denoting xyz.
    '''
    f = verify_file_arg_b(file)
    f.seek(offset + 6)
    count = unpack('h', f.read(2))[0]
    f.seek(8, 1)

    print('Parsing {} vertices at {}... '.format(count, hex(offset)), end='')


    v = []
    for _ in range(count) :
        word = list(unpack('fff', f.read(12)))
        v.append(tuple(word))
        f.seek(stride, 1)

    print('Done')

    return v

def write_vertices(file, vertices) :
    f = verify_file_arg_o(file)

    verts = vertices
    print('Writing vertices to {}'.format(f.name))
    if not verts :
        print('\tNo vertices found!')
        return None
    
    for v in verts :
        ln = 'v {} {} {}\n'.format(v[0], v[1], v[2])
        f.write(ln)

if __name__=='__main__' :
    main()