"""Titles and ⓘ of the ownership groups except ABG, NH and Genossenschaften. Pure module."""
from __future__ import annotations

from pipeline.shared.core import palette
from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import (format_de, QUARTERS_ONLY, QUARTERS_RULE, TIP_DWELLINGS_RULE, TIP_DWELLINGS_UNCERTAINTY, Indicator, Source,
                                             estimate_backtest)
from pipeline.use_cases.ownership_cells.catalog import OWN_AS_OF, OWN_LEGEND_NOTE
from pipeline.use_cases.ownership_cells.model import GROUPS
from pipeline.use_cases.ownership_shares.model import BACKTEST_AREAS, BACKTEST_HITS, OtherNumbers

# Quelle of the groups this package declares (docs/texts.md, ⓘ protocol)
OTHER_SOURCE = ("Zensus 2022, 100-m-Gitter (Gebäude nach Eigentumsform, Wohnungen); Tabelle 4000W-2002 · Zensus 2011, "
                "wo 2022 die Eigentumsform fehlt")


def _own(kid: str, title: str, color: str, members: str = "", ramp_color: str = "", **kw) -> Indicator:
    """members: the sentence on who belongs to the group, where the title does not say it. ramp_color: the end of the
    ramp of the layer, where it differs from the colour of the group. Only a layer has a tooltip with the count. The
    Rechnung is the worked example alone (README, Formula)."""
    layer = kw.get("layer", True)
    return Indicator(kid, title, "Eigentum", "%", QUARTERS_ONLY, OTHER_SOURCE, OWN_AS_OF,
                     "", f"color:{ramp_color or color}",
                     color=color, legend_note=OWN_LEGEND_NOTE if layer else "",
                     rule=QUARTERS_RULE + (f" {members}" if members else "") + (f" {TIP_DWELLINGS_RULE}" if layer else ""),
                     uncertainty=estimate_backtest(kid, BACKTEST_HITS, BACKTEST_AREAS)
                     + (f" {TIP_DWELLINGS_UNCERTAINTY}" if layer else ""), estimate=True, **kw, section="ownership")


# Prominent examples of the group (research/2026-10-14-who-are-the-private-companies.md). Each name stands in the ⓘ;
# check_examples finds its phrases in the source (a path in pipeline/config.py). Vonovia: the number stays only in
# the phrase of EXAMPLES, which the check finds in the press release.
VONOVIA_DWELLINGS = "16.000"
COMPANY_EXAMPLES_SOURCE = Source(
    "Beispiele privater Unternehmen: Pressemitteilung Vonovia, Antwort des Magistrats F 3283/2025, Geschäftsbericht GWH "
    "2022, Catella, cash-online", "2014–2026",
    "Veröffentlichungen der Unternehmen, des Magistrats und der Presse")
SOURCES = [COMPANY_EXAMPLES_SOURCE]
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

INDICATORS: list[Indicator] = [
    # Zensus definition of both company classes (research/2026-10-09-private-companies-2011-2022.md)
    _own("OWN_COMPANY", "Private Unternehmen", palette.COMPANIES, "Zur Gruppe gehören privatwirtschaftliche Wohnungsunternehmen, "
         "zum Beispiel Vonovia. Ein weiteres Beispiel ist die GWH, eine Tochter der Landesbank Helaba. Dazu kommen andere privatwirtschaftliche "
         "Unternehmen wie Banken, Fonds & Co. Ihr Hauptgeschäft ist nicht die Vermietung. Beispiele sind die "
         "Fondsgesellschaften Industria Wohnen und Hamburg Trust.",
         legend_detail="Zum Beispiel Vonovia, GWH und Fonds wie Industria Wohnen"),
    _own("OWN_PERSON", "Privatpersonen und WEG", palette.PERSONS_AND_CONDOS,
         "Zur Gruppe gehören Privatpersonen und Gemeinschaften von Wohnungseigentümer*innen.",
         legend_detail="Einzelne Personen und Gemeinschaften von Wohnungseigentümer*innen"),
    # a ramp to the light colour of the group turns muddy when darkened: the layer takes the ramp of the public red
    _own("OWN_STATE", "Bund oder Land", palette.STATE,
         "Die Nassauische Heimstätte gehört nicht dazu. Der Zensus 2022 zählt sie als kommunal.", palette.PUBLIC),
    _own("OWN_NONPROFIT", "Organisationen ohne Erwerbszweck", palette.NONPROFIT, layer=False),
]


# The Stadtteil of each worked example: one with a high share, mostly the highest. ABG and NH: Niederrad (5th), with
# large fills, so the reader sees why the sum needs them (public_housing README). The numbers come from the build.
CALC_EXAMPLE_QUARTERS = {"OWN_PUBLIC": "Niederrad", "OWN_COOP": "Riederwald", "OWN_COMPANY": "Innenstadt",
                         "OWN_PERSON": "Nieder-Erlenbach", "OWN_STATE": "Ginnheim", "OWN_NONPROFIT": "Gutleutviertel"}
BUILDING_LABELS = {"housing_company": "Gebäude von Wohnungsunternehmen", "other_company": "Gebäude anderer Unternehmen",
                   "condo": "Gebäude von WEG", "person": "Gebäude von Privatpersonen",
                   "state": "Gebäude von Bund oder Land", "nonprofit": "Gebäude von Organisationen ohne Erwerbszweck"}
GROUP_WORDS = {"OWN_COMPANY": "privater Unternehmen", "OWN_PERSON": "von Privatpersonen und WEG",
               "OWN_STATE": "von Bund oder Land", "OWN_NONPROFIT": "von Organisationen ohne Erwerbszweck"}


def other_calc_example(group: str, area: str, n: OtherNumbers, share: float) -> CalcExample:
    """The written sum of one of the four other groups: rounded rows, result rows are the values of the build."""
    classes = GROUPS[group]
    rows: list[Row] = []
    products = []
    if len(classes) == 1:
        k = classes[0]
        factor = round(n.factors[k], 1)
        products.append(round(n.buildings[k] * factor))
        rows += [Row("", n.buildings[k], 0, BUILDING_LABELS[k]),
                 Row("×", factor, 1, "Wohnungen je Gebäude von " + BUILDING_LABELS[k].removeprefix("Gebäude von ")
                     + " im 100-m-Gitter, im Schnitt in Frankfurt")]
    else:
        for i, k in enumerate(classes):
            factor = round(n.factors[k], 1)
            products.append(round(n.buildings[k] * factor))
            rows.append(Row("+" if i else "", products[-1], 0, f"{format_de(n.buildings[k], 0)} {BUILDING_LABELS[k]} × "
                                                              f"{format_de(factor, 1)} Wohnungen je Gebäude"))
    product = sum(products)
    rows.append(Row("", product, 0, "Wohnungen nach dem Schnitt", total=True))
    rest = n.dwellings - n.from_2011
    if product > 0:
        rows.append(Row("×", round(rest / product, 2), 2, "angeglichen an die Wohnungen in den 100-m-Feldern"))
    word = f"Wohnungen {GROUP_WORDS[group]}"
    with_2011 = round(n.from_2011) > 0
    rows.append(Row("", round(rest), 0, "" if with_2011 else word, total=True, estimate=True))
    if with_2011:
        rows.append(Row("+", round(n.from_2011), 0, "aus dem Zensus 2011, wo 2022 die Eigentumsform fehlt",
                        estimate=True))
        rows.append(Row("", round(n.dwellings), 0, word, total=True, estimate=True))
    rows.append(Row("÷", round(n.total), 0, "alle Wohnungen"))
    rows.append(Row("", round(share, 1), 1, "Wert auf der Karte", total=True, estimate=True, unit="%"))
    return CalcExample(area, tuple(rows))
