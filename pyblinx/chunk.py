from struct import unpack
from typing import BinaryIO, List, TextIO

from pyblinx.constants import ESCAPE, TEXTURE_MAGIC, TEXTURE_TYPE_SPEC
from pyblinx.models.vertex import Vertex
from pyblinx.node import Node
from pyblinx.address import get_raw_address
from pyblinx.material_list import MaterialList
from pyblinx.world_transform import transform


class Chunk(Node):
    def __init__(
        self,
        xbe: BinaryIO,
        entry_offset: int,
        section: str,
        material_list: MaterialList = None,
        parent_coords: tuple = None,
        parsed: bool = True,
    ):
        super(Chunk, self).__init__(
            xbe, entry_offset, section, material_list, parent_coords
        )

        geometry_header = self.parse_geometry_header()
        self.vertex_list_offset = (
            get_raw_address(geometry_header["vertex_list_offset"], self.section)
            if geometry_header["vertex_list_offset"]
            else None
        )
        self.triangle_list_offset = (
            get_raw_address(geometry_header["triangle_list_offset"], self.section)
            if geometry_header["triangle_list_offset"]
            else None
        )

        self.name = "ch_" + self.section + "_" + hex(self.offset)

        self._vertices: List[Vertex] = None
        self._triangles = None

        # Sometimes chunks can't be parsed -- it happens. Do not write errored chunks.
        self.errored = False

        if parsed:
            self._vertices, self._triangles = self.parse_geometry(world=True)

    def __str__(self):
        return self.name

    @property
    def vertices(self) -> List[Vertex]:
        if not self._vertices:
            return self.parse_vertices()
        return self._vertices

    @property
    def triangles(self) -> list:
        if not self._triangles:
            return self.parse_triangles()
        return self._triangles

    def parse_geometry_header(self) -> dict:
        """
        Parse geometry header and return pointers to vertices and triangles.
        """
        offset = get_raw_address(self.geometry_header, self.section)
        self.xbe.seek(offset)

        vertex_list_offset = unpack("i", self.xbe.read(4))[0]
        if vertex_list_offset == 0:
            vertex_list_offset = None

        triangle_list_offset = unpack("i", self.xbe.read(4))[0]
        if triangle_list_offset == 0:
            triangle_list_offset = None

        float_array = []
        for _ in range(6):
            float_array.append(unpack("f", self.xbe.read(4))[0])

        return {
            "vertex_list_offset": vertex_list_offset,
            "triangle_list_offset": triangle_list_offset,
            "farray": float_array,  # unknown use
        }

    # TODO: this method could be useful to DRY up some caller code. it should maybe populate the instance variables too.
    def parse_geometry(self, world: bool = True):
        """
        Parse vetices and triangles in chunk.
        """
        print(f"{self.name}: Parsing chunk with entry value {self.entry}")
        v = self.parse_vertices(world=world)
        t = self.parse_triangles()
        return v, t

    def write_obj(self, file: TextIO, material_list: MaterialList = None, **kwargs):
        """
        Write .obj to open file handle. If material_list exists, reference material library.
        """
        if self.errored:
            print(
                f"Chunk {self.name} had a parsing error. Cannot write .obj for errored chunk."
            )
            return

        if material_list and not kwargs.get("ignore_mtllib_line"):
            file.write(f"mtllib {material_list}.mtl\n")

        print(f'{self.name}: Writing chunk to {file.name}')
        file.write(f"o {self.name}\n")
        self._write_vertices(file)
        self._write_texture_coordinates(file)
        self._write_triangles(file, material_list)

    def parse_vertices(self, world: bool = True) -> list:
        """
        Reads vertex list from xbe. Returns a list[count], where each element is a tuple[3] denoting xyz.
        """
        if self._vertices:
            print(f"\t{self.name}: Vertices already parsed")
            return self._vertices

        if not self.vertex_list_offset:
            print(f"\t{self.name}: This chunk contains no vertices")
            return []

        self.xbe.seek(self.vertex_list_offset)
        self.xbe.seek(6, 1)  # skip 6 unknown bytes

        count = unpack("h", self.xbe.read(2))[0]
        self.xbe.seek(8, 1)  # skip 8 more unkown bytes

        print(
            f"\tParsing {count} vertices at {hex(self.vertex_list_offset)}... ",
            end="",
        )

        vertices = []
        for _ in range(count):
            coordinates = unpack("fff", self.xbe.read(12))
            self.xbe.seek(4, 1)  # skip 4 unknown bytes

            vertex = Vertex(*coordinates)
            if world:
                v_local = transform(vertex, self.world_coords)
                vertex = transform(v_local, self.parent_coords)

            vertices.append(vertex)

        print("\tDone")

        self._vertices = vertices
        return vertices

    # TODO: refactor me!! this function is a mess. maybe make actual objects for triparts, tristrips, etc.
    def parse_triangles(self) -> list:
        """
        Read tripart list from xbe. Returns a list of tuples (tripart, material_list index) as defined in parse_tripart() without escape flags.
        """
        if not self.triangle_list_offset:
            print(f"\t{hex(self.offset)}: This chunk contains no triangles")
            return

        self.xbe.seek(self.triangle_list_offset)
        print(f"\tParsing triangles at {hex(self.triangle_list_offset)}... ")

        # Hacky fix around unknown value at 0xbc58 in MDLEN. Probably others like it.
        if unpack("i", self.xbe.read(4))[0] > 50:
            self.xbe.seek(-4, 1)

        # TODO: looks like we're skipping a header here. look into that, could be some cool stuff!
        self.xbe.seek(2, 1)
        header_size = unpack("h", self.xbe.read(2))[0] * 2
        self.xbe.seek(header_size, 1)

        triparts = []
        i = 0
        while True:
            # TODO: what is a triangle section?
            print(f"\tParsing triangle section {i}")
            i += 1
            j = 0
            previous_material_list_index = 0
            final = False
            while True:
                print(f"\t\t\tParsing tripart {j}...\t")
                j += 1

                tripart = self.parse_tripart(
                    previous_material_list_index=previous_material_list_index
                )

                if tripart["tripart_data"] and tripart["material_list_index"]:
                    triparts.append(
                        (tripart["tripart_data"], tripart["material_list_index"])
                    )
                    previous_material_list_index = tripart["material_list_index"]

                if tripart["is_final"]:
                    final = True

                if tripart["escape_symbol_found"]:
                    break

            if final:  # FIXME: handle case where tripart = None
                break

        print("\tDone\n")
        self._triangles = triparts
        return triparts

    # TODO: make "type" an enum
    def parse_tripart(
        self, type: str = "texture", previous_material_list_index: int = 0
    ) -> dict:
        """
        Reads tripart. Returns tuple (tripart, material_list index, last, final) where tripart is a list of tuples (vertex index, tex_x, tex_y),
        material_list index assigns the texture, last is the escape flag, and final flag is true if there does not exist another triangle section.
        """
        f = self.xbe

        t = []
        escape = False  # Assume this is not the final tripart
        final = True  # Assume this is the final triangle section

        # First, observe the first two bytes as an int16. This will be used to determine the type of the tripart: simple, textured with declared index,
        # or textured without declared index. pyBlinx current does not support parsing simple triparts, and they will be skipped.
        type_spec = unpack("h", f.read(2))[0]
        # TODO: make logical flow for this section more intuitive
        material_list_index = 0

        # The case where the texture index is not declared, but the tripart is textured. It uses the texture index passed into the method.
        if type_spec == TEXTURE_MAGIC:
            material_list_index = previous_material_list_index

        # The case where the tripart is simple. The next tripart is probed for the escape symbol, but no actual parsing happens.
        elif (type_spec - TEXTURE_TYPE_SPEC) % 0x1000 != 0:
            print("\t\t\t\tNon-texture tripart.")
            type = "simple"  # Currently unused

            tripart_size = unpack("h", f.read(2))[0] * 2
            f.seek(tripart_size, 1)
            tripart_end = f.tell()
            esc_candidate = f.read(4)
            if esc_candidate == ESCAPE:
                print("\t\t\t\tEscape symbol encountered in simple tripart")
                return {
                    "tripart_data": None,
                    "material_list_index": None,
                    "escape_symbol_found": True,
                    "is_final": True,
                }
            else:
                print("\t\t\t\tEscape symbol NOT encountered in simple tripart")
                f.seek(-4, 1)
                return {
                    "tripart_data": None,
                    "material_list_index": None,
                    "escape_symbol_found": False,
                    "is_final": True,
                }

        # The case where the tripart's texture index is declared.
        else:
            material_list_index = unpack("h", f.read(2))[0] ^ 0x4000
            f.seek(2, 1)

        # This next section navigates to the end of the tripart and probes four bytes. Using different interpretations of these bytes, it determines
        # the behavior after the tristrip is parsed. More specifically, it determines the existence of more triparts or triangle sections. The output
        # of this section will be passed in the returned tuple as booleans at [2] and [3].
        tripart_size = unpack("h", f.read(2))[0] * 2
        f.seek(tripart_size, 1)
        tripart_end = f.tell()
        esc_candidate = f.read(4)

        can_float = unpack("f", esc_candidate)[0]
        can_ints = unpack("HH", esc_candidate)

        # The first four bytes of tripart headers that declare texture indexes is a float ~2.0. This is hacky and will falsely identify a simple tripart
        # or a tripart that uses the previous texture index. I'm looking to phase this out when possible, since it is nondeterministic and relies on
        # sketchy math.
        if can_float < 1.5:
            escape = True

        # The case where the next tripart does exist and uses the texture index declared in the current one. This would have been falsely marked positive by
        # the previous check.
        if can_ints[0] == TEXTURE_MAGIC:
            print(
                f"\t\t\t\tMagic number {hex(TEXTURE_MAGIC)} encountered: another tripart exists"
            )
            escape = False

        # The case where the next 4 bytes is the escape symbol, thus terminating triangle parsing after the current tristrip.
        if esc_candidate == ESCAPE:
            print(
                f"\t\t\t\tEscape symbol {str(ESCAPE)} encountered: terminating triangle parsing after this strip"
            )
            escape = True

        # The case where the current tristrip is the last in its triangle section but there exists a next triangle section. New triangle sections always
        # start with 0x25XX 0xYYYY where XX is arbitrary (as far as I know) and YYYY is the size of the header. Headers have not been observed to be larger
        # than 0x20 bytes.
        if can_ints[0] >> 0x8 == 0x25 and can_ints[1] < 0x20:
            print("\t\t\t\tAnother tripart exists")
            final = False
            escape = True

        f.seek(-(tripart_size + 4), 1)  # Return to beginning of tripart.

        # Parse the tripart.
        t_length = unpack("h", f.read(2))[0]
        if t_length > 255:
            raise ValueError('t_length too long')

        for _ in range(t_length):
            strip = []
            s_length = abs(unpack("h", f.read(2))[0])
            # TODO: more robust handling here
            if s_length > 255:
                raise ValueError('s_length too long')

            for _ in range(s_length):
                # type is currently unused and will always be 'texture'.
                if type == "texture":
                    raw_point = list(unpack("hhh", f.read(6)))
                    raw_point[0] += 1  # TODO: clean up
                    raw_point[1] /= 255.0
                    raw_point[2] /= -255.0
                    raw_point[2] += 1.0

                else:
                    raw_point = [unpack("h", f.read(2))[0] + 1, 0, 0]

                data_point = tuple(raw_point)
                strip.append(data_point)

            t.append(strip)

        f.seek(tripart_end)  # Verify file pointer is at end of tripart.

        return {
            "tripart_data": t,
            "material_list_index": material_list_index,
            "escape_symbol_found": escape,
            "is_final": final,
        }

    def _write_vertices(self, file: TextIO):
        if self.vertices:
            print(f"\t{len(self._vertices)} vertices")
        else:
            print("\tNo vertices to write!")
            return

        for vertex in self._vertices:
            file.write(vertex.obj())

    def _write_triangles(self, file: TextIO, material_list: MaterialList = None):
        if self.triangles:
            print(f"\t{len(self.triangles)} triparts")
        else:
            print("\tNo triangles to write!")
            return

        # TODO: write non-texture materials
        # TODO: implement material writing
        # TODO: remove redundant code
        vt = 1
        for tripart in self.triangles:
            if material_list:
                try:
                    material_name = material_list.material_names[tripart[1]]
                    file.write(f"usemtl {material_name}\n")
                except IndexError:
                    print(
                        f"Material list index {tripart[1]} out of range for material list {material_list.name} of size {len(material_list.material_names)}"
                    )

            for tristrip in tripart[0]:
                for c in range(len(tristrip) - 2):
                    if c % 2 == 0:
                        ln = f"f {tristrip[c][0]}/{vt} {tristrip[c+1][0]}/{vt+1} {tristrip[c+2][0]}/{vt+2}\n"
                    else:
                        ln = f"f {tristrip[c+1][0]}/{vt+1} {tristrip[c][0]}/{vt} {tristrip[c+2][0]}/{vt+2}\n"

                    vt += 1
                    file.write(ln)
                vt += 2

    def _write_texture_coordinates(self, file: TextIO):
        """
        Given an open file handle or path, write texture coordinates as indicies as they appear in the triangle array
        """
        if self._triangles:
            print(f"\t{len(self.triangles)} texture coordinates")
        else:
            print("\tNo texture coordinates to write!")
            return


        # TODO: Clean up
        for tp in self._triangles:
            # if tp[2] is False :
            for ts in tp[0]:
                for c in ts:
                    vt = list(c[1:])
                    ln = f"vt {vt[0]} {vt[1]}\n"
                    file.write(ln)


def is_chunk(xbe, offset: int, section: str) -> bool:
    """
    Probe the header and determine if a node is a chunk. Undefined behavior if offset
    is not a node entry offset.
    """
    raw_offset = get_raw_address(offset, section)
    xbe.seek(raw_offset + 4)  # skip entry
    geometry_header_pointer = unpack("I", xbe.read(4))[0]

    return geometry_header_pointer != 0
