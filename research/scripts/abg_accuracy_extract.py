"""Frankfurt extract of the grids for the accuracy test of the ownership estimate (finding research/2026-10-10-abg-estimate-accuracy.md).

Reads the Zensus grids from cache/ and writes long tables to cache/abg_accuracy/:
- grid_2011.csv: cell_id, kind (buildings | dwellings), feature, code, count; features INSGESAMT, EIGENTUM,
  ZAHLWOHNGN_HHG, GEBTYPGROESSE
- grid_2022.csv: cell_id, kind, feature, code, count; buildings by number of dwellings, buildings and dwellings by
  Gebäudetyp-Größe (codes as in 2011)

Cells: all cells of interim/cells_2022.csv. Run: .venv/bin/python -I research/scripts/abg_accuracy_extract.py
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "cache"
OUT = CACHE / "abg_accuracy"
FEATURES = {"INSGESAMT", "EIGENTUM", "ZAHLWOHNGN_HHG", "GEBTYPGROESSE"}
# 2022 columns of the type-size grids, mapped to the GEBTYPGROESSE codes of 2011
TYPE_SIZE = {"FreiEFH": 1, "EFH_DHH": 2, "EFH_Reihenhaus": 3, "Freist_ZFH": 4, "ZFH_DHH": 5, "ZFH_Reihenhaus": 6,
             "MFH_3bis6Wohnungen": 7, "MFH_7bis12Wohnungen": 8, "MFH_13undmehrWohnungen": 9, "AndererGebaeudetyp": 10}
BY_NUMBER = {"1_Wohnung": 1, "2_Wohnungen": 2, "3bis6_Wohnungen": 3, "7bis12_Wohnungen": 4, "13undmehr_Wohnungen": 5}


def cells() -> set[str]:
    return set(pd.read_csv(ROOT / "interim" / "cells_2022.csv", usecols=["cell_id"])["cell_id"])


def extract_2011(zip_name: str, member: str, kind: str, keep: set[str]) -> pd.DataFrame:
    parts = []
    with zipfile.ZipFile(CACHE / zip_name) as z, z.open(member) as f:
        reader = pd.read_csv(io.TextIOWrapper(f, encoding="latin-1"), dtype=str, chunksize=2_000_000,
                             usecols=["Gitter_ID_100m_neu", "Merkmal", "Auspraegung_Code", "Anzahl"])
        for ch in reader:
            ch = ch[ch["Merkmal"].isin(FEATURES) & ch["Gitter_ID_100m_neu"].isin(keep)]
            parts.append(ch)
    d = pd.concat(parts)
    return pd.DataFrame({"cell_id": d["Gitter_ID_100m_neu"], "kind": kind, "feature": d["Merkmal"],
                         "code": d["Auspraegung_Code"].astype(int), "count": d["Anzahl"].astype(int)})


def extract_2022(zip_name: str, kind: str, feature: str, codes: dict[str, int], keep: set[str]) -> pd.DataFrame:
    with zipfile.ZipFile(CACHE / zip_name) as z:
        member = next(n for n in z.namelist() if n.endswith("100m-Gitter.csv"))
        with z.open(member) as f:
            d = pd.read_csv(f, sep=";", dtype=str, encoding="utf-8")
    d = d[d["GITTER_ID_100m"].isin(keep)]
    long = d.melt(id_vars="GITTER_ID_100m", value_vars=list(codes), var_name="column", value_name="count")
    long["count"] = pd.to_numeric(long["count"].str.replace("–", "0", regex=False)).fillna(0).astype(int)
    return pd.DataFrame({"cell_id": long["GITTER_ID_100m"], "kind": kind, "feature": feature,
                         "code": long["column"].map(codes), "count": long["count"]})


def main() -> None:
    OUT.mkdir(exist_ok=True)
    keep = cells()
    g11 = pd.concat([extract_2011("zensus2011_buildings.zip", "Geb100m.csv", "buildings", keep),
                     extract_2011("zensus2011_dwellings.zip", "Wohnungen100m.csv", "dwellings", keep)])
    g11.to_csv(OUT / "grid_2011.csv", index=False)
    g22 = pd.concat([extract_2022("zensus_buildings_by_size.zip", "buildings", "ZAHLWOHNGN_HHG", BY_NUMBER, keep),
                     extract_2022("zensus_buildings_by_type_size.zip", "buildings", "GEBTYPGROESSE", TYPE_SIZE, keep),
                     extract_2022("zensus_dwellings_by_type_size.zip", "dwellings", "GEBTYPGROESSE", TYPE_SIZE, keep)])
    g22.to_csv(OUT / "grid_2022.csv", index=False)
    for name, g in (("2011", g11), ("2022", g22)):
        print(name, g.groupby(["kind", "feature"])["count"].sum().to_string(), sep="\n")


if __name__ == "__main__":
    main()
