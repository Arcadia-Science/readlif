from readlif.utilities import get_xml


def test_get_xml_header(xyzt_example_lif_filepath):
    _, test = get_xml(xyzt_example_lif_filepath)
    assert test.startswith('<LMSDataContainerHeader Version="2">')
