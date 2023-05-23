import os

from argparse import ArgumentParser
from pathlib import Path
from struct import unpack
from tkinter import Tk, filedialog

from pyblinx.address import find_section
from pyblinx.constants import DATA_SECTION_RAW_ADDRESS, MAP_TABLE_OFFSET, PROP_TABLE_COUNT, PROP_TABLE_OFFSET
from pyblinx.texlist import Texlist
from pyblinx.tree import Tree

# TODO: this file is a mess, should be totally refactored. Maybe the whole app could be a class that holds context internally.
#
# The CLI should have a high-level interface that's able to:
#   - extract maps
#   - extract props
# It should have a low-level interface that's able to:
#   - extract a chunk given a coffset and soffset


def main():
    cli_args = get_cli_args()

    in_directory = (
        os.path.abspath(cli_args.directory) if cli_args.directory else _tk_load_dir("base")
    )
    out_directory = (
        os.path.abspath(cli_args.out) if cli_args.out else _tk_load_dir("out")
    )

    # sect = cli_args.section or "MDLB1"
    # coffset = cli_args.coffset or 0xDE9464
    # soffset = cli_args.soffset or 0xD80280
    # models = [(coffset, soffset, sect)]

    with open(in_directory + "/default.xbe", "rb") as xbe:
        models = parse_map_table(xbe, section=cli_args.section)
        # models = parse_prop_table(xbe)
        for section, offsets in models.items():
            print(f'{section}:\t{hex(offsets["geometry_offset"])}\t{hex(offsets["texlist_offset"])}')
        print("--------------------------------------------------")
        run(models, xbe, in_directory, out_directory)


def get_cli_args():
    parser = ArgumentParser()
    parser.add_argument("-d", "--directory", help="Path to Blinx directory", type=str)
    parser.add_argument("-o", "--out", help="Path to output directory", type=str)
    parser.add_argument("-s", "--section", help="Section containing chunk", type=str)
    parser.add_argument(
        "-co",
        "--coffset",
        help="Chunk entry offset (virtual address)",
        type=lambda x: int(x, 16),
    )
    parser.add_argument(
        "-so",
        "--soffset",
        help="Stringlist file entry offset (virtual address)",
        type=lambda x: int(x, 16),
    )
    parser.add_argument("-to", "--toffset", help="Pointer table offset", type=str)

    return parser.parse_args()


# TODO: make this work!
def parse_prop_table(xbe, toffset=(PROP_TABLE_OFFSET + DATA_SECTION_RAW_ADDRESS), count=PROP_TABLE_COUNT):
    """
    WIP: read the prop table and extract the list of models.
    """
    xbe.seek(toffset)
    # models = []
    models = {}
    # section = "DATA"
    for _ in range(count):
        # m = list(unpack("II", f.read(8)))
        # section = find_section(m[0])
        # m.append(section)
        # m = tuple(m)
        # if m[0] != 0 and m[1] != 0 and m[2] != "MDLEN":
        #     models.append(m)
        # f.seek(72, 1)
        # print(m)

        prop_addresses = unpack("II", xbe.read(8))
        geometry_offset = prop_addresses[0]
        texlist_offset = prop_addresses[1]
        section = find_section(geometry_offset)
        if section != 'MDLEN' and geometry_offset not in [0, 1] and texlist_offset not in [0, 1]: # why not MDLEN??
            models[section] = {'geometry_offset': geometry_offset, 'texlist_offset': texlist_offset}

    return models


def parse_map_table(xbe, toffset=(MAP_TABLE_OFFSET + DATA_SECTION_RAW_ADDRESS), section=None):
    """
    Read the map table and extract a list of models.
    """
    f = xbe
    f.seek(toffset)
    maps = [
        ["MAP11", "MAP12", "MAP13", "MDLB1"], # round 1 - Time Square
        ["MAP21", "MAP22", "MAP23", "MDLB2"], # round 2 - Deja Vu Canals
        ["MAP31", "MAP32", "MAP33", "MDLB3"], # round 3 - Hourglass Caves
        ["MAP41", "MAP42", "MAP43", "MDLB4"], # round 4 - Forgotten City
        ["MAP51", "MAP52", "MAP53", "MDLB5"], # round 5 - Temple of Lost Time
        ["MAP61", "MAP62", "MAP63", "MDLB6"], # round 6 - Mine of Precious Moments
        ["MAP11", "MAP11", "MAP11", "MAP11"], # unused??
        ["MAP81", "MAP82", "MAP83", "MDLB8"], # round 7 - Everwinter
        ["MAP91", "MAP92", "MAP93", "MDLB9"], # round 8 - Forge of Hours
        ["MDLB10", "MDLB102", "MAP11", "MDLB10"], # final boss, section 3 unused
    ]
    
    models = {}
    for round in maps:
        for map in round:
            map_addresses = unpack("III", f.read(12)) # what is map_pointers[0]??
            geometry_offset = map_addresses[1]
            texlist_offset = map_addresses[2]
            models[map] = {'geometry_offset': geometry_offset, 'texlist_offset': texlist_offset}

    # TODO: can we lazy load? or at lease do this logic upstream?
    if section:
        models = {section: models[section]}

    return models


def run(models, xbe, in_directory, out_directory):
    i = 0
    for section, model in models.items():
        geo_offset = model['geometry_offset']
        texlist_offset = model['texlist_offset']
        print(
            f"Model {i} in {section}:\tGeometry offset -- {hex(geo_offset)}\tTexlist offset -- {hex(texlist_offset)}"
        )
        i += 1

        # TODO: fully implement pathlib for paths
        Path(f"{out_directory}/{section}").mkdir(parents=True, exist_ok=True)

        texlist = Texlist(xbe, texlist_offset, section)
        texlist.parse_strlist()
        with open(f"{out_directory}/{section}/{texlist.name}.mtl", "w+") as m:
            texlist.write_mtl(m, in_directory + "/media")

        # TODO: handle specific exceptions

        tree = Tree(xbe, geo_offset, section, texlist)
        tree.build_tree_rec(tree.root)
        tree.parse_chunks(verts=True, tris=True)
        tree.write(f"{out_directory}/{section}")


#        chunklist = Chunklist(xbe, coffset, sect, texlist)
#        chunklist.discover_local_chunks()
#        chunklist.parse_all_chunks()
#        with open('{}/{}.obj'.format(out_directory, chunklist.name), 'w+') as f :
#            chunklist.write(f, texlist=texlist, outdir=out_directory)

#        chunk = Chunk(xbe, coffset, sect, full=False)
#        chunk.parse_triangles()
#        with open('{}/{}.obj'.format(out_directory, chunk.name), 'w+') as f :
#            chunk.write_texcoords(f)


# TODO: might be worth refactoring this or at least moving to a helper file.
def _tk_load_dir(dir_type):
    Tk().withdraw()
    if dir_type == "base":
        titlestr = "Select game folder"
    elif dir_type == "out":
        titlestr = "Select output folder"
    else:
        return None

    in_path = filedialog.askdirectory(title=titlestr)
    return in_path

# eww
if __name__ == "__main__":
    main()
