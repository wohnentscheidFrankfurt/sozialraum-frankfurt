"""Ids of the 100 m and 1 km Zensus grids (EPSG:3035)."""
from __future__ import annotations

import re

_CELL_ID = re.compile(r"N(\d+)E(\d+)$")
_KM_CELL_ID = re.compile(r"^CRS3035RES1000mN(\d+)E(\d+)$")
KM = 1000


def cell_center(cell_id: str) -> tuple[int, int]:
    """Center (x, y) of a 100 m cell in EPSG:3035, for example from 'CRS3035RES100mN2691700E4341100'."""
    m = _CELL_ID.search(cell_id)
    if not m:
        raise ValueError(f"unknown grid id: {cell_id!r}")
    return int(m.group(2)) + 50, int(m.group(1)) + 50


def km_cell(cell_id: str) -> str:
    """The 1 km cell that holds a 100 m cell: north and east of the lower left corner rounded down to the
    kilometre, for example 'CRS3035RES100mN3002900E4222800' -> 'CRS3035RES1000mN3002000E4222000'."""
    m = re.fullmatch(r"CRS3035RES100mN(\d+)E(\d+)", cell_id)
    if not m:
        raise ValueError(f"unknown grid id: {cell_id!r}")
    north, east = (int(g) // KM * KM for g in m.groups())
    return f"CRS3035RES1000mN{north}E{east}"


def km_cell_corner(cell_id: str) -> tuple[int, int]:
    """Lower left corner (x, y) of a 1 km cell in EPSG:3035, for example from 'CRS3035RES1000mN3002000E4222000'."""
    m = _KM_CELL_ID.match(cell_id)
    if not m:
        raise ValueError(f"unknown grid id: {cell_id!r}")
    return int(m.group(2)), int(m.group(1))
