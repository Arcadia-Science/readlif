from readlif.reader import _check_magic, _check_mem, _read_int
import xml.etree.ElementTree as ET


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


# Todo: dump_lif('outdir') function
