from pyblinx.constants import ESCAPE, TEXTURE_MAGIC, TEXTURE_TYPE_SPEC
from pyblinx.node import Node
from pyblinx.address import get_section_address_mapping, get_raw_address
from pyblinx.helpers import validate_file_handle
from pyblinx.material_list import MaterialList
from pyblinx.world_transform import transform
from struct import unpack


class Chunk(Node):
    section_table = get_section_address_mapping()

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

        block = self.parse_block()
        self.voffset = (
            get_raw_address(block["voffset"], self.section, self.section_table)
            if block["voffset"]
            else None
        )
        self.toffset = (
            get_raw_address(block["toffset"], self.section, self.section_table)
            if block["toffset"]
            else None
        )

        self.name = "ch_" + self.section + "_" + hex(self.offset)

        self.vertices = None
        self.triangles = None

        if full:
            self.vertices, self.triangles = self.parse(world=True)

    def __str__(self):
        return self.name

    def parse_block(self):
        """
        Parse pointer block and return data.
        """
        offset = get_raw_address(self.block, self.section, self.section_table)
        self.xbe.seek(offset)

        vdata_offset = unpack("i", self.xbe.read(4))[0]
        if vdata_offset == 0:
            vdata_offset = None

        tdata_offset = unpack("i", self.xbe.read(4))[0]
        if tdata_offset == 0:
            tdata_offset = None

        float_array_0 = []
        for _ in range(6):
            float_array_0.append(unpack("f", self.xbe.read(4))[0])

        return {
            "voffset": vdata_offset,
            "toffset": tdata_offset,
            "farray": float_array_0,
        }

    def parse(self, world=True):
        """
        Parse vetices and triangles in chunk.
        """
        print(f"Parsing chunk at {self.entry}")
        v = self.parse_vertices(world=world)
        t = self.parse_triangles()
        return v, t

    def write(self, file, material_list: MaterialList = None):
        """
        Write .obj to open file handle. If material_list exists, reference material library.
        """
        f = validate_file_handle(file, usage="w+")
        if material_list:
            f.write("mtllib {}.mtl\n".format(material_list.name))

        f.write("o {}\n".format(self.name))
        self.write_vertices(f)
        self.write_texcoords(f)

        matlist = material_list.material_names if material_list else None
        self.write_triangles(f, matlist)

    def parse_vertices(self, world=True):
        """
        Reads vertex list from xbe. Returns a list[count], where each element is a tuple[3] denoting xyz.
        """
        if self.voffset is None:
            print(f"\t{hex(self.offset)}: This chunk contains no vertices")
            return None

        f = self.xbe
        f.seek(self.voffset + 6)
        count = unpack("h", f.read(2))[0]
        f.seek(8, 1)

        print(
            f"\t{hex(self.offset)}: Parsing {count} vertices at {hex(self.voffset)}... ",
            end="",
        )

        v = []
        for _ in range(count):
            vertex = list(unpack("fff", f.read(12)))

            if world is True:
                v_local = transform(vertex, self.world_coords)
                v_global = transform(v_local, self.parent_coords)
                vertex = v_global

                # w = tuple(map(operator.add, self.world_coords, self.parent_coords))
                # print(str(self.world_coords[:3]) + ' + ' + str(self.parent_coords[:3]) + ' = ' + str(w[:3]))
                # vertex = transform(vertex, w)

            v.append(tuple(vertex))
            f.seek(4, 1)

        print("\tDone")

        self.vertices = v
        return v

    def parse_triangles(self):
        """
        Read tripart list from xbe. Returns a list of tuples (tripart, material_list index) as defined in parse_tripart() without escape flags.
        """
        if self.toffset is None:
            print(f"\t{hex(self.offset)}: This chunk contains no triangles")
            return None

        f = self.xbe
        f.seek(self.toffset)
        print(f"\tParsing triangles at {hex(self.toffset)}... ")

        # Hacky fix around unknown value at 0xbc58 in MDLEN. Probably others like it.
        if unpack("i", f.read(4))[0] > 50:
            f.seek(-4, 1)

        f.seek(2, 1)
        header_size = unpack("h", f.read(2))[0] * 2
        f.seek(header_size, 1)

        t = []
        i = 0
        while True:
            print(f"\tParsing triangle section {i}")
            i += 1

            j = 0
            prev_tindex = 0
            final = True
            while True:
                print(f"\t\tParsing tripart {j}")
                j += 1

                tripart = self.parse_tripart(prev_tindex=prev_tindex)
                if (
                    tripart[0] is not None and tripart[1] is not None
                ):  # TODO: improve readability
                    t.append((tripart[0], tripart[1]))
                    prev_tindex = tripart[1]

                if tripart[3]:
                    final = True

                if tripart[2]:
                    break

            if final:  # FIXME: handle case where tripart = None
                break

        print("\tDone\n")
        self.triangles = t
        return t

    def parse_tripart(self, type="texture", prev_tindex=0):
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
            print(f"\t\t\t\tUsing prev tindex {prev_tindex}")
            material_list_index = prev_tindex

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
                return (None, None, True, True)
            else:
                print("\t\t\t\tESCAPE SYMBOL NOT FOUND IN SIMPLE TRIPART")
                f.seek(-4, 1)
                return (None, None, False, True)

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
        return (
            t,
            material_list_index,
            escape,
            final,
        )

    def write_vertices(self, file):
        f = validate_file_handle(file, usage="a+")

        verts = self.vertices
        if not verts:
            print("\tNo vertices found!")
            return None
        else:
            print(f"Writing {len(verts)} vertices to {f.name}")

        for v in verts:
            ln = f"v {v[0]} {v[1]} {v[2]}\n"
            f.write(ln)

    def write_triangles(self, file, matlist=None):
        f = validate_file_handle(file, usage="a+")

        triangles = self.triangles
        if not triangles:
            print("\tNo triangles found!")
            return None
        else:
            print(f"Writing {len(triangles)} triparts to {f.name}")

        # TODO: write non-texture materials
        # TODO: implement material writing
        # TODO: remove redundant code
        vt = 1
        for tp in triangles:
            if matlist is not None:
                ln = f"usemtl {matlist[tp[1]]}\n"
                f.write(ln)

            #            if tp[2] is False :
            for ts in tp[0]:
                for c in range(len(ts) - 2):
                    if c % 2 == 0:
                        ln = f"f {ts[c][0]}/{vt} {ts[c+1][0]}/{vt+1} {ts[c+2][0]}/{vt+2}\n"
                    else:
                        ln = f"f {ts[c+1][0]}/{vt+1} {ts[c][0]}/{vt} {ts[c+2][0]}/{vt+2}\n"

                    vt += 1
                    f.write(ln)
                vt += 2

    #            else :
    #                for ts in tp[0] :
    #                    for c in range(len(ts) - 2) :
    #                        if c % 2 == 0 :
    #                            ln = f'f {ts[c][0]} {ts[c+1][0]} {ts[c+2][0]}\n'
    #                        else :
    #                            ln = f'f {ts[c+1][0]} {ts[c][0]} {ts[c+2][0]}\n'
    #
    #                        f.write(ln)

    def write_texcoords(self, file):
        """
        Given an open file discriptor or path, write texture coordinates as indexes as they appear in the triangle array
        """
        f = validate_file_handle(file, usage="a+")
        triangles = self.triangles

        if not triangles:
            print("\tNo texcoords found!")
            return None

        # TODO: Clean up
        for tp in triangles:
            # if tp[2] is False :
            for ts in tp[0]:
                for c in ts:
                    vt = list(c[1:])
                    ln = f"vt {vt[0]} {vt[1]}\n"
                    f.write(ln)


def is_chunk(xbe, offset, section):
    """
    Probe the header and determine whether a block section exists. If offset is not the entry_offset of a Node or Chunk, behavior is undefined.
    """
    raw_offset = get_raw_address(offset, section, addresses=Chunk.section_table)
    xbe.seek(raw_offset + 4)  # skip entry
    block_pointer = unpack("I", xbe.read(4))[0]

    return block_pointer != 0
