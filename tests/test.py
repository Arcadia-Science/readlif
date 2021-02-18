import unittest
import os
from readlif.reader import LifFile
from readlif.utilities import get_xml
from PIL import Image

# Todo: Test a truncated image


def downloadPrivateFile(filename):
    import requests
    pwd = os.environ.get('READLIF_TEST_DL_PASSWD')

    dl_url = "https://cdn.nimne.com/readlif/" + str(filename)

    if not os.path.exists("./tests/private/"):
        os.makedirs("./tests/private/")

    if not os.path.exists("./tests/private/" + filename):
        with requests.get(dl_url, stream=True, auth=('readlif', pwd)) as r:
            r.raise_for_status()
            with open("./tests/private/" + filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)


class TestReadMethods(unittest.TestCase):
    def test_image_loading(self):
        # order = c, z, t
        test_array = [[0, 0, 0], [0, 2, 0], [0, 2, 2], [1, 0, 0]]
        for i in test_array:
            c = str(i[0])
            z = str(i[1])
            t = str(i[2])
            ref = Image.open("./tests/tiff/c" + c + "z" + z + "t" + t + ".tif")

            obj = LifFile("./tests/xyzt_test.lif").get_image(0)
            test = obj.get_frame(z=z, t=t, c=c)
            self.assertEqual(test.tobytes(), ref.tobytes())

    def test_image_loading_from_buffer(self):
        # order = c, z, t
        test_array = [[0, 0, 0], [0, 2, 0], [0, 2, 2], [1, 0, 0]]
        for i in test_array:
            c = str(i[0])
            z = str(i[1])
            t = str(i[2])
            ref = Image.open("./tests/tiff/c" + c + "z" + z + "t" + t + ".tif")

            with open("./tests/xyzt_test.lif", "rb") as open_f:
                obj = LifFile(open_f).get_image(0)
                test = obj.get_frame(z=z, t=t, c=c)
                self.assertEqual(test.tobytes(), ref.tobytes())

    def test_XML_header(self):
        etroot, test = get_xml("./tests/xyzt_test.lif")
        self.assertEqual(
            test[:50], '<LMSDataContainerHeader Version="2"><Element Name='
        )

    def test_iterators(self):
        images = [i for i in LifFile("./tests/xyzt_test.lif").get_iter_image()]
        self.assertEqual(len(images), 1)

        obj = LifFile("./tests/xyzt_test.lif").get_image(0)
        self.assertEqual(repr(obj), "'LifImage object with "
                                    "dimensions: "
                                    "Dims(x=1024, y=1024, z=3, t=3, m=1)'")

        c_list = [i for i in obj.get_iter_c()]
        self.assertEqual(len(c_list), 2)

        t_list = [i for i in obj.get_iter_t()]
        self.assertEqual(len(t_list), 3)

        z_list = [i for i in obj.get_iter_z()]
        self.assertEqual(len(z_list), 3)

    def test_not_lif_file(self):
        with self.assertRaises(ValueError):
            LifFile("./tests/tiff/c0z0t0.tif")

    def test_not_that_many_images(self):
        obj = LifFile("./tests/xyzt_test.lif")
        self.assertEqual(repr(obj), "'LifFile object with 1 image'")

        with self.assertRaises(ValueError):
            obj.get_image(10)

        image = obj.get_image(0)
        with self.assertRaises(ValueError):
            image.get_frame(z=10, t=0, c=0)

        with self.assertRaises(ValueError):
            image.get_frame(z=0, t=10, c=0)

        with self.assertRaises(ValueError):
            image.get_frame(z=0, t=0, c=10)

        with self.assertRaises(ValueError):
            image.get_frame(z=0, t=0, c=0, m=10)

        with self.assertRaises(ValueError):
            image._get_item(100)

    def test_scale(self):
        obj = LifFile("./tests/xyzt_test.lif").get_image(0)
        self.assertAlmostEqual(obj.scale[0], 9.8709062997224)

    def test_depth(self):
        obj = LifFile("./tests/xyzt_test.lif").get_image(0)
        self.assertEqual(obj.bit_depth[0], 8)

    def test_private_images_16bit(self):
        # These tests are for images that are not public.
        # These images will be pulled from a protected web address
        # during CI testing.
        if os.environ.get('READLIF_TEST_DL_PASSWD') is not None:
            downloadPrivateFile("16bit.lif")
            downloadPrivateFile("i1c0z2_16b.tif")
            # Note - readlif produces little endian files,
            # ImageJ makes big endian files for 16bit by default
            obj = LifFile("./tests/private/16bit.lif").get_image(1)

            self.assertEqual(obj.bit_depth[0], 12)

            ref = Image.open("./tests/private/i1c0z2_16b.tif")
            test = obj.get_frame(z=2, c=0)

            self.assertEqual(test.tobytes(), ref.tobytes())
        else:
            print("\nSkipped private test for 16-bit images\n")

    def test_private_images_mosaic(self):
        # These tests are for images that are not public.
        # These images will be pulled from a protected web address
        # during CI testing.
        if os.environ.get('READLIF_TEST_DL_PASSWD') is not None:
            downloadPrivateFile("tile_002.lif")
            downloadPrivateFile("i0c1m2z0.tif")

            obj = LifFile("./tests/private/tile_002.lif").get_image(0)
            self.assertEqual(obj.dims.m, 165)

            m_list = [i for i in obj.get_iter_m()]
            self.assertEqual(len(m_list), 165)

            ref = Image.open("./tests/private/i0c1m2z0.tif")
            test = obj.get_frame(c=1, m=2)

            self.assertEqual(test.tobytes(), ref.tobytes())

        else:
            print("\nSkipped private test for mosaic images\n")


if __name__ == "__main__":
    unittest.main()
