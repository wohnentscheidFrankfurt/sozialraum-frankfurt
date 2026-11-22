"""Readers of the table extracts of the Zensus database (4000W and 3000G) from sources/."""
from __future__ import annotations

import csv
import re

from pipeline.shared.zensus.model import CLASSES, SIZES


# Long CSV of the Zensus database (pipeline/update_sources.py), tables 4000W-1011, 4000W-2002, 4000W-1008 and 3000G-2001
GEBEG1_CODES = dict(zip(CLASSES, ["EIG-GEMEIN", "EIG-PRIVAT", "EIG-GENOSS", "EIG-KOMMUN", "EIG-UNT-PRIVAT1",
                                  "EIG-UNT-PRIVAT2", "EIG-BUND-LAND", "EIG-ORGA"])) | {"total": "%TOTAL%"}
REFERENCE_DAYS = {"2011-05-09": 2011, "2022-05-15": 2022}
DWELLINGS_COUNT, BUILDINGS_COUNT = "WHG002$ID0004", "GEB001$QMU"  # counts; "WHG002$PO0004" are percentages
# Table 4000W-2002: use of the dwelling (WHGNZ2) by ownership type; the vacancy readers use three uses
USE_CODES = {"vacant": "NUTZ-LEER", "owner": "NUTZ-EIGEN", "rented": "NUTZ-MIETE"}
ALL = "%TOTAL%"


def _long_rows(text: str, content: str) -> list[dict]:
    rows = [r for r in csv.DictReader(text.lstrip("\ufeff").splitlines(), delimiter=";") if r["content"] == content]
    if not rows:
        raise ValueError(f"no rows with content {content}")
    return rows


def _check_complete(values: dict[int, dict], keys: list[str], what: str, years=REFERENCE_DAYS.values()) -> None:
    for year in years:
        missing = sorted(set(keys) - set(values.get(year, {})))
        if missing:
            raise ValueError(f"{what}: {year} has no values for {missing}")


def long_values(text: str, content: str, key: str, codes: dict[str, str], years=REFERENCE_DAYS.values(),
                fixed: dict[str, str] | None = None) -> dict[int, dict[str, int]]:
    """Counts of one content per year and name from a long CSV: name -> code of the column `key`; `fixed` holds the
    codes of other columns (for example the total of the use). Stops on a missing code or year, a blank or a double
    value."""
    by_code = {v: k for k, v in codes.items()}
    out: dict[int, dict[str, int]] = {}
    what = ""
    for r in _long_rows(text, content):
        what = f"table {r['table']}"
        year = REFERENCE_DAYS[r["STAG"]]
        if year not in years or r[key] not in by_code or any(r[c] != v for c, v in (fixed or {}).items()):
            continue
        name = by_code[r[key]]
        if not r["value"].strip():
            raise ValueError(f"{what}: {year} {name} has no value")
        if name in out.setdefault(year, {}):
            raise ValueError(f"{what}: {year} {name} twice")
        out[year][name] = int(float(r["value"]))
    _check_complete(out, list(codes), what or "table", years)
    return out


def read_dwellings_history(text: str) -> dict[int, dict[str, int]]:
    """Dwellings per ownership type (CLASSES and 'total') and year from table 4000W-1011."""
    return long_values(text, DWELLINGS_COUNT, "GEBEG1", GEBEG1_CODES)


def read_4000w(text: str) -> dict[str, int]:
    """Dwellings per ownership type (CLASSES and 'total') in 2022 over all uses, from table 4000W-2002."""
    return long_values(text, DWELLINGS_COUNT, "GEBEG1", GEBEG1_CODES, years=[2022], fixed={"WHGNZ2": ALL})[2022]


def read_vacancy_4000w(text: str) -> dict[str, int]:
    """Vacant dwellings, and occupied plus vacant dwellings (all ownership types) in 2022 from table 4000W-2002
    (pipeline/use_cases/housing/README.md)."""
    v = long_values(text, DWELLINGS_COUNT, "WHGNZ2", USE_CODES, years=[2022], fixed={"GEBEG1": ALL})[2022]
    return {"vacant": v["vacant"], "occupied_and_vacant": v["vacant"] + v["owner"] + v["rented"]}


def read_condo_use(text: str) -> dict[int, dict[str, int]]:
    """Dwellings of the WEG class by use per year from table 4000W-2002: owner-occupied, rented and all uses."""
    return long_values(text, DWELLINGS_COUNT, "WHGNZ2", {"owner": USE_CODES["owner"], "rented": USE_CODES["rented"],
                                                         "total": ALL}, fixed={"GEBEG1": GEBEG1_CODES["condo"]})


# Table 3000G-2001: the decades of construction (GEBBJ5) and the key of their text in the language files
# (pipeline/use_cases/ownership_history/texts.<lang>.yaml, decade_labels). The label of the source stays in the data.
DECADE_KEYS = {"BAU0000B1918": "before_1919", "BAU1919B1949": "1919_1949", "BAU1950B1959": "1950_1959",
               "BAU1960B1969": "1960_1969", "BAU1970B1979": "1970_1979", "BAU1980B1989": "1980_1989",
               "BAU1990B1999": "1990_1999", "BAU2000B2009": "2000_2009", "BAU2010B2015": "2010_2015",
               "BAU2016BXXXX": "from_2016"}


def _first_year(code: str) -> int:
    return int(re.match(r"BAU(\d{4})", code).group(1))


def read_buildings_by_decade(text: str) -> tuple[list[dict], dict[int, dict[str, dict[str, int]]]]:
    """Buildings per year of construction (decades), ownership type and year from table 3000G-2001.
    The decades keep the order of the source; the decade '%TOTAL%' becomes 'total'. Each decade carries the key of its
    text (DECADE_KEYS); an unknown decade raises KeyError."""
    by_code = {v: k for k, v in GEBEG1_CODES.items()}
    decades: dict[str, dict] = {}
    out: dict[int, dict[str, dict[str, int]]] = {}
    for r in _long_rows(text, BUILDINGS_COUNT):
        decade = "total" if r["GEBBJ5"] == "%TOTAL%" else r["GEBBJ5"]
        if decade != "total" and decade not in decades:
            if decade not in DECADE_KEYS:
                raise KeyError(f"table 3000G-2001: unknown decade {decade}; add it to DECADE_KEYS and its text")
            decades[decade] = {"decade": decade, "key": DECADE_KEYS[decade],
                               "label": r["GEBBJ5_label"].replace(" - ", "–"), "first_year": _first_year(decade)}
        out.setdefault(REFERENCE_DAYS[r["STAG"]], {}).setdefault(by_code[r["GEBEG1"]], {})[decade] = int(float(r["value"]))
    _check_complete(out, list(GEBEG1_CODES), "table 3000G-2001")
    return list(decades.values()), out


# Tables 3000G-2007 and 4000W-2013: ownership type by dwellings in the building (GEBWG2)
SIZE_CODES = dict(zip(SIZES, ["WOHN01", "WOHN02", "WOHN03B06", "WOHN07B12", "WOHN13UM"]))
DWELLINGS_BY_SIZE = "WHG002$QMU"


def _read_by_size(text: str, content: str, table: str) -> dict[int, dict[str, dict[str, int]]]:
    by_code = {v: k for k, v in GEBEG1_CODES.items()}
    by_size = {v: k for k, v in SIZE_CODES.items()} | {"%TOTAL%": "total"}
    out: dict[int, dict[str, dict[str, int]]] = {}
    for r in _long_rows(text, content):
        for column, known in (("STAG", REFERENCE_DAYS), ("GEBEG1", by_code), ("GEBWG2", by_size)):
            if r[column] not in known:
                raise ValueError(f"table {table}: unknown {column} code {r[column]}")
        year, k, size = REFERENCE_DAYS[r["STAG"]], by_code[r["GEBEG1"]], by_size[r["GEBWG2"]]
        # a blank cell must not become 0: the size sums would not notice a small gap
        if not r["value"].strip():
            raise ValueError(f"table {table}: {year} {k} size {size} has no value")
        out.setdefault(year, {}).setdefault(k, {})[size] = int(float(r["value"]))
    _check_complete(out, list(GEBEG1_CODES), f"table {table}")
    for year in sorted(out):
        for k, sizes in out[year].items():
            missing = sorted(set(SIZES + ["total"]) - set(sizes), key=(SIZES + ["total"]).index)
            if missing:
                raise ValueError(f"table {table}: {year} {k} has no values for {missing}")
    return out


def read_buildings_by_size(text: str) -> dict[int, dict[str, dict[str, int]]]:
    """Buildings per ownership type (CLASSES and 'total'), size (SIZES and 'total') and year from table 3000G-2007."""
    return _read_by_size(text, BUILDINGS_COUNT, "3000G-2007")


def read_dwellings_by_size(text: str) -> dict[int, dict[str, dict[str, int]]]:
    """Dwellings per ownership type, size and year from table 4000W-2013."""
    return _read_by_size(text, DWELLINGS_BY_SIZE, "4000W-2013")


# Table 4000W-1008 of the Zensus database: dwellings by year of construction in Mikrozensus classes, Frankfurt, 2011
# and 2022; long CSV of pipeline/update_sources.py (pipeline/use_cases/construction_year/README.md)
CONSTRUCTION_CODES = {"pre1919": "BAU0000B1918", "1949_1978": "BAU1949B1978", "total": ALL}


def read_dwellings_by_construction_year(text: str) -> dict[int, dict[str, int]]:
    """Dwellings before 1919, from 1949 to 1978 and in total, per year, from table 4000W-1008. Stops on a missing
    class or year."""
    return long_values(text, DWELLINGS_COUNT, "GEBBJ7", CONSTRUCTION_CODES)


# Tables 4000W-0001 and 4000W-0004 of the Zensus database: one value for Frankfurt (checks of `housing`)
OWNER_RATE, RENT_SQM = "WHG007$QMU", "WHG012$QMU"  # Eigentumsquote (%), durchschnittliche Nettokaltmiete (€/m²)
VACANCY_RATE = "WHG009$QMU"  # Leerstandsquote (%), table 4000W-0001


def read_city_value(text: str, content: str, day: str = "2022-05-15") -> float:
    """The value of one content on one reference day from a long CSV of the Zensus database
    (pipeline/update_sources.py). Stops when the row is missing or appears twice."""
    rows = [r for r in _long_rows(text, content) if r["STAG"] == day]
    if len(rows) != 1:
        raise ValueError(f"content {content} on {day}: {len(rows)} rows, expected 1")
    return float(rows[0]["value"])
