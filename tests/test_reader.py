import pytest
from PIL import Image

from readlif.reader import LifFile


def test_lif_file_with_file_path(valid_lif_filepath):
    lif_image = LifFile(valid_lif_filepath).get_image(0)
    # This should not raise an error.
    lif_image.get_frame(z=0, t=0, c=0)


def test_lif_file_with_file_buffer(valid_lif_filepath):
    with open(valid_lif_filepath, "rb") as file:
        lif_image = LifFile(file).get_image(0)
        # This should not raise an error.
        lif_image.get_frame(z=0, t=0, c=0)


def test_lif_file_with_non_lif_files(tmp_path, artifacts_dirpath):
    with open(tmp_path / "not-a-lif-file.txt", "w") as file:
        with pytest.raises(ValueError):
            LifFile(file)

    with pytest.raises(ValueError):
        LifFile(artifacts_dirpath / "misc" / "valid-tiff.tif")


def test_lif_file_with_single_image_lif(valid_single_image_lif_filepath):
    lif_file = LifFile(valid_single_image_lif_filepath)
    assert repr(lif_file) == "'LifFile object with 1 image'"
    assert len(lif_file.image_list) == 1
    with pytest.raises(ValueError):
        lif_file.get_image(1)


def test_lif_file_get_iter_image(valid_single_image_lif_filepath, valid_multi_image_lif_filepath):
    images = [image for image in LifFile(valid_single_image_lif_filepath).get_iter_image()]
    assert len(images) == 1

    images = [image for image in LifFile(valid_multi_image_lif_filepath).get_iter_image()]
    assert len(images) > 1


def test_lif_file_with_new_lasx(artifacts_dirpath):
    """
    TODO(KC): figure out what is special or "new" about the "new_lasx.lif" file.
    """
    lif_file = LifFile(artifacts_dirpath / "misc" / "new_lasx.lif")
    assert len(lif_file.image_list) == 1


def test_lif_image_get_frame_out_of_range_args(xyzt_example_lif_filepath):
    lif_image = LifFile(xyzt_example_lif_filepath).get_image(0)

    for dimension_kwarg, lif_image_attr in [
        ("z", "nz"),
        ("t", "nt"),
        ("c", "channels"),
        ("m", "n_mosaic"),
    ]:
        max_index_for_dimension = getattr(lif_image, lif_image_attr) - 1
        lif_image.get_frame(**{dimension_kwarg: max_index_for_dimension})
        with pytest.raises(ValueError):
            lif_image.get_frame(**{dimension_kwarg: max_index_for_dimension + 1})

    # TODO: use a better-justified out of range index for this test.
    with pytest.raises(ValueError):
        lif_image._get_item(100)


def test_lif_image_settings(xz_example_lif_filepath):
    """
    TODO: expand this test to cover more attributes and use more than one LIF file.
    """
    lif_image = LifFile(xz_example_lif_filepath).get_image(0)
    assert lif_image.settings["ObjectiveNumber"] == "11506353"


def test_lif_image_attributes(xyzt_example_lif_filepath):
    """
    TODO: expand this test to cover more attributes and use more than one LIF file.
    """
    lif_image = LifFile(xyzt_example_lif_filepath).get_image(0)
    assert lif_image.scale[0] == pytest.approx(9.8709062997224)
    assert lif_image.bit_depth[0] == 8


def test_lif_image_get_frame(xyzt_example_lif_filepath):
    lif_image = LifFile(xyzt_example_lif_filepath).get_image(0)
    czt_pairs = [[0, 0, 0], [0, 2, 0], [0, 2, 2], [1, 0, 0]]
    for c, z, t in czt_pairs:
        reference_image = Image.open(
            xyzt_example_lif_filepath.parent / "expected-outputs" / f"c{c}z{z}t{t}.tif"
        )
        lif_image_frame = lif_image.get_frame(z=z, t=t, c=c)
        assert lif_image_frame.tobytes() == reference_image.tobytes()


def test_lif_image_get_plane(xyzt_example_lif_filepath):
    """
    TODO: eliminate duplication with `test_lif_image_get_frame`.
    """
    lif_image = LifFile(xyzt_example_lif_filepath).get_image(0)
    czt_pairs = [[0, 0, 0], [0, 2, 0], [0, 2, 2], [1, 0, 0]]
    for c, z, t in czt_pairs:
        reference_image = Image.open(
            xyzt_example_lif_filepath.parent / "expected-outputs" / f"c{c}z{z}t{t}.tif"
        )
        lif_image_plane = lif_image.get_plane(c=c, requested_dims={3: z, 4: t})
        assert lif_image_plane.tobytes() == reference_image.tobytes()


def test_lif_image_get_plane_on_xz_image(xz_example_lif_filepath):
    lif_image = LifFile(xz_example_lif_filepath).get_image(0)
    for c, t in [(0, 0), (1, 8)]:
        reference_image = Image.open(
            xz_example_lif_filepath.parent / "expected-outputs" / f"c{c}t{t}.tif"
        )
        lif_image_plane = lif_image.get_plane(c=c, requested_dims={4: t})
        assert lif_image_plane.tobytes() == reference_image.tobytes()


def test_lif_image_get_plane_nonexistent_plane(artifacts_dirpath):
    """
    TODO: determine if another, less mysterious LIF file can be used for this test.
    """
    lif_image = LifFile(
        artifacts_dirpath / "misc" / "LeicaLASX_wavelength-sweep_example.lif"
    ).get_image(0)
    with pytest.raises(NotImplementedError):
        lif_image.get_plane(display_dims=(1, 5), c=0, requested_dims={2: 31})


def test_lif_image_repr(xyzt_example_lif_filepath):
    lif_image = LifFile(xyzt_example_lif_filepath).get_image(0)
    assert (
        repr(lif_image) == "'LifImage object with dimensions: Dims(x=1024, y=1024, z=3, t=3, m=1)'"
    )


def test_lif_image_get_iters(xyzt_example_lif_filepath):
    lif_image = LifFile(xyzt_example_lif_filepath).get_image(0)
    assert len([image for image in lif_image.get_iter_c()]) == 2
    assert len([image for image in lif_image.get_iter_t()]) == 3
    assert len([image for image in lif_image.get_iter_z()]) == 3
