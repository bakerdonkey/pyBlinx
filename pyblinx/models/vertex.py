from struct import unpack
from typing import BinaryIO, List


class Vertex:
    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z

    def obj(self):
        """
        Render a string that represents the vertex in .obj files
        """
        return f"v {self.x} {self.y} {self.z}\n"
