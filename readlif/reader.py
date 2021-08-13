import struct
import xml.etree.ElementTree as ET
from PIL import Image
from collections import namedtuple
import warnings
from functools import reduce
import os
import io


class LifImage:
    """
    This should not be called directly. This should be generated while calling
    get_image or get_iter_image from a LifFile object.

    Attributes:
        path (str): path / name of the image
        dims (tuple): (x, y, z, t, m)
        display_dims (tuple): The first two dimensions of the lif file.
            This is used to decide what dimensions are returned in a 2D plane.
        dims_n (dict): {0: length, 1: length, 2: length, n: length}

            For atypical imaging experiments, i.e. those not simple photos
            of XY frames, this attribute will be more useful than `dims`.
            This attribute will hold a dictionary with the length of each
            dimension, in the order it is referenced in the .lif file.

            Currently, only some of the 10 possible dimensions are used / known:

            - 1: x-axis

            - 2: y-axis

            - 3: z-axis

            - 4: time

            - 5: detection wavelength

            - 6-8: Unknown

            - 9: illumination wavelength

            - 10: mosaic tile

        name (str): image name
        offsets (list): Byte position offsets for each image.
        filename (str, bytes, os.PathLike, io.IOBase): The name of the LIF file
            being read
        channels (int): Number of channels in the image
        nz (int): number of 'z' frames

            Note, it is recommended to use `dims.z` instead. However, this will
            be kept for compatibility.
        nt (int): number of 't' frames

            Note, it is recommended to use `dims.t` instead. However, this will
            be kept for compatibility.
        scale (tuple): (scale_x, scale_y, scale_z, scale_t).

            Conversion factor: px/µm for x, y and z; images/frame for t. For
            time, this is the duration for the entire image acquisition.
        scale_n (dict): {1: scale_x, 2: scale_y, 3: scale_z, 4: scale_t}.

            Conversion factor: px/µm for x, y and z; images/sec for t. Related
            to `dims_n` above.
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
        self.display_dims = image_info["display_dims"]  # Tuple with two numbered values
        self.dims_n = image_info["dims_n"]
        self.scale_n = image_info["scale_n"]
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

    def _get_len_nondisplay_dims(self):
        non_display_dims_len = [self.dims_n[d] for d in self.dims_n.keys()
                                if d not in self.display_dims]
        if len(non_display_dims_len) >= 2:
            len_nondisplay = reduce(lambda x, y: x * y, non_display_dims_len)
            # Todo: Check if this is needed..
        elif len(non_display_dims_len) == 1:
            len_nondisplay = non_display_dims_len[0]
        else:
            len_nondisplay = 1
        return int(len_nondisplay)

    def _get_item(self, n):
        """
        Gets specified item from the image set (private).

        Note, this will likely be replaced by calls to get_plane in future
        releases.

        Args:
            n (int): what item (n item in the block) to retrieve

        Returns:
            PIL image
        """
        n = int(n)

        seek_distance = (self.channels * self._get_len_nondisplay_dims())

        if n >= seek_distance:
            raise ValueError("Invalid item trying to be retrieved.")

        if isinstance(self.filename, (str, bytes, os.PathLike)):
            image = open(self.filename, "rb")
        elif isinstance(self.filename, io.IOBase):
            image = self.filename
        else:
            raise TypeError(
                f"expected str, bytes, os.PathLike, or io.IOBase, "
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
            return Image.frombytes("L",
                                   (self.dims_n[self.display_dims[0]],
                                    self.dims_n[self.display_dims[1]]),
                                   data)
        elif self.bit_depth[0] <= 16:
            return Image.frombytes("I;16",
                                   (self.dims_n[self.display_dims[0]],
                                    self.dims_n[self.display_dims[1]]),
                                   data)
        else:
            raise ValueError("Unknown bit-depth, please submit a bug report"
                             " on Github")

    def get_plane(self, display_dims=None, c=0, requested_dims=None):
        """
        Gets the specified frame from image.

        Args:
            display_dims (tuple): Two value tuple (1, 2) specifying the
                two dimension plane to return. This will default to the first
                two dimensions in the LifFile, specified by LifFile.display_dims
            c (int): channel
            requested_dims (dict): Dictionary indicating the item to be returned,
                as described by a numerical dictionary, ex: {3: 0, 4: 1}

        Returns:
            Pillow Image object
        """
        c = int(c)
        if requested_dims is None:
            requested_dims = {}

        if display_dims is None:
            display_dims = self.display_dims
        elif type(display_dims) is not tuple or len(display_dims) != 2:
            raise ValueError("display_dims must be a two value tuple")

        if requested_dims.keys() in display_dims:
            warnings.warn("One or more of the display_dims is in the "
                          "requested_dims dictionary. Currently this has no "
                          "effect. All data from the display_dims will be "
                          "returned.")

        if display_dims != self.display_dims:
            raise NotImplementedError("Arbitrary dimensions are not yet supported")

        # Set all requested dims to 0:
        for i in range(1, 11):
            requested_dims[i] = int(requested_dims.get(i, 0))

        # Check if any of the dims exceeds what is in the image
        for i in self.dims_n.keys():
            if (requested_dims[i] + 1) > self.dims_n.get(i, 0):
                raise ValueError(f"Requested frame in dimension {str(i)} "
                                 f"doesn't exist")

        if isinstance(self.filename, (str, bytes, os.PathLike)):
            image = open(self.filename, "rb")
        elif isinstance(self.filename, io.IOBase):
            image = self.filename
        else:
            raise TypeError(
                f"expected str, bytes, os.PathLike, or io.IOBase, "
                f"not {type(self.filename)}"
            )

        # Read the specified data into the buffer
        with open(self.filename, "rb") as image:
            # Start at the beginning of the specified image
            image.seek(self.offsets[0])
            data = bytes()

            # This code is here for future flexibility, to define a range to return
            display_x = range(0, self.dims_n[display_dims[0]])
            display_y = range(0, self.dims_n[display_dims[1]])

            dim_len = [self.dims_n[i] for i in self.dims_n.keys()]  # For calculations below - list of dimension lengths
            key_idx = range(0, len(dim_len))  # For calculations below

            # Note, this does not include the first dim, need to index i - 1 later
            precalc_dim_prod = tuple([reduce(lambda x, y: x * y, dim_len[:i])
                                      for i in key_idx if len(dim_len[:i]) > 0])

            # Define the size of the plane to return
            total_len = self.dims_n[display_dims[0]] * self.dims_n[display_dims[1]]
            channel_offset = c * total_len

            # Speedup for the common case where the display_dims are the first two dims
            if display_dims == self.display_dims:
                px_pos = 0
                px_pos += channel_offset
                for key, i in zip(self.dims_n.keys(), key_idx):
                    # Multiply requested n by the length of all dims < than n
                    remaining_dims = dim_len[:i]

                    if len(remaining_dims) > 0:
                        px_pos += requested_dims[key] * precalc_dim_prod[i - 1] * self.channels
                    else:
                        px_pos += requested_dims[key] * self.channels

                if self.offsets[1] == 0:
                    data = data + b"\00" * total_len
                else:
                    image.seek(self.offsets[0] + px_pos)
                    data = data + image.read(total_len)

            # Handle the less common case, where the display_dims are arbitrary
            else:
                # Todo: Fix channel offset problems
                for pos_y in display_y:
                    for pos_x in display_x:
                        px_pos = 0  # Reset position on every loop
                        px_pos += channel_offset

                        requested_dims[display_dims[0]] = pos_x
                        requested_dims[display_dims[1]] = pos_y
                        for key, i in zip(self.dims_n.keys(), key_idx):
                            # Multiply requested n dims by the length of all dims below n in the hierarchy
                            remaining_dims = dim_len[:i]
                            if len(remaining_dims) > 0:
                                px_pos += requested_dims[key] * precalc_dim_prod[i - 1] * self.channels
                            else:
                                px_pos += requested_dims[key] * self.channels
                        if self.offsets[1] == 0:
                            data = data + b"\00" * 1
                        else:
                            image.seek(self.offsets[0] + px_pos)
                            data = data + image.read(1)

        # LIF files can be either 8-bit of 16-bit.
        # Because of how the image is read in, all of the raw
        # data is already in 'data', we just need to tell Pillow
        # how to set the bit depth
        # 'L' is 8-bit, 'I;16' is 16 bit

        # len(data) is the number of bytes (8-bit)
        # However, it is safer to let the lif file tell us the resolution
        if self.bit_depth[0] == 8:
            return Image.frombytes("L",
                                   (self.dims_n[display_dims[0]],
                                    self.dims_n[display_dims[1]]),
                                   data)
        elif self.bit_depth[0] <= 16:
            return Image.frombytes("I;16",
                                   (self.dims_n[display_dims[0]],
                                    self.dims_n[display_dims[1]]),
                                   data)
        else:
            raise ValueError("Unknown bit-depth, please submit a bug report"
                             " on Github")

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
        if self.display_dims != (1, 2):
            raise ValueError("Atypical imaging experiment, please use "
                             "get_plane() instead of get_frame()")

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

        >>> # For non-xy imaging experiments
        >>> img_0 = new.get_image(0)
        >>> for i in range(0, img_0.dims_n[4]):
        >>>     plane = img_0.get_plane(requested_dims = {4: i})
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

                # Find the dimensions, get them in order
                dims = item.findall("./Data/Image/ImageDescription/"
                                    "Dimensions/")

                # Get first two dims, if that fails, set X, Y
                # Todo: Check a 1-d image
                try:
                    dim1 = int(dims[0].attrib["DimID"])
                    dim2 = int(dims[1].attrib["DimID"])
                except (AttributeError, IndexError):
                    dim1 = 1
                    dim2 = 2

                dims_dict = {int(d.attrib["DimID"]):
                             int(d.attrib["NumberOfElements"])
                             for d in dims}

                # Get the scale from each image
                scale_dict = {}
                for d in dims:
                    # Length is not always present, need a try-except
                    dim_n = int(d.attrib["DimID"])
                    try:
                        len_n = float(d.attrib["Length"])

                        # other conversion factor for times needed
                        # returns scale in frames per second
                        if dim_n == 4:
                            scale_dict[dim_n] = ((int(dims_dict[dim_n]) - 1)
                                                 / float(len_n))
                        # Convert from meters to micrometers
                        else:
                            scale_dict[dim_n] = ((int(dims_dict[dim_n]) - 1)
                                                 / (float(len_n) * 10**6))
                    except (AttributeError, ZeroDivisionError):
                        scale_dict[dim_n] = None

                # This code block is to maintain compatibility with programs
                # written before 0.5.0

                # Known LIF dims:
                # 1: x
                # 2: y
                # 3: z
                # 4: t
                # 5: detection wavelength
                # 6: Unknown
                # 7: Unknown
                # 8: Unknown
                # 9: illumination wavelength
                # 10: Mosaic tile

                # The default value needs to be 1, because even if a dimension
                # is missing, it still has to exist. For example, an image that
                # is an x-scan still has one y-dimension.
                dim_x = dims_dict.get(1, 1)
                dim_y = dims_dict.get(2, 1)
                dim_z = dims_dict.get(3, 1)
                dim_t = dims_dict.get(4, 1)
                dim_m = dims_dict.get(10, 1)

                scale_x = scale_dict.get(1, None)
                scale_y = scale_dict.get(2, None)
                scale_z = scale_dict.get(3, None)
                scale_t = scale_dict.get(4, None)

                # Determine number of channels
                channel_list = item.findall(
                    "./Data/Image/ImageDescription/Channels/ChannelDescription"
                )
                n_channels = int(len(channel_list))
                # Iterate over each channel, get the resolution
                bit_depth = tuple([int(c.attrib["Resolution"]) for
                                   c in channel_list])

                # Get the position data if the image is tiled
                m_pos_list = []
                if dim_m > 1:
                    for tile in item.findall("./Data/Image/Attachment/Tile"):
                        FieldX = int(tile.attrib["FieldX"])
                        FieldY = int(tile.attrib["FieldY"])
                        PosX = float(tile.attrib["PosX"])
                        PosY = float(tile.attrib["PosY"])

                        m_pos_list.append((FieldX, FieldY, PosX, PosY))

                Dims = namedtuple("Dims", "x y z t m")

                data_dict = {
                    "dims": Dims(dim_x, dim_y, dim_z, dim_t, dim_m),
                    "display_dims": (dim1, dim2),
                    "dims_n": dims_dict,
                    "scale_n": scale_dict,
                    "path": str(path + "/"),
                    "name": item.attrib["Name"],
                    "channels": n_channels,
                    "scale": (scale_x, scale_y, scale_z, scale_t),
                    "bit_depth": bit_depth,
                    "mosaic_position": m_pos_list,
                    # "metadata_xmlroot": metadata_xmlroot
                }

                return_list.append(data_dict)

        return return_list

    def __init__(self, filename):
        self.filename = filename

        if isinstance(filename, (str, bytes, os.PathLike)):
            f = open(filename, "rb")
        elif isinstance(filename, io.IOBase):
            f = filename
        else:
            raise TypeError(
                f"expected str, bytes, os.PathLike, or io.IOBase, "
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
