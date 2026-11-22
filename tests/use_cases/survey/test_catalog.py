import re

from pipeline.map.assembly.catalog import CATALOG
from pipeline.use_cases.survey import catalog
from pipeline.use_cases.survey.catalog import HALF_WIDTH_NAMES, T
from pipeline.use_cases.survey.model import BREAKDOWN_IDS, INCOME_LIMITS, MIN_CASES, STEP
from pipeline.use_cases.survey.sources import FIGURES

TEXTS = T["de"]
INCOME_CALC, INCOME_LEAD = catalog.INCOME_CALC["de"], catalog.INCOME_LEAD["de"]
INCOME_RULE, INCOME_TITLES = catalog.INCOME_RULE["de"], catalog.INCOME_TITLES["de"]
INCOME_UNCERTAINTY = catalog.INCOME_UNCERTAINTY["de"]
MICRODATA, RENT_BURDEN_UNCERTAINTY = TEXTS["microdata"], TEXTS["rent_burden_uncertainty"]
CALC_EXAMPLE_HOUSEHOLD = TEXTS["calc_example.household"]
# the income limits as the map prints them
LOWER, UPPER = (TEXTS.number(limit, 0) for limit in INCOME_LIMITS)


def test_survey_indicators_in_the_catalog():
    ids = [k.id for k in CATALOG]
    k = {x.id: x for x in CATALOG}
    assert ids[ids.index("HOU_RENT") + 1] == "LIF_RENT_BURDEN_RATIO"
    assert ids[ids.index("SOC_INDEX") + 1] == "LIF_ATTACHMENT"
    assert k["LIF_RENT_BURDEN_RATIO"].section == "rent"
    assert k["LIF_ATTACHMENT"].section == "situation"
    for s in ("LIF_RENT_BURDEN_RATIO", "LIF_ATTACHMENT"):
        assert k[s].levels == ("district",) and k[s].type == "classes" and k[s].unit == "%" and k[s].layer
    # the margin of ±4 to 4.5 points holds for shares of respondents, not for the rent burden of renters
    rent = k["LIF_RENT_BURDEN_RATIO"]
    assert rent.uncertainty.startswith(RENT_BURDEN_UNCERTAINTY)
    # the ± of the income groups is their own bootstrap, never the margin of the shares of respondents
    assert "±4 bis 4,5" not in rent.uncertainty
    # the 29 is the printed city value of sources.py (a pure catalog may not import it, so the text holds the literal
    # and this test ties both)
    assert f" {FIGURES['LIF_RENT_BURDEN_RATIO']['city']} Prozent " in rent.calc


def test_the_income_groups_are_hidden_lines_of_the_rent_burden():
    k = {x.id: x for x in CATALOG}
    ids = [x.id for x in CATALOG]
    i = ids.index("LIF_RENT_BURDEN_RATIO")
    assert ids[i + 1:i + 4] == list(BREAKDOWN_IDS) == list(INCOME_TITLES)
    # the titles name the income limits of model.INCOME_LIMITS
    assert [re.findall(r"\d[\d.]*", t) for t in INCOME_TITLES.values()] == [[LOWER], [LOWER, UPPER], [UPPER]]
    assert all(t.endswith(" €") for t in INCOME_TITLES.values())
    for kid, title in INCOME_TITLES.items():
        e = k[kid]
        assert (e.title, e.unit, e.decimals, e.layer, e.criterion, e.estimate) == (title, "%", 0, False, False, True)
        assert e.breakdown_of == "LIF_RENT_BURDEN_RATIO" and e.legend_note == "" and e.levels == ("district",)
        assert e.section == "rent" and e.survey_area and e.breakdown_lead == ""
    assert k["LIF_RENT_BURDEN_RATIO"].breakdown_lead == INCOME_LEAD
    assert k["LIF_RENT_BURDEN_RATIO"].breakdown_of == "" and k["LIF_ATTACHMENT"].breakdown_lead == ""


def test_the_info_of_the_rent_burden_explains_the_income_groups():
    """Quelle, Stand, Rechnung, Regel and Unsicherheit of the rent burden carry the texts of the income groups."""
    rent = next(x for x in CATALOG if x.id == "LIF_RENT_BURDEN_RATIO")
    assert rent.source.endswith(f", Abbildung 4.5 · {MICRODATA}")
    assert rent.as_of == "Mai–August 2025 · April–August 2024"
    assert rent.calc.endswith(INCOME_CALC)
    assert all(f"{{city_{kid}}}" in rent.calc for kid in BREAKDOWN_IDS)
    assert rent.rule.endswith(INCOME_RULE)
    assert (STEP, MIN_CASES) == (5, 30)
    assert f" {STEP} Prozentpunkte" in INCOME_RULE and f" {MIN_CASES} " in INCOME_RULE
    assert rent.uncertainty.endswith(INCOME_UNCERTAINTY)
    assert f"{LOWER} €" in INCOME_UNCERTAINTY
    assert all(f"±{{{name}}}" in rent.uncertainty for name in HALF_WIDTH_NAMES.values())
    assert "range_" not in rent.uncertainty


def test_the_microdata_stand_in_the_footer():
    SOURCES = catalog.SOURCES["de"]
    assert [(s.as_of, s.license) for s in SOURCES][1:] == [("2024, 2025", "dl-de/by-2-0, Stadt Frankfurt am Main")]
    assert "Leben in Frankfurt" in SOURCES[1].title and "2024" in SOURCES[1].title and "2025" in SOURCES[1].title
    assert "(Einzeldaten)" in SOURCES[1].title


def test_survey_calc_example_rows():
    from pipeline.use_cases.survey.catalog import survey_calc_example
    e = survey_calc_example({"rent": 550.0, "rent_low": 500, "rent_high": 600, "costs": 175.0, "costs_low": 150,
                             "costs_high": 200, "income": 1500.0, "income_low": 1000, "income_high": 2000,
                             "ratio": 48.33}, TEXTS)
    assert e.area == CALC_EXAMPLE_HOUSEHOLD
    assert [(r.op, r.number, r.decimals, r.total, r.unit) for r in e.rows] == [
        ("", 550, 0, False, "€"), ("+", 175, 0, False, "€"), ("", 725, 0, True, "€"), ("÷", 1500, 0, False, "€"),
        ("", 48, 0, True, "%")]
    # the classes of the answers, in German number format
    assert "500 bis 600 €" in e.rows[0].text and "150 bis 200 €" in e.rows[1].text
    assert "1.000 bis 2.000 €" in e.rows[3].text
    assert all(r.text for r in e.rows) and not any(r.estimate for r in e.rows)
    # half up to whole percent, never banker's rounding; one household, no tilde
    half = survey_calc_example({"rent": 550.0, "rent_low": 500, "rent_high": 600, "costs": 175.0, "costs_low": 150,
                                "costs_high": 200, "income": 1500.0, "income_low": 1000, "income_high": 2000,
                                "ratio": 48.5}, TEXTS)
    assert half.rows[-1].number == 49 and not any(r.estimate for r in half.rows)


def test_half_width_numbers_are_whole_numbers_rounded_half_up():
    from pipeline.use_cases.survey.catalog import half_width_numbers
    assert half_width_numbers({"typical": 4.5, "max_low": 13.33, "max_upper": 3.49}, TEXTS) == {
        "typical_LIF_RENT_BURDEN_INCOME_LOW": "5", "max_LIF_RENT_BURDEN_INCOME_LOW": "13",
        "max_LIF_RENT_BURDEN_INCOME_UPPER": "3"}
