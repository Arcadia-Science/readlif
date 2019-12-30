[![Documentation Status](https://readthedocs.org/projects/readlif/badge/?version=latest)](https://readlif.readthedocs.io/en/latest/?badge=latest)
[![Test Status](https://travis-ci.org/nimne/readlif.svg?branch=master)](https://travis-ci.org/nimne/readlif)

readlif README file
===
The readlif package was developed to be a fast, python only, reader for Leica Lif files. This is tested in Python 3.6 and 3.7.

The basic premise is to read an image from a Lif file into a Pillow object. The only additional requirement for this package is Pillow>=4.2.0.

This code is inspired by the [Open Microscopy Bio-Formats project](https://github.com/openmicroscopy/bioformats).

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

This has only been tested on Lif files that were generated with Leica LAS X and Leica LAS AF. There will likely be files that will not work with this software. In that case, please open an issue on github!

Auto-generated documentation is available [here](https://readlif.readthedocs.io/en/latest/).

Changelog
======
0.2.1 - Fixed `ZeroDivisionError` when the Z-dimension is defined, but has a length of 0. Clarified an error message. Added fix for truncated files.

0.2.0 - `LifImage.scale` now returns px/nm conversions

0.1.1 - Style changes

0.1.0 - Initial release

