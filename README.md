# pyBlinx
A tool for extracting 3d assets from BLiNX: The Time Sweeper. Information on patterns and format is available in `./docs`, which will be updated as research progresses.

This tool is still in early development, contact me directly if you need any help!

## Getting Started
Dependencies are managed through pipenv. I recommend using pyenv to manage environment versions.
```
pip install pipenv
```

To extract an asset, you will need:
- NTSC-U, "black box" (not Platinum Hits) copy of BLiNX: The Time Sweeper (MS-019 v1.05) default.xbe file
- The object index of the model you wish to extract

## Usage
```
pipenv run python run.py [action] [mode]
```
All geometry is stored in a Tree structure, composed of Nodes, some of which are Chunks. pyBlinx can read the structure of these Trees, parse their geometry, and write it out to .obj files. This behavior is driven by the `action` argument:
- `peek` reads the tree (only for debug)
- `parse` reads the tree and parses its geometry into memory (only for debug)
- `extract` (_recommended_) reads the tree, parses its geometry, and writes it out to file

Blinx stores a list of these Trees as big lists in its code. There are two of these lists. pyBlinx can parse the list given a `mode`:
- `map` (_recommended_) can extract maps (stages)
    - use `--section` to select the map. ex `MAP11` => Round 1, Stage 1. Otherwise pyBlinx will attempt to extract all maps.
- `prop` can extract props, such as Trash, Time Crystals, etc.
    - this is still under construction and doesn't really work currently :(
- `custom` can extract any arbitrary Tree (only for debug)
    - provide `--chunk_offset` with (virtual) address of Tree root trunk
    - optionally provide `--material_list_offset` to extract the material library for the Tree

Example: Extract Round 1 Stage 1 and put output in a directory `../out`
```
python run.py extract map --section MAP11 -o `../out`
```

Example: Extract a Tree with materials at given addresses
```
python run.py extract custom --chunk_offset 0x21fbdc8 --material_list_offset 0x20aa500 --verbose
```

Use `--help` for full definitions of arguments. Check `./docs` for information on how to find addresses and how to calculate virtual addresses

__pyBlinx does not currently support extracting character models or untextured geometry!__


## Examples

![16 Ton](https://s15.postimg.cc/ot5s9pqwr/16ton_tex.png)
![arrow](https://s15.postimg.cc/ydugtg723/arrow_signs.png)
![map11](https://s15.postimg.cc/p628cks8b/untitled.png)
