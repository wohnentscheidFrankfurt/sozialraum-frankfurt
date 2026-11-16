"""Title and ⓘ of the Genossenschaften. Pure module."""
from __future__ import annotations

from pipeline.shared.core import palette
from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import (QUARTERS_ONLY, QUARTERS_RULE, TIP_DWELLINGS_RULE, TIP_DWELLINGS_UNCERTAINTY, Z11_AS_OF, Z22_AS_OF,
                                             Indicator, estimate_up_to)
from pipeline.use_cases.ownership_cells.catalog import OWN_LEGEND_NOTE_COOP

INDICATORS: list[Indicator] = [
    Indicator("OWN_COOP", "Genossenschaften", "Eigentum", "%", QUARTERS_ONLY,
              "Zensus 2011, 100-m-Gitter (Wohnungen nach Eigentumsform) · Zensus 2022, 100-m-Gitter (Gebäude nach "
              "Eigentumsform, Wohnungen); Tabelle 4000W-2002", f"{Z11_AS_OF} · {Z22_AS_OF}",
              "",  # the Rechnung is the worked example alone (README, Formula)
              f"color:{palette.COOP}",
              rule=f"{QUARTERS_RULE} Die Karte geht von den Genossenschaftswohnungen 2011 aus. Verkäufe seit 2011 sind deshalb "
                   f"nicht erfasst. {TIP_DWELLINGS_RULE}",
              uncertainty=f"{estimate_up_to('OWN_COOP')} {TIP_DWELLINGS_UNCERTAINTY}", estimate=True, color=palette.COOP,
              legend_note=OWN_LEGEND_NOTE_COOP, section="ownership"),
]


def coop_calc_example(area: str, row: dict, total: float, share: float) -> CalcExample:
    """The written sum of the Genossenschaften: rounded rows, the result row is the value of the build."""
    rows = [Row("", round(row["counted_2011"]), 0, "Wohnungen von Genossenschaften, 2011 gezählt"),
            Row("+", round(row["gap_2011"]), 0,
                "Wohnungen ohne bekannte Eigentumsform 2011, nach dem Anteil der Genossenschaften 2022")]
    if round(row["estimate_2022"]) > 0:
        rows.append(Row("+", round(row["estimate_2022"]), 0,
                        "geschätzt aus den Gebäuden 2022, wo 2011 keine Genossenschaft war"))
    rows += [Row("", round(row["coop_value"]), 0, "Wohnungen von Genossenschaften", total=True, estimate=True),
             Row("÷", round(total), 0, "alle Wohnungen"),
             Row("", round(share, 1), 1, "Wert auf der Karte", total=True, estimate=True, unit="%")]
    return CalcExample(area, tuple(rows))
