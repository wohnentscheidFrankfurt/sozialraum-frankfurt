"""An indicator of the map and the texts several catalogs share. Pure module."""
from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.shared.core.numbers import format_number, format_range
from pipeline.shared.core.texts import Texts, package_texts

CORE: dict[str, Texts] = package_texts(__file__)


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
QUARTERS_ONLY = ("quarter",)


def year_of(as_of: str) -> str:
    """The year at the end of an as-of date: „15.5.2022“ and „Ende 2022“ give „2022“."""
    return as_of[-4:]


def format_de(value: float, decimals: int, unit: str = "") -> str:
    """German number with thousands separator, as the map shows it: 18,4 %; 69.219."""
    return format_number(value, decimals, unit)


def range_de(low: float, high: float, decimals: int = 1) -> str:
    """German range, see format_range."""
    return format_range(low, high, decimals)


# Texts several catalogs share: keys of texts.<lang>.yaml in this folder (docs/texts.md, Terms). The constants are the
# German aliases of the transition; use cases reference {@core.<key>} in their own files.
_DE = CORE["de"]
Z22 = _DE["z22"]
Z22_AS_OF = _DE["z22_as_of"]
Z11_AS_OF = _DE["z11_as_of"]
ZENSUS_LICENSE = _DE["zensus_license"]
QUARTERS_RULE = _DE["quarters_rule"]
TIP_DWELLINGS_RULE = _DE["tip_dwellings_rule"]
TIP_DWELLINGS_UNCERTAINTY = _DE["tip_dwellings_uncertainty"]
TEST_2011 = _DE["test_2011"]
FIELD_MIDPOINT = _DE["field_midpoint"]
FIELD_EDGE = _DE["field_edge"]
FIELD_SUM = _DE["field_sum"]
DASH_MEANING = _DE["dash_meaning"]


def _unit(t: Texts, unit_key: str) -> str:
    """A unit word: a key under `units.` of the core file, else a key of the caller's texts."""
    try:
        return t[f"core.units.{unit_key}"]
    except KeyError:
        return t[unit_key]


def _transitional(old):
    """Until the use cases are migrated, the helpers also take the old German arguments (a Texts first: new form)."""
    def wrap(new):
        def helper(*args, **kwargs):
            if args and isinstance(args[0], Texts):
                return new(*args, **kwargs)
            return old(*args, **kwargs)
        helper.__name__, helper.__doc__ = new.__name__, new.__doc__
        return helper
    return wrap


def _old_tooltip_rounding(dwellings: str, step: int) -> str:
    return _DE.fill("core.templates.tooltip_rounding", dwellings=dwellings, step=step)


def _old_field_mean(weight: str) -> str:
    return _DE.fill("core.templates.field_mean", weight=weight)


def _old_estimate_range(kid: str, unit: str = "Prozentpunkte") -> str:
    return _DE.fill("core.templates.estimate_range", kid=kid, unit=unit)


def _old_estimate_up_to(kid: str) -> str:
    return _DE.fill("core.templates.estimate_up_to", kid=kid)


def _old_estimate_backtest(kid: str, hits: int, areas: int) -> str:
    return _DE.fill("core.templates.estimate_backtest", kid=kid, hits=hits, areas=areas)


@_transitional(_old_tooltip_rounding)
def tooltip_rounding(t: Texts, dwellings_key: str, step: int) -> str:
    """Regel of a share whose count the tooltip rounds to step (`round_to`, APP.countLine in web/js/01_base.js);
    dwellings_key: the key of the caller's text for the dwellings (German: accusative and dative plural alike)."""
    return t.fill("core.templates.tooltip_rounding", dwellings=t[dwellings_key], step=step)


@_transitional(_old_field_mean)
def field_mean(t: Texts, weight_key: str) -> str:
    """How the map averages the 100-m fields of an area, weighted by the text at weight_key of the caller."""
    return t.fill("core.templates.field_mean", weight=t[weight_key])


@_transitional(_old_estimate_range)
def estimate_range(t: Texts, kid: str, unit_key: str = "points") -> str:
    """Unsicherheit of ABG and NH: the smallest to largest half range per Stadtteil (placeholder range_<kid>)."""
    return t.fill("core.templates.estimate_range", kid=kid, unit=_unit(t, unit_key))


@_transitional(_old_estimate_up_to)
def estimate_up_to(t: Texts, kid: str) -> str:
    """Unsicherheit of the Genossenschaften: the largest half range (placeholder high_<kid>); counted Stadtteile
    have none."""
    return t.fill("core.templates.estimate_up_to", kid=kid)


@_transitional(_old_estimate_backtest)
def estimate_backtest(t: Texts, kid: str, hits: int, areas: int) -> str:
    """Unsicherheit of a group with a fixed half range: in how many Stadtteile the backtest on 2011 stayed within it."""
    return t.fill("core.templates.estimate_backtest", kid=kid, hits=hits, areas=areas)
