# Test artifacts

This directory contains test artifacts for the `readlif` package. These artifacts consist of example LIF files from various sources. In some cases, they are paired with expected outputs in the form of TIFF files containing the image data for selected 2D (X-Y) planes in the corresponding LIF file. In these cases, there is one TIFF file for each plane, and the TIFF files are named according to the plane they represent.

## About the LIF files

These are brief informal notes about the contents of the LIF files in this directory. They were determined by manually opening the LIF files in Fiji using the BioFormats plugin and examining the metadata.

### `xyzt-example/xyzt-example.lif`

Contains a single image. 1024 x 1024. 8-bit. Shape: 2C, 3T, 3Z.

### `xz-example/xz-example.lif`

Contains three images. All three are XZ in the first two dimensions.

BioFormats labels:

- xzt: 128 x 128; 2C x 20T
- xzy: 128 x 128; 2C x 23Z (note: the 'y' dimension in 'xzy' is loaded as Z by BioFormats)
- xz: 512 x 512; 2C.

### `misc/LeicaLASX_wavelength-sweep_example.lif`

Contains three images. All 64 x 64. The time dimension appears to be a Lambda scan but the metadata implies it was a time dimension (it contains `Plane` elements with `"deltaT"` attributes). BioFormats loads the images as XYZT.

The BioFormats labels of the three images are (in pseudo-regex):

```
x y (lambdaEmi|lambdaExc): 64x64; (20T|15T|(11Z x 20T))
```

### `misc/new_lasx.lif`

Contains a single image. 1024 x 1024. 8-bit. Shape: 2C, 39Z.

This file was added in #36; there is no other documentation of what it contains.
