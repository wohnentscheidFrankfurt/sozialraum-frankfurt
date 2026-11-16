"""An indicator of the map and the texts several catalogs share. Pure module."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Indicator:
    id: str
    title: str
    group: str
    unit: str
    levels: tuple[str, ...]
    source: str  # Quelle: work and table or figure; any text field may hold {name} placeholders (map/assembly/catalog.py)
    as_of: str  # Stand
    calc: str  # Rechnung: how the value of an area is computed
    ramp: str = "teal"  # a named ramp of shared/core/colours.py, or "color:#rrggbb" = 5 steps from almost white to the colour
    decimals: int = 1
    layer: bool = True
    type: str = "number"
    criterion: bool = True  # selectable in the own query; False for counts that cannot be compared between areas
    rule: str = ""  # Regel: only when needed (no value, what does not count, merges)
    uncertainty: str = ""  # Unsicherheit: range of an estimate or sampling error
    round_to: int = 0  # a count: the tooltip shows it rounded to this step, below it "unter <step>"; 0: as it is
    estimate: bool = False  # the map writes „~“ before the value (docs/texts.md, Numbers)
    color: str = ""  # colour of an owner group in the profile and the grid (pipeline/shared/core/palette.py)
    colors: tuple[str, ...] = ()  # the 5 hex colours of `ramp` (shared/core/colours.py); assembly fills them, the map reads them
    legend_note: str = ""  # the line under the legend title: what the number is (docs/texts.md, Map: legend)
    legend_detail: str = ""  # the second note line of the legend, under legend_note (docs/texts.md, Map: legend)
    rank: int = 0  # the value is a rank among this many areas; tooltip and profile read „Rang 46 von 114“ (docs/texts.md, Map: tooltip); 0: no rank
    count_of: str = ""  # a count without layer: the id of the share whose tooltip shows it in a line „<unit>: <number>“; the ⓘ of the share explains it
    count_total: str = ""  # a count: the id of an area property whose value the tooltip adds as „ von <N>“ (voters of the eligible)
    breakdown_of: str = ""  # a value without layer: the id of the layer whose tooltip lists it as „<title>: <value>“ under the layer's breakdown_lead
    breakdown_lead: str = ""  # a layer with breakdown lines: the line above them in the tooltip („Nach Haushaltsnettoeinkommen“)
    section: str = ""  # the topic the browser's logic keys on; `group` is only its heading: ownership, situation, rent, stock, land, planning, election
    survey_area: bool = False  # a value of the Umfragebezirk, not of the area: tooltip and profile name the Umfragebezirk
    calc_example: dict | None = None  # worked example of the Rechnung (indicators with a written sum): {"area", "rows"}; assembly fills it


@dataclass(frozen=True)
class Source:
    """One line of the source list in the footer of the map (German, visible)."""
    title: str
    as_of: str  # {fetch_date} stands for the fetch date of the WFS data; assembly puts it in
    license: str
    url: str = ""  # the page of the publisher: the footer links the title to it (docs/design.md, Layouts)


PLACEHOLDER = re.compile(r"\{(\w+)\}")  # {name} in a catalog text; fill puts the number in


def fill(text: str, numbers: dict[str, str]) -> str:
    """Puts the numbers of the build into the {name} placeholders of a text; an unknown name raises KeyError. Any other
    brace stays as it is."""
    return PLACEHOLDER.sub(lambda m: numbers[m.group(1)], text)


BOTH = ("district", "quarter")
Z22 = "Zensus 2022, 100-m-Gitter"
Z22_AS_OF = "15.5.2022"
Z11_AS_OF = "9.5.2011"
ZENSUS_LICENSE = "dl-de/by-2-0, Statistische Ämter des Bundes und der Länder"
QUARTERS_ONLY = ("quarter",)


def year_of(as_of: str) -> str:
    """The year at the end of an as-of date: „15.5.2022“ and „Ende 2022“ give „2022“."""
    return as_of[-4:]


def format_de(value: float, decimals: int, unit: str = "") -> str:
    """German number with thousands separator, as the map shows it: 18,4 %; 69.219."""
    text = f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    return f"{text} {unit}" if unit else text


# Texts several catalogs share (docs/texts.md, Terms)
QUARTERS_RULE = "Den Wert gibt es nur für Stadtteile."
# The count of an owner group in the map tooltip (APP.tooltipHead and APP.dwellingsText in web/js/01_base.js); the ⓘ of each
# ownership layer explains it (docs/texts.md, ⓘ protocol)
TIP_DWELLINGS_RULE = ("Im Tooltip rundet die Karte die Wohnungen auf 50. Liegt auch die obere Grenze der Schätzung "
                      "unter 200, steht dort „unter 200“. Kann die Zahl um mehr als ein Drittel abweichen, steht dort "
                      "„unsicher“.")
TIP_DWELLINGS_UNCERTAINTY = "Die Wohnungen im Tooltip können so stark abweichen wie der Anteil."


def tooltip_rounding(dwellings: str, step: int) -> str:
    """Regel of a share whose count the tooltip rounds to step (`round_to`, APP.countLine in web/js/01_base.js);
    dwellings in the accusative and dative plural („Wohnungen“, „leer stehenden Wohnungen“)."""
    return (f"Im Tooltip rundet die Karte die {dwellings} auf {step}. Unter {step} {dwellings} steht dort "
            f"„unter {step}“.")


TEST_2011 = "Die Karte hat die Schätzung mit den Zahlen von 2011 getestet."
FIELD_MIDPOINT = "Jedes Feld gehört zu dem Gebiet, in dem sein Mittelpunkt liegt."
FIELD_EDGE = ("Felder auf einer Gebietsgrenze zählen ganz zu einem Gebiet. In kleinen Bezirken kann das den Wert "
              "spürbar verschieben.")
FIELD_SUM = f"Die Karte summiert die 100-m-Felder im Gebiet. {FIELD_MIDPOINT}"
# meaning of „–“ in the Zensus 2022 (Cell-Key-Methode; pipeline/use_cases/housing/README.md)
DASH_MEANING = ("Ein Strich („–“) im Zensus steht für null oder für einen Wert, den der Zensus aus Datenschutzgründen auf null "
                "gesetzt hat.")


def field_mean(weight: str) -> str:
    """How the map averages the 100-m fields of an area, weighted by weight (German, dative plural)."""
    return f"Die Karte mittelt die 100-m-Felder im Gebiet, gewichtet nach {weight}. {FIELD_MIDPOINT}"


def estimate_range(kid: str, unit: str = "Prozentpunkte") -> str:
    """Unsicherheit of ABG and NH: the smallest to largest half range per Stadtteil (placeholder range_<kid>)."""
    return f"Je nach Stadtteil kann die Schätzung um {{range_{kid}}} {unit} abweichen."


def estimate_up_to(kid: str) -> str:
    """Unsicherheit of the Genossenschaften: the largest half range (placeholder high_<kid>); counted Stadtteile
    have none."""
    return f"Je nach Stadtteil kann die Schätzung um bis zu {{high_{kid}}} Prozentpunkte abweichen."


def estimate_backtest(kid: str, hits: int, areas: int) -> str:
    """Unsicherheit of a group with a fixed half range: in how many Stadtteile the backtest on 2011 stayed within it."""
    return (f"{TEST_2011} In {hits} von {areas} Stadtteilen wich die Schätzung um höchstens {{high_{kid}}} "
            "Prozentpunkte vom gezählten Wert ab.")


def range_de(low: float, high: float, decimals: int = 1) -> str:
    """Smallest and largest half range: „0,6 bis 8,8“; one number where both round alike („3,5“); no „,0“."""
    a, b = (format_de(x, decimals).removesuffix("," + "0" * decimals) if decimals else format_de(x, 0)
            for x in (low, high))
    return a if a == b else f"{a} bis {b}"
