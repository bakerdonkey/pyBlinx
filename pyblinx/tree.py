import operator

from struct import unpack
from pyblinx.node import Node
from pyblinx.chunk import Chunk, is_chunk
from pyblinx.helpers import validate_file_handle


class Tree:
    def __init__(self, xbe, entry_offset, section, material_list=None):
        self.xbe = validate_file_handle(xbe)
        self.section = section
        self.material_list = material_list

        if is_chunk(self.xbe, entry_offset, section):
            self.root = Chunk(self.xbe, entry_offset, self.section, self.material_list)
        else:
            self.root = Node(self.xbe, entry_offset, self.section, self.material_list)

    def build_tree(self, node=None, level=0, verbose=False):
        """
        Build tree starting at self.root by discovering node stubs. Does not parse nodes.
        """
        if not node:
            node = self.root

        if verbose:
            pad = "\t" * level
            print(f"{pad}{type(node).__name__} {hex(node.entry)} {hex(node.offset)}")

        level += 1

        if node.left_pointer:
            transformed_coords = tuple(
                map(operator.add, node.parent_coords, node.world_coords)
            )  # apply parent matrix
            candidate = Node(
                self.xbe,
                node.left_pointer,
                self.section,
                material_list=self.material_list,
                parent_coords=transformed_coords,
            )

            # If block exists, node is a chunk. Otherwise node
            node.left_node = candidate
            if candidate.block:
                node.left_node = Chunk(
                    self.xbe,
                    node.left_pointer,
                    self.section,
                    material_list=self.material_list,
                    parent_coords=transformed_coords,
                    full=False,
                )

            self.build_tree(node.left_node, level, verbose=verbose)

        if node.right_pointer:
            candidate = Node(
                self.xbe,
                node.right_pointer,
                self.section,
                material_list=self.material_list,
                parent_coords=node.parent_coords,
            )
            node.right_node = candidate
            if candidate.block is not None:
                node.right_node = Chunk(
                    self.xbe,
                    node.right_pointer,
                    self.section,
                    self.material_list,
                    node.parent_coords,
                    full=False,
                )

            self.build_tree(node.right_node, level - 1, verbose=verbose)

    def parse_chunks(self, node=None, verts=True, tris=True):
        """
        Recurse through tree and parse all chunks. Nodes are not parsed.
        """
        if not node:
            node = self.root

        # TODO: use custom exception and more robust handling
        try:
            if (
                isinstance(node, Chunk) and node.entry != 0x12
            ):  # FIXME: strange chunk in chronoblob is 0x12. Not verified against others
                if verts:
                    node.parse_vertices(world=True)

                if tris:
                    node.parse_triangles()

        except Exception:
            print(f"An error has occured when parsing chunk at {hex(node.offset)}")
            node.vertices = None
            node.triangles = None

        if node.left_pointer:
            self.parse_chunks(node.left_node, verts, tris)

        if node.right_pointer:
            self.parse_chunks(node.right_node, verts, tris)

    def write(self, outdir, node=None):
        """
        Write all full chunks in tree. Does not support character chunks
        """
        if not node:
            node = self.root

        if isinstance(node, Chunk):
            with open(f"{outdir}/{node.name}.obj", "w+") as obj_file:
                node.write(obj_file, material_list=self.material_list)

        if node.left_pointer:
            self.write(outdir, node.left_node)

        if node.right_pointer:
            self.write(outdir, node.right_node)
