"""QA of Lage and Belastung (research/2026-10-17-qa-situation-burden.md): four ways to share the 2011
construction-year classes on the 2022 dwellings.

Run from the repo root: .venv/bin/python -I research/scripts/qa_construction_year_variants.py
Reads interim/cells_2022.csv and interim/cells_2011_dwellings.csv (both from the build) and, for variant V4 only,
cache/zensus_construction_year.zip (skipped when the file is missing). Writes research/results/qa_construction_year_*.

Variants (share of the dwellings of the 2022 grid, in percent):
- V0: 2011 class ÷ 2022 dwellings (the map before the QA; Hausen 86.2 % for 1949-1978).
- V1: 2011 class ÷ 2011 dwellings (the 2011 share, not comparable to 2022 dwellings).
- V2: per cell the class counts at most the 2022 dwellings (the map's method; Hausen 61.7 %).
- V3: per cell the class is scaled by 2022 dwellings ÷ 2011 dwellings.
- V4: 2022 dwellings × share of buildings of that class in the 2022 grid (buildings only, no dwellings).
"""
import io
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
BUILDINGS_ZIP = ROOT / "cache" / "zensus_construction_year.zip"
BUILDINGS_CSV = ("Gebaeude_nach_Baujahr_in_Mikrozensus_Klassen/"
                 "Zensus2022_Gebaeude_nach_Baujahr_in_MZ_Klassen_100m-Gitter.csv")
# Zensus 2022 tables 4000W-1008 (2022) and 2011: dwellings in total and the two classes (Frankfurt, city value)
TABLE_2022 = {"total": 402826, "pre1919": 66790, "1949_1978": 189598}
TABLE_2011 = {"total": 365401, "pre1919": 67328, "1949_1978": 187254}
BUILDING_COLUMN = {"pre1919": "Vor1919", "1949_1978": "a1949bis1978"}
CLASSES = ("pre1919", "1949_1978")
lines: list[str] = []


def say(text: str = "") -> None:
    print(text)
    lines.append(text)


def read_buildings_2022(cells: set[str]) -> pd.DataFrame | None:
    """Buildings of the 2022 grid per class in the given cells; None when the download is not in cache/."""
    if not BUILDINGS_ZIP.exists():
        return None
    rows = []
    with zipfile.ZipFile(BUILDINGS_ZIP) as zf, zf.open(BUILDINGS_CSV) as f:
        head = f.readline().decode("utf-8-sig").strip().split(";")
        for line in io.TextIOWrapper(f, encoding="utf-8"):
            parts = line.rstrip("\n").split(";")
            if parts[0] in cells:
                rows.append(parts)
    frame = pd.DataFrame(rows, columns=head).rename(columns={"GITTER_ID_100m": "cell_id"})
    for column in head[3:]:
        frame[column] = pd.to_numeric(frame[column].str.replace("–", "0").str.replace(",", "."),
                                      errors="coerce").fillna(0)
    return frame[["cell_id", "Insgesamt_Gebaeude", *BUILDING_COLUMN.values()]]


def main() -> None:
    c22 = pd.read_csv(ROOT / "interim" / "cells_2022.csv", dtype={"cell_id": str})
    c11 = pd.read_csv(ROOT / "interim" / "cells_2011_dwellings.csv", dtype={"cell_id": str})
    merged = c22[c22.edge == 0][["cell_id", "district", "quarter", "dwellings"]].merge(c11, on="cell_id", how="outer")
    b22 = read_buildings_2022(set(c22.cell_id))
    if b22 is not None:
        merged = merged.merge(b22, on="cell_id", how="left")
    counts = ["dwellings", *[c for c in merged.columns if c.startswith("dw_")]]  # never the area columns
    merged[counts] = merged[counts].fillna(0)
    inside = merged[merged.quarter.notna()].copy()  # 2011 cells without a 2022 cell drop out, as in the map
    scale = (inside.dwellings / inside.dw_total_2011).where(inside.dw_total_2011 > 0, 0).clip(upper=1)
    for k in CLASSES:
        source = inside[f"dw_{k}_2011"].fillna(0)
        inside[f"v2_{k}"] = source.clip(upper=inside.dwellings)
        inside[f"v3_{k}"] = source * scale
        if b22 is not None:
            share = (inside[BUILDING_COLUMN[k]] / inside.Insgesamt_Gebaeude).where(inside.Insgesamt_Gebaeude > 0, 0)
            inside[f"v4_{k}"] = inside.dwellings * share
    variants = ("v2", "v3", "v4") if b22 is not None else ("v2", "v3")
    total_2022 = inside.dwellings.sum()
    say(f"city: dwellings 2022 grid {total_2022:.0f} (table {TABLE_2022['total']}) | "
        f"2011 grid {inside.dw_total_2011.sum():.0f} (table {TABLE_2011['total']})")
    for k in CLASSES:
        say(f"{k}: table 2022 {TABLE_2022[k]} = {100 * TABLE_2022[k] / TABLE_2022['total']:.2f} % | "
            f"table 2011 {TABLE_2011[k]} = {100 * TABLE_2011[k] / TABLE_2011['total']:.2f} %")
        say(f"  V0 {inside[f'dw_{k}_2011'].sum():.0f} = {100 * inside[f'dw_{k}_2011'].sum() / total_2022:.2f} %")
        say(f"  V1 {100 * inside[f'dw_{k}_2011'].sum() / inside.dw_total_2011.sum():.2f} %")
        for v in variants:
            say(f"  {v.upper()} {inside[f'{v}_{k}'].sum():.0f} = {100 * inside[f'{v}_{k}'].sum() / total_2022:.2f} %")
    for level in ("quarter", "district"):
        grouped = inside.groupby(level).sum(numeric_only=True)
        out = pd.DataFrame(index=grouped.index)
        for k in CLASSES:
            out[f"V0_{k}"] = 100 * grouped[f"dw_{k}_2011"] / grouped.dwellings
            out[f"V1_{k}"] = 100 * grouped[f"dw_{k}_2011"] / grouped.dw_total_2011
            for v in variants:
                out[f"{v.upper()}_{k}"] = 100 * grouped[f"{v}_{k}"] / grouped.dwellings
        out.round(1).to_csv(RESULTS / f"qa_construction_year_variants_{level}.csv")
        if level == "quarter":
            say("top quarters 1949-1978 (V0 before, V2 after):")
            say(out.sort_values("V0_1949_1978", ascending=False).round(1).head(8).to_string())
            say("top quarters before 1919:")
            say(out.sort_values("V0_pre1919", ascending=False).round(1).head(6).to_string())
        for k in CLASSES:
            say(f"{level} {k}: rank correlation (Spearman) V1~V3 {out[f'V1_{k}'].rank().corr(out[f'V3_{k}'].rank()):.3f}, "
                f"max |V2-V3| {(out[f'V2_{k}'] - out[f'V3_{k}']).abs().max():.1f} points")
    (RESULTS / "qa_construction_year_variants.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
