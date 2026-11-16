"""ABG and Nassauische Heimstätte per Stadtteil: count of 2011 × change up to 2022 (README, Formula). Pure module."""
from __future__ import annotations

import numpy as np
import pandas as pd
from pyproj import Transformer

from pipeline.shared.zensus.model import CLASSES, SIZES

P90_CHANGE = 0.16  # error of the estimate per Stadtteil, 9 of 10 (research/2026-10-10-abg-estimate-accuracy.md)
LAST_NEW_YEAR = 2021  # the Zensus counts on 15 May 2022: buildings of 2022 may be missing
RADIUS = {"A": 150, "Q": 350}  # m around a research site; "O" has no location
_TO_25832 = Transformer.from_crs(4326, 25832, always_xy=True)


def size_tables(buildings: dict[str, dict[str, int]], dwellings: dict[str, dict[str, int]]) -> tuple[np.ndarray, np.ndarray]:
    """For one year of tables 3000G-2007 and 4000W-2013: buildings per ownership type and size (start values of the
    fit) and dwellings per building of type and size (8 × 5)."""
    seed = np.array([[buildings[k][s] for s in SIZES] for k in CLASSES], dtype=float)
    mean = np.array([[dwellings[k][s] / buildings[k][s] if buildings[k][s] else 0.0 for s in SIZES] for k in CLASSES])
    return seed, mean


def ipf(seed: np.ndarray, rows: np.ndarray, cols: np.ndarray, steps: int = 50) -> np.ndarray:
    """Buildings per ownership type (rows) and size (cols) of one cell, fitted to both margins. Secrecy makes the two
    totals differ, so the size margin is scaled to the type total. Without sizes the start values of the types in the
    cell serve as size margin."""
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
        c = m.sum(axis=0)
        m = m * np.divide(cols, c, out=np.zeros_like(cols), where=c > 0)[None, :]
    return m


def estimate_by_size(b_owner: pd.DataFrame, b_size: pd.DataFrame, total: pd.Series, seed: np.ndarray,
                     mean: np.ndarray) -> pd.DataFrame:
    """Dwellings per ownership type and cell from buildings per type (columns CLASSES) and per size (columns SIZES),
    scaled to the dwellings of the cell."""
    bo, bs = b_owner[list(CLASSES)].to_numpy(float), b_size[SIZES].to_numpy(float)
    raw = np.zeros_like(bo)
    for i in range(len(bo)):
        raw[i] = (ipf(seed, bo[i], bs[i]) * mean).sum(axis=1)
    s, t = raw.sum(axis=1), total.to_numpy(float)
    scale = np.divide(t, s, out=np.zeros_like(t), where=s > 0)
    return pd.DataFrame(raw * scale[:, None], index=b_owner.index, columns=list(CLASSES))


def new_research_sites(sites: pd.DataFrame) -> pd.DataFrame:
    """New ABG buildings of the research from 2011 to LAST_NEW_YEAR with a location, in coordinates EPSG:25832."""
    s = sites[(sites["level"] == "neubau") & sites["year"].between(2011, LAST_NEW_YEAR)
              & sites["precision"].isin(list(RADIUS))].copy()
    s["x"], s["y"] = _TO_25832.transform(s["lon"].to_numpy(), s["lat"].to_numpy())
    return s.reset_index(drop=True)


def research_cells(sites: pd.DataFrame, cells: pd.DataFrame) -> list[tuple[int, list[str]]]:
    """Per site its number of dwellings and the cells (index of `cells`, columns x25832, y25832) within its radius."""
    out = []
    for _, p in sites.iterrows():
        d = np.hypot(cells["x25832"] - p["x"], cells["y25832"] - p["y"])
        out.append((int(p["dwellings"]), list(cells.index[d <= RADIUS[p["precision"]]])))
    return out


def public_housing(cells: pd.DataFrame, e11: pd.DataFrame, e22: pd.DataFrame,
                   sites: list[tuple[int, list[str]]]) -> pd.DataFrame:
    """ABG and NH per Stadtteil. `cells` (index cell_id): quarter, dwellings, bld_<type> (2022), dw_<type>_2011,
    dw_total_2011, bld_<type>_2011. e11, e22: `estimate_by_size` per cell and type. `sites`: new ABG buildings of the
    research (research_cells)."""
    e11 = e11.reindex(cells.index, fill_value=0.0)
    e22 = e22.reindex(cells.index, fill_value=0.0)
    d11 = cells[[f"dw_{k}_2011" for k in CLASSES]].set_axis(list(CLASSES), axis=1).astype(float)
    b11 = cells[[f"bld_{k}_2011" for k in CLASSES]].sum(axis=1)
    b22 = cells[[f"bld_{k}" for k in CLASSES]].set_axis(list(CLASSES), axis=1)
    t11, t22 = cells["dw_total_2011"].astype(float), cells["dwellings"].astype(float)
    area = cells["quarter"]
    known22, known11 = b22.sum(axis=1) > 0, b11 > 0
    old = (d11["municipal"] + d11["state"]) > 0
    nh_cell = old & ((b22["municipal"] > 0) | ~known22)  # README
    # secrecy 2011: dwellings without an owner get the municipal share of the cell in 2022
    no_owner = (t11 - d11.sum(axis=1)).clip(lower=0)
    filled = known22 & old
    fill = (no_owner * (e22["municipal"] / t22.where(t22 > 0)).fillna(0.0)).where(filled, 0.0)
    counted = pd.DataFrame({"abg": d11["municipal"].where(old, 0.0), "nh": d11["state"].where(nh_cell, 0.0)})
    counted = counted.groupby(area).sum()
    total = counted.sum(axis=1)
    part = area.map((counted["abg"] / total.where(total > 0)).fillna(1.0)).fillna(1.0)
    base_abg = d11["municipal"].where(old, 0.0) + fill * part
    base_nh = d11["state"].where(nh_cell, 0.0) + fill * (1 - part)
    factor_cells, scaled, fill_cells = old & known22 & known11, old & known22, old & ~known22
    new = ~old & (b22["municipal"] > 0)
    quarters = pd.Index(sorted(area.unique()), name="quarter")

    def per_quarter(x: pd.Series) -> pd.Series:
        return x.groupby(area).sum().reindex(quarters, fill_value=0.0)

    num = per_quarter(e22["municipal"].where(factor_cells, 0.0))
    den = per_quarter((e11["municipal"] + e11["state"].where(nh_cell, 0.0)).where(factor_cells, 0.0))
    factor = (num / den.where(den > 0)).fillna(1.0)
    cap = np.minimum(1.0, (t22 / t11.where(t11 > 0)).fillna(1.0))
    q = pd.DataFrame(index=quarters)
    q["factor"] = factor
    for name, base in (("abg", base_abg), ("nh", base_nh)):
        q[f"{name}_2011"] = per_quarter(base.where(old, 0.0))
        q[f"{name}_scaled"] = per_quarter(base.where(scaled, 0.0)) * factor
        q[f"{name}_fill"] = per_quarter((base * cap).where(fill_cells, 0.0))
    q["scaled_2011"] = per_quarter((base_abg + base_nh).where(scaled, 0.0))  # the count the factor scales
    q["fill_2011"] = per_quarter(fill)
    q["new"] = per_quarter(e22["municipal"].where(new, 0.0))
    q["research_new"] = _research_new(sites, new, known22, e22["municipal"], area, quarters)
    diff = per_quarter((e22["municipal"] - e11["municipal"] - e11["state"].where(nh_cell, 0.0)).where(factor_cells, 0.0))
    q["public_additive"] = per_quarter((base_abg + base_nh).where(scaled, 0.0)) + diff
    q["no_owner_2011"] = per_quarter(no_owner.where(~filled, 0.0))  # not filled
    q["abg"] = q["abg_scaled"] + q["abg_fill"] + q["research_new"]
    q["nh"] = q["nh_scaled"] + q["nh_fill"]
    q["public"] = q["abg"] + q["nh"] + q["new"]
    return q


def _research_new(sites, new: pd.Series, known22: pd.Series, municipal: pd.Series, area: pd.Series,
                  quarters: pd.Index) -> pd.Series:
    """Research number minus what `estimate_by_size` finds in the new cells of the site (no public stock 2011, or no owner 2022).
    A cell counts for the first site only. Sites with old stock only add nothing: the factor holds their growth. The
    number goes to the Stadtteil of the new cells (their most common one)."""
    add = pd.Series(0.0, index=quarters)
    used: set[str] = set()
    for dwellings, cs in sites:
        own = [c for c in cs if new[c] or not known22[c]]
        if not own:
            continue
        free = [c for c in own if c not in used]
        used.update(free)
        found = float(municipal[free].sum()) if free else 0.0
        if dwellings > found:
            add[area[own].mode().iat[0]] += dwellings - found
    return add


def public_range(q: pd.DataFrame, gap_public: float, gap_municipal: float) -> pd.DataFrame:
    """Value and half range per Stadtteil, a budget (README).
    gap_public, gap_municipal: dwellings 2011 of table 4000W-1011 minus the grid (public = Kommune + Bund oder Land).
    The rest after the fill is spread by the dwellings without an owner that were not filled."""
    q = q.copy()
    spread = q["no_owner_2011"].sum()
    share = q["no_owner_2011"] / spread if spread > 0 else q["no_owner_2011"] * 0.0
    q["gap_public"] = max(gap_public - q["fill_2011"].sum(), 0.0) * share
    q["gap_municipal"] = max(gap_municipal - q["fill_2011"].sum(), 0.0) * share
    stock = q["abg_scaled"] + q["nh_scaled"] + q["abg_fill"] + q["nh_fill"]
    change = stock - (q["abg_2011"] + q["nh_2011"]) + q["new"]
    q["err_change"] = np.maximum(P90_CHANGE * change.abs(), (q["abg_scaled"] + q["nh_scaled"] - q["public_additive"]).abs())
    q["public_value"] = q["public"] + q["gap_municipal"]
    q["public_half"] = q["err_change"] + q["gap_public"]
    q["abg_value"] = q["abg"] + q["new"] / 2 + q["gap_municipal"]  # new cells: ABG or NH; for the checks only
    return q
