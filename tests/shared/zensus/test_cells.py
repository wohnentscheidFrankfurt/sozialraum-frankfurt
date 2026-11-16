import pandas as pd

from pipeline.engine.datasets import CELLS_2022
from pipeline.engine.store import Store
from pipeline.shared.zensus.cells import inner_cells


def test_inner_cells_drops_edge_cells(tmp_path):
    store = Store(tmp_path)
    store.write(CELLS_2022, pd.DataFrame({"cell_id": ["a", "b"], "district": ["1", "1"], "quarter": ["Q", "Q"],
                                          "edge": [0, 1]}))
    assert inner_cells(store)["cell_id"].tolist() == ["a"]


def test_steps_knows_no_zensus_cells():
    from pipeline.engine import steps
    assert not hasattr(steps, "inner_cells")


def test_annotations_resolve():
    """The return type of inner_cells names pandas, so cells.py must import it."""
    import typing
    assert typing.get_type_hints(inner_cells)["return"] is pd.DataFrame
