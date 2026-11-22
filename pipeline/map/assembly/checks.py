"""Checks of the joined result: population per district and Stadtteil and the ⓘ protocols (docs/architecture.md,
Checks; docs/texts.md, ⓘ protocol). Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.checks import FAIL, OK, WARN, Check
from pipeline.shared.core.indicator import PLACEHOLDER
from pipeline.shared.core.texts import SOURCE_LANGUAGE
from pipeline.shared.geography.model import is_small

MIN_POP_DIFF_FAIL = 500  # FAIL only above 25 % and above 500 residents difference (docs/data-rules.md, Checks)


def check_population(districts: pd.DataFrame) -> list[Check]:
    """Grid against monitoring, without small districts. FAIL per district for a gross error of the assignment. WARN per
    Stadtteil after the offset of the city: the Zensus counts fewer residents than the register, and each cell lies in
    the district of its centre, so neighbouring districts err in opposite directions."""
    g = districts[is_small(districts["POP_MONITORING"], districts["POP"]) == 0]
    diff = (g["POP"] - g["POP_MONITORING"]).abs()
    hits = g[(diff / g["POP_MONITORING"] > 0.25) & (diff > MIN_POP_DIFF_FAIL)]
    listing = "; ".join(f"{r['name']} ({r['id']}): grid {r['POP']:.0f}, monitoring {r['POP_MONITORING']:.0f}"
                        for _, r in hits.iterrows())
    out = [Check("Population per district: over 25 % and over 500 residents difference", FAIL if len(hits) else OK,
                 listing or "no district")]
    name = "Population per Stadtteil: 10 % or more difference after the offset of the city"
    q = g.groupby("quarter", sort=False, dropna=False)[["POP", "POP_MONITORING"]].sum()
    if q["POP"].sum() <= 0 or (q["POP_MONITORING"] <= 0).any():
        return out + [Check(name, WARN, "no residents in the grid or in the monitoring of a Stadtteil")]
    offset = q["POP"].sum() / q["POP_MONITORING"].sum()
    expected = offset * q["POP_MONITORING"]
    far = q[(q["POP"] - expected).abs() / expected >= 0.10]
    head = f"offset of the city {round(100 * (offset - 1), 1) + 0.0:+.1f} %".replace("-", "−")
    listing = "; ".join(f"{quarter}: grid {r['POP']:.0f}, monitoring {r['POP_MONITORING']:.0f}"
                        for quarter, r in far.iterrows())
    return out + [Check(name, WARN if len(far) else OK,
                        f"{head}: {listing}" if len(far) else f"{head}; all Stadtteile under 10 % after it")]


def check_info_protocols(catalog: list, overlays: dict[str, dict], lang: str = SOURCE_LANGUAGE) -> Check:
    """Every ⓘ is a result protocol (docs/texts.md, ⓘ protocol): indicators need Quelle, Stand and Rechnung,
    overlays Quelle, Stand and Regel. A worked example is a Rechnung. The check of the source language keeps its name;
    another language adds its code, so the names stay unique."""
    gaps = [f"{k.id}: {f}" for k in catalog for f in ("source", "as_of", "calc")
            if not getattr(k, f).strip() and not (f == "calc" and k.calc_example)]
    gaps += [f"overlay {n}: {f}" for n, v in overlays.items() for f in ("source", "as_of", "rule")
             if not v.get(f, "").strip()]
    # a placeholder left in a text means the build did not fill it
    fields = ("source", "as_of", "calc", "rule", "uncertainty")
    gaps += [f"{k.id}: {f} has a placeholder" for k in catalog for f in fields if PLACEHOLDER.search(getattr(k, f))]
    gaps += [f"overlay {n}: {f} has a placeholder" for n, v in overlays.items() for f, t in v.items()
             if isinstance(t, str) and PLACEHOLDER.search(t)]
    name = "ⓘ: every layer has its protocol" + ("" if lang == SOURCE_LANGUAGE else f" ({lang})")
    return Check(name, FAIL if gaps else OK,
                 "; ".join(gaps) or f"{len(catalog)} indicators, {len(overlays)} overlays")
