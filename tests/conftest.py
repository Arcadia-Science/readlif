import pathlib

import pytest


@pytest.fixture
def artifacts_dirpath():
    return pathlib.Path(__file__).parent / "artifacts"


@pytest.fixture
def valid_lif_filepath(artifacts_dirpath):
    """
    The filepath to a LIF file that is valid and can be read by the reader.
    """
    return artifacts_dirpath / "misc" / "new_lasx.lif"


@pytest.fixture
def valid_single_image_lif_filepath(artifacts_dirpath):
    """
    The filepath to a LIF file that contains only one image.
    """
    return artifacts_dirpath / "xyzt-example" / "xyzt-example.lif"


@pytest.fixture
def valid_multi_image_lif_filepath(artifacts_dirpath):
    """
    The filepath to a LIF file that contains multiple images.
    """
    return artifacts_dirpath / "xz-example" / "xz-example.lif"


@pytest.fixture
def valid_tiff_filepath(artifacts_dirpath):
    """
    The filepath to a TIFF file that is valid.
    """
    return artifacts_dirpath / "misc" / "valid-tiff.tif"


@pytest.fixture
def xyzt_example_lif_filepath(artifacts_dirpath):
    """
    The filepath to a LIF file that contains XYZT data.
    """
    return artifacts_dirpath / "xyzt-example" / "xyzt-example.lif"


@pytest.fixture
def xz_example_lif_filepath(artifacts_dirpath):
    """
    The filepath to a LIF file that contains an image in which the second dimension
    is Z rather than Y.
    """
    return artifacts_dirpath / "xz-example" / "xz-example.lif"
