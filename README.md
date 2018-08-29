# Blinx Rev
A tool for extracting 3d assets from BLiNX: The Time Sweeper. Information on patterns and format is available in `./docs`, which will be updated as research progresses. Requires Python 3.5+.

### Getting Started
To extract an asset, you will need:
- A legal, non-platinum hits, NTSC-U<sup>1</sup> copy of BLiNX: The Time Sweeper (MS-019 v1.05).
- The virtual address of the asset's geometry
- The virtual address of the asset's texture references
- The name of the section<sup>2</sup> the asset is contained within

<sup>1.</sup> Other versions have not been tested and are not explicitly supported.

<sup>2.</sup> All assets are in sections of default.xbe. Use [XBE Explorer](https://sourceforge.net/projects/dxbx/files/XBE%20Explorer/) to find the section names, locations, and sizes.

#### Usage
```
python blinx_rev -co GEOMETRY_ADDRESS -so TEXTURE_ADDRESS -s SECTION
```
Use `--help` for full definitions of arguments.

Sample geometry and texture addresses are in `./data/entries.csv`. Blinx_rev does not currently support extracting character models.

### Disclaimer
The intention of this project is experimental and educational. All research is conducted on legally obtained software and with publicly available information. 
