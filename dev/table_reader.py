from struct import unpack
from struct import pack
from argparse import ArgumentParser
from tkinter import filedialog
from tkinter import Tk
import csv

def tk_load_bin() :
    Tk().withdraw()
    in_path = filedialog.askopenfilename(initialdir='../../blinx/bin/data', title="Select Section file")
    return in_path

def section_addresses() :
    with open('../data/sectionaddress.csv', 'r') as csv_file :
        sectionreader = csv.reader(csv_file)
        next(sectionreader)
        addresses = {line[0] : (int(line[1], 16), int(line[2], 16)) for line in sectionreader}
    return addresses

parser = ArgumentParser()
parser.add_argument('offset', type=lambda x: int(x,16))
parser.add_argument('-i', '--iterations', type=int)
parser.add_argument('-s', '--section', type=str)
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()


addresses = section_addresses()
base_address = 0
section = ''
if args.section :
    section = args.section
    base_address = addresses[section][0]

offset = args.offset
iterations = args.iterations if args.iterations else 120
path = tk_load_bin()
pointer_list = []
with open(path, 'rb') as f:
    # [(little endian representation, section-specific offset),...]
    
    raw_pointer = 0
    f.seek(offset)
    for i in range(iterations):
        raw_pointer = unpack('I', f.read(4))[0]

        local_offset_c = raw_pointer - base_address if raw_pointer - base_address >= 0 else 0
        local_offset = hex(local_offset_c)

        

        li_pointer = hex(unpack( '<I', pack('>I', raw_pointer))[0])
        #li_pointer = hex(raw_pointer)
        pointer_list.append((li_pointer, local_offset,))

with open(f'./{hex(offset)}_{section}.txt', 'w+') as w :
    i=0
    for ptr in pointer_list:
        if i % 8 == 0 and args.verbose :
            w.write('---------------------------\n')
        w.write(f'{ptr[0]}\t{ptr[1]}\n')
        i+=1