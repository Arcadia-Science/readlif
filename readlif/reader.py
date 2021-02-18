import struct
import xml.etree.ElementTree as ET
from PIL import Image
from collections import namedtuple
import warnings
import os
import io


class LifImage:
    """
    This should not be called directly. This should be generated while calling
    get_image or get_iter_image from a LifFile object.

    Attributes:
        path (str): path / name of the image
        dims (tuple): (x, y, z, t, m)
        name (str): image name
        offsets (list): Byte position offsets for each image.
        filename (str, bytes, os.PathLike, io.BufferedIOBase): The name of the LIF file
            being read
        channels (int): Number of channels in the image
        nz (int): number of 'z' frames
        nt (int): number of 't' frames
        scale (tuple): (scale_x, scale_y, scale_z, scale_t).
            Conversion factor: px/µm for x, y and z; sec/image for t.
        bit_depth (tuple): A tuple of ints that indicates the bit depth of
            each channel in the image.
        mosaic_position (list): If the image is a mosaic (tiled), this contains
            a list of tuples with four values: `(FieldX, FieldY, PosX, PosY)`.
            The length of this list is equal to the number of tiles.
        info (dict): Direct access to data dict from LifFile, this is most
            useful for debugging. These are values pulled from the Leica XML.


    """

    def __init__(self, image_info, offsets, filename):
        self.dims = image_info["dims"]  # Named tuple (x, y, z, t, m)
        self.path = image_info["path"]
        self.offsets = offsets
        self.info = image_info
        self.filename = filename
        self.name = image_info["name"]
        self.channels = image_info["channels"]
        self.nz = int(image_info["dims"].z)
        self.nt = int(image_info["dims"].t)
        self.scale = image_info["scale"]
        self.bit_depth = image_info["bit_depth"]
        self.mosaic_position = image_info["mosaic_position"]
        self.n_mosaic = int(image_info["dims"].m)

    def __repr__(self):
        return repr('LifImage object with dimensions: ' + str(self.dims))

    def _get_item(self, n):
        """
        Gets specified item from the image set (private).
        Args:
            n (int): what item to retrieve

        Returns:
            PIL image
        """
        n = int(n)
        # Channels, times z, times t.
        # This is the number of 'images' in the block.
        seek_distance = (self.channels * self.dims.z
                         * self.dims.t * self.dims.m)
        if n >= seek_distance:
            raise ValueError("Invalid item trying to be retrieved.")

        if isinstance(self.filename, (str, bytes, os.PathLike)):
            image = open(self.filename, "rb")
        elif isinstance(self.filename, io.BufferedIOBase):
            image = self.filename
        else:
            raise TypeError(
                f"expected str, bytes, os.PathLike, or io.BufferedIOBase, "
                f"not {type(self.filename)}"
            )

        # self.offsets[1] is the length of the image
        if self.offsets[1] == 0:
            # In the case of a blank image, we can calculate the length from
            # the metadata in the LIF. When this is read by the parser,
            # it is set to zero initially.
            image_len = seek_distance * self.dims.x * self.dims.y
        else:
            image_len = int(self.offsets[1] / seek_distance)

        # self.offsets[0] is the offset in the file
        image.seek(self.offsets[0] + image_len * n)

        # It is not necessary to read from disk for truncated files

        # Todo: Update this for 16-bit images if there is a test file
        if self.offsets[1] == 0:
            data = b"\00" * image_len
        else:
            data = image.read(image_len)

        # LIF files can be either 8-bit of 16-bit.
        # Because of how the image is read in, all of the raw
        # data is already in 'data', we just need to tell Pillow
        # how to set the bit depth
        # 'L' is 8-bit, 'I;16' is 16 bit

        # len(data) is the number of bytes (8-bit)
        # However, it is safer to let the lif file tell us the resolution
        if self.bit_depth[0] == 8:
            read_image = Image.frombytes("L", (self.dims.x, self.dims.y), data)
        elif self.bit_depth[0] <= 16:
            read_image = Image.frombytes("I;16", (self.dims.x, self.dims.y), data)
        else:
            raise ValueError(
                "Unknown bit-depth, please submit a bug report" " on Github"
            )

        if isinstance(self.filename, (str, bytes, os.PathLike)):
            image.close()

        return read_image

    def get_frame(self, z=0, t=0, c=0, m=0):
        """
        Gets the specified frame (z, t, c, m) from image.

        Args:
            z (int): z position
            t (int): time point
            c (int): channel
            m (int): mosaic image

        Returns:
            Pillow Image object
        """
        t = int(t)
        c = int(c)
        z = int(z)
        m = int(m)
        if z >= self.nz:
            raise ValueError("Requested Z frame doesn't exist.")
        elif t >= self.nt:
            raise ValueError("Requested T frame doesn't exist.")
        elif c >= self.channels:
            raise ValueError("Requested channel doesn't exist.")
        elif m >= self.n_mosaic:
            raise ValueError("Requested mosaic image doesn't exist.")

        total_items = self.channels * self.nz * self.nt * self.n_mosaic

        t_offset = self.channels * self.nz
        t_requested = t_offset * t

        z_offset = self.channels
        z_requested = z_offset * z

        c_requested = c

        m_offset = self.channels * self.nz * self.nt
        m_requested = m_offset * m

        item_requested = t_requested + z_requested + c_requested + m_requested
        if item_requested > total_items:
            raise ValueError("The requested item is after the end of the image")

        return self._get_item(item_requested)

    def get_iter_t(self, z=0, c=0, m=0):
        """
        Returns an iterator over time t at position z and channel c.

        Args:
            z (int): z position
            c (int): channel
            m (int): mosaic image

        Returns:
            Iterator of Pillow Image objects
        """
        z = int(z)
        c = int(c)
        m = int(m)
        t = 0
        while t < self.nt:
            yield self.get_frame(z=z, t=t, c=c, m=m)
            t += 1

    def get_iter_c(self, z=0, t=0, m=0):
        """
        Returns an iterator over the channels at time t and position z.

        Args:
            z (int): z position
            t (int): time point
            m (int): mosaic image

        Returns:
            Iterator of Pillow Image objects
        """
        t = int(t)
        z = int(z)
        m = int(m)
        c = 0
        while c < self.channels:
            yield self.get_frame(z=z, t=t, c=c, m=m)
            c += 1

    def get_iter_z(self, t=0, c=0, m=0):
        """
        Returns an iterator over the z series of time t and channel c.

        Args:
            t (int): time point
            c (int): channel
            m (int): mosaic image

        Returns:
            Iterator of Pillow Image objects
        """
        t = int(t)
        c = int(c)
        m = int(m)
        z = 0
        while z < self.nz:
            yield self.get_frame(z=z, t=t, c=c, m=m)
            z += 1

    def get_iter_m(self, z=0, t=0, c=0):
        """
        Returns an iterator over the z series of time t and channel c.

        Args:
            t (int): time point
            c (int): channel
            z (int): z position

        Returns:
            Iterator of Pillow Image objects
        """
        t = int(t)
        c = int(c)
        m = 0
        while m < self.n_mosaic:
            yield self.get_frame(z=z, t=t, c=c, m=m)
            m += 1


def _read_long(handle):
    """Reads eight bytes, returns the long (Private)."""
    long_data, = struct.unpack("Q", handle.read(8))
    return long_data


def _check_truncated(handle):
    """Checks if the LIF file is truncated by reading in 100 bytes."""
    handle.seek(-4, 1)
    if handle.read(100) == (b"\x00" * 100):
        handle.seek(-100, 1)
        return True
    handle.seek(-100, 1)
    return False


def _check_magic(handle, bool_return=False):
    """Checks for lif file magic bytes (Private)."""
    if handle.read(4) == b"\x70\x00\x00\x00":
        return True
    else:
        if not bool_return:
            handle.close()
            raise ValueError("This is probably not a LIF file. "
                             "Expected LIF magic byte at " + str(handle.tell()))
        else:
            return False


def _check_mem(handle, bool_return=False):
    """Checks for 'memory block' bytes (Private)."""
    if handle.read(1) == b"\x2a":
        return True
    else:
        if not bool_return:
            raise ValueError("Expected LIF memory byte at " + str(handle.tell()))
        else:
            return False


def _read_int(handle):
    """Reads four bytes, returns the int (Private)."""
    int_data, = struct.unpack("I", handle.read(4))
    return int_data


def _get_len(handle):
    """Returns total file length (Private)."""
    position = handle.tell()
    handle.seek(0, 2)
    file_len = handle.tell()
    handle.seek(position)
    return file_len


class LifFile:
    """
    Given a path or buffer to a lif file, returns objects containing
    the image and data.

    This is based on the java openmicroscopy bioformats lif reading code
    that is here: https://github.com/openmicroscopy/bioformats/blob/master/components/formats-gpl/src/loci/formats/in/LIFReader.java # noqa

    Attributes:
        xml_header (string): The LIF xml header with tons of data
        xml_root (ElementTree): ElementTree XML representation
        offsets (list): Byte positions of the files
        num_images (int): Number of images
        image_list (dict): Has the keys: path, folder_name, folder_uuid,
            name, image_id, frames


    Example:
        >>> from readlif.reader import LifFile
        >>> new = LifFile('./path/to/file.lif')

        >>> for image in new.get_iter_image():
        >>>     for frame in image.get_iter_t():
        >>>         frame.image_info['name']
        >>>         # do stuff
    """

    def _recursive_image_find(self, tree, return_list=None, path=""):
        """Creates list of images by parsing the XML header recursively"""

        if return_list is None:
            return_list = []

        children = tree.findall("./Children/Element")
        if len(children) < 1:  # Fix for 'first round'
            children = tree.findall("./Element")
        for item in children:
            folder_name = item.attrib["Name"]
            if path == "":
                appended_path = folder_name
            else:
                appended_path = path + "/" + folder_name
            has_sub_children = len(item.findall("./Children/Element")) > 0
            is_image = (
                len(item.findall("./Data/Image/ImageDescription/Dimensions")) > 0
            )

            if has_sub_children:
                self._recursive_image_find(item, return_list, appended_path)

            elif is_image:
                # If additional XML data extraction is needed, add it here.

                # Don't need a try / except block, all images have x and y
                dim_x = int(item.find(
                    "./Data/Image/ImageDescription/"
                    "Dimensions/"
                    "DimensionDescription"
                    '[@DimID="1"]'
                ).attrib["NumberOfElements"])
                dim_y = int(item.find(
                    "./Data/Image/ImageDescription/"
                    "Dimensions/"
                    "DimensionDescription"
                    '[@DimID="2"]'
                ).attrib["NumberOfElements"])
                # Try to get z-dimension
                try:
                    dim_z = int(item.find(
                        "./Data/Image/ImageDescription/"
                        "Dimensions/"
                        "DimensionDescription"
                        '[@DimID="3"]'
                    ).attrib["NumberOfElements"])
                except AttributeError:
                    dim_z = 1

                # Get number of frames (time points)
                try:
                    dim_t = int(item.find(
                        "./Data/Image/ImageDescription/"
                        "Dimensions/"
                        "DimensionDescription"
                        '[@DimID="4"]'
                    ).attrib["NumberOfElements"])
                except AttributeError:
                    dim_t = 1

                # m for mosaic images
                try:
                    dim_m = int(item.find(
                        "./Data/Image/ImageDescription/"
                        "Dimensions/"
                        "DimensionDescription"
                        '[@DimID="10"]'
                    ).attrib["NumberOfElements"])
                except AttributeError:
                    dim_m = 1

                # Determine number of channels
                channel_list = item.findall(
                    "./Data/Image/ImageDescription/Channels/ChannelDescription"
                )

                n_channels = int(len(channel_list))

                # Iterate over each channel, get the resolution
                bit_depth = tuple([int(c.attrib["Resolution"]) for
                                   c in channel_list])

                # Find the scale of the image. All images have x and y,
                # only some have z and t.
                # It is plausible that 'Length' is not defined - use try/except.
                try:
                    len_x = item.find(
                        "./Data/Image/ImageDescription/"
                        "Dimensions/"
                        "DimensionDescription"
                        '[@DimID="1"]'
                    ).attrib["Length"]  # Returns len in meters
                    scale_x = (int(dim_x) - 1) / (float(len_x) * 10**6)
                except (AttributeError, ZeroDivisionError):
                    scale_x = None

                try:
                    len_y = item.find(
                        "./Data/Image/ImageDescription/"
                        "Dimensions/"
                        "DimensionDescription"
                        '[@DimID="2"]'
                    ).attrib["Length"]  # Returns len in meters
                    scale_y = (int(dim_y) - 1) / (float(len_y) * 10**6)
                except (AttributeError, ZeroDivisionError):
                    scale_y = None

                # Try to get z-dimension
                try:
                    len_z = item.find(
                        "./Data/Image/ImageDescription/"
                        "Dimensions/"
                        "DimensionDescription"
                        '[@DimID="3"]'
                    ).attrib["Length"]  # Returns len in meters
                    scale_z = int(dim_z) / (float(len_z) * 10**6)
                except (AttributeError, ZeroDivisionError):
                    scale_z = None

                try:
                    len_t = item.find(
                        "./Data/Image/ImageDescription/"
                        "Dimensions/"
                        "DimensionDescription"
                        '[@DimID="4"]'
                    ).attrib["Length"]  # Returns len in meters
                    scale_t = int(dim_t) / float(len_t)
                except (AttributeError, ZeroDivisionError):
                    scale_t = None

                # Get the position data if the image is tiled
                m_pos_list = []
                if dim_m > 1:
                    for tile in item.findall("./Data/Image/Attachment/Tile"):
                        FieldX = int(tile.attrib["FieldX"])
                        FieldY = int(tile.attrib["FieldY"])
                        PosX = float(tile.attrib["PosY"])
                        PosY = float(tile.attrib["PosY"])

                        m_pos_list.append((FieldX, FieldY, PosX, PosY))

                Dims = namedtuple("Dims", "x y z t m")

                data_dict = {
                    "dims": Dims(dim_x, dim_y, dim_z, dim_t, dim_m),
                    "path": str(path + "/"),
                    "name": item.attrib["Name"],
                    "channels": n_channels,
                    "scale": (scale_x, scale_y, scale_z, scale_t),
                    "bit_depth": bit_depth,
                    "mosaic_position": m_pos_list
                }

                return_list.append(data_dict)

        return return_list

    def __init__(self, filename):
        self.filename = filename

        if isinstance(filename, (str, bytes, os.PathLike)):
            f = open(filename, "rb")
        elif isinstance(filename, io.BufferedIOBase):
            f = filename
        else:
            raise TypeError(
                f"expected str, bytes, os.PathLike, or io.BufferedIOBase, "
                f"not {type(filename)}"
            )
        f_len = _get_len(f)

        _check_magic(f)  # read 4 byte, check for magic bytes
        f.seek(8)
        _check_mem(f)  # read 1 byte, check for memory byte

        header_len = _read_int(f)  # length of the xml header
        self.xml_header = f.read(header_len * 2).decode("utf-16")
        self.xml_root = ET.fromstring(self.xml_header)

        self.offsets = []
        truncated = False
        while f.tell() < f_len:
            try:
                # To find offsets, read magic byte
                _check_magic(f)  # read 4 byte, check for magic bytes
                f.seek(4, 1)
                _check_mem(f)  # read 1 byte, check for memory byte

                block_len = _read_int(f)

                # Not sure if this works, as I don't have a file to test it on
                # This is based on the OpenMicroscopy LIF reader written in in java
                if not _check_mem(f, True):
                    f.seek(-5, 1)
                    block_len = _read_long(f)
                    _check_mem(f)

                description_len = _read_int(f) * 2

                if block_len > 0:
                    self.offsets.append((f.tell() + description_len, block_len))

                f.seek(description_len + block_len, 1)

            except ValueError:
                if _check_truncated(f):
                    truncation_begin = f.tell()
                    warnings.warn("LIF file is likely truncated. Be advised, "
                                  "it appears that some images are blank. ",
                                  UserWarning)
                    truncated = True
                    f.seek(0, 2)

                else:
                    raise

        if isinstance(filename, (str, bytes, os.PathLike)):
            f.close()

        self.image_list = self._recursive_image_find(self.xml_root)

        # If the image is truncated we need to manually add the offsets because
        # the LIF magic bytes aren't present to guide the location.
        if truncated:
            num_truncated = len(self.image_list) - len(self.offsets)
            for i in range(num_truncated):
                # In the special case of a truncation,
                # append an offset with length zero.
                # This will be taken care of later when the images are retrieved.
                self.offsets.append((truncation_begin, 0))

        if len(self.image_list) != len(self.offsets) and not truncated:
            raise ValueError("Number of images is not equal to number of "
                             "offsets, and this file does not appear to "
                             "be truncated. Something has gone wrong.")
        else:
            self.num_images = len(self.image_list)

    def __repr__(self):
        if self.num_images == 1:
            return repr('LifFile object with ' + str(self.num_images)
                        + ' image')
        else:
            return repr('LifFile object with ' + str(self.num_images)
                        + ' images')

    def get_image(self, img_n=0):
        """
        Specify the image number, and this returns a LifImage object
        of that image.

        Args:
            img_n (int): Image number to retrieve

        Returns:
            LifImage object with specified image
        """
        img_n = int(img_n)
        if img_n >= len(self.image_list):
            raise ValueError("There are not that many images!")
        offsets = self.offsets[img_n]
        image_info = self.image_list[img_n]
        return LifImage(image_info, offsets, self.filename)

    def get_iter_image(self, img_n=0):
        """
        Returns an iterator of LifImage objects in the lif file.

        Args:
            img_n (int): Image to start iteration at

        Returns:
            Iterator of LifImage objects.
        """
        img_n = int(img_n)
        while img_n < len(self.image_list):
            offsets = self.offsets[img_n]
            image_info = self.image_list[img_n]
            yield LifImage(image_info, offsets, self.filename)
            img_n += 1
