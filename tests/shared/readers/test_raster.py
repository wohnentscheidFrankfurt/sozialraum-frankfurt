import io
import zipfile

import numpy as np
import pymupdf
import tifffile

from pipeline.shared.readers.raster import mosaic, png_rgb, read_tile


def _name(tx, ty):
    return f"T_{tx}_{ty}.tif"


def _zip(path, tiles):
    with zipfile.ZipFile(path, "w") as z:
        for (tx, ty), arr in tiles.items():
            buf = io.BytesIO()
            tifffile.imwrite(buf, arr, compression="lzw")
            z.writestr(_name(tx, ty), buf.getvalue())
    return zipfile.ZipFile(path)


def test_mosaic_joins_two_tiles_across_a_km_border(tmp_path):
    a = np.full((1000, 1000), 10, dtype=np.float32)
    b = np.full((1000, 1000), 20, dtype=np.float32)
    a[0, 999] = 99  # north-east corner pixel of tile (5, 7): centre (5999.5, 7999.5)
    b[999, 0] = 77  # south-west corner pixel of tile (6, 7): centre (6000.5, 7000.5)
    z = _zip(tmp_path / "t.zip", {(5, 7): a, (6, 7): b})
    m = mosaic(z, _name, 5990, 7990, 6010, 8000)
    assert m.shape == (10, 20)
    assert m[0, 9] == 99 and m[0, 10] == 20 and m[0, 8] == 10
    m2 = mosaic(z, _name, 5990, 7000, 6010, 7010)
    assert m2[9, 10] == 77 and m2[9, 9] == 10
    assert m2.dtype == np.float32


def test_nodata_and_missing_tiles_are_nan(tmp_path):
    a = np.full((1000, 1000), 5, dtype=np.float32)
    a[999, 0] = -9999
    z = _zip(tmp_path / "t.zip", {(5, 7): a})
    assert read_tile(z, "nope.tif") is None
    assert np.isnan(read_tile(z, _name(5, 7))[999, 0])
    m = mosaic(z, _name, 5000, 7000, 5002, 7001)
    assert np.isnan(m[0, 0]) and m[0, 1] == 5
    out = mosaic(z, _name, 4999, 7000, 5001, 7001)
    assert np.isnan(out[0, 0])


def test_png_rgb_shape():
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 3, 2), False)
    pix.set_rect(pix.irect, (10, 20, 30))
    rgb = png_rgb(pix.tobytes("png"))
    assert rgb.shape == (2, 3, 3)
    assert rgb[0, 0].tolist() == [10, 20, 30]
