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

    def build_tree(self, node: Node = None, level: int = 0, verbose: bool = False):
        """
        Build tree starting at self.root by discovering node stubs. Does not parse nodes.
        """
        if not node:
            node = self.root

        if verbose:
            pad = "\t" * level
            print(f"{pad}{type(node).__name__} {hex(node.entry)} {hex(node.offset)}")

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
        verticies_exist: bool = True,
        triangles_exist: bool = True,
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
                if verticies_exist:
                    node.parse_vertices(world=True)

                if triangles_exist:
                    node.parse_triangles()

            except Exception:
                print(f"An error has occured when parsing chunk at {hex(node.offset)}")
                node._vertices = None
                node._triangles = None

        if node.left_child_offset:
            self.parse_chunks(node.left_child, verticies_exist, triangles_exist)

        if node.right_child_offset:
            self.parse_chunks(node.right_child, verticies_exist, triangles_exist)

    def write(self, section_directory: Path, node: Node = None):
        """
        Write all full chunks in tree. Does not support character chunks
        """
        if not node:
            node = self.root

        if isinstance(node, Chunk):
            obj_path = section_directory / f"{node.name}.obj"
            with obj_path.open("w+") as obj_file:
                node.write_obj(obj_file, material_list=self.material_list)

        if node.left_child_offset:
            self.write(section_directory, node.left_child)

        if node.right_child_offset:
            self.write(section_directory, node.right_child)
