# Blinx_rev: Reverse Engineering Notes

## Foreward
This is my first foray into reverse engineering. Information on data structures contained within the game’s files included in this document came from observing patterns in static binary data and drawing conclusions. I wrote it all in Python 3. Having never coded in Python in the past, it's been quite the learning experience. I used [XBEExplorer](http://dxbx-emu.com/information/xbeexplorer/) for virtual and raw addresses, [dexbe](http://www.theisozone.com/downloads/xbox/tools/dexbe-eur/) to extract section files, and [HxD](https://mh-nexus.de/en/hxd/) as a primary hex editor. I extend a warm thanks to everyone on the BLiNX Corps discord server for assisting research and helping along the way. My initial inspiration for this project came from [JSRF Inside](http://jsrf-inside.blogspot.com/).

## Definitions
* __xbe__ - refers to default.xbe, the main executable
* __Media directory__ - (BLINX)/Media. Contains .dds texture files among other data
* __Section__ - a section of the xbe as defined in the xbe's header. Addresses can be accessed in XBEExplorer.

### Quick note about pointers
All addresses in the xbe can be represented as virtual and raw addresses. All sections have base virtual and a base raw addresses. All pointers are in terms of virtual addresses, while raw addresses are the actual offsets in the xbe. Therefore, to follow a pointer, you must know the section of the pointer’s destination and calculate the raw address.

`raw_pointer = (pointer - base_virtualaddress) + base_rawaddress`

where `base_virtualaddress` and `base_rawaddress` are the base addresses for the pointer’s destination’s section. 

For example:

`pointer = DEFF74`

which is an address in MDLB1. Thus,

`base_virtualaddress = D80280`

`base_rawaddress = 239A000`

therefore,

`raw_pointer = 2409CF4`

## Chunks
A structure that contains information about a 3d model. All chunks have a __header__, which often contains pointers to the __vertex data__ and __triangle data__. Non-standard chunks (such as character models) may not explicitly follow this definition.

### Header
A 84-byte region of data that provides all the data the game needs to assemble the chunk as a 3d model.

```
        struct header {
0x0         vertex_list*    vlist;          // pointer to vertex data (virtual address)
0x4         tripart_list*   tlist;          // pointer to triangle data (virtual address)
0x8         float32[6]      flist;          // usage unknown
0x32        u_int32         entry;          // chunk entry point
0x36        void*           top;            // address of the top of the header [1]
0x40        float32[9]      world;          // locrotscale of whole chunk
0x76        chunk*          clist_ptr_0;    // points to head of local chunklist
0x80        chunk*          clist_ptr_1;    // points to next chunklist
        } chunk;
```
<sup>1.</sup> The existence of this pointer and the fact the entry point is not the top of the structure provide reason to believe this defines two structures. This is consistent with chunklists, which do not have vlist, tlist, or flists, and their top pointer is null. However, my implementation still follows the model defined above, but may change in the future.

#### Entry

A pointer to a chunk points to the chunk's __entry__ int. This is probably a DWORD that holds flags, but my implementation considers it as an int. The value of __entry__ defines the type of the chunk. Most values are not researched yet. 

* __06__ - control chunk, a standard chunk that is the head of a local chunklist and points to the next chunklist
* __16__ - member chunk, a standard chunk that is a member of a chunklist
* __17__ - atomic chunk, a standard chunk that is is not a member of any chunklist structures
* __0f__ - chunklist header, not a chunk (by current model), but points to chunks and chunklists

### Vertex data
Vertices are stored in a list called a __vertex list__. This list has a 16-byte header. At `0x6` in the header is the count, which defines the length of the list.

The list itself contains triples of floats that define x, y, and z coordinates for each vertex in the model. Each triple is delimited by 4 bytes. The usage of these 4 bytes is unknown and is ignored.

All vertex lists exit at the escape symbol `ff000000`

### Triangle data

Triangles are stored as triangle strips, or tristrips. Each tristrip has a header short (int16) that defines the length of the the tristrip. The members of the strip are shorts that reference indexes of the chunk's associated vertex list. Some strips are "complex", where the members are short[3]s, and the two additional elements define texture coordinates.

Tristrips are stored in a list called a tripart. A tripart has a 10-byte header, much of which is unknown. All tristrips in an individual tripart share a texture defined in the header.

```
        struct tripart {
0x0         u_int16 short0;         // usage unknown
0x2         u_int16 texlist_index;  // defines the texture used in this tripart
0x4         u_int16 short2;         // usage unknown
0x6         u_int16 size;           // total size of tripart in shorts. Includes any padding.
0x8         u_int16 count;          // number of tristrips in tripart
        }
```
Triparts containing simple tristrips may have a different header, since there is no defined texture. However, the size and count are in the same location.

The tripart list stores the triparts. It has a variable length header (defined in short at 0x2). Most symbols in the header are unknown. The header does not define the length of the tripart list. Some chunks have multiple tripart lists, but the reason is unknown.

All triangle data sections exit with the escape symbol `ff000000`.
