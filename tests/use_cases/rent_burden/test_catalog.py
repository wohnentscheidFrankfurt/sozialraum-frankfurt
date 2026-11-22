import re
from string import Formatter

from pipeline import config
from pipeline.shared.core import palette
from pipeline.shared.core.numbers import format_number
from pipeline.use_cases.new_construction.catalog import PHRASES as NEW_CONSTRUCTION_PHRASES
from pipeline.use_cases.new_construction.catalog import RENT_FROM, RENT_TO, SURVEY_DATES, shown_date
from pipeline.use_cases.rent_burden.catalog import (CEILING_ABOVE, CLASS_COLOURS, CLASSES, CONTRACTS, FACTOR_RANGE,
                                                    FLAT_M2, MEASURED, NEBENKOSTEN_MONTH, PERSONS, PHRASES,
                                                    SENSITIVITY_POINTS, SURVEY_YEARS, T)
from pipeline.use_cases.rent_burden.catalog import LOW_INCOME_TEXTS as LOW_INCOME_BY_LANGUAGE
from pipeline.use_cases.rent_burden.catalog import SOURCES as SOURCES_BY_LANGUAGE
from pipeline.use_cases.rent_burden.catalog import WAGE_TEXTS as WAGE_BY_LANGUAGE
from pipeline.use_cases.survey import catalog as survey_catalog
from pipeline.use_cases.survey.model import BREAKDOWN_IDS, INCOME_LIMITS

LOW_INCOME_TEXTS, SOURCES, WAGE_TEXTS = LOW_INCOME_BY_LANGUAGE["de"], SOURCES_BY_LANGUAGE["de"], WAGE_BY_LANGUAGE["de"]
BA_LICENSE = T["de"]["ba_license"]
MIETSPIEGEL_WINDOW = NEW_CONSTRUCTION_PHRASES["de"]["mietspiegel_window"]


def low_income_texts():
    t = LOW_INCOME_TEXTS
    return [*(t[k] for k in ("title", "lead", "source", "median_label", "tip_bar", "tip_segment")),
            *t["info"].values(), *t["groups"].values(), *t["classes"]]


WAGE_LINES = ("title", "lead", "source", "explain", "rent_label", "net_label", "left_label", "tip")


def all_texts():
    return [*(WAGE_TEXTS[k] for k in WAGE_LINES), *WAGE_TEXTS["info"].values(), *WAGE_TEXTS["names"].values(),
            *WAGE_TEXTS["contracts"].values()]


def fields(text):
    return {name for _, name, _, _ in Formatter().parse(text) if name}


def test_wage_texts_are_a_protocol_without_banned_terms(banned):
    """docs/texts.md, ⓘ protocol: the five lines in their order; Regel and Unsicherheit are full sentences."""
    info = WAGE_TEXTS["info"]
    assert list(info) == ["source", "as_of", "calc", "rule", "uncertainty"]
    assert all(info.values())
    assert all(info[k][0].isupper() and info[k].endswith(".") for k in ("rule", "uncertainty"))
    assert [(w, t) for t in all_texts() for w in banned if w in t] == []


def test_as_of_follows_the_constants():
    """T3: rents and rules on the survey day of RENT_TO, Nebenkosten of the BA month, wages on 31.12., the wage
    distribution of Hessen in its month (the Regel „gut 11 %“); no prices: S1 shows one year."""
    parts = WAGE_TEXTS["info"]["as_of"].split(" · ")
    hsl = next(s for s in SOURCES if "N I 9 j/25" in s.title)
    survey = shown_date(RENT_TO, T["de"])
    dates = [survey, f"{T['de'].month(NEBENKOSTEN_MONTH)} {RENT_TO}", f"31.12.{RENT_TO}", survey, hsl.as_of]
    assert len(parts) == len(dates) and all(p.endswith(d) for p, d in zip(parts, dates))


def test_nebenkosten_month_is_the_month_of_the_ba_files():
    assert all(path.name.startswith(f"kdu-06412-0-{year}{NEBENKOSTEN_MONTH:02d}")
               for year, path in config.BA_KDU_XLSX.items())
    assert set(config.BA_KDU_XLSX) == set(SURVEY_DATES)


def test_link_is_fixed_ascii():
    """docs/design.md, Direct links: once published it never changes."""
    assert WAGE_TEXTS["link"] == "warmmiete-und-lohn"
    assert re.fullmatch(r"[a-z]+(-[a-z]+)*", WAGE_TEXTS["link"])


def test_texts_name_the_checked_constants():
    """checks.py tests these constants against the data; the texts take them, not literals."""
    info = WAGE_TEXTS["info"]
    assert isinstance(CEILING_ABOVE, int) and f"{CEILING_ABOVE} %" in info["rule"]
    assert f"{MEASURED} %" in info["uncertainty"]
    assert all(str(n) in info["uncertainty"] for n in SENSITIVITY_POINTS)
    assert f"{FLAT_M2} m²" in WAGE_TEXTS["explain"]
    assert FACTOR_RANGE[0] < 3 < FACTOR_RANGE[1]


def test_every_person_and_contract_has_its_texts():
    assert set(WAGE_TEXTS["names"]) == set(PERSONS) and set(WAGE_TEXTS["contracts"]) == set(CONTRACTS)
    assert all(WAGE_TEXTS["names"].values()) and all(WAGE_TEXTS["contracts"].values())


def test_wage_texts_have_their_placeholders():
    """wage_view fills them from the table of the latest year."""
    assert {k: fields(WAGE_TEXTS[k]) for k in WAGE_LINES} == {
        "title": set(), "lead": {"left_low", "left_high"}, "source": set(), "explain": set(),
        "rent_label": {"rent"}, "net_label": {"net"}, "left_label": {"left"},
        "tip": {"contract", "name", "warm_rent", "net", "share", "left"}}
    assert not set(WAGE_TEXTS) & {"charts", "tip_head", "tip_row", "tip_real", "tip_no_survey"}


def test_the_prose_leaves_the_formulas_to_the_sums():
    """docs/texts.md, Written sums: the prose does not repeat what the sum shows."""
    assert not any(op in WAGE_TEXTS["info"]["calc"] for op in ("=", "×", "÷"))
    assert not any(op in LOW_INCOME_TEXTS["info"]["calc"] for op in ("=", "×", "÷"))
    assert fields(WAGE_TEXTS["calc_net"]["gross"]) == {"hourly"}
    assert all(t for t in [*WAGE_TEXTS["calc_net"].values(), *WAGE_TEXTS["calc_share"].values()])


def test_wage_info_names_the_source_of_the_rule():
    """The Regel „gut 11 %“ rests on the wage distribution of the HSL: Quelle names it, and the source line too."""
    assert "Hessisches Statistisches Landesamt" in WAGE_TEXTS["info"]["source"]
    assert "Hessisches Statistisches Landesamt" in WAGE_TEXTS["source"]


def test_wage_source_names_the_latest_mietspiegel_only():
    """The Mietspiegel of a year rests on the survey of the year before."""
    assert f"Mietspiegel {RENT_TO + 1}" in WAGE_TEXTS["source"]
    assert str(RENT_FROM + 1) not in WAGE_TEXTS["source"]
    assert "Verbraucherpreisindex" not in WAGE_TEXTS["info"]["source"]


def test_uncertainty_has_no_trend_sentence():
    """S1 shows one year: the window of the Mietspiegel moves the trend, not the level of a year."""
    assert MIETSPIEGEL_WINDOW not in WAGE_TEXTS["info"]["uncertainty"]


def test_the_source_line_names_its_sources_itself():
    """The browser prints it as it is (like the block of rents): „Quellen:“ stands in the line."""
    assert "Quellen: " in WAGE_TEXTS["source"]


def test_sources_for_the_footer():
    titles = [s.title for s in SOURCES]
    assert len(SOURCES) == 4 and all(s.as_of and s.license for s in SOURCES)
    assert sum(s.license == BA_LICENSE for s in SOURCES) == 2
    assert any("N I 9 j/25" in t and "2.2.4" in t for t in titles)
    assert any("Wohnungsmarktbericht 2019/2020" in t for t in titles)
    hsl = next(s for s in SOURCES if "N I 9 j/25" in s.title)
    assert hsl.license == "dl-de/by-2-0, Hessisches Statistisches Landesamt"


# --- S2, tenants by income group ---


def test_low_income_texts_are_a_protocol_without_banned_terms(banned):
    """docs/texts.md, ⓘ protocol: the five lines in their order; Regel and Unsicherheit are full sentences."""
    info = LOW_INCOME_TEXTS["info"]
    assert list(info) == ["source", "as_of", "calc", "rule", "uncertainty"]
    assert all(info.values())
    assert all(info[k][0].isupper() and info[k].endswith(".") for k in ("rule", "uncertainty"))
    assert [(w, t) for t in low_income_texts() for w in banned if w in t] == []


def test_low_income_link_is_fixed_ascii():
    assert LOW_INCOME_TEXTS["link"] == "warmmiete-und-einkommen"


def test_class_names_follow_the_classes():
    """The agreed names of the burden classes and the income groups, from their bounds."""
    assert CLASSES == ((0, 30), (30, 40), (40, 50), (50, None))
    assert LOW_INCOME_TEXTS["classes"] == ["unter 30 %", "30 bis unter 40 %", "40 bis unter 50 %", "50 % und mehr"]
    low, high = (format_number(v, 0) for v in INCOME_LIMITS)
    assert list(LOW_INCOME_TEXTS["groups"]) == list(BREAKDOWN_IDS)
    assert list(LOW_INCOME_TEXTS["groups"].values()) == [f"unter {low} €", f"{low} bis unter {high} €",
                                                         f"{high} € und mehr"]


def test_class_colours_are_the_red_family_darker_for_heavier_burden():
    """Call 2 of the plan: under 30 % STATE, then NONPROFIT, PUBLIC, COOP."""
    assert CLASS_COLOURS == (palette.STATE, palette.NONPROFIT, palette.PUBLIC, palette.COOP)


def test_low_income_texts_name_their_limits_and_placeholders():
    t = LOW_INCOME_TEXTS
    low, high = (format_number(v, 0) for v in INCOME_LIMITS)
    assert f"{low} €" in t["title"] and f"{high} €" in t["lead"] and "{share}" in t["lead"]
    assert all(p in t["info"]["uncertainty"] for p in ("{low}", "{high}", "{mikrozensus}"))
    assert all(p in t["tip_bar"] for p in ("{group}", "{share}", "{median}"))
    assert all(p in t["tip_segment"] for p in ("{group}", "{value}", "{name}"))
    assert "{median}" in t["median_label"]
    assert set(t["mikrozensus"]) == {"under 900", "1,500-2,000"}


def test_low_income_as_of_and_sources_name_the_survey_years():
    """T4 and T7; the years are those of the microdata the build reads."""
    assert SURVEY_YEARS == tuple(config.SURVEY_MICRODATA)
    years = f"{SURVEY_YEARS[0]} und {SURVEY_YEARS[1]}"
    assert LOW_INCOME_TEXTS["info"]["as_of"].endswith(years)
    assert years in LOW_INCOME_TEXTS["info"]["source"] and years in LOW_INCOME_TEXTS["source"]
    assert LOW_INCOME_TEXTS["source"].startswith("Quelle: ")  # the browser prints the line as it is


def test_the_microdata_stand_once_in_the_footer():
    """The survey catalog lists the microdata; this catalog does not list them again."""
    assert any("Einzeldaten" in s.title for s in survey_catalog.SOURCES["de"])
    assert not any("Leben in Frankfurt" in s.title for s in SOURCES)


def test_the_phrases_that_checks_guard_stand_in_the_texts():
    """checks.py quotes these statements in its messages; every language of the map says each of them."""
    for lang, phrases in PHRASES.items():
        wage, low = WAGE_BY_LANGUAGE[lang], LOW_INCOME_BY_LANGUAGE[lang]
        assert phrases["factor"] in wage["title"] and phrases["ceiling_above"] in wage["info"]["rule"]
        assert phrases["measured"] in wage["info"]["uncertainty"]
        assert phrases["about_half"] in low["title"] and phrases["almost_quarter"] in low["lead"]
        assert f"{CEILING_ABOVE}" in phrases["ceiling_above"] and f"{MEASURED}" in phrases["measured"]
