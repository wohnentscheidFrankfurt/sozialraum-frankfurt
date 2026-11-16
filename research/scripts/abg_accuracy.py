"""Accuracy of the ownership estimate per district and Stadtteil (finding research/2026-10-10-abg-estimate-accuracy.md).

The 2022 grid counts buildings per ownership type, not dwellings. The map turns buildings into dwellings. This script
runs the methods on the 2011 grid, where the dwellings per ownership type are also observed, and measures the error.

Methods (each scaled to the dwellings of the cell):
- E0: buildings per type × dwellings per building of the type in Frankfurt (the method of the map).
- E1: buildings per type and size class, fitted per cell to the buildings per type and the buildings per number of
  dwellings (iterative proportional fitting, start: table 3000G-2007), × dwellings per building of type and size in
  Frankfurt (4000W-2013 ÷ 3000G-2007).
- E2: as E1, but the dwellings per building of the classes 3–6, 7–12 and 13+ come from the cell (dwellings ÷ buildings
  of the Gebäudetyp-Größe), adjusted by the ratio of the type in Frankfurt.

Input: cache/abg_accuracy/ (research/scripts/abg_accuracy_extract.py), interim/cells_2022.csv, sources/zensus.
Output: research/results/abg_accuracy_*.csv and a summary on stdout.
Run: .venv/bin/python -I research/scripts/abg_accuracy.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipeline import config as c  # noqa: E402
from pipeline.shared.zensus.model import CLASSES, SIZES  # noqa: E402
from pipeline.shared.zensus.tables import read_buildings_by_size, read_dwellings_by_size  # noqa: E402

EXTRACT = ROOT / "cache" / "abg_accuracy"
RESULTS = ROOT / "research" / "results"
MFH = {"3_6": 7, "7_12": 8, "13_plus": 9}  # size class -> Gebäudetyp-Größe code
TOL_REL, TOL_PP, MIN_COUNT = 0.15, 3.0, 200  # tolerance agreed with the user (docs/data-rules.md, Checks)
INDICATORS = {"municipal": ["municipal"], "public": ["municipal", "state"], "coop": ["coop"]}
CLASS_BOUNDS = [5, 15, 30]  # share classes in %: under 5, 5–15, 15–30, 30 and more
OFFICIAL_MUNICIPAL_2022 = 69558  # table 4000W-2002, class Kommune


def wide(g: pd.DataFrame, kind: str, feature: str, codes: dict[int, str]) -> pd.DataFrame:
    d = g[(g["kind"] == kind) & (g["feature"] == feature) & g["code"].isin(list(codes))]
    w = d.pivot_table(index="cell_id", columns="code", values="count", aggfunc="sum", fill_value=0)
    return w.reindex(columns=list(codes), fill_value=0).rename(columns=codes)


def year_frame(year: int) -> dict[str, pd.DataFrame]:
    cells = pd.read_csv(ROOT / "interim" / "cells_2022.csv")
    cells = cells[cells["edge"] == 0].set_index("cell_id")
    owners = dict(enumerate(CLASSES, start=1))
    sizes = dict(enumerate(SIZES, start=1))
    types = {i: i for i in range(1, 11)}
    g = pd.read_csv(EXTRACT / f"grid_{year}.csv")
    g = g[g["cell_id"].isin(cells.index)]
    f = {"area": cells[["district", "quarter"]],
         "b_size": wide(g, "buildings", "ZAHLWOHNGN_HHG", sizes),
         "b_type": wide(g, "buildings", "GEBTYPGROESSE", types),
         "d_type": wide(g, "dwellings", "GEBTYPGROESSE", types)}
    if year == 2011:
        f["b_owner"] = wide(g, "buildings", "EIGENTUM", owners)
        f["d_owner"] = wide(g, "dwellings", "EIGENTUM", owners)  # observed: the truth of the backtest
        f["d_total"] = wide(g, "dwellings", "INSGESAMT", {0: "total"})["total"]
    else:
        f["b_owner"] = cells[[f"bld_{k}" for k in CLASSES]].set_axis(list(CLASSES), axis=1)
        f["d_total"] = cells["dwellings"]
    index = f["b_owner"].index
    for k in list(f):
        if k != "area":
            f[k] = f[k].reindex(index, fill_value=0)
    f["area"] = f["area"].reindex(index)
    return f


def city_tables(year: int, b_owner: pd.DataFrame):
    b = read_buildings_by_size(c.ZENSUS_3000G_2007.read_text(encoding="utf-8"))[year]
    d = read_dwellings_by_size(c.ZENSUS_4000W_2013.read_text(encoding="utf-8"))[year]
    seed = np.array([[b[k][s] for s in SIZES] for k in CLASSES], dtype=float)
    mean = np.array([[d[k][s] / b[k][s] if b[k][s] else 0.0 for s in SIZES] for k in CLASSES])
    mean_all = np.array([sum(d[k][s] for k in CLASSES) / max(sum(b[k][s] for k in CLASSES), 1) for s in SIZES])
    # E0 as in the map: dwellings of the type in Frankfurt ÷ buildings of the type in the grid
    e0 = np.array([d[k]["total"] / b_owner[k].sum() if b_owner[k].sum() else 0.0 for k in CLASSES])
    return seed, mean, mean_all, e0


def ipf(seed: np.ndarray, rows: np.ndarray, cols: np.ndarray, steps: int = 50) -> np.ndarray:
    """Buildings per type (rows) and size (cols) of one cell. The size margin is scaled to the type total: secrecy
    makes both totals differ. A size class with buildings but no seed keeps no weight."""
    if rows.sum() == 0:
        return np.zeros_like(seed)
    if cols.sum() == 0:
        cols = seed[rows > 0].sum(axis=0)
    cols = cols * rows.sum() / cols.sum()
    m = seed * (rows > 0)[:, None] * (cols > 0)[None, :]
    if m.sum() == 0:
        return np.outer(rows, cols) / rows.sum()
    for _ in range(steps):
        r = m.sum(axis=1)
        m = m * np.divide(rows, r, out=np.zeros_like(rows), where=r > 0)[:, None]
        s = m.sum(axis=0)
        m = m * np.divide(cols, s, out=np.zeros_like(cols), where=s > 0)[None, :]
    return m


def estimate(f: dict, year: int) -> dict[str, pd.DataFrame]:
    seed, mean, mean_all, e0 = city_tables(year, f["b_owner"])
    bo = f["b_owner"][list(CLASSES)].to_numpy(float)
    bs = f["b_size"][SIZES].to_numpy(float)
    bt, dt = f["b_type"].to_numpy(float), f["d_type"].to_numpy(float)
    raw = {"E0": bo * e0, "E1": np.zeros_like(bo), "E2": np.zeros_like(bo)}
    for i in range(len(bo)):
        joint = ipf(seed, bo[i], bs[i])
        raw["E1"][i] = (joint * mean).sum(axis=1)
        m = mean.copy()
        for j, s in enumerate(SIZES):
            t = MFH.get(s)
            if t and bt[i, t - 1] > 0 and dt[i, t - 1] > 0:
                m[:, j] = mean[:, j] * (dt[i, t - 1] / bt[i, t - 1]) / mean_all[j]
        raw["E2"][i] = (joint * m).sum(axis=1)
    total = f["d_total"].to_numpy(float)
    out = {}
    for name, r in raw.items():
        s = r.sum(axis=1)
        scale = np.divide(total, s, out=np.zeros_like(total), where=s > 0)
        out[name] = pd.DataFrame(r * scale[:, None], index=f["b_owner"].index, columns=list(CLASSES))
    return out


def errors(est: pd.DataFrame, obs: pd.DataFrame, area: pd.Series) -> pd.DataFrame:
    rows = []
    for ind, cols in INDICATORS.items():
        e = est[cols].sum(axis=1).groupby(area).sum()
        o = obs[cols].sum(axis=1).groupby(area).sum()
        e_base, o_base = est.sum(axis=1).groupby(area).sum(), obs.sum(axis=1).groupby(area).sum()
        d = pd.DataFrame({"indicator": ind, "observed": o, "estimated": e,
                          "share_obs": 100 * o / o_base, "share_est": 100 * e / e_base})
        d["rel"] = (d["estimated"] - d["observed"]) / d["observed"].where(d["observed"] > 0)
        d["pp"] = d["share_est"] - d["share_obs"]
        rows.append(d)
    return pd.concat(rows).rename_axis("area").reset_index()


def summary(err: pd.DataFrame) -> pd.DataFrame:
    def one(d: pd.DataFrame) -> pd.Series:
        big = d[d["observed"] >= MIN_COUNT]
        p90 = big["rel"].abs().quantile(0.9)
        mx = d["pp"].abs().max()
        return pd.Series({"areas": len(d), "areas_200": len(big), "rel_median": big["rel"].abs().median(),
                          "rel_p90": p90, "rel_max": big["rel"].abs().max(), "pp_p90": d["pp"].abs().quantile(0.9),
                          "pp_max": mx, "passes": bool(p90 <= TOL_REL and mx <= TOL_PP),
                          "same_class": float((np.digitize(d["share_obs"], CLASS_BOUNDS)
                                               == np.digitize(d["share_est"], CLASS_BOUNDS)).mean()),
                          "class_off_2": int((abs(np.digitize(d["share_obs"], CLASS_BOUNDS)
                                                  - np.digitize(d["share_est"], CLASS_BOUNDS)) > 1).sum())})
    return err.groupby(["method", "level", "indicator"]).apply(one, include_groups=False).reset_index()


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    f = year_frame(2011)
    obs = f["d_owner"][list(CLASSES)].astype(float)
    known = (f["b_owner"].sum(axis=1) > 0) & (obs.sum(axis=1) > 0)  # without buildings per type 2022 fills from 2011
    print(f"2011: {len(obs)} cells, {known.sum()} with buildings and dwellings per type; dwellings in them "
          f"{obs[known].to_numpy().sum():,.0f} of {obs.to_numpy().sum():,.0f}")
    ests = estimate(f, 2011)
    errs = []
    for method, est in ests.items():
        for level in ("district", "quarter"):
            e = errors(est[known], obs[known], f["area"].loc[known, level])
            e.insert(0, "level", level)
            e.insert(0, "method", method)
            errs.append(e)
    err = pd.concat(errs).dropna(subset=["share_obs"])
    err.to_csv(RESULTS / "abg_accuracy_backtest_2011.csv", index=False, float_format="%.4f")
    s = summary(err)
    s.to_csv(RESULTS / "abg_accuracy_summary_2011.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 200)
    print(s.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    for method in ests:
        worst = err[(err["method"] == method) & (err["level"] == "district") & (err["indicator"] == "municipal")
                    & (err["observed"] >= MIN_COUNT)].assign(a=lambda d: d["rel"].abs()).nlargest(6, "a")
        print(f"\n{method}, worst districts (municipal):")
        print(worst[["area", "observed", "estimated", "rel", "pp"]].to_string(index=False, float_format=lambda x: f"{x:.2f}"))

    check_2022(f)


def check_2022(f11: dict) -> None:
    """2022: the methods against the city count, and against the observed dwellings of 2011 per Stadtteil."""
    f = year_frame(2022)
    est = estimate(f, 2022)
    pipeline = pd.read_csv(ROOT / "interim" / "ownership_cells.csv")["dw_municipal"].sum()
    print(f"\n2022, municipal dwellings in Frankfurt: E0 {est['E0']['municipal'].sum():,.0f}, "
          f"E2 {est['E2']['municipal'].sum():,.0f}, map (E0 + fill from 2011) {pipeline:,.0f}, "
          f"table 4000W-2002 {OFFICIAL_MUNICIPAL_2022:,}")
    b11 = f11["b_owner"].reindex(f["b_owner"].index, fill_value=0)
    d11 = f11["d_owner"].reindex(f["b_owner"].index, fill_value=0)
    gone = ((b11["municipal"] + b11["state"] > 0) & (f["b_owner"]["municipal"] == 0)
            & (f["b_owner"].sum(axis=1) > 0))
    print(f"public dwellings 2011 in cells with buildings 2022 but no municipal building: "
          f"{(d11['municipal'] + d11['state'])[gone].sum():,.0f} (sold, or 1–2 buildings kept secret in 2022)")
    area = f["area"]["quarter"]
    q = pd.DataFrame({"observed_public_2011": (d11["municipal"] + d11["state"]).groupby(area).sum(),
                      "E0_2022": est["E0"]["municipal"].groupby(area).sum(),
                      "E2_2022": est["E2"]["municipal"].groupby(area).sum()})
    q.round(0).to_csv(RESULTS / "abg_accuracy_quarters_2022.csv")


if __name__ == "__main__":
    main()
