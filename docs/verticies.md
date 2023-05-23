# Verticies
__(wip)__

Vertices for simple meshes are stored in a vertex list. Lists have two parts, a header and the list itself.

The header is 16-bytes long. Bytes 0 - 6 are unknown. Offset 6 defines a short with the length of the list. The rest is padded with 0s.

Lists are composed of 16-byte lines, each containing 3 32-bit floats and a 32-bit delimiter. This fourth delimiting value is currently unknown. The three floats denote 3d coordinates for each vertex.

The structure terminates with the escape symbol `0xff000000`.
