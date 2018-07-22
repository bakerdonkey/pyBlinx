import csv

#TODO: make a class to avoid redundant computation. Therefore, csv parsing only have to happen once.

def section_addresses() :
    addresses = {}
    with open('data/sectionaddress.csv', 'r') as csv_file :
        sectionreader = csv.reader(csv_file)
        next(sectionreader)
        for line in sectionreader :
            addresses[line[0]] = (int(line[1], 16), int(line[2], 16))
    return addresses

def rawaddress(virtaddress, section) :
    '''
    Converts a virtual address to a raw address using Blinx's defined section offsets.
    '''
    rawaddress = -1
    with open('data/sectionaddress.csv', 'r') as csv_file :
        section_index = __section_index(section)
        assert(section_index is not None)
        
        sectionreader = csv.reader(csv_file)
        line = next((x for i, x in enumerate(sectionreader) if i == section_index), None)
        virtbase = int(line[1], 16)
        rawbase = int(line[2], 16)

        offset = virtaddress - virtbase
        rawaddress = rawbase + offset

        print('index ' + str(section_index))

    return rawaddress
         
#TODO: Make more pythonic. Use a generator or something clever.
def find_section(virtaddress) :
    '''
    Finds the section containg a virtual address.
    '''
    with open('data/sectionaddress.csv', 'r') as csv_file :
        reader = csv.reader(csv_file)
        line = next()
        #TODO: finish


def __section_index(section) :
    candidate = section.upper()

    switcher = {}
    with open('data/sectionaddress.csv', 'r') as csv_file :
        
        reader = csv.reader(csv_file)
        next(reader)            #skip header
        for c, line in enumerate(reader, 1) :
            switcher[line[0]] = c

    return switcher.get(candidate)
    