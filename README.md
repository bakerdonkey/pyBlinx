# Blinx Rev
Work towards extracting assets and data from Blinx: The Time Sweeper. In its current phase, the goal of the project is to extract 3d assets from the game's binary and store them as .obj files. Information on patterns and format is available in the wiki, which will be updated as research progresses. Requires Python 3.5+.

### Getting Started
The project is currently experimental and requires extremely specific usage to provide meaningful results. This setup is prone to simplify as research is conducted and implemented.

All 3d assets are contained in Blinx's xbe. Use [XBE Explorer](https://sourceforge.net/projects/dxbx/files/XBE%20Explorer/) to find the proper sections. Everything after .data and before DOLBY is potential asset data.

Once you choose a section, look for a chunk that represents a model. Chunks have two parts, a triangle list and a vertex list. All elements of the triangle list are 16-bit ints, while elements of the vertex list are 32-bit floats.


#### Mode
The project has two modes -- chunk=0, vert/tri=1. 

### Chunk Mode
3d assets in Blinx are stored in self-contained regions of data called chunks. There are a few different types, but they all have three fundimental parts: The Tripart list, the Vertex List, and the Footer.

Seperate a chunk from the xbe, store in a file. If the file does not contain Vertex list and Tripart list pointers, offsets must be input.

### Vert/Tri Mode (currently bugged)
Seperate the vertex list and tripart list from the same chunk of the xbe into files.


#### Chunk Header
Usually 0x80 (128) bytes long. Contains addresses, floats, and other unknown values. The first 8 bytes define the (virtual) offset of the previous chunk.

### Disclaimer
The development of these tools is purely experimental and educational. All research is conducted on legally-obtained games and with publicly-available information. 
