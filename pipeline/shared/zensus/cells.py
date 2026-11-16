"""Step helper for the Zensus grid: the inner cells of 2022, read through the store; steps of use cases and of map/
import it."""
from __future__ import annotations

import pandas as pd

from pipeline.engine.datasets import CELLS_2022


def inner_cells(store) -> pd.DataFrame:
    """Cells of the 2022 grid inside Frankfurt (no edge cells)."""
    cells = store.read(CELLS_2022)
    return cells[cells["edge"] == 0].reset_index(drop=True)

