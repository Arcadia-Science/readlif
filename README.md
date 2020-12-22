[![Documentation Status](https://readthedocs.org/projects/readlif/badge/?version=latest)](https://readlif.readthedocs.io/en/latest/?badge=latest)
[![Test Status](https://travis-ci.com/nimne/readlif.svg?branch=master)](https://travis-ci.com/github/nimne/readlif)

readlif README file
===
The readlif package was developed to be a fast, python only, reader for Leica Lif files. This is tested in Python 3.6 through 3.9.

The basic premise is to read an image from a Lif file into a Pillow object. The only additional requirement for this package is Pillow>=7.2.0.

This code is inspired by the [Open Microscopy Bio-Formats project](https://github.com/openmicroscopy/bioformats).

Auto-generated documentation is available [here](https://readlif.readthedocs.io/en/latest/).

Installation
===
This package is available on pypi, so you can install it with pip
```
pip install readlif
```
Alternatively, clone the git repo and install with setuptools
```
python setup.py install
```

Known issues
===
This package is not yet updated to support tiled / mosaic LIF files. Version 0.3.1 should
now give an error message when attempting to load a mosaic image. See Issue #7.

There may also be an issue where a truncated 16-bit file will load incorrectly, however
this is not tested.

There is not yet support for FlipX, FlipY and SwapXY metadata.

12- and 16-bit images
===
As of 0.3.0, `reaflif` will now support images with bit depth greater than 8.

However, note that while some images will be returned as a 16 bit array, they may
actually 10 or 12 bit images. It is not simple to easily convert these without
the potential of losing data, so a new `bit_depth` attribute has been added
to `LifImage` to indicate the bit depth of each channel in the image.

It is up to the user to decide how, or if, to convert these. There is an upscaling example below.

Examples
===
Everything in this package is numbered starting from 0, which is not consistent with how things like ImageJ operate.

The basic object is the LifFile object.
```python
from readlif.reader import LifFile
new = LifFile('./path/to/file.lif')
```
This object contains a few methods to access the images contained within the Lif file. All images, in a folder or not, will be accessible sequentially from the `LifFile` object.
```python
# Access a specific image directly
img_0 = new.get_image(0)
# Create a list of images using a generator
img_list = [i for i in new.get_iter_image()]
```
The resulting `LifImage` object has a few methods to access the specific two-dimensional frame contained in the image, where z is the z position, t is the timepoint, and c is the channel.
```python
# Access a specific item
img_0.get_frame(z=0, t=0, c=0)
# Iterate over different items
frame_list   = [i for i in img_0.get_iter_t(c=0, z=0)]
z_list       = [i for i in img_0.get_iter_z(t=0, c=0)]
channel_list = [i for i in img_0.get_iter_c(t=0, z=0)]

```
The two dimensional images returned by these methods are Pillow objects, so the applicable methods (`.show()`) will work with them.

If it is necessary to scale a 12-bit image to the full 16-bit range, it is possible to do this with numpy.
```python
import numpy as np

# Assumes all channels have the same bit depth
scale_factor = (16 - img_0.bit_depth[0]) ** 2  
frame = img_0.get_frame(z=0, t=0, c=0)
img_array = np.uint16(np.array(frame) * scale_factor)

Image.fromarray(img_array).show()
```

This has only been tested on Lif files that were generated with Leica LAS X and Leica LAS AF. There will likely be files that will not work with this software. In that case, please open an issue on github!


Changelog
======
#### 0.3.1
- Added error message for tiled images, pending feature addition

#### 0.3.0
- Added support for 16-bit images, increased minimum Pillow version to 7.2.0.
    - New `LifImage` attribute `bit_depth` is a tuple of intigers descibing the bit
    depth for each channel in the image. 
- Changed type from `str` to `int` for `dims` and `channels` in the `info` dictionary
- Added python 3.9 to build testing

#### 0.2.1 
- Fixed `ZeroDivisionError` when the Z-dimension is defined, but has a length of 0. Clarified an error message. Added fix for truncated files.

#### 0.2.0 
- `LifImage.scale` now returns px/nm conversions

#### 0.1.1 
- Style changes

#### 0.1.0 
- Initial release

