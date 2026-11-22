"""Title and ⓘ of the Genossenschaften (texts.<lang>.yaml). Pure module."""
from __future__ import annotations

from pipeline.shared.core import palette
from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import QUARTERS_ONLY, Indicator, estimate_up_to
from pipeline.shared.core.texts import Texts, package_texts, per_language
from pipeline.use_cases.ownership_cells.catalog import OWN_LEGEND_NOTE_COOP

T: dict[str, Texts] = package_texts(__file__)


def _indicators(t: Texts) -> list[Indicator]:
    return [
        Indicator("OWN_COOP", t["OWN_COOP.title"], t["core.groups.ownership"], "%", QUARTERS_ONLY,
                  t["OWN_COOP.source"], t["OWN_COOP.as_of"],
                  "",  # the Rechnung is the worked example alone (README, Formula)
                  f"color:{palette.COOP}",
                  rule=t["OWN_COOP.rule"],
                  uncertainty=t.fill("OWN_COOP.uncertainty", estimate=estimate_up_to(t, "OWN_COOP")), estimate=True,
                  color=palette.COOP, legend_note=OWN_LEGEND_NOTE_COOP[t.lang], section="ownership"),
    ]


INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)


def coop_calc_example(area: str, row: dict, total: float, share: float, t: Texts) -> CalcExample:
    """The written sum of the Genossenschaften: rounded rows, the result row is the value of the build.
    t: the texts of this package (T[lang])."""
    rows = [Row("", round(row["counted_2011"]), 0, t["calc_example.counted_2011"]),
            Row("+", round(row["gap_2011"]), 0, t["calc_example.gap_2011"])]
    if round(row["estimate_2022"]) > 0:
        rows.append(Row("+", round(row["estimate_2022"]), 0, t["calc_example.estimate_2022"]))
    rows += [Row("", round(row["coop_value"]), 0, t["calc_example.coop_value"], total=True, estimate=True),
             Row("÷", round(total), 0, t["core.calc_rows.all_dwellings"]),
             Row("", round(share, 1), 1, t["core.calc_rows.map_value"], total=True, estimate=True, unit="%")]
    return CalcExample(area, tuple(rows))
