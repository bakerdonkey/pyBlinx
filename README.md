# pyBlinx
A tool for extracting 3d assets from BLiNX: The Time Sweeper. Information on patterns and format is available in `./docs`, which will be updated as research progresses. Requires Python 3.5+.

This tool is still in early development, and this document may become outdated as the interface is designed and implemented. Contact me directly if you need any help!

### Getting Started
To extract an asset, you will need:
- A legal, non-platinum hits, NTSC-U<sup>1</sup> copy of BLiNX: The Time Sweeper (MS-019 v1.05).
- The object index <sup>2.</sup> of the model you wish to extract.

<sup>1.</sup> Other versions have not been tested and are not explicitly supported.
<sup>2.</sup> Currently only supports map models. Indices as follows: MAP11 -> 1, MAP12 -> 2, MAP13 -> 3 BOSS1 -> 4, MAP21 -> 3, etc.
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

### Disclaimer
The intention of this project is experimental and educational. All research is conducted on legally obtained software and with publicly available information. 
