# Definitions:
__xbe__ - Xbox executable format. More info [here](http://xboxdevwiki.net/Xbe). This contains most of Blinx's geometry asset data.

__Data Section__ - Sections of the xbe that only contain asset data.

__Chunk__ - A region of data containing vertex data, triangle data, and metadata. There are different types of chunks, however all contain at least three distinct data fields:
* __Tripart List__ - Every model contains a list of one or more __triparts__. Has its own header that (sometimes) defines the number of triparts.
  * __Tripart__ - A structure that defines a section of the model that shares a single texture. A tripart has a header and a list of __tristrips__. The header defines the number of tristrips.
  * __Tristrip__ - A structure that has a short int defining its length and a list of short ints defining a [triangle strip](https://en.wikipedia.org/wiki/Triangle_strip).

* __Vertex List__ - A region that contains all usable vertex data for the model defined by the chunk. Has a header and an array of vertex structures. The header is 16 bytes and contains the number of vertices and some other unknown data. The vertex list is composed of 16-byte vertex structures.
  * __Vertex structure__- Three 4-byte floats and a 4-byte unknown value.

* __Footer__ - Contains pointers and floats. This is likely metadata for the model in the chunk.

__String list__ - a region of data with at list of 32-byte strings with names of texture files in the `./Media` folder. They also contain a pointer to the top of the list and a short defining the length of the list. All chunks following a string list with texture coordinates use the texture files defined in the list.
