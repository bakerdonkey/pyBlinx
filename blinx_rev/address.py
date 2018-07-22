import csv

#TODO: make a class to avoid redundant computation. Therefore, csv parsing only have to happen once.

def rawaddress(virtaddress, section) :
    '''
    Converts a virtual address to a raw address using Blinx's defined section offsets.
    '''
    rawaddress = -1
    with open('sectionaddress.csv', 'r') as csv_file :
        section_index = __section_index(section)
        assert(section_index is not None)
        
        sectionreader = csv.reader(csv_file)
        line = next((x for i, x in enumerate(sectionreader) if i == section_index), None)
        virtbase = int(line[1], 0)
        rawbase = int(line[2], 0)

        offset = virtaddress - virtbase
        rawaddress = rawbase + offset

        print('index ' + str(section_index))

    return rawaddress
         
#TODO: Make more pythonic. Use a generator or something clever.
def find_section(virtaddress) :
    '''
    Finds the section containg a virtual address.
    '''
    with open('sectionaddress.csv', 'r') as csv_file :
        reader = csv.reader(csv_file)
        line = next()



def __section_index(section) :
    candidate = section.upper()

    switcher = {}
    with open('sectionaddress.csv', 'r') as csv_file :
        
        reader = csv.reader(csv_file)
        next(reader)
        for c, line in enumerate(reader, 1) :
            switcher[line[0]] = c

    return switcher.get(candidate)
    


def main() :
    print(hex(rawaddress(0x1D8AC94, 'MAP11')))

if __name__ == '__main__' :
    main()