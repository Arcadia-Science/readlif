[![Documentation Status](https://readthedocs.org/projects/readlif/badge/?version=latest)](https://readlif.readthedocs.io/en/latest/?badge=latest)
[![CI-Tests](https://github.com/nimne/readlif/workflows/CI-Tests/badge.svg)](https://github.com/nimne/readlif/actions?query=workflow%3ACI-Tests)

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

There may be an issue where a truncated 16-bit file will load incorrectly, however
this is not tested. If you have an example file, open an issue!

There is not support for FlipX, FlipY and SwapXY metadata. If you need this, 
please open an issue!

Truncated images are returned as blank images.

There is currently no support for returning arbitrary planes from `get_plane`
by specifying `display_dims`. This is in progress.

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
#### 0.6.4
- Fixed bug and incompatibility in 0.6.3
- Added preliminary fix for images captured with stage navigator


#### 0.6.3
- Added support for updated LasX with additional data in the Lif file
- Changed the way file names are assigned, now includes folder path
  - This fix is intended to clarify imaging sets with many duplicate names

#### 0.6.2
- Fixed bug where the time and image scale were calculated incorrectly
- Clarified scaling documentation


#### 0.6.1
- Update readme


#### 0.6.0
- Added support for non-XY images with `get_plane()`. See docs for usage.
    - Note: Reading arbitrary planes (i.e. an XZ plane of an XY image) is not yet supported. 

#### 0.5.2
- Bugfix: Fix error in mosaic parsing. `PosX` metadata was incorrectly read from `PosY`

#### 0.5.1
- Bugfix: switch from `io.BufferedIOBase` to `io.IOBase`

#### 0.5.0
- Added support for loading files from buffers
    - Thans to PR from @JacksonMaxfield

#### 0.4.1
- Fixed critical documentaiton error:
    - `LifImage.scale` is in px/µm, not px/nm for X and Y dimensions

#### 0.4.0
- Added support for tiled images
    - `m` was added as a new dimension (for tiled images)
    - `LifImage` changes:
        - New `get_iter_m()` function
        - New `mosaic_position` attribute with `(FieldX, FieldY, PosX, PosY)`
- Under the hood changes
    - `LifImage.dims` is now a named tuple for clearer code
- Other things
    - Prettier outputs for `repr()`
    - Switch to github CI

#### 0.3.1
- Added error message for tiled images, pending feature addition

#### 0.3.0
- Added support for 16-bit images, increased minimum Pillow version to 7.2.0.
    - New `LifImage` attribute `bit_depth` is a tuple of intigers descibing the bit
    depth for each channel in the image. 
    - Thanks to @DirkRemmers for providing the example file.
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

