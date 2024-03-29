import operator
from pathlib import Path
from typing import BinaryIO
from pyblinx.material_list import MaterialList

from pyblinx.node import Node
from pyblinx.chunk import Chunk, is_chunk


class Tree:
    def __init__(
        self,
        xbe: BinaryIO,
        entry_offset: int,
        section: str,
        material_list: MaterialList = None,
    ):
        self.xbe = xbe
        self.section = section
        self.material_list = material_list

        if is_chunk(self.xbe, entry_offset, section):
            self.root = Chunk(self.xbe, entry_offset, self.section, self.material_list)
        else:
            self.root = Node(self.xbe, entry_offset, self.section, self.material_list)

        self.name = "tree_" + self.section + "_" + hex(entry_offset)

    def build_tree(self, node: Node = None, level: int = 0, verbose: bool = False):
        """
        Build tree starting at self.root by discovering node stubs. Does not parse nodes.
        """
        if not node:
            node = self.root

        if verbose:
            pad = "\t" * level
            print(f"{pad}{type(node).__name__}: {hex(node.raw_offset)} -> {node.entry}")

        level += 1

        if node.left_child_offset:
            transformed_coords = tuple(
                map(operator.add, node.parent_coords, node.world_coords)
            )  # apply parent matrix

            if is_chunk(self.xbe, node.left_child_offset, self.section):
                node.left_child = Chunk(
                    self.xbe,
                    node.left_child_offset,
                    self.section,
                    material_list=self.material_list,
                    parent_coords=transformed_coords,
                    parsed=False,
                )
            else:
                node.left_child = Node(
                    self.xbe,
                    node.left_child_offset,
                    self.section,
                    material_list=self.material_list,
                    parent_coords=transformed_coords,
                )

            self.build_tree(node.left_child, level, verbose=verbose)

        if node.right_child_offset:
            if is_chunk(self.xbe, node.right_child_offset, self.section):
                node.right_child = Chunk(
                    self.xbe,
                    node.right_child_offset,
                    self.section,
                    self.material_list,
                    node.parent_coords,
                    parsed=False,
                )
            else:
                node.right_child = Node(
                    self.xbe,
                    node.right_child_offset,
                    self.section,
                    material_list=self.material_list,
                    parent_coords=node.parent_coords,
                )

            self.build_tree(node.right_child, level - 1, verbose=verbose)

    def parse_chunks(
        self,
        node: Node = None,
        vertices_exist: bool = True,
        triangles_exist: bool = True,
        verbose: bool = False
    ):
        """
        Recurse through tree and parse all chunks. Nodes are not parsed.
        """
        if not node:
            node = self.root

        # strange chunk in chronoblob is 0x12. Not verified against others
        if isinstance(node, Chunk) and node.entry != 0x12:
            # TODO: let's figure out this error handling
            try:
                node.parse_geometry(world=True, verbose=verbose)

            except Exception as e:
                print(
                    f"Error parsing chunk {node.name}: {str(e)}\n"
                )
                node.errored = True

        if node.left_child_offset:
            self.parse_chunks(node.left_child, vertices_exist, triangles_exist)

        if node.right_child_offset:
            self.parse_chunks(node.right_child, vertices_exist, triangles_exist)

    def write(
        self, section_directory: Path, node: Node = None, separate_objs: bool = False
    ):
        """
        Write all full chunks in tree. Does not support character chunks
        """
        if not node:
            node = self.root

        # TODO: all as one file is broken since mesh indexes are ambiguous.
        # might take some serious work in triangle writing :(
        separate_objs = True

        if isinstance(node, Chunk):
            obj_name = f"{node.name}.obj" if separate_objs else f"{self.name}.obj"
            obj_path = section_directory / obj_name
            file_exists = obj_path.exists()

            with obj_path.open("a+") as obj_file:
                node.write_obj(
                    obj_file,
                    material_list=self.material_list,
                    ignore_mtllib_line=file_exists,  # only declare "mtllib" in .obj for new files
                )

        if node.left_child_offset:
            self.write(section_directory, node.left_child)

        if node.right_child_offset:
            self.write(section_directory, node.right_child)
