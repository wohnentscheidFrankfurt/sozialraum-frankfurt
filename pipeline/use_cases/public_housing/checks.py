"""Checks of ABG and Nassauische Heimstätte against the Zensus table, the group report and the chronicle. Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.checks import FAIL, OK, WARN, Check, check_agreed_tolerance, check_tolerance, thousands

# the user accepted a number with range, though only 35 of 41 Stadtteile meet the agreed tolerance (README, Checks)
ACCEPTED_AREAS = (35, 41)


def public_checks(public: pd.DataFrame, table_municipal: int, reference: dict[str, float],
                  gap_municipal: float) -> list[Check]:
    """public: the table public_housing_quarters with the column quarter."""
    return [check_tolerance("Public housing: Frankfurt against 4000W-2002 (Kommune)", public["public_value"].sum(),
                            table_municipal, rel=0.03),
            check_tolerance("ABG: city total against group report (31.12.2022)", public["abg_value"].sum(),
                            reference["abg_group_2022"], rel=0.10, on_failure=WARN),
            check_tolerance("ABG: Gallus against ABG chronicle (2015)",
                            public.set_index("quarter").loc["Gallus", "abg_value"],
                            reference["abg_gallus_chronicle_2015"], rel=0.15, on_failure=WARN),
            check_secrecy_fill(public["fill_2011"].sum(), gap_municipal),
            check_public_quarters(public),
            check_agreed_tolerance("Public housing: tolerance of 10.10.2026", public["public_value"].tolist(),
                                   public["public_half"].tolist(), accepted=ACCEPTED_AREAS)]


def check_secrecy_fill(filled: float, gap: float, low: float = 0.8, high: float = 1.1) -> Check:
    """README: the dwellings filled from 2022 should cover the municipal
    gap of the 2011 grid (table 4000W-1011 − grid)."""
    ratio = filled / gap if gap else 1.0
    status = OK if low <= ratio <= high else WARN
    return Check("Public housing: secrecy 2011 filled from 2022", status,
                 f"{thousands(round(filled))} of {thousands(round(gap))} ({100 * ratio:.0f} %) municipal dwellings "
                 f"missing in the 2011 grid; allowed {100 * low:.0f} to {100 * high:.0f} %")


def check_public_quarters(q: pd.DataFrame) -> Check:
    bad = q[(q["public_value"] < 0) | (q["public_half"] < 0)]["quarter"].tolist()
    return Check("Public housing: value and range not negative", FAIL if bad else OK,
                 f"negative in {bad}" if bad else f"{len(q)} Stadtteile")
