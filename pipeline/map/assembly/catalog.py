"""Metadata of every indicator: title, group and the result protocol of its ⓘ (source, as-of date, calculation,
rule, uncertainty; docs/texts.md, ⓘ protocol). Pure module."""
from __future__ import annotations

from dataclasses import asdict, fields, replace

from pipeline.shared.core.colours import ramp
from pipeline.shared.core.numbers import format_number
from pipeline.shared.core.texts import LANGUAGES, package_texts
from pipeline.use_cases.building_gaps import catalog as building_gaps_catalog
from pipeline.use_cases.construction_year import catalog as construction_year_catalog
from pipeline.use_cases.coops import catalog as coops_catalog
from pipeline.shared.core.indicator import Indicator, Source, fill
from pipeline.use_cases.election import catalog as election_catalog
from pipeline.use_cases.election.catalog import election_indicators
from pipeline.use_cases.flat_roofs import catalog as flat_roofs_catalog
from pipeline.use_cases.housing import catalog as housing_catalog
from pipeline.use_cases.land import catalog as land_catalog
from pipeline.use_cases.monitoring import catalog as monitoring_catalog
from pipeline.use_cases.new_construction import catalog as new_construction_catalog
from pipeline.use_cases.ownership_cells.catalog import GRID_OVERLAY, ZENSUS_2011, ZENSUS_2022
from pipeline.use_cases.ownership_history import catalog as ownership_history_catalog
from pipeline.use_cases.ownership_shares import catalog as ownership_shares_catalog
from pipeline.use_cases.protection import catalog as protection_catalog
from pipeline.use_cases.public_housing import catalog as public_housing_catalog
from pipeline.use_cases.rent_burden import catalog as rent_burden_catalog
from pipeline.use_cases.social_housing import catalog as social_housing_catalog
from pipeline.use_cases.survey import catalog as survey_catalog
from pipeline.use_cases.survey.model import round_half_up


T = package_texts(__file__)


def _entries(lang: str) -> list[Indicator]:
    return [
        *public_housing_catalog.INDICATORS[lang],
        *coops_catalog.INDICATORS[lang],
        *ownership_shares_catalog.INDICATORS[lang],
        *monitoring_catalog.INDICATORS[lang],
        *social_housing_catalog.INDICATORS[lang],
        *housing_catalog.INDICATORS[lang],
        *construction_year_catalog.INDICATORS[lang],
        *survey_catalog.INDICATORS[lang],
        *land_catalog.INDICATORS[lang],
        *protection_catalog.INDICATORS[lang],
        *flat_roofs_catalog.INDICATORS[lang],
        *building_gaps_catalog.INDICATORS[lang],
    ]


_ENTRIES: dict[str, list[Indicator]] = {lang: _entries(lang) for lang in LANGUAGES}


# Order of the layers in the map: the single place for it (docs/architecture.md, Use-case packages)
# by topic (docs/texts.md, Map: profile): Eigentum, Soziale Lage, Miete, Wohnungsbestand, Boden, Planung
LAYER_ORDER = ("OWN_PUBLIC", "OWN_COOP", "OWN_COMPANY", "OWN_PERSON", "OWN_STATE", "OWN_NONPROFIT",
               "SOC_MIN_INCOME", "SOC_UNEMPLOYED", "SOC_INDEX", "LIF_ATTACHMENT",
               "HOU_RENTERS", "HOU_RENT", "LIF_RENT_BURDEN_RATIO", "LIF_RENT_BURDEN_INCOME_LOW",
               "LIF_RENT_BURDEN_INCOME_MID", "LIF_RENT_BURDEN_INCOME_HIGH",
               "SH_SHARE", "SH_COUNT", "HOU_VACANT_MARKET", "HOU_VACANT_MARKET_DWELLINGS", "HOU_VACANT_ALL",
               "HOU_VACANT_ALL_DWELLINGS",
               "HOU_PRE1919", "HOU_PRE1919_DWELLINGS", "HOU_1949_1978", "HOU_1949_1978_DWELLINGS",
               "LAND_VALUE", "ROOF_FLAT", "GAP_AREA", "PROT_SOCIAL", "LAND_PENDING_PLAN")
_BY_ID = {lang: {k.id: k for k in entries} for lang, entries in _ENTRIES.items()}
CATALOG: dict[str, list[Indicator]] = {lang: [_BY_ID[lang][i] for i in LAYER_ORDER] for lang in LANGUAGES}


# Order of the source list in the footer of the map: the single place for it, the same for every language
def _source_order(lang: str) -> tuple[Source, ...]:
    return (ZENSUS_2022[lang], ZENSUS_2011[lang], ownership_history_catalog.ZENSUS_DATABASE[lang],
            public_housing_catalog.ABG_NEW_BUILDINGS[lang], ownership_shares_catalog.COMPANY_EXAMPLES_SOURCE[lang],
            ownership_history_catalog.OTHER_EXAMPLES_SOURCE[lang], *monitoring_catalog.SOURCES[lang],
            *social_housing_catalog.SOURCES[lang], *new_construction_catalog.SOURCES[lang],
            *rent_burden_catalog.SOURCES[lang], *survey_catalog.SOURCES[lang], *election_catalog.SOURCES[lang],
            *protection_catalog.SOURCES[lang], *land_catalog.SOURCES[lang], *flat_roofs_catalog.SOURCES[lang],
            *building_gaps_catalog.SOURCES[lang], Source(**T[lang].tree("basemap")))


SOURCE_ORDER: dict[str, tuple[Source, ...]] = {lang: _source_order(lang) for lang in LANGUAGES}


_INDICATOR_TEXTS = ("source", "as_of", "calc", "rule", "uncertainty")


def catalog_numbers(ranges: dict[str, dict], lang: str) -> dict[str, str]:
    """Numbers of the build that the ⓘ names: the smallest to largest half range per Stadtteil ("range_<ID>") and the
    largest alone ("high_<ID>"; docs/texts.md, ⓘ protocol). ranges holds low and high, in points for
    a share, in dwellings for a count (rounded to 10). The fetch date ("fetch_date") comes from the caller."""
    out = {}
    for kid, r in ranges.items():
        share = _BY_ID[lang][kid].unit == "%"
        low, high = (r["low"], r["high"]) if share else (round(r["low"], -1), round(r["high"], -1))
        decimals = 1 if share else 0
        out[f"range_{kid}"] = T[lang].number_range(low, high, decimals)
        out[f"high_{kid}"] = T[lang].number_range(high, high, decimals)
    return out


def breakdown_numbers(city: list[dict], lang: str) -> dict[str, str]:
    """City value of every breakdown line ("city_<ID>") as the tooltip shows it: rounded half up to the step of the
    breakdown (survey), with „~“ for an estimate (docs/texts.md, Numbers). city: rows indicator, value, kind. A line
    without its city value raises KeyError."""
    values = {r["indicator"]: r["value"] for r in city}
    return {f"city_{k.id}": ("~" if k.estimate else "")
            + format_number(round_half_up(values[k.id]), k.decimals, k.unit, lang)
            for k in CATALOG[lang] if k.breakdown_of}


def _filled(item, names: tuple[str, ...], numbers: dict[str, str]):
    return replace(item, **{n: fill(getattr(item, n), numbers) for n in names})


def map_catalog(numbers: dict[str, str], lists: list[dict], examples: dict[str, dict] | None,
                lang: str) -> list[Indicator]:
    """Every indicator the map shows with its texts finished and the 5 colours of its ramp; the checks see the same
    list. numbers: fetch_date, range_<ID>, high_<ID>. examples: the worked example per indicator id."""
    examples = examples or {}
    return [replace(_filled(k, _INDICATOR_TEXTS, numbers), colors=tuple(ramp(k.ramp)), calc_example=examples.get(k.id))
            for k in [*CATALOG[lang], *election_indicators(lists, election_catalog.T[lang])]]


def merge_examples(*parts: dict[str, dict]) -> dict[str, dict]:
    """The worked examples of all use cases as one dict per indicator id. A duplicate id is an error."""
    merged: dict[str, dict] = {}
    for part in parts:
        if dup := sorted(merged.keys() & part.keys()):
            raise ValueError(f"worked example given twice: {', '.join(dup)}")
        merged |= part
    return merged


def map_catalog_payload(catalog: list[Indicator]) -> list[dict]:
    """The indicators as the browser reads them: the colours stand in `colors`, so the name of the ramp stays in
    Python."""
    return [{k: v for k, v in asdict(i).items() if k != "ramp"} for i in catalog]


def map_overlays(numbers: dict[str, str], lang: str) -> dict[str, dict]:
    """Result protocol for the ⓘ of every overlay with its texts finished (docs/texts.md, ⓘ protocol)."""
    raw = {**protection_catalog.OVERLAYS[lang], **land_catalog.OVERLAYS[lang], **flat_roofs_catalog.OVERLAYS[lang],
           **building_gaps_catalog.OVERLAYS[lang], "grid": GRID_OVERLAY[lang]}
    return {name: {f: fill(t, numbers) for f, t in v.items()} for name, v in raw.items()}


def map_sources(numbers: dict[str, str], lang: str) -> list[dict]:
    """Sources in the footer of the map (visible) with their texts finished."""
    return [asdict(_filled(s, tuple(f.name for f in fields(s)), numbers)) for s in SOURCE_ORDER[lang]]
