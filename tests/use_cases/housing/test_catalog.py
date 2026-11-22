from pipeline.map.assembly.catalog import CATALOG as CATALOG_BY_LANGUAGE
from pipeline.shared.core.indicator import tooltip_rounding
from pipeline.use_cases.housing import catalog
from pipeline.use_cases.housing.catalog import (CALC_EXAMPLE_QUARTERS, COUNT_STEP, COUNTS, T,
                                                INDICATORS as BY_LANGUAGE, renters_calc_example,
                                                vacancy_calc_example as _vacancy_calc_example)

CATALOG = CATALOG_BY_LANGUAGE["de"]

INDICATORS, TEXTS = BY_LANGUAGE["de"], T["de"]
DASH_MEANING, FIELD_EDGE = TEXTS["core.dash_meaning"], TEXTS["core.field_edge"]
FIELD_UNSURE = TEXTS["field_unsure"]
VACANCY_RULE = TEXTS["vacancy_rule"]
VACANCY_ROUNDING = tooltip_rounding(TEXTS, "vacant_dwellings_phrase", COUNT_STEP)
VACANCY_UNCERTAINTY_COUNT = TEXTS["vacancy_uncertainty_count"]
VACANT_WORDS = {k: TEXTS[f"calc_example.vacant.{k}"] for k in ("HOU_VACANT_ALL", "HOU_VACANT_MARKET")}
OCCUPIED = TEXTS["calc_example.occupied"]
Z22_VACANCY = TEXTS["z22_vacancy"]


def vacancy_calc_example(*args):
    return _vacancy_calc_example(*args, TEXTS)


def test_housing_indicators_in_the_catalog():
    k = {x.id: x for x in INDICATORS}
    assert list(k) == ["HOU_RENTERS", "HOU_RENT", "HOU_VACANT_MARKET", "HOU_VACANT_MARKET_DWELLINGS",
                       "HOU_VACANT_ALL", "HOU_VACANT_ALL_DWELLINGS"]
    ids = [x.id for x in CATALOG]
    i, j = ids.index("HOU_RENTERS"), ids.index("HOU_VACANT_MARKET")
    assert ids[i:i + 2] == list(k)[:2] and ids[j:j + 4] == list(k)[2:]
    assert [x.section for x in INDICATORS] == ["rent"] * 2 + ["stock"] * 4
    # one group for the rent, one for the stock
    rent, stock = INDICATORS[0].group, INDICATORS[2].group
    assert rent != stock and [x.group for x in INDICATORS] == [rent] * 2 + [stock] * 4
    assert COUNTS == frozenset({"HOU_VACANT_MARKET_DWELLINGS", "HOU_VACANT_ALL_DWELLINGS"})


def test_vacancy_counts_are_tooltip_lines_of_their_shares():
    k = {x.id: x for x in INDICATORS}
    for share in ("HOU_VACANT_MARKET", "HOU_VACANT_ALL"):
        c, s = k[share + "_DWELLINGS"], k[share]
        assert c.title and c.title != s.title and c.unit and c.unit != "%"
        assert c.levels == s.levels == ("district", "quarter")
        assert (c.source, c.as_of) == (s.source, s.as_of) and c.calc
        assert (c.decimals, c.layer, c.criterion, c.estimate, c.round_to) == (0, False, False, True, 10)
        assert c.count_of == share and c.section == "stock" and not c.rule and not c.uncertainty
        assert s.rule.endswith(" " + VACANCY_ROUNDING) and s.uncertainty.endswith(" " + VACANCY_UNCERTAINTY_COUNT)
    # the ⓘ names the step the tooltip rounds to
    assert COUNT_STEP == 10 and str(COUNT_STEP) in VACANCY_ROUNDING


def test_vacancy_protocols_use_the_shared_phrases():
    k = {x.id: x for x in INDICATORS}
    assert k["HOU_VACANT_MARKET"].rule == k["HOU_VACANT_ALL"].rule == f"{VACANCY_RULE} {VACANCY_ROUNDING}"


def test_vacancy_shares_are_estimates_from_both_grids():
    k = {x.id: x for x in INDICATORS}
    assert VACANCY_RULE.startswith(DASH_MEANING + " ")
    for i in ("HOU_VACANT_MARKET", "HOU_VACANT_ALL"):
        assert k[i].estimate and k[i].uncertainty == f"{FIELD_UNSURE} {VACANCY_UNCERTAINTY_COUNT}"
    # the two quotas of the Zensus, never swapped: the market one counts only dwellings available within three months
    assert k["HOU_VACANT_MARKET"].source == f"{Z22_VACANCY}, marktaktive Leerstandsquote"
    assert k["HOU_VACANT_ALL"].source == f"{Z22_VACANCY}, Leerstandsquote"


def test_rent_has_one_decimal_and_the_edge_note():
    k = {x.id: x for x in INDICATORS}
    assert k["HOU_RENT"].decimals == 1 and k["HOU_RENT"].uncertainty == FIELD_EDGE
    assert k["HOU_RENTERS"].uncertainty == FIELD_UNSURE and FIELD_UNSURE.startswith(FIELD_EDGE + " ")
    assert not k["HOU_RENTERS"].estimate and not k["HOU_RENT"].estimate


def _numbers(e):
    return [(r.op, r.number) for r in e.rows]


def test_vacancy_example_follows_the_spec():
    e = vacancy_calc_example("HOU_VACANT_ALL", "Innenstadt", 334.3, 7.2, 4282, 7.975)
    assert e.area == "Innenstadt"
    assert _numbers(e) == [("", 334), ("+", 7), ("", 342), ("÷", 4282), ("", 8.0)]
    assert e.rows[2].text == VACANT_WORDS["HOU_VACANT_ALL"] and all(r.text for r in e.rows)
    assert [r.estimate for r in e.rows] == [True, True, True, False, True]
    assert [r.total for r in e.rows] == [False, False, True, False, True]
    assert [r.decimals for r in e.rows] == [0, 0, 0, 0, 1]
    assert [r.unit for r in e.rows] == ["", "", "", "", "%"]


def test_vacancy_example_without_km_part():
    e = vacancy_calc_example("HOU_VACANT_ALL", "X", 334.3, 0.3, 4282, 7.975)
    assert _numbers(e) == [("", 335), ("÷", 4282), ("", 8.0)]  # the first row is the rounded total, as the tooltip
    assert e.rows[0].text == VACANT_WORDS["HOU_VACANT_ALL"] and e.rows[0].estimate and not e.rows[0].total
    market = vacancy_calc_example("HOU_VACANT_MARKET", "Bahnhofsviertel", 99.9, 8.7, 2173, 4.998)
    assert _numbers(market) == [("", 100), ("+", 9), ("", 109), ("÷", 2173), ("", 5.0)]
    assert market.rows[2].text == VACANT_WORDS["HOU_VACANT_MARKET"]
    assert vacancy_calc_example("HOU_VACANT_MARKET", "X", 99.9, 0.2, 2173, 4.6).rows[0].text == (
        VACANT_WORDS["HOU_VACANT_MARKET"])


def test_renters_example_follows_the_spec():
    e = renters_calc_example("Riederwald", 2469.0, 30.9, 98.748, TEXTS)
    assert e.area == "Riederwald"
    assert _numbers(e) == [("", 2469), ("−", 31), ("", 2438), ("÷", 2469), ("", 98.7)]
    assert e.rows[0].text == e.rows[3].text == OCCUPIED and all(r.text for r in e.rows)
    assert [r.estimate for r in e.rows] == [True, True, True, True, False]
    assert [r.total for r in e.rows] == [False, False, True, False, True]
    assert (e.rows[-1].unit, e.rows[-1].decimals) == ("%", 1)


def test_the_examples_carry_the_rechnung():
    k = {x.id: x for x in INDICATORS}
    assert CALC_EXAMPLE_QUARTERS == {"HOU_VACANT_ALL": "Innenstadt", "HOU_VACANT_MARKET": "Bahnhofsviertel",
                                     "HOU_RENTERS": "Riederwald"}
    assert all(k[i].calc == "" for i in CALC_EXAMPLE_QUARTERS)
    assert k["HOU_RENT"].calc and k["HOU_VACANT_ALL_DWELLINGS"].calc and k["HOU_VACANT_MARKET_DWELLINGS"].calc
    assert not hasattr(catalog, "VACANCY_CALC_COUNT")
    assert not [x.id for x in INDICATORS if "Die leer stehenden Wohnungen im Tooltip sind" in x.calc]
