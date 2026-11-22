from dataclasses import replace

import pandas as pd

from pipeline.map.assembly.catalog import CATALOG, breakdown_numbers, catalog_numbers, map_catalog, map_overlays
from pipeline.shared.core.indicator import Indicator
from pipeline.use_cases.survey.catalog import T as SURVEY_TEXTS, half_width_numbers
from pipeline.map.assembly.checks import check_info_protocols, check_population
from pipeline.shared.core.checks import FAIL, OK, WARN


def test_check_population_fails_per_district():
    districts = pd.DataFrame({"id": ["a", "b", "c", "d", "e"], "name": list("ABCDE"), "quarter": list("PPQQR"),
                              "POP": [1000, 1150, 1400, 10, 2000], "POP_MONITORING": [1000, 1000, 1000, 500, 1400]})
    found = {c.name: c for c in check_population(districts)}
    fail = "Population per district: over 25 % and over 500 residents difference"
    assert found[fail].status == FAIL
    assert "E (e)" in found[fail].text and "C (c)" not in found[fail].text


def test_check_population_warns_per_quarter_after_the_city_offset():
    # the Zensus counts 10 % fewer residents than the register in the whole city: that offset is no warning
    districts = pd.DataFrame({"id": list("abcd"), "name": list("ABCD"), "quarter": list("PPQR"),
                              "POP": [2200, 1700, 1800, 1500], "POP_MONITORING": [2000, 2000, 2000, 2000]})
    found = {c.name: c for c in check_population(districts)}
    fail = "Population per district: over 25 % and over 500 residents difference"
    warn = "Population per Stadtteil: 10 % or more difference after the offset of the city"
    assert {n: c.status for n, c in found.items()} == {fail: OK, warn: WARN}
    # P: 3,900 against 0.9 × 4,000 = 3,600 (+8 %), Q: 1,800 against 1,800, R: 1,500 against 1,800 (−17 %)
    assert found[warn].text.startswith("offset of the city −10.0 %: R: grid 1500, monitoring 2000")
    assert "P:" not in found[warn].text and "Q:" not in found[warn].text


def test_check_population_leaves_out_small_districts():
    # a district under 1,000 residents in the grid or in the monitoring counts neither for FAIL nor for the offset
    districts = pd.DataFrame({"id": list("abc"), "name": list("ABC"), "quarter": list("PQQ"), "POP": [1000, 1000, 5000],
                              "POP_MONITORING": [1000, 1000, 900]})
    assert [c.status for c in check_population(districts)] == [OK, OK]


def test_check_population_warns_with_a_positive_offset_and_without_residents():
    districts = pd.DataFrame({"id": list("ab"), "name": list("AB"), "quarter": list("PQ"), "POP": [1500, 1100],
                              "POP_MONITORING": [1000, 1000]})
    warn = check_population(districts)[1]
    assert warn.status == WARN and warn.text.startswith("offset of the city +30.0 %: P: grid 1500")
    empty = check_population(districts.iloc[0:0])
    assert [c.status for c in empty] == [OK, WARN] and "no residents" in empty[1].text


def test_check_population_ok():
    districts = pd.DataFrame({"id": list("ab"), "name": list("AB"), "quarter": list("PQ"), "POP": [1000, 1050],
                              "POP_MONITORING": [1000, 1000]})
    assert [(c.status, c.text) for c in check_population(districts)] == [
        (OK, "no district"), (OK, "offset of the city +2.5 %; all Stadtteile under 10 % after it")]


def test_check_info_protocols(example_ids):
    numbers = ({"fetch_date": "1.10.2026"} | catalog_numbers({k.id: {"low": 1.0, "high": 2.0} for k in CATALOG})
               | breakdown_numbers([{"indicator": k.id, "value": 30.0} for k in CATALOG if k.breakdown_of])
               | half_width_numbers({"typical": 5.0, "max_low": 13.0, "max_upper": 4.0}, SURVEY_TEXTS["de"]))
    examples = {kid: {"area": "X", "rows": []} for kid in example_ids}
    catalog, overlays = map_catalog(numbers, [], examples), map_overlays(numbers)
    assert check_info_protocols(catalog, overlays).status == OK
    # an ownership group has no Rechnung text: without its worked example the ⓘ has no Rechnung
    c = check_info_protocols(map_catalog(numbers, []), overlays)
    assert c.status == FAIL and "OWN_STATE: calc" in c.text
    i = next(i for i, k in enumerate(catalog) if not k.calc_example)
    c = check_info_protocols(catalog[:i] + [replace(catalog[i], calc="")] + catalog[i + 1:], overlays)
    assert c.status == FAIL and catalog[i].id in c.text
    assert check_info_protocols(catalog, {**overlays, "grid": {"source": "x", "as_of": "y", "rule": ""}}).status == FAIL
    # a text the build did not fill must not reach the map
    c = check_info_protocols(CATALOG, overlays)
    assert c.status == FAIL and "PROT_SOCIAL: as_of has a placeholder" in c.text


def test_info_protocols_ignore_a_literal_brace():
    k = Indicator("X", "t", "g", "%", ("quarter",), "s", "15.5.2022", "c", rule="Menge {a, b}.")
    assert check_info_protocols([k], {}).status == OK


def test_info_protocols_fail_on_an_unfilled_placeholder():
    k = Indicator("X", "t", "g", "%", ("quarter",), "s", "15.5.2022", "c", uncertainty="±{range_X}")
    c = check_info_protocols([k], {})
    assert c.status == "FAIL" and "X: uncertainty has a placeholder" in c.text
