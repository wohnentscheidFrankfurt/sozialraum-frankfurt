"""Answers of the GENESIS web clients (Zensus database, Regionaldatenbank) as long tables of one region
(pipeline/update_sources.py, sources/README.md)."""
from __future__ import annotations

import csv
import io
import itertools


def _positions(index) -> dict[int, str]:
    """A JSON-stat index is an object (code -> position) or a list of codes in order."""
    return dict(enumerate(index)) if isinstance(index, list) else {i: code for code, i in index.items()}


def _at(values, flat: int, empty=None):
    """Values and status are lists or objects keyed by the flat position."""
    if isinstance(values, list):
        return values[flat]
    return values.get(str(flat), empty)


def _order(ds: dict) -> tuple:
    """Datasets in the order of their variables, then of their codes: the API sends them in no fixed order, and two
    datasets can share their variables (for example one per content)."""
    return ds["id"], [sorted(map(str, _positions(ds["dimension"][k]["category"]["index"]).values())) for k in ds["id"]]


def long_rows(structure: dict, answer: dict, table: str, region_var: str, region: str,
              region_column: str) -> list[dict]:
    """One row per value of the region: the code and label of every other variable, the value and its quality.
    Datasets without the region variable (the country, the Länder) are skipped."""
    if "variableValues" not in structure:
        raise ValueError(f"{table}: the structure has no variableValues; the API has changed")
    labels = {code: v["label"]["de"] for code, v in structure["variableValues"].items()}
    rows = []
    for ds in sorted(answer["data"], key=_order):
        ids, size = ds["id"], ds["size"]
        if region_var not in ids:
            continue
        codes = {k: _positions(ds["dimension"][k]["category"]["index"]) for k in ids}
        strides = [1] * len(size)
        for i in range(len(size) - 2, -1, -1):
            strides[i] = strides[i + 1] * size[i + 1]
        status = ds.get("status") or {}
        for combo in itertools.product(*[range(n) for n in size]):
            if codes[region_var][combo[ids.index(region_var)]] != region:
                continue
            flat = sum(c * s for c, s in zip(combo, strides))
            row = {"table": table, region_column: region}
            for k, c in zip(ids, combo):
                if k not in (region_var, "statistic"):
                    row[k] = codes[k][c]
                    row[k + "_label"] = labels.get(codes[k][c], "")
            row.update(value=_at(ds["value"], flat), quality=_at(status, flat, ""))
            rows.append(row)
    if not rows:
        raise ValueError(f"no values for {region} in {table}")
    return rows


def long_csv(rows: list[dict], order: tuple[str, ...] = ()) -> str:
    """Semicolon CSV with every column once, in the order the columns first appear. `order` sorts the rows by these
    columns (missing = empty); the sort is stable."""
    fields = list(dict.fromkeys(k for r in rows for k in r))
    if order:
        rows = sorted(rows, key=lambda r: tuple(r.get(k, "") for k in order))
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()
