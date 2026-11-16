"""Genossenschaften per Stadtteil: (a) dwellings counted in 2011, (b) their share of the secrecy gap of 2011, (c) the
estimate 2022 in cells without a coop in 2011 (README, Formula).
Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.zensus.model import CLASSES

# half range on the estimated part (b + c): the estimate errs by 34 % per Stadtteil in 9 of 10 (backtest 2011,
# research/results/formula_review.txt, round 2); the counted part (a) has no range
HALF_ESTIMATED = 0.34


def coop_cells(cells: pd.DataFrame) -> pd.DataFrame:
    """Per cell: counted_2011 (a), gap_2011 (b), estimate_2022 (c). cells: inner cells of 2022 with bld_<class>,
    dwellings, dw_coop (ownership_cells) and the 2011 columns dw_<class>_2011, dw_total_2011 (missing = 0)."""
    old = cells["dw_coop_2011"] > 0
    known_2022 = cells[[f"bld_{k}" for k in CLASSES]].sum(axis=1) > 0
    no_owner_2011 = (cells["dw_total_2011"] - cells[[f"dw_{k}_2011" for k in CLASSES]].sum(axis=1)).clip(lower=0)
    share_2022 = (cells["dw_coop"] / cells["dwellings"].where(cells["dwellings"] > 0)).fillna(0.0)
    return pd.DataFrame({"quarter": cells["quarter"],
                         "counted_2011": cells["dw_coop_2011"].where(old, 0),
                         "gap_2011": (no_owner_2011 * share_2022).where(old & known_2022, 0.0),
                         "estimate_2022": cells["dw_coop"].where(~old, 0.0)})


def coops_by_quarter(parts: pd.DataFrame) -> pd.DataFrame:
    """Sums per Stadtteil (in the order of the cells), the value a + b + c and the half range on b + c."""
    q = parts.groupby("quarter", sort=False)[["counted_2011", "gap_2011", "estimate_2022"]].sum()
    q["coop_value"] = q["counted_2011"] + q["gap_2011"] + q["estimate_2022"]
    q["coop_half"] = HALF_ESTIMATED * (q["gap_2011"] + q["estimate_2022"])
    return q.reset_index()
