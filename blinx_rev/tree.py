from struct import unpack
from node import Node
from chunk import Chunk
from helpers import verify_file_arg_b

class Tree :
    def __init__(self, xbe, entry_offset, section, texlist=None) :
        self.xbe = verify_file_arg_b(xbe)
        self.section = section
        self.texlist = texlist
         
        f = self.xbe
        self.root = Node(f, entry_offset, self.section, texlist)

    def build_tree_rec(self, node, level=0) :
        type_name = 'Chunk' if isinstance(node, Chunk) else 'Node'
        pad = ' ' * level
        print('{}{} {} {}'.format(pad, type_name, hex(node.entry), hex(node.offset)))
        level += 1

        if node.left is not None :
            nex = Node(self.xbe, node.left, self.section, self.texlist)
            # If block exists, node is a chunk. Otherwise, it's a node
            if nex.block is not None :
                node.left_node = Chunk(self.xbe, node.left, self.section, self.texlist, full=False)

            else :
                node.left_node = nex
            
            self.build_tree_rec(node.left_node, level)
        if node.right is not None:
            nex = Node(self.xbe, node.right, self.section, self.texlist)
            if nex.block is not None :
                node.right_node = Chunk(self.xbe, node.right, self.section, self.texlist, full=False)

            else :
                node.right_node = nex

            self.build_tree_rec(node.right_node, level - 1)


    