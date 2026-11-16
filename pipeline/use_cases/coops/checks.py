"""Checks of the Genossenschaften against the Zensus table. Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.checks import FAIL, OK, Check, check_agreed_tolerance, check_tolerance


def coop_checks(q: pd.DataFrame, table_coop: int) -> list[Check]:
    """q: the table coops_quarters. Frankfurt within 3 % of table 4000W-2002, as for ABG and NH."""
    bad = q[(q["coop_value"] < 0) | (q["coop_half"] < 0)]["quarter"].tolist()
    return [check_tolerance("Coops: Frankfurt against 4000W-2002 (Wohnungsgenossenschaft)", q["coop_value"].sum(),
                            table_coop, rel=0.03),
            Check("Coops: value and range not negative", FAIL if bad else OK,
                  f"negative in {bad}" if bad else f"{len(q)} Stadtteile"),
            check_agreed_tolerance("Coops: tolerance of 10.10.2026", q["coop_value"].tolist(), q["coop_half"].tolist())]
