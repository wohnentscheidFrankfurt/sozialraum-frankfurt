from pipeline.shared.core.checks import FAIL, OK
from pipeline.use_cases.ownership_history import catalog
from pipeline.use_cases.ownership_history.catalog import CHARTS, CONDO_RENTED, GROUP_TEXTS
from pipeline.use_cases.ownership_history.checks import (check_class_sum, check_condo_rented, check_history_headings,
                                                         check_size_sums, history_checks)

W2022 = {"condo": 98759, "person": 134116, "coop": 12932, "municipal": 69558, "housing_company": 57076,
         "other_company": 19264, "state": 5651, "nonprofit": 5471, "total": 402826}


def test_check_class_sum():
    assert check_class_sum("x", W2022).status == OK  # parts add up to 402,827
    assert check_class_sum("x", W2022 | {"total": 402800}).status == FAIL


FACTS = {"company_factor": 2.017, "company_share_2022": 0.1895,
         "company_growth": 2276, "company_growth_before_2010": 1741, "share_before_2010": 0.765,
         "company_building_factor": 1.503, "company_building_share_2022": 0.0842,
         "company_large_share_2011": 0.156, "company_large_share_2022": 0.322,
         "company_large_growth": 25277, "company_dwelling_growth": 38493, "large_growth_share": 0.657,
         "smallest_company_dwellings_per_building_2022": 11.03, "largest_other_dwellings_per_building_2022": 8.28}
def _failed(facts=FACTS, charts=CHARTS):
    return [c.name for c in check_history_headings(facts, charts) if c.status == FAIL]


def test_check_history_headings_all_hold():
    checks = check_history_headings(FACTS, CHARTS)
    assert len(checks) == 10 and all(c.status == OK for c in checks), [c.text for c in checks if c.status != OK]


def test_each_statement_fails_on_its_own():
    cases = [{"company_building_share_2022": 0.0851},  # HOUSES_LEAD_BUILDINGS: 8 % rounds to 9
             {"company_share_2022": 0.1951},           # HOUSES_LEAD_DWELLINGS: 19 % rounds to 20
             # HOUSES_TITLE needs each company class strictly above every other group
             {"largest_other_dwellings_per_building_2022": 11.03},
             {"smallest_company_dwellings_per_building_2022": 8.28},
             {"company_factor": 1.94}, {"company_factor": 2.06},
             {"company_building_factor": 1.44}, {"company_building_factor": 1.56},
             {"company_large_share_2022": 0.299}, {"company_large_share_2022": 0.361},
             {"company_large_share_2011": 0.149}, {"company_large_share_2011": 0.181},
             {"large_growth_share": 0.619}, {"large_growth_share": 0.701},
             {"share_before_2010": 0.7199}, {"share_before_2010": 0.7801}]
    for change in cases:
        assert len(_failed(FACTS | change)) == 1, (change, _failed(FACTS | change))
    for edge in ({"company_factor": 1.95}, {"company_factor": 2.05}, {"company_building_factor": 1.45},
                 {"company_building_factor": 1.55}, {"company_large_share_2022": 0.30},
                 {"large_growth_share": 0.62}, {"share_before_2010": 0.72}):
        assert _failed(FACTS | edge) == [], edge
    assert len(_failed(FACTS | {"share_before_2010": 0.69})) == 2  # DECADES_TITLE and DECADES_LEAD
    # fewer company buildings: the ratio can still look right, but nothing grew
    shrank = {"company_growth": -1000, "company_growth_before_2010": -750, "share_before_2010": 0.75}
    assert len(_failed(FACTS | shrank)) == 2


def test_a_changed_text_fails_its_check():
    for chart, field, phrase in (("houses", "title", catalog.HOUSES_TITLE),
                                 ("houses", "lead", catalog.HOUSES_LEAD_BUILDINGS),
                                 ("houses", "lead", catalog.HOUSES_LEAD_DWELLINGS),
                                 ("arrows", "title", catalog.ARROWS_TITLE), ("arrows", "lead", catalog.ARROWS_LEAD),
                                 ("sizes", "title", catalog.SIZES_TITLE), ("sizes", "lead", catalog.SIZES_LEAD),
                                 ("sizes", "tip_large", catalog.SIZES_TIP),
                                 ("decades", "title", catalog.DECADES_TITLE),
                                 ("decades", "lead", catalog.DECADES_LEAD)):
        changed = CHARTS | {chart: CHARTS[chart] | {field: CHARTS[chart][field].replace(phrase, "X")}}
        assert len(_failed(charts=changed)) == 1, phrase


def test_check_size_sums():
    ok = {"person": {"1": 5, "2": 5, "total": 10}, "coop": {"1": 1, "2": 1, "total": 12}}
    assert check_size_sums("x", ok, tolerance=10).status == OK
    c = check_size_sums("x", ok, tolerance=9)
    assert c.status == FAIL and "coop: -10" in c.text


def _tables():
    """Consistent tables for both years: each class has one dwelling per house, all in size class '1'."""
    history = {y: dict(W2022) for y in (2011, 2022)}
    buildings = {y: {k: {"total": n} for k, n in history[y].items()} for y in history}
    sizes = {y: {k: {"1": n, "total": n} for k, n in history[y].items()} for y in history}
    return history, buildings, sizes


def test_history_checks_in_the_order_of_the_check_report():
    history, buildings, sizes = _tables()
    # the parts add up to 402,827 and the total says 402,826: inside the tolerance of 10
    examples = [{"name": "A", "source": "A_PDF", "phrases": ["A hat Wohnungen"]}]
    found = history_checks(history, buildings, sizes, sizes, history[2022], FACTS, {"A_PDF": "A hat Wohnungen"},
                           examples)
    assert len(found) == 24 and [c.status for c in found] == ["OK"] * 24
    assert [c.name for c in found[:5]] == [
        "Ownership 2011–2022: 4000W-2013 equals 4000W-1011, 2011",
        "Ownership 2011–2022: 3000G-2007 equals 3000G-2001, 2011",
        "Ownership 2011–2022: size classes add up to the total, buildings 2011",
        "Ownership 2011–2022: size classes add up to the total, dwellings 2011",
        "Ownership 2011–2022: 4000W-2013 equals 4000W-1011, 2022"]
    assert found[8].name == "Ownership 2011–2022: 4000W-1011 equals 4000W-2002 in 2022"
    assert [c.name for c in found[9:13]] == [
        "Ownership 2011–2022: classes add up to the total, dwellings 2011",
        "Ownership 2011–2022: classes add up to the total, dwellings 2022",
        "Ownership 2011–2022: classes add up to the total, buildings 2011",
        "Ownership 2011–2022: classes add up to the total, buildings 2022"]
    assert found[13].name == f"Heading '{catalog.HOUSES_TITLE}'"
    assert found[-1].name == "Ownership 2011–2022: examples in the tooltips stand in their sources"
    assert history_checks(history, buildings, sizes, sizes, history[2022], FACTS, {}, examples)[-1].status == FAIL


def test_history_checks_fail_when_the_history_differs_from_the_map_table():
    history, buildings, sizes = _tables()
    found = history_checks(history, buildings, sizes, sizes, W2022 | {"coop": 12933}, FACTS, {}, [])
    c = next(c for c in found if c.name == "Ownership 2011–2022: 4000W-1011 equals 4000W-2002 in 2022")
    assert c.status == FAIL and c.text == "coop: 12932 against 12933"


def test_history_checks_fail_when_the_tables_disagree():
    history, buildings, sizes = _tables()
    changed = {y: {k: {**v, "total": v["total"] + (1000 if k == "coop" else 0)} for k, v in sizes[y].items()}
               for y in sizes}
    failed = [c.name for c in history_checks(history, buildings, changed, changed, history[2022], FACTS, {}, [])
              if c.status == FAIL]
    assert "Ownership 2011–2022: 3000G-2007 equals 3000G-2001, 2011" in failed
    assert "Ownership 2011–2022: size classes add up to the total, dwellings 2022" in failed


def test_the_sahle_examples_stand_in_the_stored_sources_and_fail_without_their_phrases():
    from pipeline import config
    from pipeline.shared.readers.html import example_texts
    from pipeline.use_cases.ownership_history.catalog import EXAMPLES
    from pipeline.use_cases.ownership_history.checks import check_examples
    sahle = [e for e in EXAMPLES if e["name"] == "Sahle Wohnen"]
    assert len(sahle) == 2
    texts = example_texts(config, sahle)
    name = "Ownership 2011–2022: examples in the tooltips stand in their sources"
    assert check_examples(name, texts, sahle).status == "OK"
    for e in sahle:
        for phrase in e["phrases"]:
            broken = {e["source"]: texts[e["source"]].replace(phrase.split()[0], "X")}
            failed = check_examples(name, texts | broken, sahle)
            assert failed.status == "FAIL" and phrase in failed.text


def test_check_condo_rented():
    about = GROUP_TEXTS["condo"]["about"]
    use = {2011: {"owner": 37175, "rented": 62620, "total": 101464},
           2022: {"owner": 42903, "rented": 53076, "total": 98759}}
    c = check_condo_rented(use, about)
    assert c.status == OK and c.text == "rented WEG dwellings: 2011 61.7 %, 2022 53.7 %; more than 50 % in every year"
    assert check_condo_rented(use | {2022: {"owner": 49000, "rented": 49000, "total": 98759}}, about).status == FAIL
    changed = check_condo_rented(use, about.replace(CONDO_RENTED, "X"))
    assert changed.status == FAIL and f"no longer says '{CONDO_RENTED}'" in changed.text
