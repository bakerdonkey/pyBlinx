from argparse import ArgumentParser
from pathlib import Path
from struct import unpack
import sys
import time
from typing import BinaryIO

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


def main():
    cli_args = get_cli_args()

    in_directory = (
        Path(cli_args.directory) if cli_args.directory else tk_load_dir("base")
    )
    out_directory = Path(cli_args.out) if cli_args.out else tk_load_dir("out")

    main_xbe = in_directory / XBE_FILE_NAME
    with main_xbe.open("rb") as xbe:
        if cli_args.mode == "map":
            models = parse_map_table(xbe, map_section=cli_args.map_section)

        elif cli_args.mode == "prop":
            models = parse_prop_table(xbe)
            out_directory = get_output_subdirectory(out_directory, "props")

        else:
            models = []
            if cli_args.chunk_offset:
                section = get_section_for_address(cli_args.chunk_offset)
                model = {
                    "section": section,
                    "geometry_offset": cli_args.chunk_offset,
                    "material_list_offset": None,
                }
                if cli_args.material_list_offset:
                    model["material_list_offset"] = cli_args.material_list_offset

                models.append(model)

        for model in models:
            print(
                f'{model["section"]}:\t{hex(model["geometry_offset"])}\t{hex(model["material_list_offset"])}'
            )
        print("--------------------------------------------------")
        run(
            models,
            xbe,
            in_directory,
            out_directory,
            cli_args.action,
            verbose=cli_args.verbose,
        )


def get_output_subdirectory(output_directory: Path, name: str):
    subdirectory = Path(f"{output_directory}/{name}")

    # delete all data if directory exists.
    if subdirectory.exists():
        for file in subdirectory.iterdir():
            file.unlink()
        subdirectory.rmdir()
    
    subdirectory.mkdir(parents=True)
    return subdirectory

def run(models, xbe, in_directory, out_directory, action, verbose=False):
    i = 0
    for model in models:
        section = model["section"]
        geometry_offset = model["geometry_offset"]
        material_list_offset = model["material_list_offset"]
        print(
            f"Model {i}: {section}:\tGeometry virtual offset -- {hex(geometry_offset)}\tMaterialList virtual offset -- {hex(material_list_offset)}"
        )
        i += 1

        section_directory = get_output_subdirectory(out_directory, section)

        if material_list_offset:
            material_list = MaterialList(xbe, material_list_offset, section)
            material_list.parse_texture_names()

            if action == "extract":
                mtl_path = section_directory / f"{material_list.name}.mtl"
                with mtl_path.open("w+") as mtl:
                    material_list.write_material_library(
                        mtl, in_directory / MEDIA_DIRECTORY_NAME
                    )
        else:
            material_list = None

        tree = Tree(xbe, geometry_offset, section, material_list)

        if action in ["peek", "parse", "extract"]:
            print(f"Building Tree at {hex(geometry_offset)}")
            tree.build_tree(tree.root, verbose=verbose)
            if action in ["parse", "extract"]:
                tree.parse_chunks(vertices_exist=True, triangles_exist=True)
                if action == "extract":
                    tree.write(section_directory)


def get_cli_args():
    parser = ArgumentParser()
    parser.add_argument(
        "action",
        choices=["peek", "parse", "extract"],
        help="What pyblinx does with the model tree.",
    )
    parser.add_argument(
        "mode",
        choices=["map", "prop", "custom"],
        help="Operating mode for pyblinx",
        type=str,
    )
    parser.add_argument("-d", "--directory", help="Path to Blinx directory", type=str)
    parser.add_argument("-o", "--out", help="Path to output directory", type=str)
    parser.add_argument(
        "-s",
        "--map_section",
        help="Section name containing map geometry. Mode must be 'map'",
        type=str,
    )
    parser.add_argument(
        "--chunk_offset",
        required="--material_list_offset" in sys.argv,
        help="Chunk entry offset (virtual address). Mode must be 'custom'",
        type=lambda x: int(x, 16),  # input is a hexadecimal
    )
    parser.add_argument(
        "--material_list_offset",
        help="MaterialList entry offset (virtual address).  Mode must be 'custom'",
        type=lambda x: int(x, 16),
    )
    parser.add_argument(
        "-v", "--verbose", help="Print verbose output", action="store_true"
    )

    return parser.parse_args()


# TODO: make this work!
def parse_prop_table(xbe, count=PROP_TABLE_COUNT):
    """
    WIP: read the prop table and extract the list of models.
    """
    xbe.seek(PROP_TABLE_OFFSET + DATA_SECTION_RAW_ADDRESS)
    models = []
    # models = {}
    section = "DATA"
    for _ in range(count):
        prop_addresses = unpack("II", xbe.read(8))
        geometry_offset = prop_addresses[0]
        material_list_offset = prop_addresses[1]
        section = get_section_for_address(geometry_offset)
        if (
            section != "MDLEN" and geometry_offset != 0 and material_list_offset != 0
        ):  # MDLEN props might be character models??
            model = {
                "section": section,
                "geometry_offset": geometry_offset,
                "material_list_offset": material_list_offset,
            }
            print(f"{model['section']}\t{hex(model['geometry_offset'])}\t{hex(model['material_list_offset'])}")
            models.append(model)

        xbe.seek(72, 1) # i wonder what data we're skipping here

    return models


def parse_map_table(xbe: BinaryIO, map_section: str = None):
    """
    Read the map table and extract a list of models.
    """
    xbe.seek(MAP_TABLE_OFFSET + DATA_SECTION_RAW_ADDRESS)
    maps = [
        ["MAP11", "MAP12", "MAP13", "MDLB1"],  # round 1 - Time Square
        ["MAP21", "MAP22", "MAP23", "MDLB2"],  # round 2 - Deja Vu Canals
        ["MAP31", "MAP32", "MAP33", "MDLB3"],  # round 3 - Hourglass Caves
        ["MAP41", "MAP42", "MAP43", "MDLB4"],  # round 4 - Temple of Lost Time
        ["MAP51", "MAP52", "MAP53", "MDLB5"],  # round 5 - Forgotten City
        ["MAP61", "MAP62", "MAP63", "MDLB6"],  # round 6 - Mine of Precious Moments
        ["_MAP71", "_MAP72", "_MAP71", "_MDLB7"],  # unused
        ["MAP81", "MAP82", "MAP83", "MDLB8"],  # round 7 - Everwinter
        ["MAP91", "MAP92", "MAP93", "MDLB9"],  # round 8 - Forge of Hours
        ["MDLB10", "MDLB102", "_MDLB103", "_MDLB104"],  # final boss, section 3-4 unused
    ]

    models = []
    for round in maps:
        for map in round:
            map_addresses = unpack("III", xbe.read(12))  # what is map_addresses[0]??
            geometry_offset = map_addresses[1]
            material_list_offset = map_addresses[2]
            models.append(
                {
                    "section": map,
                    "geometry_offset": geometry_offset,
                    "material_list_offset": material_list_offset,
                }
            )

    if map_section:
        models = [model for model in models if model["section"] == map_section]

    return models


# eww
if __name__ == "__main__":
    main()
