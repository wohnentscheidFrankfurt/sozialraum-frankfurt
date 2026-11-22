import re
from string import Formatter

import pytest

from pipeline import config
from pipeline.use_cases.new_construction import sources
from pipeline.use_cases.new_construction.catalog import (BASE_EFFECTS, GERMAN_MONTHS, LAST_YEAR, PHRASES, PRICE_MONTH,
                                                         RENT_FROM, RENT_MARGIN, RENT_SOURCES, RENT_TO,
                                                         RENTS_TEXTS as RENTS_BY_LANGUAGE, REPORT_GROWTHS,
                                                         SOURCES as SOURCES_BY_LANGUAGE, STOCK_BREAKS,
                                                         SUBSIDISED_SOURCES, SURVEY_DATES, T,
                                                         TEXTS as TEXTS_BY_LANGUAGE, WAGE_QUARTERS, YEARS,
                                                         shown_month)

TEXTS, RENTS_TEXTS, SOURCES = TEXTS_BY_LANGUAGE["de"], RENTS_BY_LANGUAGE["de"], SOURCES_BY_LANGUAGE["de"]
FIFTH, EIGHTH, OUTFLOW_CAVEAT = (PHRASES["de"][k] for k in ("fifth", "eighth", "outflow_caveat"))


def all_texts():
    return [TEXTS["title"], TEXTS["lead"], TEXTS["source"], *TEXTS["key"].values(), *TEXTS["info"].values(),
            *(RENTS_TEXTS[k] for k in ("title", "lead", "source", "break_note", "old_base", "old_base_note")),
            *RENTS_TEXTS["info"].values()]


def numbers(text):
    """The numbers of a text as it shows them: „4.100“, „1,84“, „31.12.2025“, „7,8 %“."""
    return re.findall(r"\d+(?:[.,]\d+)*(?: %)?", text)


def test_heading_and_lead_name_the_checked_phrases_and_numbers():
    # checks.py tests FIFTH, EIGHTH and the average against the data
    assert FIFTH in TEXTS["title"] and EIGHTH in TEXTS["title"]
    assert numbers(TEXTS["title"]) == [str(LAST_YEAR), str(LAST_YEAR - 1)]
    assert str(YEARS) in numbers(TEXTS["lead"])


def test_key_names_the_four_parts_of_a_column():
    # web/js/08_new_construction.js reads these keys
    assert set(TEXTS["key"]) == {"new", "subsidised", "provisional", "conversions"}


def test_both_figures_have_their_link():
    """docs/design.md, Direct links: a link names the question of the figure and never changes once published."""
    assert (TEXTS["link"], RENTS_TEXTS["link"]) == ("gefoerderte-wohnungen", "wohnungen-und-mieten")


def test_as_of_names_the_last_year_and_the_dates_of_report_and_answers():
    as_of = TEXTS["info"]["as_of"]
    assert all(date in as_of for date in (str(LAST_YEAR), "Mai 2026", "August 2026"))


def test_no_catalog_source_carries_the_prefix_quelle():
    # the browser writes „Quelle: “ before every source line (APP.chartFigure)
    assert not TEXTS["source"].startswith("Quelle") and not RENTS_TEXTS["source"].startswith("Quelle")


def test_info_is_a_protocol_without_banned_terms(banned):
    assert {"source", "as_of", "calc"} <= set(TEXTS["info"]) <= {"source", "as_of", "calc", "rule", "uncertainty"}
    assert all(TEXTS["info"][k] for k in ("source", "as_of", "calc"))
    assert [(w, t) for t in all_texts() for w in banned if w in t] == []


def test_every_year_from_2023_has_both_programmes_from_an_answer():
    pairs = {(s["year"], s["programme"]) for s in SUBSIDISED_SOURCES}
    assert pairs == {(y, p) for y in (2023, 2024, 2025) for p in ("fw1", "fw2")}
    assert all(s["config"].startswith("ANSWER_") and s["pattern"] and s["group"] >= 1 for s in SUBSIDISED_SOURCES)


def test_sources_for_the_footer():
    assert [s.title for s in SOURCES][0].startswith("Hessisches Statistisches Landesamt")
    first = SOURCES[0].title
    assert all(t in first for t in ("31121-01-02-4", "31121-02-02-4", "31121-03-02-4", "F II 2 2025"))
    report = first.split("F II 2 2025", 1)[1]  # the tables of the report
    assert all(table in report for table in ("15", "17", "19"))


def test_stock_sources_for_the_footer():
    titles = [s.title for s in SOURCES]
    stock = next(s for s in SOURCES if "31231-02-01-4" in s.title)
    assert all(t in stock.title for t in ("F I 1 j/25", "F I 1 j/22 (Juli 2023)", "31231-02-01-4"))
    assert (stock.as_of, stock.license) == ("Juni 2026", "dl-de/by-2-0, Hessisches Statistisches Landesamt")
    population = next(s for s in SOURCES if "12411-01-01-4" in s.title)
    assert all(t in population.title for t in ("12411-01-01-4", "A I 2", "2. Halbjahr 2022 (Juni 2023)",
                                                "2. Halbjahr 2025 (Juli 2026)"))
    assert (population.as_of, population.license) == ("Juli 2026", "dl-de/by-2-0, Hessisches Statistisches Landesamt")
    assert len(titles) == len(set(titles))


def test_rents_sources_for_the_footer():
    # sources/README.md: the VPI report, the wage press table, the Mietspiegel files and the open data of the city
    prices, wages, rents, households = SOURCES[3:7]
    assert "M I 2 j/25" in prices.title and re.search(r"\bTabelle 3\b", prices.title)
    assert "Pressetabelle" in wages.title
    assert "Entwicklung des Reallohn-, Nominallohn- und Verbraucherpreisindex" in wages.title
    assert "Mietspiegel" in rents.title and all(str(y) in rents.title for y in (2018, 2022, 2024, 2026))
    assert "Wohnungswesen" in rents.title  # the office that publishes the Mietspiegel
    # the open data set of the city: persons in households per Stadtbezirk
    assert "Melderegister" in households.title and "Haushalten" in households.title
    assert [(s.as_of, s.license) for s in SOURCES[3:7]] == [
        ("Januar 2026", "dl-de/by-2-0, Hessisches Statistisches Landesamt"),
        ("3. Quartal 2025", "dl-de/by-2-0, Hessisches Statistisches Landesamt"),
        ("2018–2026", "Stadt Frankfurt am Main"), ("31.12.2025", "dl-de/by-2-0, Stadt Frankfurt am Main")]
    # in this order: after the population, before the answers of the Magistrat
    assert "12411-01-01-4" in SOURCES[2].title and "F 158/2026" in SOURCES[7].title
    assert len(SOURCES) == 8


# --- view „Neubau“, second block: rents, prices and wages ---

def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)


def test_rent_constants():
    assert (RENT_FROM, PRICE_MONTH, WAGE_QUARTERS, RENT_MARGIN) == (2017, 7, (2, 3), 0.04)
    assert SURVEY_DATES == {2017: "Juni 2017", 2021: "1.7.2021", 2023: "1.7.2023", 2025: "1.7.2025"}


def test_the_rents_block_ends_at_the_last_survey_year_which_the_stock_has():
    # the columns and the stock run to LAST_YEAR; a year without Mietspiegel survey must not stop the step
    assert RENT_TO == max(SURVEY_DATES) == RENT_SOURCES[-1]["year"] == 2025
    assert RENT_FROM < RENT_TO <= LAST_YEAR


def test_rents_texts_have_the_keys_of_both_charts_and_the_years_of_the_constants():
    t = RENTS_TEXTS
    assert set(t["charts"]) == {"nominal", "real"}
    assert all({"title", "explain", "key"} <= set(chart) for chart in t["charts"].values())
    assert set(t["charts"]["nominal"]["key"]) == {"dwellings", "population", "new", "old", "prices", "wages",
                                                  "old_base"}
    assert set(t["charts"]["real"]["key"]) == {"new", "old", "prices", "wages"}
    assert set(t["names"]) == {"new", "old", "prices", "wages", "dwellings", "population"}
    assert numbers(t["title"]) == [str(RENT_FROM)]  # checks.py: the heading starts „Seit 2017“


def placeholders(template):
    return {field for _, field, _, _ in Formatter().parse(template) if field is not None}


def test_rents_tooltip_templates_have_their_placeholders():
    assert placeholders(RENTS_TEXTS["tip_head"]) == {"year", "base"} and "= 100" in RENTS_TEXTS["tip_head"]
    assert placeholders(RENTS_TEXTS["tip_old_base"]) == {"dwellings", "population"}


def test_rents_info_names_the_codes_of_its_sources():
    # the numbers of the ⓘ are checked against the data by checks.py („rents households“, „rents uncertainty“)
    info = RENTS_TEXTS["info"]
    assert all(code in info["source"] for code in ("F I 1 j/25", "31231-02-01-4", "12411-01-01-4", "A I 2",
                                                    "M I 2 j/25", "Mietspiegel", "Melderegister"))
    # the reports on the old base are those of the break year (the hollow dots)
    old_base = STOCK_BREAKS[0]
    assert f"j/{old_base % 100}" in info["source"] and f"2. Halbjahr {old_base}" in info["source"]
    assert re.search(r"\bTabelle 3\b", info["source"])  # of the VPI report
    # the press table reaches the last wage quarter of the last rent year
    assert f"Pressetabelle {WAGE_QUARTERS[-1]}. Quartal {RENT_TO}" in info["source"]


def test_rents_info_as_of_follows_the_constants():
    """docs/texts.md, Neubau: the Stand names the day of each series, derived from RENT_TO."""
    as_of = RENTS_TEXTS["info"]["as_of"]
    price_month = T["de"].month(shown_month(SURVEY_DATES[RENT_TO])[1])  # the survey month: RENT_TO is a survey year
    days = (f"31.12.{RENT_TO}", SURVEY_DATES[RENT_TO], f"{price_month} {RENT_TO}",
            f"{WAGE_QUARTERS[-1]}. Quartal {RENT_TO}")
    assert [d for d in days if d not in as_of] == []
    assert set(re.findall(r"(?:19|20)\d\d", as_of)) == {str(RENT_TO)}


def test_info_names_base_effects_and_caveat():
    uncertainty = RENTS_TEXTS["info"]["uncertainty"]
    assert BASE_EFFECTS == (25679, 4378)
    assert "25.679" in uncertainty and "4.378" in uncertainty
    assert OUTFLOW_CAVEAT in uncertainty


def test_rents_texts_have_no_banned_terms_and_no_quelle_prefix(banned):
    texts = list(_strings(RENTS_TEXTS))
    assert [(w, t) for t in texts for w in banned if w in t] == []
    assert not RENTS_TEXTS["source"].startswith("Quelle")
    assert {"source", "as_of", "calc"} <= set(RENTS_TEXTS["info"]) <= {"source", "as_of", "calc", "rule", "uncertainty"}


def test_the_prose_leaves_the_formulas_to_the_sums():
    """docs/texts.md, Written sums: the prose does not repeat what the sum shows."""
    assert "Säule zeigt" not in TEXTS["info"]["calc"] and "÷" not in TEXTS["info"]["calc"]
    assert f"starten {RENT_FROM} bei 100" not in RENTS_TEXTS["info"]["calc"]
    assert "Ohne Inflation heißt" not in RENTS_TEXTS["info"]["calc"]
    fields = lambda text: {name for _, name, _, _ in Formatter().parse(text) if name}
    assert {k: fields(v) for k, v in RENTS_TEXTS["calc_rent"].items()} == {
        "label": {"year"}, "rent": {"year"}, "base": {"first"}, "nominal": {"first"}, "prices": {"year", "first"},
        "real": set()}
    assert fields(TEXTS["calc_column"]["label"]) == fields(TEXTS["calc_share"]["label"]) == {"year"}
    assert all(TEXTS["calc_column"].values()) and all(TEXTS["calc_share"].values())


def test_rent_sources_cover_the_surveys():
    assert [s["year"] for s in RENT_SOURCES] == [2017, 2021, 2023, 2025]
    for s in RENT_SOURCES:
        values, date = s["values"], s["date"]
        assert set(values) == {"config", "pattern", "new_group", "old_group"}
        assert set(date) == {"config", "pattern"}
        for part in (values, date):
            path = getattr(config, part["config"])
            assert path.exists(), part["config"]
        compiled = re.compile(values["pattern"])
        assert {values["new_group"], values["old_group"]} <= set(range(1, compiled.groups + 1))
        assert values["new_group"] != values["old_group"]
        names = set(re.compile(date["pattern"]).groupindex)
        assert names == {"month", "year"}  # the day is no group: the pattern pins it (test below)


def test_report_growths_cover_both_reports():
    assert [(g["year"], g["base"]) for g in REPORT_GROWTHS] == [(2021, 2017), (2025, 2023)]
    for g in REPORT_GROWTHS:
        assert getattr(config, g["config"]).exists()
        assert {g["new_group"], g["old_group"]} <= set(range(1, re.compile(g["pattern"]).groups + 1))


@pytest.fixture(scope="module")
def report_text(page_texts):
    # the rule of read_answer: spaces and line breaks count as one space
    return lambda name: re.sub(r"\s+", " ", " ".join(page_texts(getattr(config, name))))


def test_every_pinned_phrase_matches_the_real_report_exactly_once(report_text):
    phrases = [(s["year"], "values", s["values"]) for s in RENT_SOURCES]
    phrases += [(s["year"], "date", s["date"]) for s in RENT_SOURCES]
    phrases += [(g["year"], "growths", g) for g in REPORT_GROWTHS]
    assert len(phrases) == 10  # four values, four dates, two growth sentences
    for year, kind, p in phrases:
        hits = list(re.finditer(p["pattern"], report_text(p["config"])))
        assert len(hits) == 1, (year, kind, len(hits))


def test_a_survey_day_other_than_the_first_finds_no_hit_so_the_reader_stops(report_text):
    # the three date patterns pin the day as the literal 01; SURVEY_DATES shows „1.7.“ for them
    for s in RENT_SOURCES[1:]:
        date = s["date"]
        text = report_text(date["config"])
        hit = re.search(date["pattern"], text).group(0)
        assert re.search(r"\b01\.\d{2}\.\d{4}$", hit), hit
        moved = text.replace(hit, re.sub(r"01(\.\d{2}\.\d{4})$", r"02\1", hit))
        assert re.search(date["pattern"], moved) is None, s["year"]


def test_the_german_months_are_the_ones_of_the_reader():
    # sources.py may not import the catalog (tests/test_architecture.py), so both modules keep the list
    assert GERMAN_MONTHS == sources.GERMAN_MONTHS and sorted(GERMAN_MONTHS.values()) == list(range(1, 13))


def test_the_pinned_phrases_read_the_agreed_numbers(report_text):
    read = {}
    for s in RENT_SOURCES:
        v, d = s["values"], s["date"]
        m = re.search(v["pattern"], report_text(v["config"]))
        read[s["year"]] = (m.group(v["new_group"]), m.group(v["old_group"]),
                           re.search(d["pattern"], report_text(d["config"])).groupdict())
    assert read == {
        2017: ("10,21", "8,69", {"month": "Juni", "year": "2017"}),
        2021: ("11,56", "9,14", {"month": "07", "year": "2021"}),
        2023: ("13,05", "9,43", {"month": "07", "year": "2023"}),
        2025: ("13,95", "10,11", {"month": "07", "year": "2025"}),
    }
    growths = {}
    for g in REPORT_GROWTHS:
        m = re.search(g["pattern"], report_text(g["config"]))
        growths[g["year"]] = (m.group(g["new_group"]), m.group(g["old_group"]))
    assert growths == {2021: ("13,2", "5,2"), 2025: ("6,9", "7,2")}


def test_the_phrases_that_checks_guard_stand_in_the_texts():
    """checks.py tests these statements against the data; every language of the map says each of them."""
    from pipeline.use_cases.new_construction.catalog import HOUSEHOLD_RANGE
    for lang, phrases in PHRASES.items():
        t, rents = TEXTS_BY_LANGUAGE[lang], RENTS_BY_LANGUAGE[lang]
        assert phrases["fifth"] in t["title"] and phrases["eighth"] in t["title"]
        assert phrases["lead_average"] in t["lead"]
        assert phrases["provisional_span"] in t["info"]["rule"] and phrases["provisional_span"] in t["info"]["uncertainty"]
        assert rents["title"].startswith(phrases["since"] + " ") and phrases["older_less"] in rents["lead"]
        low, high = (T[lang].number(x, 2) for x in HOUSEHOLD_RANGE)
        assert phrases["household_sentence"].format(low=low, high=high) in rents["info"]["rule"]
        assert phrases["outflow_caveat"] in rents["info"]["uncertainty"]
        assert phrases["mietspiegel_window"] in rents["info"]["uncertainty"]


def test_the_growths_of_the_uncertainty_come_from_the_constants():
    from pipeline.use_cases.new_construction.catalog import PUBLISHED_GROWTH, SAME_BASE_GROWTH
    uncertainty = RENTS_TEXTS["info"]["uncertainty"]
    shown = [T["de"].number(g, 1, "%") for g in (*SAME_BASE_GROWTH, *PUBLISHED_GROWTH)]
    assert [uncertainty.index(g) for g in shown] == sorted(uncertainty.index(g) for g in shown)
    assert shown == ["7,8 %", "5,3 %", "6,6 %", "1,8 %"]
