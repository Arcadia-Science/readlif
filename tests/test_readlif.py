import pathlib

import pytest
from PIL import Image

from readlif.reader import LifFile
from readlif.utilities import get_xml

ARTIFACTS_DIRPATH = pathlib.Path(__file__).parent / "artifacts"
TIFF_FILES_DIRPATH = ARTIFACTS_DIRPATH / "tiff-files"
LIF_FILES_DIRPATH = ARTIFACTS_DIRPATH / "lif-files"


def test_image_loading():
    test_array = [[0, 0, 0], [0, 2, 0], [0, 2, 2], [1, 0, 0]]
    for i in test_array:
        c = str(i[0])
        z = str(i[1])
        t = str(i[2])
        ref = Image.open(TIFF_FILES_DIRPATH / f"c{c}z{z}t{t}.tif")
        obj = LifFile(LIF_FILES_DIRPATH / "xyzt_test.lif").get_image(0)
        test = obj.get_frame(z=z, t=t, c=c)
        assert test.tobytes() == ref.tobytes()


def test_image_loading_from_buffer():
    test_array = [[0, 0, 0], [0, 2, 0], [0, 2, 2], [1, 0, 0]]
    for i in test_array:
        c = str(i[0])
        z = str(i[1])
        t = str(i[2])
        ref = Image.open(TIFF_FILES_DIRPATH / f"c{c}z{z}t{t}.tif")

        with open(LIF_FILES_DIRPATH / "xyzt_test.lif", "rb") as open_f:
            obj = LifFile(open_f).get_image(0)
            test = obj.get_frame(z=z, t=t, c=c)
            assert test.tobytes() == ref.tobytes()


def test_xml_header():
    _, test = get_xml(LIF_FILES_DIRPATH / "xyzt_test.lif")
    assert test[:50] == '<LMSDataContainerHeader Version="2"><Element Name='


def test_iterators():
    images = [i for i in LifFile(LIF_FILES_DIRPATH / "xyzt_test.lif").get_iter_image()]
    assert len(images) == 1

    obj = LifFile(LIF_FILES_DIRPATH / "xyzt_test.lif").get_image(0)
    assert repr(obj) == "'LifImage object with dimensions: Dims(x=1024, y=1024, z=3, t=3, m=1)'"

    c_list = [i for i in obj.get_iter_c()]
    assert len(c_list) == 2

    t_list = [i for i in obj.get_iter_t()]
    assert len(t_list) == 3

    z_list = [i for i in obj.get_iter_z()]
    assert len(z_list) == 3


def test_not_lif_file():
    with pytest.raises(ValueError):
        LifFile(TIFF_FILES_DIRPATH / "c0z0t0.tif")


def test_not_that_many_images():
    obj = LifFile(LIF_FILES_DIRPATH / "xyzt_test.lif")
    assert repr(obj) == "'LifFile object with 1 image'"

    with pytest.raises(ValueError):
        obj.get_image(10)

    image = obj.get_image(0)
    with pytest.raises(ValueError):
        image.get_frame(z=10, t=0, c=0)

    with pytest.raises(ValueError):
        image.get_frame(z=0, t=10, c=0)

    with pytest.raises(ValueError):
        image.get_frame(z=0, t=0, c=10)

    with pytest.raises(ValueError):
        image.get_frame(z=0, t=0, c=0, m=10)

    with pytest.raises(ValueError):
        image._get_item(100)


def test_scale():
    obj = LifFile(LIF_FILES_DIRPATH / "xyzt_test.lif").get_image(0)
    assert obj.scale[0] == pytest.approx(9.8709062997224)


def test_depth():
    obj = LifFile(LIF_FILES_DIRPATH / "xyzt_test.lif").get_image(0)
    assert obj.bit_depth[0] == 8


def test_get_plane_on_normal_img():
    # order = c, z, t
    test_array = [[0, 0, 0], [0, 2, 0], [0, 2, 2], [1, 0, 0]]
    for i in test_array:
        c = str(i[0])
        z = str(i[1])
        t = str(i[2])
        ref = Image.open(TIFF_FILES_DIRPATH / f"c{c}z{z}t{t}.tif")

        obj = LifFile(LIF_FILES_DIRPATH / "xyzt_test.lif").get_image(0)
        # 3: z
        # 4: t
        test = obj.get_plane(c=c, requested_dims={3: z, 4: t})
        assert test.tobytes() == ref.tobytes()


def test_get_plane_on_xz_img():
    ref = Image.open(TIFF_FILES_DIRPATH / "xz_c0_t0.tif")
    obj = LifFile(LIF_FILES_DIRPATH / "testdata_2channel_xz.lif").get_image(0)
    test = obj.get_plane(c=0, requested_dims={4: 0})
    assert test.tobytes() == ref.tobytes()

    ref2 = Image.open(TIFF_FILES_DIRPATH / "xz_c1_t8.tif")
    # 3: z
    # 4: t
    test2 = obj.get_plane(c=1, requested_dims={4: 8})
    assert test2.tobytes() == ref2.tobytes()


def test_arbitrary_plane_on_xzt_img():
    obj = LifFile(LIF_FILES_DIRPATH / "LeicaLASX_wavelength-sweep_example.lif").get_image(0)
    with pytest.raises(NotImplementedError):
        obj.get_plane(display_dims=(1, 5), c=0, requested_dims={2: 31})


def test_new_lasx():
    obj = LifFile(LIF_FILES_DIRPATH / "new_lasx.lif")
    assert len(obj.image_list) == 1


def test_settings():
    obj = LifFile(LIF_FILES_DIRPATH / "testdata_2channel_xz.lif").get_image(0)
    assert obj.settings["ObjectiveNumber"] == "11506353"
