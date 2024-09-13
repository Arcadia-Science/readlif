import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from readlif.reader import _check_magic, _check_mem, _read_int


def get_xml(filename):
    """
    Given a lif file, returns two values (xml_root, xml_header) where
    xml_root is an ElementTree root, and xml_header is the text.

    This is useful for debugging.

    Some private functions are used from readlif.reader.

    Args:
        filename (string): what file to open?
    """
    f = open(filename, "rb")
    _check_magic(f)  # read 4 byte, check for magic bytes
    f.seek(8)
    _check_mem(f)  # read 1 byte, check for memory byte

    header_len = _read_int(f)  # length of the xml header
    xml_header = f.read(header_len * 2).decode("utf-16")
    xml_root = ET.fromstring(xml_header)
    f.close()
    return xml_root, xml_header


def get_image_xml(filename, image_name):
    """Get a chunk of xml data corresponding to a particular image within a lif file."""
    _, xml_header = get_xml(filename)
    xml_data = BeautifulSoup(xml_header, "lxml")

    # get chunk of xml data corresponding to the given image name
    xml_chunk = None
    for element in xml_data.find_all("element"):
        if element["name"] == image_name:
            xml_chunk = element

    if xml_chunk is None:
        raise ValueError(f"'{image_name}' not found in xml header.")

    return xml_chunk


def get_laser_data(filename, image_name):
    """Parse lif file for laser data from a particular image acquisition."""
    # get chunk of xml data corresponding to an acquisition using a laser
    laser_xml_data = get_image_xml(filename, image_name)

    # parse xml chunk for data corresponding to the laser
    laser_data = []
    for laser_values in laser_xml_data.find_all("laservalues"):
        laser_data.append(laser_values.attrs)

    return laser_data
