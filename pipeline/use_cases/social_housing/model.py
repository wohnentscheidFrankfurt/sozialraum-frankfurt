"""Social housing per quarter (README)."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.areas import city_rows
from pipeline.shared.geography.model import AIRPORT_MERGED

OUTSIDE = "außerhalb frankfurts"


def merge_quarters(table: dict[str, list[int]], quarters: set[str]) -> tuple[dict[str, list[int]], list[int]]:
    """Flughafen joins Sachsenhausen-Süd as in the map, „außerhalb Frankfurts“ is kept apart. Stops on unknown or
    missing quarters."""
    rest = {n: v for n, v in table.items() if n != "Gesamt"}
    outside = [rest.pop(n) for n in list(rest) if n.lower() == OUTSIDE]
    if len(outside) != 1:
        raise ValueError("row 'außerhalb Frankfurts' missing or duplicate")
    south, airport = rest.pop("Sachsenhausen-Süd", None), rest.pop("Flughafen", None)
    if south is None or airport is None:
        raise ValueError("Sachsenhausen-Süd or Flughafen missing")
    rest[AIRPORT_MERGED] = [a + b for a, b in zip(south, airport)]
    unknown, missing = sorted(set(rest) - quarters), sorted(quarters - set(rest))
    if unknown or missing:
        raise ValueError(f"quarters do not match: unknown {unknown}, missing {missing}")
    return rest, outside[0]


def stock_on_quarters(stock: dict[str, int], quarters: set[str], airport_row: str) -> dict[str, float]:
    """Dwellings of the city per quarter of the map; the row with the airport is the merged quarter. Stops on unknown
    or missing quarters."""
    out = {AIRPORT_MERGED if n == airport_row else n: float(v) for n, v in stock.items()}
    unknown, missing = sorted(set(out) - quarters), sorted(quarters - set(out))
    if unknown or missing:
        raise ValueError(f"dwelling stock: quarters do not match: unknown {unknown}, missing {missing}")
    return out


def indicators(stock: dict[str, list[int]], dwellings: dict[str, float]) -> pd.DataFrame:
    rows = []
    for q in sorted(stock):
        n = stock[q][0]
        rows.append({"quarter": q, "SH_COUNT": n, "SH_SHARE": 100 * n / dwellings[q] if dwellings.get(q) else None})
    return pd.DataFrame(rows)


def city_totals(stock: dict[str, list[int]], dwellings: dict[str, float]) -> dict:
    n = sum(v[0] for v in stock.values())
    return {"SH_COUNT": n, "SH_SHARE": 100 * n / sum(dwellings.values())}


def city_values_rows(info: dict) -> list[dict]:
    return city_rows({"SH_SHARE": info["SH_SHARE"]})
