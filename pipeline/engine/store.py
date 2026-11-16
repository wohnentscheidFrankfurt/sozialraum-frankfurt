"""Interim datasets on disk. Steps exchange data only through the store."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pipeline.engine.datasets import Dataset


class Store:
    def __init__(self, root: Path, producers: dict[str, str] | None = None):
        self.root = root
        self.producers = producers or {}

    def path(self, dataset: Dataset) -> Path:
        return self.root / f"{dataset.name}.{dataset.kind}"

    def read(self, dataset: Dataset):
        path = self.path(dataset)
        if not path.exists():
            producer = self.producers.get(dataset.name)
            hint = f"; run `--step {producer}` first" if producer else ""
            raise FileNotFoundError(f"{path.name} missing in {self.root}{hint}")
        if dataset.kind == "csv":
            columns = pd.read_csv(path, nrows=0, float_precision="round_trip").columns
            return pd.read_csv(path, dtype={k: str for k in dataset.keys if k in columns},
                               float_precision="round_trip")
        text = path.read_text(encoding="utf-8")
        return json.loads(text) if dataset.kind == "json" else text

    def write(self, dataset: Dataset, data) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.path(dataset)
        if dataset.kind == "csv":
            data.to_csv(path, index=False)
        elif dataset.kind == "json":
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            path.write_text(data, encoding="utf-8")
        return path
