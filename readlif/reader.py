import struct
import xml.etree.ElementTree as ET
from PIL import Image


class LifImage:
    """
    This should not be called directly. This should be generated while calling
    get_image or get_iter_image from a LifFile object.

    Attributes:
        path (str): path / name of the image
        dims (tuple): (x, y, z, t)
        name (str): image name
        offsets (list): Byte position offsets for each image.
        filename (str): The name of the LIF file being read
        channels (int): Number of channels in the image
        nz (int): number of 'z' frames
        nt (int): number of 't' frames
        scale (tuple): (scale_x, scale_y, scale_z, scale_t).
            Conversion factor: px/nm for x, y and z; sec/image for t.
        info (dict): Direct access to data dict from LifFile, this is most
            useful for debugging. These are values pulled from the Leica XML.


    """

    def __init__(self, image_info, offsets, filename):
        self.dims = (
            int(image_info["dims"][0]),
            int(image_info["dims"][1]),
            int(image_info["dims"][2]),
            int(image_info["dims"][3]),
        )
        self.path = image_info["path"]
        self.offsets = offsets
        self.info = image_info
        self.filename = filename
        self.name = image_info["name"]
        self.channels = image_info["channels"]
        self.nz = int(image_info["dims"][2])
        self.nt = int(image_info["dims"][3])
        self.scale = image_info["scale"]  # likely: image_info["scale"]

    def _get_item(self, n):
        """
        Gets specified item from the image set (private).
        Args:
            n (int): what item to retrieve

        Returns:
            PIL image
        """
        n = int(n)
        # Channels, times z, times t
        seek_distance = self.channels * self.dims[2] * self.dims[3]
        if n >= seek_distance:
            raise ValueError("Invalid item trying to be retrieved.")
        with open(self.filename, "rb") as image:
            image_len = int(self.offsets[1] / seek_distance)
            # first position is the offset
            image.seek(self.offsets[0] + image_len * n)
            # second position is the length
            data = image.read(image_len)
            return Image.frombytes("L", (self.dims[0], self.dims[1]), data)

    def get_frame(self, z=0, t=0, c=0):
        """
        Gets the specified frame (z, t, c) from image.

        Args:
            z (int): z position
            t (int): time point
            c (int): channel

        Returns:
            Pillow Image object
        """
        t = int(t)
        c = int(c)
        z = int(z)
        if z >= self.nz:
            raise ValueError("Requested Z frame doesn't exist.")
        elif t >= self.nt:
            raise ValueError("Requested T frame doesn't exist.")
        elif c >= self.channels:
            raise ValueError("Requested channel doesn't exist.")

        total_items = self.channels * self.nz * self.nt

        t_offset = self.channels * self.nz
        t_requested = t_offset * t

        z_offset = self.channels
        z_requested = z_offset * z

        c_requested = c

        item_requested = t_requested + z_requested + c_requested
        if item_requested > total_items:
            raise ValueError("The requested item is after the end of the image")

        return self._get_item(item_requested)

    def get_iter_t(self, z=0, c=0):
        """
        Returns an iterator over time t at position z and channel c.

        Args:
            z (int): z position
            c (int): channel

        Returns:
            Iterator of Pillow Image objects
        """
        z = int(z)
        c = int(c)
        t = 0
        while t < self.nt:
            yield self.get_frame(z=z, t=t, c=c)
            t += 1

    def get_iter_c(self, z=0, t=0):
        """
        Returns an iterator over the channels at time t and position z.

        Args:
            z (int): z position
            t (int): time point

        Returns:
            Iterator of Pillow Image objects
        """
        t = int(t)
        z = int(z)
        c = 0
        while c < self.channels:
            yield self.get_frame(z=z, t=t, c=c)
            c += 1

    def get_iter_z(self, t=0, c=0):
        """
        Returns an iterator over the z series of time t and channel c.

        Args:
            t (int): time point
            c (int): channel

        Returns:
            Iterator of Pillow Image objects
        """
        t = int(t)
        c = int(c)
        z = 0
        while z < self.nz:
            yield self.get_frame(z=z, t=t, c=c)
            z += 1


def _read_long(handle):
    """Reads eight bytes, returns the long (Private)."""
    long_data, = struct.unpack("Q", handle.read(8))
    return long_data


def _check_magic(handle, bool_return=False):
    """Checks for lif file magic bytes (Private)."""
    if handle.read(4) == b"\x70\x00\x00\x00":
        return True
    else:
        if not bool_return:
            handle.close()
            raise ValueError("Expected LIF magic byte at " + str(handle.tell()))
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
    Given a path to a lif file, returns objects containing
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
                # Todo: get real dims. It's in the Dimension Description as attribute 'Length'
                # Get number of frames (time points)
                try:
                    dim_t = item.find(
                        "./Data/Image/ImageDescription/"
                        "Dimensions/"
                        "DimensionDescription"
                        '[@DimID="4"]'
                    ).attrib["NumberOfElements"]
                except AttributeError:
                    dim_t = 1

                # Don't need a try / except block, all images have x and y
                dim_x = item.find(
                    "./Data/Image/ImageDescription/"
                    "Dimensions/"
                    "DimensionDescription"
                    '[@DimID="1"]'
                ).attrib["NumberOfElements"]
                dim_y = item.find(
                    "./Data/Image/ImageDescription/"
                    "Dimensions/"
                    "DimensionDescription"
                    '[@DimID="2"]'
                ).attrib["NumberOfElements"]
                # Try to get z-dimension
                try:
                    dim_z = item.find(
                        "./Data/Image/ImageDescription/"
                        "Dimensions/"
                        "DimensionDescription"
                        '[@DimID="3"]'
                    ).attrib["NumberOfElements"]
                except AttributeError:
                    dim_z = 1

                # Determine number of channels
                channel_list = item.findall(
                    "./Data/Image/ImageDescription/Channels/ChannelDescription"
                )

                n_channels = len(channel_list)

                # Find the scale of the image. All images have x and y,
                # only some have z and t.
                len_x = item.find(
                    "./Data/Image/ImageDescription/"
                    "Dimensions/"
                    "DimensionDescription"
                    '[@DimID="1"]'
                ).attrib["Length"]  # Returns len in meters
                scale_x = (int(dim_x) - 1) / (float(len_x) * 10**6)
                len_y = item.find(
                    "./Data/Image/ImageDescription/"
                    "Dimensions/"
                    "DimensionDescription"
                    '[@DimID="2"]'
                ).attrib["Length"]  # Returns len in meters
                scale_y = (int(dim_y) - 1) / (float(len_y) * 10**6)
                # Try to get z-dimension
                try:
                    len_z = item.find(
                        "./Data/Image/ImageDescription/"
                        "Dimensions/"
                        "DimensionDescription"
                        '[@DimID="3"]'
                    ).attrib["Length"]  # Returns len in meters
                    scale_z = int(dim_z) / (float(len_z) * 10**6)
                except AttributeError:
                    scale_z = None

                try:
                    len_t = item.find(
                        "./Data/Image/ImageDescription/"
                        "Dimensions/"
                        "DimensionDescription"
                        '[@DimID="4"]'
                    ).attrib["Length"]  # Returns len in meters
                    scale_t = int(dim_t) / float(len_t)
                except AttributeError:
                    scale_t = None

                data_dict = {
                    "dims": (dim_x, dim_y, dim_z, dim_t),
                    "path": str(path + "/"),
                    "name": item.attrib["Name"],
                    "channels": n_channels,
                    "scale": (scale_x, scale_y, scale_z, scale_t),
                }

                return_list.append(data_dict)

        return return_list

    def __init__(self, filename):
        self.filename = filename
        f = open(filename, "rb")
        f_len = _get_len(f)

        _check_magic(f)  # read 4 byte, check for magic bytes
        f.seek(8)
        _check_mem(f)  # read 1 byte, check for memory byte

        header_len = _read_int(f)  # length of the xml header
        self.xml_header = f.read(header_len * 2).decode("utf-16")
        self.xml_root = ET.fromstring(self.xml_header)

        self.offsets = []
        while f.tell() < f_len:
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

        f.close()

        self.image_list = self._recursive_image_find(self.xml_root)

        if len(self.image_list) != len(self.offsets):
            raise ValueError("Number of images is not equal to number of offsets")
        else:
            self.num_images = len(self.image_list)

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
