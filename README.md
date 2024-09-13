# readlif

The `readlif` package is a fast, pure Python reader for Leica Image Format (LIF) files. It supports Python 3.9 and above.

This code is inspired by the [Open Microscopy Bio-Formats project](https://github.com/openmicroscopy/bioformats).

Auto-generated documentation is available [here](https://readlif.readthedocs.io/en/latest/).

## Project status: Ownership change

In September 2024, ownership of the `readlif` package was transferred from [Nick Negretti](https://github.com/nimne), its original author, to [Arcadia Science](https://github.com/arcadia-Science/). We are committed to maintaining and improving this project for the imaging community as part of [Arcadia's committment to open science](https://www.arcadiascience.com/about/ecosystem). For any questions or support, please open an issue in this repo.

## Roadmap

The following is a summary of recent and planned changes to the `readlif` package by Arcadia Science:

- [Done] Fix a bug related to reading 16-bit images.
- [Done] Use ruff for formatting and linting.
- [Done] migrate to pyproject.toml for package configuration.
- [Planned] add support for reading 32-bit images.
- [Planned] add support for extracting relevant metadata from the raw XML metadata embedded in LIF files.
- [Planned] refactor the `get_plane` method to make it easier to use.
- [Planned] improve tests using realistic test files from internal sources.

## Installation

This package is available on PyPI, so it can be installed with pip:

```sh
pip install readlif
```

## Development

Please see the [DEVELOPMENT.md](DEVELOPMENT.md) readme for information on how to set up a development environment for this package.

## Usage

LIF files are represented by `LifFile` instances. These objects can be created by passing the path to a LIF file:

```python
from readlif.reader import LifFile
lif_file = LifFile('./path/to/file.lif')
```

This object contains a few methods to access the images contained within the LIF file. All images, whether in a folder or not, will be accessible sequentially from the `LifFile` object.

```python
# Access a specific image directly.
image_0 = new.get_image(0)

# Create a list of images using a generator.
all_images = [image for image in lif_file.get_iter_image()]
```

The resulting `LifImage` object has a few methods to access the specific two-dimensional frame contained in the image, where z is the z position, t is the timepoint, and c is the channel.

```python
# Access a specific frame in the image.
image_0.get_frame(z=0, t=0, c=0)

# Iterate over different dimensions, holding the other dimensions fixed.
images = [image for image in image_0.get_iter_t(c=0, z=0)]
images = [image for image in image_0.get_iter_z(t=0, c=0)]
images = [image for image in image_0.get_iter_c(t=0, z=0)]
```

The two-dimensional images returned by these methods are Pillow objects, so all Pillow methods (like `.show()`) will work with them.

## Known issues

Below are known issues and limitations with the `readlif` package. If you encounter these issues, please open an issue.

- There may be an issue where a truncated 16-bit file will load incorrectly; however, this is not tested.

- There is not support for FlipX, FlipY and SwapXY metadata.

- Truncated images are returned as blank images.

- There is currently no support for returning arbitrary planes from `get_plane` by specifying `display_dims`.

- The package has only been tested with LIF files that were generated with Leica LAS X and Leica LAS AF. It may not work with LIF files from other sources.

## Note about 16-bit images

As of 0.3.0, `reaflif` supports images with bit depths greater than 8.

However, while some images will be returned as 16-bit arrays, the image data in the LIF file may actually be 10- or 12-bit. The original bit depth of each channel can be found in the `bit_depth` attribute of `LifImage`.
