# Blinx_rev: Reverse Engineering Notes

## Forward
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
0x0         u_int32         entry;          // chunk entry point
0x4         void*           block;          // pointer to chunk block
0x8         float32[9]      world;          // coordinates of chunk in current context
0x44        node*           left;           // pointer to left child (inherits coordinates)
0x48        node*           right;          // pointer to right child (same coordinate context)
        };
```

## Node types

### Pure
Superclass as defined above. The block pointer is blank, but still has an entry, coordinates, and may have children

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
Vertices are stored in a list called a __vertex list__. This list has a 16-byte header. At `0x6` in the header is the count, which defines the length of the list. The rest of the header is being actively researched, since character models have unique vertex list formats and different header values.

The list itself contains triples of floats that define x, y, and z coordinates for each vertex in the model. Each triple is delimited by 4 bytes. The usage of these 4 bytes is unknown and is ignored.

All vertex lists exit at the escape symbol `ff000000`

#### Triangle data

Triangles are stored as triangle strips, or tristrips. Each tristrip has a header short (int16) that defines the length of the the tristrip. The members of the strip are shorts that reference indexes of the chunk's associated vertex list. Some strips are "texture, where the members are short[3]s, and the two additional elements define texture coordinates.

Tristrips are stored in a list called a tripart. A tripart has a 10-byte header, much of which is unknown. All tristrips in an individual tripart share a texture defined in the header. This is the index of the resource in the __tree__'s associated __texture list__.

```
        struct tripart {
0x0         u_int16 short0;         // defines type
0x2         u_int16 texlist_index;  // defines the texture used in this tripart, if type is texture
0x4         u_int16 short2;         // usage unknown
0x6         u_int16 size;           // total size of tripart in shorts. Includes any padding.
0x8         u_int16 count;          // number of tristrips in tripart
        }
```
Triparts containing simple tristrips may have a different header, since there is no defined texture. However, the size and count are in the same location. This is currently unresearched.

The tripart list stores the triparts. It has a variable length header (the length defined at `0x2`). The usage of the symbols in the header are unknown, although the first two bytes probably define type. The header does not define the length of the tripart list (although some may?). Some chunks have multiple tripart lists.

All triangle data sections exit with the escape symbol `ff000000`.

## Model Tables
To load a full model, the program must be provided the offset of the __model tree__ root node and the offset of its associated __texture list__. In the .data section of the xbe, there are tables that define __models__, by associating these two offsets. 

There are multiple types of model tables, the specifics of each are still  not researched. Most model tables have at least one other pointer to simple geometry chunks. Some model tables also have an array of floats. The usage of this data is unknown and ignored. Two types of model table have currently been identified; map tables and object tables.

### The Map Table
At virtual offset `0x...` (near the top of the .data section), there exists the __map table__. This table is how map models are defined. It is ordered MAP11, MAP12, MAP13, MDLB1 (boss 1), MAP21, MAP22, etc. MAP71 - MDLB7 do not exist, and instead reference MAP11, and the texts is null. Each entry also contains an unknown pointer to simple geometry chunks. This table does not build all geometry in each associated map's section -- some maps' skyboxes are missing. Also, special geometry (such as the statue in MAP11 and anything referenced in the MDLR sections) are not present.  Some of this only appears in .text and extracting would be outside the current scope of pyBlinx.

### The Object Table
At virtual offset `0x...`, these exists the __object table__. This table is how assets that are reused across rounds are defined. Each entry is associated with an __object id__ int8. Each entry has many fields that are currently not researched, and each field is nullable -- even the geometry tree. This table mostly points to .data, but it also points to MDLEN for some reason. The geometry itself seems to be mostly interactive objects like trash, but also has some static objects like signposts. 
