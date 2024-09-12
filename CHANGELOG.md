
## Changelog

#### 0.6.5
- Added a new attribute `settings` to `LifImage` which contains useful capture settings (Thanks to PR from @tmtenbrink).

#### 0.6.4
- Fixed bug and incompatibility in 0.6.3.
- Added preliminary fix for images captured with stage navigator.

#### 0.6.3
- Added support for updated LasX with additional data in the LIF file.
- Changed the way file names are assigned, now includes folder path. This fix is intended to clarify imaging sets with many duplicate names.

#### 0.6.2
- Fixed bug where the time and image scale were calculated incorrectly.
- Clarified scaling documentation.

#### 0.6.1
- Update readme.

#### 0.6.0
- Added support for non-XY images with `get_plane()`. See docs for usage. Note: Reading arbitrary planes (i.e. an XZ plane of an XY image) is not yet supported.

#### 0.5.2
- Bugfix: Fix error in mosaic parsing. `PosX` metadata was incorrectly read from `PosY`.

#### 0.5.1
- Bugfix: switch from `io.BufferedIOBase` to `io.IOBase`.

#### 0.5.0
- Added support for loading files from buffers (thanks to PR from @JacksonMaxfield).

#### 0.4.1
- Fixed critical documentaiton error: `LifImage.scale` is in px/µm, not px/nm for X and Y dimensions.

#### 0.4.0
- Added support for tiled images:
    - `m` was added as a new dimension (for tiled images).
    - `LifImage` changes:
        - New `get_iter_m()` function.
        - New `mosaic_position` attribute with `(FieldX, FieldY, PosX, PosY)`.
- Under the hood changes:
    - `LifImage.dims` is now a named tuple for clearer code.
- Other changes:
    - Prettier outputs for `repr()`.
    - Switch to github CI.

#### 0.3.1
- Added error message for tiled images, pending feature addition.

#### 0.3.0
- Added support for 16-bit images, increased minimum Pillow version to 7.2.0.
    - New `LifImage` attribute `bit_depth` is a tuple of intigers descibing the bit depth for each channel in the image.
    - Thanks to @DirkRemmers for providing the example file.
- Changed type from `str` to `int` for `dims` and `channels` in the `info` dictionary.
- Added python 3.9 to build testing.

#### 0.2.1
- Fixed `ZeroDivisionError` when the Z-dimension is defined, but has a length of 0.
- Clarified an error message.
- Added fix for truncated files.

#### 0.2.0
- `LifImage.scale` now returns px/nm conversions.

#### 0.1.1
- Style changes.

#### 0.1.0
- Initial release.
