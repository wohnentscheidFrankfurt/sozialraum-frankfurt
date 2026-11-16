"""Checks of the monitoring. Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.checks import Check, check_tolerance
from pipeline.shared.core.stats import weighted_mean
from pipeline.use_cases.monitoring.model import QUARTER_WEIGHTS


def check_monitoring(by_district: pd.DataFrame, monitoring: dict[str, float]) -> list[Check]:
    """The city values recomputed from the districts against the published ones. Only the indicators of the map;
    SH_SHARE_MONITORING in the reference file serves only the social housing check."""
    return [check_tolerance(f"Monitoring: {k} recomputed", weighted_mean(by_district[k], by_district[weight]),
                            monitoring[k], absolute=0.3)
            for k, weight in QUARTER_WEIGHTS.items()]
