from struct import unpack
from .node import Node
from .chunk import Chunk
from .helpers import verify_file_arg_b
from .address import get_raw_address
import operator


class Tree:
    def __init__(self, xbe, entry_offset, section, texlist=None):
        self.xbe = verify_file_arg_b(xbe)
        self.section = section
        self.texlist = texlist

        f = self.xbe

        root_is_chunk = self.root_block_exists(f, entry_offset, section)

        if root_is_chunk:
            self.root = Chunk(f, entry_offset, self.section, texlist)
        else:
            self.root = Node(f, entry_offset, self.section, texlist)

    def build_tree_rec(self, node=None, level=0, verbose=True):
        """
        Build tree starting at self.root by discovering node stubs. Does not parse nodes.
        """
        if node is None:
            node = self.root

        if verbose:
            type_name = "Chunk" if isinstance(node, Chunk) else "Node"
            pad = "\t" * level
            print(f"{pad}{type_name} {hex(node.entry)} {hex(node.offset)}")

        level += 1
        # time.sleep(.5)

        if node.left is not None:
            nex = Node(self.xbe, node.left, self.section, self.texlist)
            nex.parent_coords = tuple(
                map(operator.add, node.parent_coords, node.world_coords)
            )  # apply parent matrix

            # If block exists, node is a chunk. Otherwise node
            if nex.block is not None:
                node.left_node = Chunk(
                    self.xbe,
                    node.left,
                    self.section,
                    self.texlist,
                    nex.parent_coords,
                    full=False,
                )
            else:
                node.left_node = nex

            self.build_tree_rec(node.left_node, level)

        if node.right is not None:
            nex = Node(self.xbe, node.right, self.section, self.texlist)
            nex.parent_coords = node.parent_coords
            if nex.block is not None:
                node.right_node = Chunk(
                    self.xbe,
                    node.right,
                    self.section,
                    self.texlist,
                    nex.parent_coords,
                    full=False,
                )

            else:
                node.right_node = nex

            self.build_tree_rec(node.right_node, level - 1)

    def parse_chunks(self, node=None, verts=True, tris=True):
        """
        Recurse through tree and parse all chunks. Nodes are not parsed.
        """
        if node is None:
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

        except Exception as e:
            print(f"An error has occured when parsing chunk at {hex(node.offset)}")
            node.vertices = None
            node.triangles = None

        if node.left is not None:
            self.parse_chunks(node.left_node, verts, tris)

        if node.right is not None:
            self.parse_chunks(node.right_node, verts, tris)

    def write(self, outdir, node=None):
        """
        Write all full chunks in tree. Does not support character chunks
        """
        if node is None:
            node = self.root

        if isinstance(node, Chunk):
            with open("{}/{}.obj".format(outdir, node.name), "w+") as fi:
                node.write(fi, texlist=self.texlist, clist=False)

        if node.left is not None:
            self.write(outdir, node.left_node)

        if node.right is not None:
            self.write(outdir, node.right_node)

    def root_block_exists(self, f, offset, section):
        """
        Probes a node at a defined offset and section and returns whether or not it has a block (thus is a chunk).
        """
        raw_offset = get_raw_address(offset, section)
        f.seek(raw_offset + 4)
        block_pointer = unpack("I", f.read(4))[0]
        if block_pointer != 0:
            return True

        else:
            return False
