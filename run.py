import os

from argparse import ArgumentParser
from pathlib import Path
from struct import unpack

from pyblinx.address import get_section_for_address
from pyblinx.constants import (
    DATA_SECTION_RAW_ADDRESS,
    MAP_TABLE_OFFSET,
    MEDIA_DIRECTORY_NAME,
    PROP_TABLE_COUNT,
    PROP_TABLE_OFFSET,
    XBE_FILE_NAME,
)
from pyblinx.helpers import tk_load_dir
from pyblinx.material_list import MaterialList
from pyblinx.tree import Tree

# TODO: this file is a mess, should be totally refactored. Maybe the whole app could be a class that holds context internally.
#
# The CLI should have a high-level interface that's able to:
#   - extract maps
#   - extract props
# It should have a low-level interface that's able to:
#   - extract an individual chunk given a coffset and soffset


def main():
    cli_args = get_cli_args()

    in_directory = (
        Path(cli_args.directory) if cli_args.directory else tk_load_dir("base")
    )
    out_directory = Path(cli_args.out) if cli_args.out else tk_load_dir("out")

    # sect = cli_args.section or "MDLB1"
    # coffset = cli_args.coffset or 0xDE9464
    # soffset = cli_args.soffset or 0xD80280
    # models = [(coffset, soffset, sect)]

    main_xbe = in_directory / XBE_FILE_NAME

    with main_xbe.open("rb") as xbe:
        models = parse_map_table(xbe, section=cli_args.section)
        # models = parse_prop_table(xbe)
        for section, offsets in models.items():
            print(
                f'{section}:\t{hex(offsets["geometry_offset"])}\t{hex(offsets["material_list_offset"])}'
            )
        print("--------------------------------------------------")
        run(models, xbe, in_directory, out_directory, verbose=cli_args.verbose)


def run(models, xbe, in_directory, out_directory, **kwargs):
    verbose = kwargs.get("verbose")
    i = 0
    for section, model in models.items():
        geo_offset = model["geometry_offset"]
        material_list_offset = model["material_list_offset"]
        print(
            f"Model {i} in {section}:\tGeometry offset -- {hex(geo_offset)}\tMaterialList offset -- {hex(material_list_offset)}"
        )
        i += 1

        section_directory = Path(f"{out_directory}/{section}")
        section_directory.mkdir(parents=True, exist_ok=True)

        material_list = MaterialList(xbe, material_list_offset, section)
        material_list.parse_texture_names()

        mtl_path = section_directory / f"{material_list.name}.mtl"
        with mtl_path.open("w+") as mtl:
            material_list.write_material_library(
                mtl, in_directory / MEDIA_DIRECTORY_NAME
            )

        tree = Tree(xbe, geo_offset, section, material_list)
        tree.build_tree(tree.root, verbose=verbose)
        tree.parse_chunks(verts=True, tris=True)
        tree.write(section_directory)


def get_cli_args():
    parser = ArgumentParser()
    parser.add_argument("-d", "--directory", help="Path to Blinx directory", type=str)
    parser.add_argument("-o", "--out", help="Path to output directory", type=str)
    parser.add_argument("-s", "--section", help="Section containing chunk", type=str)
    parser.add_argument(
        "-co",
        "--coffset",
        help="Chunk entry offset (virtual address)",
        type=lambda x: int(x, 16),  # input is a hexidecimal
    )
    parser.add_argument(
        "-so",
        "--soffset",
        help="Stringlist file entry offset (virtual address)",
        type=lambda x: int(x, 16),
    )
    parser.add_argument("-to", "--toffset", help="Pointer table offset", type=str)
    parser.add_argument(
        "-v", "--verbose", help="Print verbose output", action="store_true"
    )

    return parser.parse_args()


# TODO: make this work!
def parse_prop_table(
    xbe, toffset=(PROP_TABLE_OFFSET + DATA_SECTION_RAW_ADDRESS), count=PROP_TABLE_COUNT
):
    """
    WIP: read the prop table and extract the list of models.
    """
    xbe.seek(toffset)
    models = []
    # models = {}
    section = "DATA"
    for _ in range(count):
        m = list(unpack("II", xbe.read(8)))
        section = get_section_for_address(m[0])
        m.append(section)
        m = tuple(m)
        if m[0] != 0 and m[1] != 0 and m[2] != "MDLEN":
            models.append(m)
        xbe.seek(72, 1)
        print(m)

        # prop_addresses = unpack("II", xbe.read(8))
        # geometry_offset = prop_addresses[0]
        # material_list_offset = prop_addresses[1]
        # section = find_section(geometry_offset)
        # if section != 'MDLEN' and geometry_offset not in [0, 1] and material_list_offset not in [0, 1]: # why not MDLEN??
        #     models[section] = {'geometry_offset': geometry_offset, 'material_list_offset': material_list_offset}

    return models


def parse_map_table(
    xbe, toffset=(MAP_TABLE_OFFSET + DATA_SECTION_RAW_ADDRESS), section=None
):
    """
    Read the map table and extract a list of models.
    """
    f = xbe
    f.seek(toffset)
    maps = [
        ["MAP11", "MAP12", "MAP13", "MDLB1"],  # round 1 - Time Square
        ["MAP21", "MAP22", "MAP23", "MDLB2"],  # round 2 - Deja Vu Canals
        ["MAP31", "MAP32", "MAP33", "MDLB3"],  # round 3 - Hourglass Caves
        ["MAP41", "MAP42", "MAP43", "MDLB4"],  # round 4 - Forgotten City
        ["MAP51", "MAP52", "MAP53", "MDLB5"],  # round 5 - Temple of Lost Time
        ["MAP61", "MAP62", "MAP63", "MDLB6"],  # round 6 - Mine of Precious Moments
        ["MAP11", "MAP11", "MAP11", "MAP11"],  # unused??
        ["MAP81", "MAP82", "MAP83", "MDLB8"],  # round 7 - Everwinter
        ["MAP91", "MAP92", "MAP93", "MDLB9"],  # round 8 - Forge of Hours
        ["MDLB10", "MDLB102", "MAP11", "MDLB10"],  # final boss, section 3 unused
    ]

    models = {}
    for round in maps:
        for map in round:
            map_addresses = unpack("III", f.read(12))  # what is map_pointers[0]??
            geometry_offset = map_addresses[1]
            material_list_offset = map_addresses[2]
            models[map] = {
                "geometry_offset": geometry_offset,
                "material_list_offset": material_list_offset,
            }

    # TODO: can we lazy load? or at least do this logic upstream?
    if section:
        models = {section: models[section]}

    return models


# eww
if __name__ == "__main__":
    main()
