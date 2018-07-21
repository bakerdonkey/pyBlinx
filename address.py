import csv

def rawaddress(virtaddress, section) :
    '''
    Converts a virtual address to a raw address using Blinx's defined section offsets.
    '''
    rawaddress = -1
    with open('sectionaddress.csv', 'r') as f :

        section_index = __section_index(section)
        assert(section_index is not None)
        
        sectionreader = csv.reader(f, delimiter=',')
        line = next((x for i, x in enumerate(sectionreader) if i == section_index), None)
        virtbase = int(line[1], 0)
        rawbase = int(line[2], 0)

        offset = virtaddress - virtbase
        rawaddress = rawbase + offset
    
    return rawaddress
         


def __section_index(section) :
    candidate = section.upper()
    switcher = {
        'RDATA': 1,
        'DATA': 2,
        'MDLPL': 3,
        'MDLB1': 4,
        'MDLB10': 5,
        'MDLB2': 6,
        'MDLB3': 7, 
        'MDLB4': 8,
        'MDLB5': 9,
        'MDLB6': 10,
        'MDLB8': 11,
        'MDLB9': 12,
        'MDLEN': 13,
        'MDLB102': 14,
        'MAP13': 15,
        'MAP12': 16,
        'MAP11': 17,
        'MDLR2': 18,
        'MAP23': 19,
        'MAP22': 20,
        'MAP21': 21,
        'MAP33': 22,
        'MAP32': 23,
        'MAP31': 24,
        'MDLR4': 25,
        'MAP43': 26,
        'MAP42': 27,
        'MAP41': 28,
        'MDLR5': 29,
        'MAP53': 30,
        'MAP52': 31,
        'MAP51': 32,
        'MDLR6': 33,
        'MAP63': 34,
        'MAP62': 35,
        'MAP61': 36,
        'MDLR8': 37,
        'MAP83': 38,
        'MAP82': 39,
        'MAP81': 40,
        'MDLR9': 41,
        'MAP93': 42,
        'MAP92': 43,
        'MAP91': 44
    }
    return switcher.get(candidate)
    
def main() :
    print(hex(rawaddress(0x1D8AC94, 'MAP11')))

if __name__ == '__main__' :
    main()