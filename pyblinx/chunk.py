from struct import unpack

from pyblinx.constants import ESCAPE, TEXTURE_MAGIC, TEXTURE_TYPE_SPEC
from pyblinx.node import Node
from pyblinx.address import get_raw_address
from pyblinx.helpers import validate_file_handle
from pyblinx.material_list import MaterialList
from pyblinx.world_transform import transform


class Chunk(Node):
    def __init__(
        self,
        xbe,
        entry_offset,
        section,
        material_list=None,
        parent_coords=None,
        full=True,
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

        self._vertices = None
        self._triangles = None

        if full:
            self._vertices, self._triangles = self.parse_geometry(world=True)

    def __str__(self):
        return self.name

    @property
    def vertices(self):
        if not self._vertices:
            return self.parse_vertices()
        return self._vertices

    @property
    def triangles(self):
        if not self._triangles:
            return self.parse_triangles()
        return self._triangles

    def parse_geometry_header(self):
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

    # TODO: this method could be useful to DRY up some caller code. it should oopulate the instance variables too.
    def parse_geometry(self, world=True):
        """
        Parse vetices and triangles in chunk.
        """
        print(f"Parsing chunk at {self.entry}")
        v = self.parse_vertices(world=world)
        t = self.parse_triangles()
        return v, t

    def write_obj(self, file, material_list: MaterialList = None):
        """
        Write .obj to open file handle. If material_list exists, reference material library.
        """
        f = validate_file_handle(file, usage="w+")
        if material_list:
            f.write(f"mtllib {material_list}.mtl\n")

        f.write(f"o {self.name}\n")
        self.write_vertices(f)
        self.write_texture_coordinates(f)
        self.write_triangles(f, material_list.material_names if material_list else None)

    def parse_vertices(self, world=True):
        """
        Reads vertex list from xbe. Returns a list[count], where each element is a tuple[3] denoting xyz.
        """
        if not self.vertex_list_offset:
            print(f"\t{hex(self.offset)}: This chunk contains no vertices")
            return

        self.xbe.seek(self.vertex_list_offset)
        self.xbe.seek(6, 1)  # skip 6 unknown bytes

        count = unpack("h", self.xbe.read(2))[0]
        self.xbe.seek(8, 1)  # skip 8 more unkown bytes

        print(
            f"\t{hex(self.offset)}: Parsing {count} vertices at {hex(self.vertex_list_offset)}... ",
            end="",
        )

        vertices = []
        for _ in range(count):
            vertex = list(unpack("fff", self.xbe.read(12)))

            if world:
                v_local = transform(vertex, self.world_coords)
                vertex = transform(v_local, self.parent_coords)

            vertices.append(tuple(vertex))
            self.xbe.seek(4, 1)  # skip 4 unknown bytes

        print("\tDone")

        self._vertices = vertices
        return vertices

    # TODO: refactor me!! this function is a mess. maybe make actual objects for triparts, tristrips, etc.
    def parse_triangles(self):
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
                print(f"\t\tParsing tripart {j}")
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

    def parse_tripart(self, type="texture", previous_material_list_index=0):
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
            print(f"\t\t\t\tUsing prev tindex {previous_material_list_index}")
            material_list_index = previous_material_list_index

        # The case where the tripart is simple. The next tripart is probed for the escape symbol, but no actual parsing happens.
        elif (type_spec - TEXTURE_TYPE_SPEC) % 0x1000 != 0:
            print("\t\t\tNon-texture tripart.")
            type = "simple"  # Currently unused

            tripart_size = unpack("h", f.read(2))[0] * 2
            f.seek(tripart_size, 1)
            tripart_end = f.tell()
            esc_candidate = f.read(4)
            if esc_candidate == ESCAPE:
                print("\t\t\t\t ESCAPE SYMBOL FOUND IN SIMPLE TRIPART")
                return {
                    "tripart_data": None,
                    "material_list_index": None,
                    "escape_symbol_found": True,
                    "is_final": True,
                }
            else:
                print("\t\t\t\tESCAPE SYMBOL NOT FOUND IN SIMPLE TRIPART")
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
            print("\t\t\tTEXTURE MAGIC NUMBER")
            escape = False

        # The case where the next 4 bytes is the escape symbol, thus terminating triangle parsing after the current tristrip.
        if esc_candidate == ESCAPE:
            print("\t\t\tESCAPE SYMBOL FOUND")
            escape = True

        # The case where the current tristrip is the last in its triangle section but there exists a next triangle section. New triangle sections always
        # start with 0x25XX 0xYYYY where XX is arbitrary (as far as I know) and YYYY is the size of the header. Headers have not been observed to be larger
        # than 0x20 bytes.
        if can_ints[0] >> 0x8 == 0x25 and can_ints[1] < 0x20:
            print("\t\t\tANOTHER TRIANGLE SECTION EXISTS")
            final = False
            escape = True

        f.seek(-(tripart_size + 4), 1)  # Return to beginning of tripart.

        # Parse the tripart.
        t_length = unpack("h", f.read(2))[0]
        for _ in range(t_length):
            strip = []
            s_length = abs(unpack("h", f.read(2))[0])

            for _ in range(s_length):
                if (
                    type == "texture"
                ):  # type is currently unused and will always be 'texture'.
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

    def write_vertices(self, file):
        f = validate_file_handle(file, usage="a+")

        if self.vertices:
            print(f"Writing {len(self._vertices)} vertices to {f.name}")
        else:
            print("\tNo vertices to write!")
            return

        for vertex in self._vertices:
            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")

    def write_triangles(self, file, matlist=None):
        f = validate_file_handle(file, usage="a+")

        if self.triangles:
            print(f"Writing {len(self.triangles)} triparts to {f.name}")
        else:
            print("\tNo triangles to write!")
            return None

        # TODO: write non-texture materials
        # TODO: implement material writing
        # TODO: remove redundant code
        vt = 1
        for tp in self.triangles:
            if matlist:
                ln = f"usemtl {matlist[tp[1]]}\n"
                f.write(ln)

            for ts in tp[0]:
                for c in range(len(ts) - 2):
                    if c % 2 == 0:
                        ln = f"f {ts[c][0]}/{vt} {ts[c+1][0]}/{vt+1} {ts[c+2][0]}/{vt+2}\n"
                    else:
                        ln = f"f {ts[c+1][0]}/{vt+1} {ts[c][0]}/{vt} {ts[c+2][0]}/{vt+2}\n"

                    vt += 1
                    f.write(ln)
                vt += 2

    def write_texture_coordinates(self, file):
        """
        Given an open file discriptor or path, write texture coordinates as indicies as they appear in the triangle array
        """
        f = validate_file_handle(file, usage="a+")

        if not self._triangles:
            print("\tNo texture coordinates found!")
            return None

        # TODO: Clean up
        for tp in self._triangles:
            # if tp[2] is False :
            for ts in tp[0]:
                for c in ts:
                    vt = list(c[1:])
                    ln = f"vt {vt[0]} {vt[1]}\n"
                    f.write(ln)


def is_chunk(xbe, offset, section):
    """
    Probe the header and determine if a node is a chunk. Undefined behavior if offset
    is not a node entry offset.
    """
    raw_offset = get_raw_address(offset, section)
    xbe.seek(raw_offset + 4)  # skip entry
    geometry_header_pointer = unpack("I", xbe.read(4))[0]

    return geometry_header_pointer != 0
