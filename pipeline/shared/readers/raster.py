"""1 m height tiles (Hessen DOM1/DGM1, GeoTIFF, LZW, float32) read from a ZIP, and PNG pixels of WMS answers.

A tile covers 1 km. Row 0 is the north edge: the pixel centre of row 0 lies at y = ty * 1000 + 999.5 and the
centre of column 0 at x = tx * 1000 + 0.5 (EPSG:25832, `.tfw`). Nodata is -9999 and becomes NaN. Stateless:
callers cache tiles if they want to.
"""
from __future__ import annotations

import io
import zipfile
from collections.abc import Callable

import numpy as np
import pymupdf
import tifffile

NODATA = -9999
TILE_M = 1000


def read_tile(z: zipfile.ZipFile, name: str) -> np.ndarray | None:
    """Tile as float32 with NaN for nodata, or None if the ZIP has no such member."""
    try:
        data = z.read(name)
    except KeyError:
        return None
    a = tifffile.imread(io.BytesIO(data)).astype(np.float32)
    a[a == NODATA] = np.nan
    return a


def mosaic(z: zipfile.ZipFile, name_of: Callable[[int, int], str], x0: int, y0: int, x1: int, y1: int) -> np.ndarray:
    """Grid of 1 m pixels with centres x0+0.5 .. x1-0.5 (row 0 = north); NaN where no tile."""
    out = np.full((y1 - y0, x1 - x0), np.nan, dtype=np.float32)
    for tx in range(x0 // TILE_M, (x1 - 1) // TILE_M + 1):
        for ty in range(y0 // TILE_M, (y1 - 1) // TILE_M + 1):
            a = read_tile(z, name_of(tx, ty))
            if a is None:
                continue
            gx0, gx1 = max(x0, tx * TILE_M), min(x1, tx * TILE_M + TILE_M)
            gy0, gy1 = max(y0, ty * TILE_M), min(y1, ty * TILE_M + TILE_M)
            out[y1 - gy1:y1 - gy0, gx0 - x0:gx1 - x0] = \
                a[ty * TILE_M + TILE_M - gy1:ty * TILE_M + TILE_M - gy0, gx0 - tx * TILE_M:gx1 - tx * TILE_M]
    return out


def png_rgb(data: bytes) -> np.ndarray:
    """PNG bytes as H x W x 3 float array (alpha dropped)."""
    pix = pymupdf.Pixmap(data)
    a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    return a[..., :3].astype(float)
