import numpy as np
import pandas as pd
import pytest

from pipeline.engine.datasets import Dataset
from pipeline.engine.store import Store

CELLS = Dataset("cells", keys=("cell_id", "district"))


def test_csv_round_trip_reads_keys_as_text(tmp_path):
    store = Store(tmp_path / "interim")
    store.write(CELLS, pd.DataFrame({"cell_id": ["007"], "district": ["10"], "pop": [3]}))
    df = store.read(CELLS)
    assert df["cell_id"].tolist() == ["007"] and df["district"].tolist() == ["10"] and df["pop"].tolist() == [3]
    assert (tmp_path / "interim" / "cells.csv").read_text() == "cell_id,district,pop\n007,10,3\n"


def test_csv_round_trip_is_exact_and_keeps_keys_and_gaps(tmp_path):
    d = Dataset("t", keys=("id",))
    values = [0.1 + 0.2, 31.183145201048546, 16.44673, 9.999999999999998, np.nan]
    Store(tmp_path).write(d, pd.DataFrame({"id": ["010", "2", "3", "4", "5"], "v": values}))
    back = Store(tmp_path).read(d)
    assert back["id"].tolist() == ["010", "2", "3", "4", "5"]
    assert back["v"].iloc[:4].tolist() == values[:4] and np.isnan(back["v"].iloc[4])


def test_keys_missing_in_the_file_are_ignored(tmp_path):
    store, ds = Store(tmp_path), Dataset("x", keys=("id", "quarter"))
    store.write(ds, pd.DataFrame({"id": ["01"]}))
    assert store.read(ds)["id"].tolist() == ["01"]


def test_json_and_markdown(tmp_path):
    store = Store(tmp_path)
    lists, report = Dataset("lists", kind="json"), Dataset("report", kind="md")
    store.write(lists, {"name": "GRÜNE", "n": [1]})
    assert (tmp_path / "lists.json").read_text(encoding="utf-8") == '{\n "name": "GRÜNE",\n "n": [\n  1\n ]\n}'
    assert store.read(lists) == {"name": "GRÜNE", "n": [1]}
    store.write(report, "# Report\n")
    assert store.read(report) == "# Report\n" and lists.file == "lists.json"


def test_read_missing_dataset_names_the_producer(tmp_path):
    with pytest.raises(FileNotFoundError, match=r"cells\.csv missing in .*; run `--step zensus` first"):
        Store(tmp_path, {"cells": "zensus"}).read(CELLS)
    with pytest.raises(FileNotFoundError, match=r"cells\.csv missing in "):
        Store(tmp_path).read(CELLS)


def test_datasets_have_unique_names():
    from pipeline.engine import datasets
    found = [v for v in vars(datasets).values() if isinstance(v, Dataset)]
    assert found and len({d.name for d in found}) == len(found)
