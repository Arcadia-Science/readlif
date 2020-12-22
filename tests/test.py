import unittest
from readlif.reader import LifFile
from readlif.utilities import get_xml
from PIL import Image

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

    def test_XML_header(self):
        etroot, test = get_xml("./tests/xyzt_test.lif")
        self.assertEqual(
            test[:50], '<LMSDataContainerHeader Version="2"><Element Name='
        )

    def test_iterators(self):
        images = [i for i in LifFile("./tests/xyzt_test.lif").get_iter_image()]
        self.assertEqual(len(images), 1)

        obj = LifFile("./tests/xyzt_test.lif").get_image(0)

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
            image._get_item(100)

    def test_scale(self):
        obj = LifFile("./tests/xyzt_test.lif").get_image(0)
        self.assertAlmostEqual(obj.scale[0], 9.8709062997224)

    def test_depth(self):
        obj = LifFile("./tests/xyzt_test.lif").get_image(0)
        self.assertEqual(obj.bit_depth[0], 8)

    def test_not_implemented_mosaic(self):
        import os
        istravis = os.environ.get('TRAVIS') == 'true'
        # Can't test this in CI, don't have permission to publish this
        if not istravis:
            with self.assertRaises(NotImplementedError):
                LifFile("./tests/private/tile_002.lif").get_image(0)
        pass


if __name__ == "__main__":
    unittest.main()
