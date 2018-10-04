# Blinx_rev: Reverse Engineering Notes

## Foreward
This is my first foray into reverse engineering. Information on data structures contained within the game’s files included in this document came from observing patterns in static binary data and drawing conclusions. I wrote it all in Python 3. Having never coded in Python in the past, it's been quite the learning experience. I used [XBEExplorer](http://dxbx-emu.com/information/xbeexplorer/) for virtual and raw addresses, [dexbe](http://www.theisozone.com/downloads/xbox/tools/dexbe-eur/) to extract section files, and [HxD](https://mh-nexus.de/en/hxd/) as a primary hex editor. I extend a warm thanks to everyone on the BLiNX Corps discord server for assisting research and helping along the way. My initial inspiration for this project was from following [JSRF Inside](http://jsrf-inside.blogspot.com/).

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

## Model Trees
The highest level self-contained structure for archiving 3d assets in Blinx found so far. A binary tree composed of __nodes__. Among other things, each __node__ defines coordinates and up to two children. The left child inherets the parent matrix, while the right child shares the parent's coordinate context. Always associated with its own __Texture List__.

## Texture Lists
A list of strings that define the external resources in the Media directory (texture). Each __Texture List__ is associated with a __Model Tree__. 

## Nodes
The individual nodes that populate a __Model Tree__. Every node contains a __header__ which contains metadata, coordinates, and pointers to children nodes. It also contains an __entry__ int32, which (possibly) defines its type, although my current implementation does not take this value into account. 

```
        struct header {

0x0        	u_int32         entry;          // chunk entry point
0x4        	void*           block;          // pointer to chunk block
0x8        	float32[9]      world;          // coordnates of chunk in current context
0x44        chunk*          left;           // pointer to left child (inherets coordinates)
0x48        chunk*          right;          // pointer to right child (same coordinate context)
        } chunk;
```

## Node types

### Pure
Superclass as defined above. The block pointer is blank, but still has an entry, coordnates, and may have children

### Chunks
Subclass of __node__ that holds 3d model data. All chunks have a __header__ with a valid pointer to a __block__, which has pointers to the __vertex data__ and __triangle data__. Non-standard chunks (such as character models) may not contain all regions of data, but do have the same offsets. Pointers to `NULL` are empty. 


```
		struct block {
0x0         vertex_list*    vlist;          // pointer to vertex data 
0x4         tripart_list*   tlist;          // pointer to triangle data
0x8         float32[6]      flist;          // unknown	
		}
```


#### Vertex data
Vertices are stored in a list called a __vertex list__. This list has a 16-byte header. At `0x6` in the header is the count, which defines the length of the list. The rest of the header is being activly researched, since character models have unique vertex list formats and different header values.

The list itself contains triples of floats that define x, y, and z coordinates for each vertex in the model. Each triple is delimited by 4 bytes. The usage of these 4 bytes is unknown and is ignored.

All vertex lists exit at the escape symbol `ff000000`

#### Triangle data

Triangles are stored as triangle strips, or tristrips. Each tristrip has a header short (int16) that defines the length of the the tristrip. The members of the strip are shorts that reference indexes of the chunk's associated vertex list. Some strips are "texture, where the members are short[3]s, and the two additional elements define texture coordinates.

Tristrips are stored in a list called a tripart. A tripart has a 10-byte header, much of which is unknown. All tristrips in an individual tripart share a texture defined in the header. This is the index of the resource in the __tree__'s associated __texture list__.

```
        struct tripart {
0x0         u_int16 short0;         // usage unknown
0x2         u_int16 texlist_index;  // defines the texture used in this tripart
0x4         u_int16 short2;         // usage unknown
0x6         u_int16 size;           // total size of tripart in shorts. Includes any padding.
0x8         u_int16 count;          // number of tristrips in tripart
        }
```
Triparts containing simple tristrips may have a different header, since there is no defined texture. However, the size and count are in the same location. This is currently unresearched.

The tripart list stores the triparts. It has a variable length header (defined at `0x2`). Most symbols in the header are unknown. The header does not define the length of the tripart list (although some may?). Some chunks have multiple tripart lists. This is currently unresearched.

All triangle data sections exit with the escape symbol `ff000000`.
