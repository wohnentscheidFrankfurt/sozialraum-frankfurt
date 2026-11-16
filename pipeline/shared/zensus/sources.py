"""Zensus grid files 2022 and 2011: column names, value notation, the Frankfurt extracts (pipeline/update_sources.py)
and their readers. The table extracts of the Zensus database are read in tables.py."""
from __future__ import annotations

import csv
import io
import re
import zipfile
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from pipeline.shared.core.grid import KM, cell_center, km_cell_corner
from pipeline.shared.zensus.model import CLASSES, SIZES, in_bbox, square_meets_bbox


def count(text: str) -> int:
    """Zensus count: '–' means zero, '1,803' has a thousands separator."""
    s = text.strip()
    if s in ("", "–", "-"):
        return 0
    if re.fullmatch(r"\d{1,3}(,\d{3})+", s):
        s = s.replace(",", "")
    return int(s)


def mean(text: str) -> float | None:
    """Zensus mean with a decimal comma (rent). '–' means: no value, because an average rent of zero does
    not exist."""
    s = text.strip()
    if s in ("", "–", "-"):
        return None
    return float(s.replace(",", "."))


def rate(text: str) -> float | None:
    """Zensus rate with a decimal comma. '–' means „Genau Null oder auf Null geändert“ (dataset description)."""
    s = text.strip()
    if s in ("–", "-"):
        return 0.0
    return mean(s)


def dash(text: str) -> int:
    """Flag: 1 where the source shows '–' („Genau Null oder auf Null geändert“), else 0. It tells a rate that is
    zero or zeroed from a rate that is counted."""
    return int(text.strip() in ("–", "-"))


# kind per column: count ('–' = 0), mean ('–' = no value), rate ('–' = 0), dash (1 for '–', else 0)
READERS = {"count": count, "mean": mean, "rate": rate, "dash": dash}
# source column -> (target, kind), or a list of pairs when the column feeds several targets
GRID_FILES = {
    "zensus_population.zip": {"Einwohner": ("pop", "count")},
    "zensus_owner_rate.zip": {"Eigentuemerquote": ("owner_rate", "rate")},
    "zensus_rent.zip": {"durchschnMieteQM": ("rent_sqm", "mean"), "AnzahlWohnungen": ("rented_dwellings", "count")},
    "zensus_vacancy.zip": {"Leerstandsquote": [("vacancy_rate", "rate"), ("vacancy_rate_dash", "dash")]},
    "zensus_vacancy_market.zip": {
        "marktaktive_Leerstandsquote": [("vacancy_rate_market", "rate"), ("vacancy_rate_market_dash", "dash")]},
    "zensus_dwellings.zip": {"Insgesamt_Wohnungen": ("dwellings", "count")},
    "zensus_ownership.zip": {
        "Insgesamt_Gebaeude": ("bld_owner_total", "count"),
        "Gemeinschaft_Wohneigentuemer": ("bld_condo", "count"),
        "Privatpersonen": ("bld_person", "count"),
        "Wohnungsgenossenschaft": ("bld_coop", "count"),
        "Kommune_kommunales_Wohnunternehm": ("bld_municipal", "count"),
        "Privatwirtsch_Wohnungsunternehm": ("bld_housing_company", "count"),
        "Anderes_privatwirtsch_Unternehm": ("bld_other_company", "count"),
        "Bund_oder_Land": ("bld_state", "count"),
        "Organisation_ohne_Erwerbszweck": ("bld_nonprofit", "count"),
    },
    # buildings per number of dwellings (pipeline/use_cases/public_housing/README.md)
    "zensus_buildings_by_size.zip": dict(zip(
        ["1_Wohnung", "2_Wohnungen", "3bis6_Wohnungen", "7bis12_Wohnungen", "13undmehr_Wohnungen"],
        [(f"bld_size_{s}", "count") for s in SIZES])),
}


def targets(entry: tuple[str, str] | list[tuple[str, str]]) -> list[tuple[str, str]]:
    """The (target, kind) pairs a source column feeds."""
    return [entry] if isinstance(entry, tuple) else list(entry)


_TARGETS = [pair for columns in GRID_FILES.values() for entry in columns.values() for pair in targets(entry)]
COUNT_COLUMNS = [target for target, kind in _TARGETS if kind in ("count", "dash")]  # whole numbers, 0 where missing
VALUE_COLUMNS = [target for target, kind in _TARGETS if kind not in ("count", "dash")]
# 1 km grids of the vacancy rates: ZIP -> column of the rate (housing use case, sources/README.md)
GRID_KM_COLUMNS = {"zensus_vacancy.zip": "Leerstandsquote", "zensus_vacancy_market.zip": "marktaktive_Leerstandsquote"}

CODES_2011 = {i: f"dw_{c}_2011" for i, c in enumerate(CLASSES, start=1)}  # feature EIGENTUM, codes 1 to 8
# 2011 grid, features -> code -> column. Dwellings: per ownership type, in total and in two classes of the year of
# construction (BAUJAHR_MZ, codes 01 Vor 1919 and 03 1949–1978; pipeline/use_cases/construction_year/README.md). Buildings: per
# ownership type and per number of dwellings (ZAHLWOHNGN_HHG, codes 1 to 5).
FEATURES_2011 = {"EIGENTUM": CODES_2011, "INSGESAMT": {0: "dw_total_2011"},
                 "BAUJAHR_MZ": {1: "dw_pre1919_2011", 3: "dw_1949_1978_2011"}}
COLUMNS_2011 = ["cell_id", *CODES_2011.values(), "dw_total_2011", "dw_pre1919_2011", "dw_1949_1978_2011"]
FEATURES_2011_BUILDINGS = {"EIGENTUM": {i: f"bld_{c}_2011" for i, c in enumerate(CLASSES, start=1)},
                           "ZAHLWOHNGN_HHG": {i: f"bld_size_{s}_2011" for i, s in enumerate(SIZES, start=1)}}
COLUMNS_2011_BUILDINGS = ["cell_id", *(c for codes in FEATURES_2011_BUILDINGS.values() for c in codes.values())]
def grid_csv_name(zf: zipfile.ZipFile, zip_name: str) -> str:
    """The one 100 m CSV in a grid ZIP; stops on none or several."""
    names = [n for n in zf.namelist() if "100m" in n and n.endswith(".csv")]
    if len(names) != 1:
        raise ValueError(f"{zip_name}: expected one 100 m CSV, found {names}")
    return names[0]


def grid_km_csv_name(zf: zipfile.ZipFile, zip_name: str) -> str:
    """The one 1 km CSV in a grid ZIP; stops on none or several."""
    names = [n for n in zf.namelist() if "_1km-" in n and n.endswith(".csv")]
    if len(names) != 1:
        raise ValueError(f"{zip_name}: expected one 1 km CSV, found {names}")
    return names[0]


def _write_extract(target: Path, data: bytes, rows: int, zip_name: str) -> int:
    if not rows:
        raise ValueError(f"{zip_name}: no cell in the box around Frankfurt")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return rows


def extract_grid_2022(zip_path: Path, target: Path, columns: Iterable[str]) -> int:
    """The rows of the 100 m CSV whose cell lies in BBOX_3035, header and values unchanged (sources/README.md).
    Stops before it writes when the header lacks one of the columns the build reads."""
    with zipfile.ZipFile(zip_path) as zf, zf.open(grid_csv_name(zf, zip_path.name)) as raw:
        lines = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        head = next(lines)
        if not head.startswith("GITTER_ID_100m;"):
            raise ValueError(f"{zip_path.name}: the header does not start with GITTER_ID_100m: {head[:60]!r}")
        missing = [c for c in columns if c not in head.strip().split(";")]
        if missing:
            raise ValueError(f"{zip_path.name}: the header lacks the columns {missing}: {head.strip()[:120]!r}")
        rows = [line for line in lines if line.strip() and in_bbox(*cell_center(line.split(";", 1)[0]))]
    return _write_extract(target, (head + "".join(rows)).encode("utf-8"), len(rows), zip_path.name)


def extract_grid_km_2022(zip_path: Path, target: Path, column: str) -> int:
    """The rows of the 1 km CSV whose square meets BBOX_3035, header and values unchanged (sources/README.md). Stops
    before it writes when the header lacks the column the build reads."""
    with zipfile.ZipFile(zip_path) as zf, zf.open(grid_km_csv_name(zf, zip_path.name)) as raw:
        lines = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        head = next(lines)
        if not head.startswith("GITTER_ID_1km;"):
            raise ValueError(f"{zip_path.name}: the header does not start with GITTER_ID_1km: {head[:60]!r}")
        if column not in head.strip().split(";"):
            raise ValueError(f"{zip_path.name}: the header lacks the column {column}: {head.strip()[:120]!r}")
        rows = [line for line in lines if line.strip()
                and square_meets_bbox(*km_cell_corner(line.split(";", 1)[0]), KM)]
    return _write_extract(target, (head + "".join(rows)).encode("utf-8"), len(rows), zip_path.name)


def extract_grid_2011(zip_path: Path, target: Path, features: set[str]) -> int:
    """The rows of the 2011 100 m CSV with one of the features whose cell (Gitter_ID_100m_neu) lies in BBOX_3035,
    byte for byte (sources/README.md)."""
    with zipfile.ZipFile(zip_path) as zf, zf.open(grid_csv_name(zf, zip_path.name)) as raw:
        head = raw.readline()
        columns = head.decode("latin-1").strip().split(",")
        if columns[1:3] != ["Gitter_ID_100m_neu", "Merkmal"]:
            raise ValueError(f"{zip_path.name}: unexpected header {columns}")
        missing = [c for c in ("Auspraegung_Code", "Anzahl") if c not in columns]
        if missing:
            raise ValueError(f"{zip_path.name}: the header lacks the columns {missing}: {columns}")
        rows = []
        for line in raw:
            parts = line.decode("latin-1").split(",", 3)  # the text column may hold commas; it comes later
            if len(parts) > 3 and parts[2] in features and parts[1].startswith("CRS3035") \
                    and in_bbox(*cell_center(parts[1])):
                rows.append(line)
    return _write_extract(target, head + b"".join(rows), len(rows), zip_path.name)


FEATURES_2011_ALL = {"dwellings": set(FEATURES_2011), "buildings": set(FEATURES_2011_BUILDINGS)}


def read_grid_csv(path: Path, columns: dict[str, tuple[str, str] | list[tuple[str, str]]]) -> dict[str, dict]:
    """Reads a Frankfurt extract of a 2022 grid (sources/zensus/grid). The extract holds only cells in the rectangle
    around Frankfurt. Stops with the path when a column is missing."""
    values: dict[str, dict] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        head = next(reader)
        missing = [source for source in columns if source not in head]
        if missing:
            raise ValueError(f"{path}: the header lacks the columns {missing}")
        idx = {source: head.index(source) for source in columns}
        for row in reader:
            if not row:
                continue
            values[row[0]] = {target: READERS[kind](row[idx[source]]) for source, entry in columns.items()
                              for target, kind in targets(entry)}
    return values


def read_km_rates(path: Path, column: str) -> dict[str, float]:
    """Rates of a Frankfurt extract of a 1 km grid, per 1 km cell id ('–' = 0.0 as in the 100 m grid). Rows
    without a value are left out. Stops with the path when the column is missing."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        head = next(reader)
        if column not in head:
            raise ValueError(f"{path}: the header lacks the column {column}")
        i = head.index(column)
        rates = {row[0]: rate(row[i]) for row in reader if row}
    return {cell: value for cell, value in rates.items() if value is not None}


def read_2011(path: Path, cells: set[str]) -> pd.DataFrame:
    """Dwellings per ownership type, in total and in two classes of the year of construction in the given 2022 cells,
    from the extract of Wohnungen100m.csv."""
    return _read_2011_features(path, cells, FEATURES_2011, COLUMNS_2011)


def read_2011_buildings(path: Path, cells: set[str]) -> pd.DataFrame:
    """Buildings per ownership type and per number of dwellings in the given 2022 cells, from the extract of
    Geb100m.csv."""
    return _read_2011_features(path, cells, FEATURES_2011_BUILDINGS, COLUMNS_2011_BUILDINGS)


def _read_2011_features(path: Path, cells: set[str], features: dict[str, dict[int, str]],
                        columns: list[str]) -> pd.DataFrame:
    """Reads a Frankfurt extract of a 2011 grid and keeps the given features in the given 2022 cells. The column
    Gitter_ID_100m_neu already has the format of the 2022 grid ids. Stops on duplicate rows per cell and column,
    and on counts that are not numbers."""
    ch = pd.read_csv(path, encoding="latin-1", dtype=str,
                     usecols=["Gitter_ID_100m_neu", "Merkmal", "Auspraegung_Code", "Anzahl"])
    ch = ch[ch["Merkmal"].isin(list(features)) & ch["Gitter_ID_100m_neu"].isin(cells)]
    code = pd.to_numeric(ch["Auspraegung_Code"], errors="coerce")
    column = pd.Series([features[f].get(k) for f, k in zip(ch["Merkmal"], code)], index=ch.index, dtype=object)
    keep = column.notna()
    counts = pd.to_numeric(ch.loc[keep, "Anzahl"], errors="coerce")
    not_numbers = ch.loc[keep, "Gitter_ID_100m_neu"][counts.isna()].tolist()
    if not_numbers:
        raise ValueError(f"Zensus 2011: {len(not_numbers)} values in Anzahl are not numbers, "
                         f"for example in {sorted(set(not_numbers))[:5]}")
    df = pd.DataFrame({"cell_id": ch.loc[keep, "Gitter_ID_100m_neu"], "column": column[keep], "count": counts})
    duplicates = df[df.duplicated(["cell_id", "column"], keep=False)]
    if len(duplicates):
        raise ValueError(f"Zensus 2011: {len(duplicates)} duplicate rows per cell and column, for example "
                         f"{sorted(set(duplicates['cell_id']))[:5]}")
    if df.empty:
        return pd.DataFrame({c: pd.Series(dtype=str if c == "cell_id" else int) for c in columns})
    wide = df.pivot_table(index="cell_id", columns="column", values="count", aggfunc="first", fill_value=0)
    wide = wide.reindex(columns=columns[1:], fill_value=0).fillna(0).astype(int)
    return wide.reset_index().sort_values("cell_id").reset_index(drop=True)[columns]
