"""Reference values of the check „Vacancy: city values against the 1-km grid“ (`reference/check_reference.csv`,
`vacancy_all_km_2022` and `vacancy_market_km_2022`; pipeline/use_cases/housing/README.md, Checks).

Run from the repo root: .venv/bin/python -I research/scripts/vacancy_km.py > research/results/vacancy_km.txt
Reads interim/cells_2022.csv (from the build), the 1-km extracts of both vacancy rates in sources/zensus/grid/ and the
dwellings of the 1-km grid from cache/zensus_dwellings.zip (a download of the pipeline, not extracted to sources/).

Method: the 1-km cells wholly inside Frankfurt (every 100-m cell of the build in it has a district) and wholly
inside BBOX_3035; their rates weighted with the dwellings of the 1-km grid. „–“ counts as 0 (dataset description).
"""
import zipfile
from pathlib import Path

import pandas as pd

from pipeline.shared.zensus.model import BBOX_3035

ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "sources" / "zensus" / "grid"
DWELLINGS_ZIP = ROOT / "cache" / "zensus_dwellings.zip"
DWELLINGS_1KM = "Flaeche_der_Wohnung_10m2_Intervalle/Zensus2022_Flaeche_der_Wohnung_10m2_Intervalle_1km-Gitter.csv"
RATES = (("vacancy_all_km_2022", "Zensus2022_Leerstandsquote_1km-Gitter_Frankfurt.csv", "Leerstandsquote"),
         ("vacancy_market_km_2022", "Zensus2022_Marktaktive_Leerstandsquote_1km-Gitter_Frankfurt.csv",
          "marktaktive_Leerstandsquote"))


def number(values: pd.Series) -> pd.Series:
    """German numbers of the grid files: dot for thousands, comma for decimals, „–“ for 0."""
    text = values.str.replace(".", "", regex=False).str.replace(",", ".", regex=False).replace({"–": "0", "-": "0"})
    return pd.to_numeric(text, errors="coerce")


def km_of(cell_id: pd.Series) -> pd.Series:
    n = cell_id.str.extract(r"N(\d+)E(\d+)").astype(int)
    return "CRS3035RES1000mN" + (n[0] // 1000 * 1000).astype(str) + "E" + (n[1] // 1000 * 1000).astype(str)


def inside(km_ids: pd.Index) -> pd.Index:
    """1-km cells (lower left corner in the id) that lie wholly inside BBOX_3035."""
    corner = km_ids.str.extract(r"N(\d+)E(\d+)").astype(int)
    x0, y0, x1, y1 = BBOX_3035
    keep = ((corner[1] >= x0) & (corner[1] + 1000 <= x1) & (corner[0] >= y0) & (corner[0] + 1000 <= y1)).values
    return km_ids[keep]


def main() -> None:
    cells = pd.read_csv(ROOT / "interim" / "cells_2022.csv", dtype={"cell_id": str})
    wholly = cells.groupby(km_of(cells.cell_id)).district.apply(lambda s: s.notna().all())
    ids = inside(wholly[wholly].index)
    with zipfile.ZipFile(DWELLINGS_ZIP) as zf:
        frame = pd.read_csv(zf.open(DWELLINGS_1KM), sep=";", dtype=str, usecols=["GITTER_ID_1km", "Insgesamt_Wohnungen"])
    weight = pd.Series(number(frame.Insgesamt_Wohnungen).values, index=frame.GITTER_ID_1km.values).reindex(ids).dropna()
    print(f"1-km cells wholly inside Frankfurt and the box, with dwellings: {len(weight)}")
    print(f"dwellings of these cells (1-km grid): {int(weight.sum())}")
    for key, name, column in RATES:
        frame = pd.read_csv(GRID / name, sep=";", dtype=str, encoding="utf-8-sig")
        rate = pd.Series(number(frame[column]).values, index=frame.GITTER_ID_1km.values).reindex(weight.index)
        ok = rate.notna()
        print(f"{key}: {(rate[ok] * weight[ok]).sum() / weight[ok].sum():.3f} % ({int(ok.sum())} cells with a rate)")


if __name__ == "__main__":
    main()
