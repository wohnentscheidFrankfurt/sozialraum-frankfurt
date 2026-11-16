"""Checks of the ownership estimate per cell. Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.checks import OK, WARN, Check, check_tolerance, thousands
from pipeline.shared.zensus.model import CLASSES


def check_assigned_total(ownership: pd.DataFrame, dwellings: float) -> Check:
    return check_tolerance("Ownership: assigned plus unassigned",
                           sum(ownership[f"dw_{k}"].sum() for k in CLASSES) + ownership["dw_unassigned"].sum(),
                           dwellings, absolute=1)


def check_unassigned(unassigned: float, total: float, limit: float = 5.0) -> Check:
    share = 100 * unassigned / total if total else 0.0
    status = OK if share <= limit else WARN
    return Check("Ownership: no ownership type", status,
                 f"{thousands(round(unassigned))} of {thousands(round(total))} dwellings ({share:.1f} %) without "
                 f"ownership type, also not from Zensus 2011; allowed up to {limit:.0f} %")
