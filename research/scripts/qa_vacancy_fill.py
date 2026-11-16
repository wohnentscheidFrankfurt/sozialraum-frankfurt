"""QA of Lage and Belastung (research/2026-10-17-qa-situation-burden.md): the „–“ cells of the vacancy
rates, filled from the 1-km grid (the map's method).

Run from the repo root: .venv/bin/python -I research/scripts/qa_vacancy_fill.py
Reads interim/cells_2022.csv (inner and edge cells, from the build), the 1-km extracts in sources/zensus/grid/ and
the 100-m extract of the Eigentümerquote. The 1-km grid of the Eigentümerquote has no extract; the script reads it
from cache/zensus_owner_rate.zip and skips the owner part when the file is missing.
Writes research/results/qa_vacancy_fill.txt and qa_vacancy_fill_{quarter,district}.csv.

Method per 1-km cell: vacant dwellings the 1-km rate implies (rate × dwellings of all 100-m cells in it) minus the
vacant dwellings of the cells with a value, spread over the „–“ cells by their dwellings; a negative rest counts as 0.
The owner rate is only tested (is the fill needed?), not used by the map.
"""
import io
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "sources" / "zensus" / "grid"
RESULTS = ROOT / "research" / "results"
OWNER_ZIP = ROOT / "cache" / "zensus_owner_rate.zip"
OWNER_1KM = "Zensus2022_Eigentuemerquote_1km-Gitter.csv"
OWNER_TABLE_RENTERS = 79.9  # table 4000W-0001, share of renters (100 - Eigentümerquote), 15.5.2022
RATES = (("vacancy_rate", "vacancy_rate_dash", "Leerstandsquote", "Zensus2022_Leerstandsquote_1km-Gitter_Frankfurt.csv"),
         ("vacancy_rate_market", "vacancy_rate_market_dash", "marktaktive_Leerstandsquote",
          "Zensus2022_Marktaktive_Leerstandsquote_1km-Gitter_Frankfurt.csv"))
lines: list[str] = []


def say(text: str = "") -> None:
    print(text)
    lines.append(text)


def rate_series(frame: pd.DataFrame, column: str, index: str) -> pd.Series:
    """Rates with a decimal comma; „–“ means exactly zero or changed to zero (dataset description)."""
    values = frame[column].str.replace(",", ".", regex=False).replace({"–": "0"})
    return pd.Series(pd.to_numeric(values, errors="coerce").values, index=frame[index].values)


def km_of(cell_id: pd.Series) -> pd.Series:
    n = cell_id.str.extract(r"N(\d+)E(\d+)").astype(int)
    return "CRS3035RES1000mN" + (n[0] // 1000 * 1000).astype(str) + "E" + (n[1] // 1000 * 1000).astype(str)


def fill(cells: pd.DataFrame, known: pd.Series, dash: pd.Series, weight: pd.Series, km_rate: pd.Series):
    """Returns (filled vacant weight per cell, weight the 1-km rate implies per cell, negative rests)."""
    km = cells["km"]
    implied = km_rate / 100 * weight
    rest = implied.groupby(km).sum() - known.groupby(km).sum()
    dash_weight = weight.where(dash, 0)
    share = (rest / dash_weight.groupby(km).sum()).clip(lower=0).fillna(0)
    return known + dash_weight * km.map(share), implied, rest


def vacancy(cells: pd.DataFrame) -> None:
    inner = cells.edge == 0
    for rate, dash, column, name in RATES:
        km_frame = pd.read_csv(GRID / name, sep=";", dtype=str, encoding="utf-8-sig")
        km_rate = cells.km.map(rate_series(km_frame, column, "GITTER_ID_1km"))
        dashed = cells[dash] == 1
        known = (cells[rate].fillna(0) / 100 * cells.dwellings).where(~dashed, 0)
        filled, implied, rest = fill(cells, known, dashed, cells.dwellings, km_rate)
        with_dash = dashed.groupby(cells.km).any()
        negative = rest[(rest < 0) & with_dash.reindex(rest.index, fill_value=False)]
        say(f"{rate}: 1-km cells with a dash cell {int(with_dash.sum())}, of them with a negative rest "
            f"{len(negative)} (sum {negative.sum():.1f} dwellings); all 1-km cells {len(rest)}, negative rest "
            f"{int((rest < 0).sum())}")
        cells[rate + "_known"], cells[rate + "_km"], cells[rate + "_fill"] = known, implied, filled
    base = cells[inner].dwellings.sum()
    for rate, *_ in RATES:
        say(f"{rate} city: 100-m grid with dash as 0: {100 * cells[inner][rate + '_known'].sum() / base:.2f} % | "
            f"1-km grid {100 * cells[inner][rate + '_km'].sum() / base:.2f} % | "
            f"filled {100 * cells[inner][rate + '_fill'].sum() / base:.2f} %")
    for level in ("quarter", "district"):
        grouped = cells[inner].groupby(level)
        table = pd.DataFrame({"dwellings": grouped.dwellings.sum()})
        for rate, *_ in RATES:
            for k in ("known", "km", "fill"):
                table[f"{rate}_{k}"] = 100 * grouped[f"{rate}_{k}"].sum() / table.dwellings
        table.round(2).to_csv(RESULTS / f"qa_vacancy_fill_{level}.csv")
        say(f"{level}: areas with 0.0 % market-active vacancy: before the fill "
            f"{int((table.vacancy_rate_market_known == 0).sum())}, after {int((table.vacancy_rate_market_fill == 0).sum())}"
            f" of {len(table)}")
    quarters = pd.read_csv(RESULTS / "qa_vacancy_fill_quarter.csv", index_col=0)
    say("Innenstadt vacancy after the fill: " + f"{quarters.loc['Innenstadt', 'vacancy_rate_fill']:.1f} %"
        if "Innenstadt" in quarters.index else "")


def owner(cells: pd.DataFrame) -> None:
    """Is the owner rate to be filled? The city value of the 100-m grid equals the table, the rest is negative in many
    1-km cells."""
    if not OWNER_ZIP.exists():
        say("owner rate: skipped (cache/zensus_owner_rate.zip missing)")
        return
    with zipfile.ZipFile(OWNER_ZIP) as zf, zf.open(f"{OWNER_1KM}") as f:
        km_frame = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8-sig"), sep=";", dtype=str)
    km_rate = cells.km.map(rate_series(km_frame, "Eigentuemerquote", "GITTER_ID_1km"))
    grid = pd.read_csv(GRID / "Zensus2022_Eigentuemerquote_100m-Gitter_Frankfurt.csv", sep=";", dtype=str,
                       encoding="utf-8-sig")
    dashed = cells.cell_id.map(grid.set_index("GITTER_ID_100m").Eigentuemerquote).eq("–")
    occupied = cells.dwellings * (1 - cells.vacancy_rate.fillna(0) / 100)
    known = (cells.owner_rate.fillna(0) / 100 * occupied).where(~dashed, 0)
    filled, implied, rest = fill(cells, known, dashed, occupied, km_rate)
    with_dash = dashed.groupby(cells.km).any()
    negative = rest[(rest < 0) & with_dash.reindex(rest.index, fill_value=False)]
    inner = cells.edge == 0
    say(f"owner rate: 1-km cells with a dash cell {int(with_dash.sum())}, of them with a negative rest {len(negative)}; "
        f"all 1-km cells {len(rest)}, negative rest {int((rest < 0).sum())}")
    denominator = occupied[inner].sum()
    say(f"owner rate city, renters: map {100 - 100 * known[inner].sum() / denominator:.2f} % | "
        f"1-km grid {100 - 100 * implied[inner].sum() / denominator:.2f} % | "
        f"filled {100 - 100 * filled[inner].sum() / denominator:.2f} % | table {OWNER_TABLE_RENTERS} %")


def main() -> None:
    cells = pd.read_csv(ROOT / "interim" / "cells_2022.csv", dtype={"cell_id": str})
    cells["km"] = km_of(cells.cell_id)
    cells["dwellings"] = cells.dwellings.fillna(0)
    vacancy(cells)
    owner(cells)
    (RESULTS / "qa_vacancy_fill.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
