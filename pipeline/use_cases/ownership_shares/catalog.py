"""Titles and ⓘ of the ownership groups except ABG, NH and Genossenschaften (texts.<lang>.yaml). Pure module."""
from __future__ import annotations

from pipeline.shared.core import palette
from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import QUARTERS_ONLY, Indicator, Source, estimate_backtest
from pipeline.shared.core.texts import Texts, package_texts, per_language
from pipeline.use_cases.ownership_cells.catalog import OWN_AS_OF, OWN_LEGEND_NOTE
from pipeline.use_cases.ownership_cells.model import GROUPS
from pipeline.use_cases.ownership_shares.model import BACKTEST_AREAS, BACKTEST_HITS, OtherNumbers

T: dict[str, Texts] = package_texts(__file__)


def _own(t: Texts, kid: str, color: str, ramp_color: str = "", **kw) -> Indicator:
    """ramp_color: the end of the ramp of the layer, where it differs from the colour of the group. Only a layer has a
    tooltip with the count. The Rechnung is the worked example alone (README, Formula)."""
    layer = kw.get("layer", True)
    return Indicator(kid, t[f"{kid}.title"], t["core.groups.ownership"], "%", QUARTERS_ONLY, t["source"],
                     OWN_AS_OF[t.lang], "", f"color:{ramp_color or color}",
                     color=color, legend_note=OWN_LEGEND_NOTE[t.lang] if layer else "", rule=t[f"{kid}.rule"],
                     uncertainty=t.fill(f"{kid}.uncertainty",
                                        estimate=estimate_backtest(t, kid, BACKTEST_HITS, BACKTEST_AREAS)),
                     legend_detail=t.tree(kid).get("legend_detail", ""), estimate=True, **kw, section="ownership")


# Prominent examples of the group (research/2026-10-14-who-are-the-private-companies.md). Each name stands in the ⓘ
# (OWN_COMPANY.rule of each language file); check_examples finds its phrases in the source (a path in
# pipeline/config.py). Vonovia: the number stays only in the phrase of EXAMPLES, which the check finds in the press
# release. Names and phrases are source vocabulary: they stay here.
VONOVIA_DWELLINGS = "16.000"
COMPANY_EXAMPLES_SOURCE: dict[str, Source] = per_language(lambda t: Source(**t.tree("sources.company_examples")), T)
SOURCES: dict[str, list[Source]] = per_language(lambda t: [COMPANY_EXAMPLES_SOURCE[t.lang]], T)
EXAMPLES = [
    {"name": "Vonovia", "source": "VONOVIA_PRESS_PDF",
     "phrases": [f"Vonovia in Frankfurt einen Bestand von rund {VONOVIA_DWELLINGS} Wohnungen", "24. Februar 2026"]},
    {"name": "GWH", "source": "GWH_STOCK_PDF", "phrases": ["Der Frankfurter Wohnungsbestand der GWH umfasst"]},
    {"name": "Helaba", "source": "GWH_REPORT_PDF",
     "phrases": ["Die oberste Muttergesellschaft des Teilkonzerns ist die Landesbank Hessen"]},
    {"name": "Industria Wohnen", "source": "INDUSTRIA_PAGE_HTML",
     "phrases": ["residential portfolio of Industria Wohnen in Lyoner Quartier"]},
    {"name": "Hamburg Trust", "source": "HAMBURG_TRUST_PAGE_HTML",
     "phrases": ["Little East von Hamburg Trust hat sein Investitionsobjekt, eine Wohnanlage in Frankfurt am Main"]},
]


def _indicators(t: Texts) -> list[Indicator]:
    return [
        _own(t, "OWN_COMPANY", palette.COMPANIES),
        _own(t, "OWN_PERSON", palette.PERSONS_AND_CONDOS),
        # a ramp to the light colour of the group turns muddy when darkened: the layer takes the ramp of the public red
        _own(t, "OWN_STATE", palette.STATE, palette.PUBLIC),
        _own(t, "OWN_NONPROFIT", palette.NONPROFIT, layer=False),
    ]


INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)


# The Stadtteil of each worked example: one with a high share, mostly the highest. ABG and NH: Niederrad (5th), with
# large fills, so the reader sees why the sum needs them (public_housing README). The numbers come from the build.
CALC_EXAMPLE_QUARTERS = {"OWN_PUBLIC": "Niederrad", "OWN_COOP": "Riederwald", "OWN_COMPANY": "Innenstadt",
                         "OWN_PERSON": "Nieder-Erlenbach", "OWN_STATE": "Ginnheim", "OWN_NONPROFIT": "Gutleutviertel"}


def other_calc_example(group: str, area: str, n: OtherNumbers, share: float, t: Texts) -> CalcExample:
    """The written sum of one of the four other groups: rounded rows, result rows are the values of the build.
    t: the texts of this package (T[lang])."""
    classes = GROUPS[group]
    labels = t.tree("calc_example.building_labels")
    rows: list[Row] = []
    products = []
    if len(classes) == 1:
        k = classes[0]
        factor = round(n.factors[k], 1)
        products.append(round(n.buildings[k] * factor))
        rows += [Row("", n.buildings[k], 0, labels[k]),
                 Row("×", factor, 1, t.fill("calc_example.factor", buildings=labels[k]))]
    else:
        for i, k in enumerate(classes):
            factor = round(n.factors[k], 1)
            products.append(round(n.buildings[k] * factor))
            rows.append(Row("+" if i else "", products[-1], 0,
                            t.fill("calc_example.product", count=t.number(n.buildings[k], 0), buildings=labels[k],
                                   factor=t.number(factor, 1))))
    product = sum(products)
    rows.append(Row("", product, 0, t["calc_example.average"], total=True))
    rest = n.dwellings - n.from_2011
    if product > 0:
        rows.append(Row("×", round(rest / product, 2), 2, t["calc_example.adjusted"]))
    word = t.fill("calc_example.group_dwellings", group=t[f"calc_example.group_words.{group}"])
    with_2011 = round(n.from_2011) > 0
    rows.append(Row("", round(rest), 0, "" if with_2011 else word, total=True, estimate=True))
    if with_2011:
        rows.append(Row("+", round(n.from_2011), 0, t["calc_example.from_2011"], estimate=True))
        rows.append(Row("", round(n.dwellings), 0, word, total=True, estimate=True))
    rows.append(Row("÷", round(n.total), 0, t["core.calc_rows.all_dwellings"]))
    rows.append(Row("", round(share, 1), 1, t["core.calc_rows.map_value"], total=True, estimate=True, unit="%"))
    return CalcExample(area, tuple(rows))
