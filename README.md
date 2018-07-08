# Blinx Rev
Work towards extracting assets and data from Blinx: The Time Sweeper. In its current phase, the goal of the project is to extract 3d assets from the game's binary and store them as .obj files. Information on patterns and format is available in the wiki, which will be updated as research progresses. Requires Python 3.5+.

### Getting Started
The project is currently experimental and requires extremely specific usage to provide meaningful results. This setup is prone to simplify as research is conducted and implemented.

All 3d assets are contained in Blinx's xbe. Use [XBE Explorer](https://sourceforge.net/projects/dxbx/files/XBE%20Explorer/) to find the proper sections. Everything after .data and before DOLBY is potential asset data.

### Mode
The project has two modes -- chunk=0, vert/tri=1. 

#### Chunk Mode
3d assets in Blinx are stored in self-contained regions of data called chunks. There are a few different types, but they all have three fundimental parts: The Tripart list, the Vertex List, and the Footer.

Seperate a chunk from the xbe, store in a file, and load in with this mode. If the file does not contain Vertex list and Tripart list pointers, offsets must be input. The exact definition of a chunk changes as the development process continues.

#### Vert/Tri Mode *(currently bugged - will fix asap)*

Seperate the vertex list and tripart list from the same chunk of the xbe into files and load in. Tripart lists have a 12-byte header, where offset 4 is `b2b2b2ff` and offset 8 is usually `7f7f7fff`. They terminate terminate with escape symbol `ff000000`. Vertex lists have a 16-byte header. They terminate with `ff000000`.


### Disclaimer
The development of these tools is purely experimental and educational. All research is conducted on legally-obtained games and with publicly-available information. 
