# Example LIF files from openmicroscopy.org

This directory contains example LIF files from the [openmicroscopy.org](https://www.openmicroscopy.org/) website.

They were manually downloaded on 2024-09-14 from:

[https://downloads.openmicroscopy.org/images/Leica-LIF/](https://downloads.openmicroscopy.org/images/Leica-LIF/)

The original directory structure and filenames were preserved from this source and have no meaning in the context of this repository.

## About the LIF files

Below is a brief description of the LIF files contained in each subdirectory of this directory.

### `seanwarren/`

- One LIF file with 8 FRAP series (stacks). 448 x 448; 5T.
- Added to test the rendering of ROIs of varying scales (the ROIs are in separate files and are not included here).

### `michael/`

- One LIF file with 8 images, each with 12 planes. Shape: 2C, 3Z, 2T. 
- Added for a PR that fixed a bug when the tile dimensions is not the outer-most dimension.

### `imagesc-30856/`

- One LIF file, 8 images. 1024 x 1024. Some 2C, some Z, some 2C x 39Z, some single plane.
- Added for a bug in which the FlipX, FlipY and SwapXY fields were ignored when tiling.
