import csv

# TODO: make this a class or singleton or something? try to avoid opening and closing that file a million times.
def get_section_address_mapping():
    addresses = {}
    with open("data/sectionaddress.csv", "r") as csv_file:
        reader = csv.reader(csv_file)
        next(reader) # skip header
        for line in reader:
            base_virtual_address = int(line[1], 16)
            base_raw_address = int(line[2], 16)
            addresses[line[0]] = (base_virtual_address, base_raw_address)  # TODO; use a dict not a tuple!

    return addresses


def get_raw_address(virtual_address, section, addresses=None):
    """
    Converts a virtual address to a raw address for a given section.
    """
    section_address_map = addresses or get_section_address_mapping()
    base_addresses = section_address_map.get(section)
    if not base_addresses:
        raise RuntimeError(f'BaseAddresses not found for section {section}. Is section correct?')      

    base_virtual_address = base_addresses[0]
    base_raw_address = base_addresses[1]

    # TODO: use section size to validate this arithmetic and fail faster
    return virtual_address - base_virtual_address + base_raw_address


def get_virtual_address(raw_address, section, addresses=None):
    """
    Converts a raw address to a virtual address for a given section.
    """
    section_address_map = addresses or get_section_address_mapping()
    base_addresses = section_address_map.get(section)
    if not base_addresses:
        raise RuntimeError(f'BaseAddresses not found for section {section}. Is section correct?')

    base_virtual_address = base_addresses[0]
    base_raw_address = base_addresses[1]

    return raw_address - base_raw_address + base_virtual_address


def find_section(virtual_address, section="DATA"):
    """
    Returns the section of a given virtual address.
    """
    with open("data/sectionaddress.csv", "r") as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        for line in reader:
            base = int(line[1], 16)
            size = int(line[3], 16)
            if virtual_address > base and virtual_address < (base + size):
                section = line[0]

    return section
