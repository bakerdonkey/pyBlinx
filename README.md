# pyBlinx
A tool for extracting 3d assets from BLiNX: The Time Sweeper. Information on patterns and format is available in `./docs`, which will be updated as research progresses. Requires Python 3.5+.

This tool is still in early development, and this document may become outdated as the interface is designed and implemented. Contact me directly if you need any help!

### Getting Started
To extract an asset, you will need:
- NTSC-U, "black box" (not Platinum Hits) copy of BLiNX: The Time Sweeper (MS-019 v1.05)
- The object index of the model you wish to extract

#### Usage
```
python run.py -mi MODEL_INDEX
```
Use `--help` for full definitions of arguments. Check `./docs` for information on how to find addresses and how to calculate virtual addresses

Sample geometry and texture addresses are in `./data/entries.csv`. pyBlinx does not currently support extracting character models.

### Examples

![16 Ton](https://s15.postimg.cc/ot5s9pqwr/16ton_tex.png)
![arrow](https://s15.postimg.cc/ydugtg723/arrow_signs.png)
![map11](https://s15.postimg.cc/p628cks8b/untitled.png)
