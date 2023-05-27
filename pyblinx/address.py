import csv

from pyblinx.exceptions import RawAddressException


# TODO: use a singleton or global variable, only run this code once!
def get_section_address_mapping():
    addresses = {}
    with open('data/sectionaddress.csv', 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # skip header
        for line in reader:
            base_virtual_address = int(line[1], 16)
            base_raw_address = int(line[2], 16)
            section_size = int(line[3], 16)
            addresses[line[0]] = (
                base_virtual_address,
                base_raw_address,
                section_size,
            )  # TODO; use a dict not a tuple!

    return addresses


def get_raw_address(virtual_address: int, section: str, addresses: dict = None) -> int:
    """
    Converts a virtual address to a raw address for a given section.
    """
    # TODO: remove `addresses` param when global access to `section_address_mapping`` is available.
    # `addresses` is never expected to be anything different after all!
    section_address_map = addresses or get_section_address_mapping()
    base_addresses = section_address_map.get(section)
    if not base_addresses:
        raise RawAddressException(
            f'BaseAddresses not found for section {section}. Is section correct?',
            section=section,
        )

    base_virtual_address = base_addresses[0]
    base_raw_address = base_addresses[1]
    section_size = base_addresses[2]

    offset = virtual_address - base_virtual_address
    # if offset > section_size:
    #     raise RawAddressException(
    #         f'Virtual address {hex(virtual_address)} not in section {section}. offset: {hex(offset)} > section_size: {hex(section_size)}',
    #         section=section,
    #         virtual_address=virtual_address
    #     )
    return offset + base_raw_address


def get_virtual_address(raw_address: int, section: str, addresses: dict = None) -> int:
    """
    Converts a raw address to a virtual address for a given section.
    """
    section_address_map = addresses or get_section_address_mapping()
    base_addresses = section_address_map.get(section)
    if not base_addresses:
        raise RawAddressException(
            f'BaseAddresses not found for section {section}. Is section correct?',
            section=section,
        )

    base_virtual_address = base_addresses[0]
    base_raw_address = base_addresses[1]

    return raw_address - base_raw_address + base_virtual_address


def find_section(virtual_address, section='DATA'):
    """
    Returns the section of a given virtual address.
    """
    with open('data/sectionaddress.csv', 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        for line in reader:
            base = int(line[1], 16)
            size = int(line[3], 16)
            if virtual_address > base and virtual_address < (base + size):
                section = line[0]

    return section
