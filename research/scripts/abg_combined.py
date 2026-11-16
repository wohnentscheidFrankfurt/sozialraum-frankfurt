"""Confirmed sources first, then the estimate (finding research/2026-10-10-abg-combined-sources.md).

Step 1: the sites of the ABG research against the count of the Zensus 2011.
Step 2: backtest on 2011 of research sites + estimate E2 for the other cells.
Step 3: estimate D for 2022: count of 2011 × change up to 2022, cells without a public count 2011 with
E2. Dwellings of 2011 without an owner in the grid (secrecy) get the municipal share of their cell in 2022. New ABG
buildings of the research up to 2021 count where E2 finds fewer municipal dwellings in their new cells.
Step 4: error budget per Stadtteil (change, gap of secrecy, split ABG/NH).
Step 5: checks against the city count, the ABG annual report, Gallus and the new ABG buildings of the research.

Input: cache/abg_accuracy/ (research/scripts/abg_accuracy_extract.py), interim/cells_2022.csv, sources/zensus, the research GeoJSON in sources/other.
Output: research/results/abg_combined_*.csv and a summary on stdout.
Run: .venv/bin/python -I research/scripts/abg_combined.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "scripts"))

import abg_accuracy as acc  # noqa: E402
from pipeline import config as c  # noqa: E402
from pipeline.shared.zensus.model import CLASSES  # noqa: E402
from pipeline.shared.zensus.tables import read_dwellings_history  # noqa: E402

RESEARCH = ROOT / "sources" / "other" / "ABG-Holding-Karte.geojson"
RESULTS = ROOT / "research" / "results"
RADIUS = {"A": 150, "Q": 350}  # m, as in the research comparison of 8 Oct; "O" has no location
LAST_NEW_YEAR = 2021  # the Zensus counts on 15 May 2022: buildings of 2022 may be missing
CONFIRM = 0.85  # a site is confirmed if the count of 2011 around it reaches 85 % of its number
P90_CHANGE = 0.16  # error of E2 per Stadtteil, ABG and NH (research/2026-10-10-abg-estimate-accuracy.md)
TOL_REL, MIN_COUNT = 0.15, 200
METHOD = "E2"  # the finding uses E2; E1 gives the same within 0.1 % (69,219 against 69,236 public dwellings)
ABG_REPORT_2022 = 54122  # ABG annual report 2024, key figures, 31 Dec 2022
GALLUS_CHRONICLE = 5700  # ABG chronicle 2015, PDF page 19: "rund 5.700"


def cells() -> pd.DataFrame:
    z = pd.read_csv(ROOT / "interim" / "cells_2022.csv")
    return z[z["edge"] == 0].set_index("cell_id")


def grid_2011(index: pd.Index) -> dict[str, pd.DataFrame]:
    g = pd.read_csv(acc.EXTRACT / "grid_2011.csv")
    owners = dict(enumerate(CLASSES, start=1))
    out = {"d_owner": acc.wide(g, "dwellings", "EIGENTUM", owners), "b_owner": acc.wide(g, "buildings", "EIGENTUM", owners),
           "d_total": acc.wide(g, "dwellings", "INSGESAMT", {0: "total"})["total"]}
    return {k: v.reindex(index, fill_value=0) for k, v in out.items()}


def sites() -> pd.DataFrame:
    g = json.loads(RESEARCH.read_text(encoding="utf-8"))
    rows = []
    for f in g["features"]:
        p = f["properties"]
        if p["gebiet"] != "Frankfurt am Main" or not p["wohnungen"] or p["ebene"] not in ("bestand", "neubau"):
            continue
        years = [int(y) for y in re.findall(r"(?<!\d)(19\d\d|20\d\d)(?!\d)", str(p["stand"]))]
        lon, lat = f["geometry"]["coordinates"]
        rows.append({"id": p["id"], "name": p["name"], "level": p["ebene"], "dwellings": p["wohnungen"],
                     "precision": p["lage_genauigkeit"], "year": max(years) if years else None, "lon": lon, "lat": lat})
    s = pd.DataFrame(rows)
    s["x"], s["y"] = Transformer.from_crs(4326, 25832, always_xy=True).transform(s["lon"].values, s["lat"].values)
    # existing estates and new buildings up to 2010 belong to the stock of 2011
    s["before_2011"] = (s["level"] == "bestand") | (s["year"].fillna(9999) <= 2010)
    return s


def site_cells(s: pd.DataFrame, z: pd.DataFrame) -> dict[str, list[str]]:
    out = {}
    for _, p in s.iterrows():
        r = RADIUS.get(p["precision"])
        if r:
            d = np.hypot(z["x25832"] - p["x"], z["y25832"] - p["y"])
            out[p["id"]] = list(z.index[d <= r])
    return out


def step1(s: pd.DataFrame, cells_of: dict, g11: dict, z: pd.DataFrame) -> pd.DataFrame:
    old = s[s["before_2011"]].copy()
    mun = g11["d_owner"]["municipal"]
    old["counted_2011"] = [mun.loc[cells_of[i]].sum() if i in cells_of else np.nan for i in old["id"]]
    nearest = [z.index[np.argmin(np.hypot(z["x25832"] - x, z["y25832"] - y))] for x, y in zip(old["x"], old["y"])]
    old["quarter"] = z.loc[nearest, "quarter"].values
    old["status"] = np.select([old["counted_2011"].isna(), old["counted_2011"] == 0,
                               old["counted_2011"] >= CONFIRM * old["dwellings"]],
                              ["no location", "not found", "confirmed"], "above the count")
    return old


def step2(old: pd.DataFrame, cells_of: dict, z: pd.DataFrame) -> pd.DataFrame:
    """Backtest 2011 per Stadtteil: all research sites before 2011 (not only the confirmed ones: their selection uses
    the count of 2011) replace the estimate in their cells."""
    f = acc.year_frame(2011)
    est = acc.estimate(f, 2011)[METHOD]["municipal"]
    obs = f["d_owner"]["municipal"]
    area = f["area"]["quarter"]
    located = old[old["id"].isin(list(cells_of))]
    anchor = pd.Series(False, index=est.index)
    for i in located["id"]:
        anchor[anchor.index.isin(cells_of[i])] = True
    combined = est.where(~anchor, 0).groupby(area).sum().add(located.groupby("quarter")["dwellings"].sum(), fill_value=0)
    q = pd.DataFrame({"observed": obs.groupby(area).sum(), "E2": est.groupby(area).sum(), "combined": combined})
    q = q.fillna(0)
    for m in ("E2", "combined"):
        q[f"rel_{m}"] = q[m] / q["observed"].where(q["observed"] > 0) - 1
    return q


def step3(z: pd.DataFrame, g11: dict, s: pd.DataFrame, cells_of: dict) -> pd.DataFrame:
    f11, f22 = acc.year_frame(2011), acc.year_frame(2022)
    e11 = acc.estimate(f11, 2011)[METHOD].reindex(z.index, fill_value=0)
    e22 = acc.estimate(f22, 2022)[METHOD].reindex(z.index, fill_value=0)
    d11, b11, t11 = g11["d_owner"], g11["b_owner"], g11["d_total"].astype(float)
    b22 = z[[f"bld_{k}" for k in CLASSES]].set_axis(list(CLASSES), axis=1)
    t22 = z["dwellings"].astype(float)
    known22, known11 = b22.sum(axis=1) > 0, b11.sum(axis=1) > 0
    old = (d11["municipal"] + d11["state"]) > 0
    # rule of the map: "Bund oder Land" 2011 is NH where the cell is municipal in 2022 or has no owner in 2022
    nh_cell = old & ((b22["municipal"] > 0) | ~known22)
    # secrecy 2011: dwellings without an owner get the municipal share of the cell in 2022 (E2); split like the
    # counted public dwellings of the Stadtteil
    t22_pos = t22.where(t22 > 0)
    no_owner = (t11 - d11.sum(axis=1)).clip(lower=0)
    fill_2011 = (no_owner * (e22["municipal"] / t22_pos).fillna(0)).where(known22 & old, 0)
    counted = pd.DataFrame({"abg": d11["municipal"].where(old, 0), "nh": d11["state"].where(nh_cell, 0)}).groupby(z["quarter"]).sum()
    abg_part = (counted["abg"] / counted.sum(axis=1).where(counted.sum(axis=1) > 0)).fillna(1.0)
    part = z["quarter"].map(abg_part).fillna(1.0)
    base_abg = d11["municipal"].astype(float) + fill_2011 * part
    base_nh = d11["state"].where(nh_cell, 0).astype(float) + fill_2011 * (1 - part)
    factor_cells = old & known22 & known11
    fill = old & ~known22
    new = ~old & (b22["municipal"] > 0)
    area = z["quarter"]
    num = e22["municipal"].where(factor_cells, 0).groupby(area).sum()
    den = (e11["municipal"] + e11["state"].where(nh_cell, 0)).where(factor_cells, 0).groupby(area).sum()
    factor = (num / den.where(den > 0)).fillna(1.0)
    scaled = old & known22  # cells without an estimate 2011 get the factor of their Stadtteil too
    cap = np.minimum(1, (t22 / t11.where(t11 > 0)).fillna(1))
    out = pd.DataFrame(index=factor.index)
    out["factor"] = factor
    for name, base in (("abg", base_abg), ("nh", base_nh)):
        out[f"{name}_2011"] = base.where(old, 0).groupby(area).sum()
        out[f"{name}_scaled"] = (base.where(scaled, 0).groupby(area).sum() * factor)
        out[f"{name}_fill"] = (base * cap).where(fill, 0).groupby(area).sum()
    out["new"] = e22["municipal"].where(new, 0).groupby(area).sum()
    # confirmed new ABG buildings: the research number where E2 finds less in the new cells of the site
    add = pd.Series(0.0, index=out.index)
    done: set[str] = set()
    for _, p in s[~s["before_2011"] & (s["year"] <= LAST_NEW_YEAR)].iterrows():
        cs = [x for x in cells_of.get(p["id"], []) if new.get(x, False) or not known22.get(x, True)]
        if not cs:  # only cells with public stock 2011: the factor holds the growth
            continue
        free = [x for x in cs if x not in done]
        done.update(free)
        found = e22.loc[free, "municipal"].sum() if free else 0.0
        q = z.loc[cells_of[p["id"]], "quarter"].mode().iat[0] if cells_of.get(p["id"]) else None
        if q is not None and p["dwellings"] > found:
            add[q] = add.get(q, 0.0) + p["dwellings"] - found
    out["research_new"] = add
    # comparison: the difference instead of the factor
    diff = (e22["municipal"] - e11["municipal"] - e11["state"].where(nh_cell, 0)).where(factor_cells, 0).groupby(area).sum()
    out["public_additive"] = (base_abg + base_nh).where(scaled, 0).groupby(area).sum() + diff
    # secrecy: dwellings 2011 without an owner in the grid (whole cells and parts of cells)
    out["no_owner_2011"] = no_owner.where(~(known22 & old), 0).groupby(area).sum()  # not filled
    out["fill_2011"] = fill_2011.groupby(area).sum()
    out["unknown_new_2022"] = (t22 - t11).clip(lower=0).where(~old & ~known22, 0).groupby(area).sum()
    out["E2_2022"] = e22["municipal"].groupby(area).sum()
    out = out.fillna(0)
    out["abg"] = out["abg_scaled"] + out["abg_fill"]
    out["nh"] = out["nh_scaled"] + out["nh_fill"]
    out["abg"] = out["abg"] + out["research_new"]
    out["public"] = out["abg"] + out["nh"] + out["new"]
    return out


def step4(q: pd.DataFrame, gap_public: float, gap_municipal: float) -> pd.DataFrame:
    """Range per Stadtteil, a budget of three parts, not a measured error.
    - Gap: public dwellings 2011 the grid misses (table 4000W-1011 − grid) minus those filled from 2022. The rest of
      "Kommune" goes into the value; the whole rest only into the range, spread by the dwellings without an owner
      that were not filled. Most of it is "Bund oder Land" that did not become municipal.
    - Change: P90 of E2 per Stadtteil times the estimated change, at least the difference between factor and
      additive variant.
    - ABG only: new municipal dwellings without a research site are either ABG or NH; the value takes the middle."""
    share = q["no_owner_2011"] / q["no_owner_2011"].sum()
    q["gap_public"] = max(gap_public - q["fill_2011"].sum(), 0) * share
    q["gap_municipal"] = max(gap_municipal - q["fill_2011"].sum(), 0) * share
    change = (q["abg_scaled"] + q["nh_scaled"]) - (q["abg_2011"] + q["nh_2011"]) + q["new"]
    q["err_change"] = np.maximum(P90_CHANGE * change.abs(),
                                 (q["public"] - q["new"] - q["research_new"] - q["public_additive"]).abs())
    q["public_central"] = q["public"] + q["gap_municipal"]
    q["public_half"] = q["err_change"] + q["gap_public"]
    q["public_rel"] = q["public_half"] / q["public_central"].where(q["public_central"] > 0)
    q["abg_central"] = q["abg"] + q["new"] / 2 + q["gap_municipal"]
    q["abg_half"] = q["err_change"] + q["new"] / 2 + q["gap_public"]
    q["abg_rel"] = q["abg_half"] / q["abg_central"].where(q["abg_central"] > 0)
    return q


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    pd.set_option("display.width", 220)
    z = cells()
    g11 = grid_2011(z.index)
    s = sites()
    cells_of = site_cells(s, z)

    old = step1(s, cells_of, g11, z)
    old.drop(columns=["lon", "lat", "x", "y"]).to_csv(RESULTS / "abg_combined_step1_sites.csv", index=False)
    print("Step 1: research sites before 2011 against the count of 2011")
    print(old.groupby("status")["dwellings"].agg(["count", "sum"]).to_string())

    q2 = step2(old, cells_of, z)
    q2.to_csv(RESULTS / "abg_combined_step2_backtest.csv", float_format="%.3f")
    big = q2[q2["observed"] >= MIN_COUNT]
    print(f"\nStep 2: backtest 2011, ABG per Stadtteil ({len(big)} with at least {MIN_COUNT}), "
          f"90th percentile of the error: E2 {big['rel_E2'].abs().quantile(0.9):.1%}, "
          f"research + E2 {big['rel_combined'].abs().quantile(0.9):.1%}")

    h = read_dwellings_history(c.ZENSUS_4000W_1011.read_text(encoding="utf-8"))
    grid_mun, grid_state = g11["d_owner"]["municipal"].sum(), g11["d_owner"]["state"].sum()
    gap_mun = h[2011]["municipal"] - grid_mun
    gap_public = gap_mun + h[2011]["state"] - grid_state
    print(f"\nGap of secrecy 2011: municipal {h[2011]['municipal']:,} (table) − {grid_mun:,} (grid) = {gap_mun:,}; "
          f"public {gap_public:,}; dwellings without owner in the grid {(g11['d_total'] - g11['d_owner'].sum(axis=1)).clip(lower=0).sum():,}")

    q = step4(step3(z, g11, s, cells_of), gap_public, gap_mun)
    q.to_csv(RESULTS / "abg_combined_quarters.csv", float_format="%.1f")
    print(f"filled from 2022: {q['fill_2011'].sum():,.0f}; new ABG from the research: {q['research_new'].sum():,.0f}")
    print(f"\nStep 3/5, Frankfurt: ABG {q['abg'].sum():,.0f} + NH {q['nh'].sum():,.0f} + new {q['new'].sum():,.0f} "
          f"= {q['public'].sum():,.0f}; value {q['public_central'].sum():,.0f} "
          f"(table 4000W-2002: {h[2022]['municipal']:,}); ABG central {q['abg_central'].sum():,.0f} "
          f"(report: {ABG_REPORT_2022:,}); additive {q['public_additive'].sum() + q['new'].sum():,.0f}; "
          f"E2 {q['E2_2022'].sum():,.0f}; unknown new dwellings 2022 {q['unknown_new_2022'].sum():,.0f}")
    gallus = q.loc["Gallus"]
    print(f"Gallus ABG: {gallus['abg']:,.0f}, central {gallus['abg_central']:,.0f} ± {gallus['abg_half']:,.0f} "
          f"(chronicle 2015: about {GALLUS_CHRONICLE:,})")
    new_sites = s[~s["before_2011"]]
    print(f"New ABG buildings from 2011 in the research: {new_sites['dwellings'].sum():,}; new municipal (E2) {q['new'].sum():,.0f}")

    big = q[q["public_central"] >= MIN_COUNT]
    for k in ("public", "abg"):
        b = q[q[f"{k}_central"] >= MIN_COUNT]
        passes = (b[f"{k}_rel"] <= TOL_REL).mean()
        print(f"\nStep 4, {k}: {len(b)} Stadtteile; half range ≤ {TOL_REL:.0%} in {passes:.0%}; "
              f"90th percentile of the half range {b[f'{k}_rel'].quantile(0.9):.1%}")
    cols = ["factor", "abg_2011", "nh_2011", "new", "public", "public_central", "public_half", "public_rel",
            "abg_central", "abg_half", "abg_rel", "E2_2022"]
    print(big[cols].sort_values("public_rel", ascending=False).round(2).to_string())


if __name__ == "__main__":
    main()
