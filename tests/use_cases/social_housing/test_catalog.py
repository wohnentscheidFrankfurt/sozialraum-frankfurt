from pipeline.map.assembly.catalog import CATALOG as CATALOG_BY_LANGUAGE
from pipeline.use_cases.social_housing.catalog import SH_AS_OF, SH_CONTRACT_ONLY, SH_DATE, SOURCES as SOURCES_BY_LANGUAGE, T

CATALOG = CATALOG_BY_LANGUAGE["de"]

SOURCES = SOURCES_BY_LANGUAGE["de"]


def test_social_housing_2025_in_the_catalog():
    ids = [k.id for k in CATALOG]
    k = {x.id: x for x in CATALOG}
    i = ids.index("SH_SHARE")
    assert ids[i:i + 3] == ["SH_SHARE", "SH_COUNT", "HOU_VACANT_MARKET"]  # the start of the stock group
    assert {k[s].section for s in ("SH_SHARE", "SH_COUNT")} == {"stock"}
    assert not [x for x in ids if x.startswith("SH_ENDING")]
    for s in ("SH_SHARE", "SH_COUNT"):
        assert k[s].levels == ("quarter",) and k[s].as_of == "Ende 2025"
    assert not k["SH_COUNT"].layer and not k["SH_COUNT"].criterion


def test_the_german_as_of_date_is_the_date_of_the_report():
    assert SH_AS_OF == T["de"].date(SH_DATE)


def test_the_rule_of_the_share_names_the_contract_only_dwellings():
    k = {x.id: x for x in CATALOG}
    assert SH_CONTRACT_ONLY == 2294
    assert "2.294 " in k["SH_SHARE"].rule


def test_the_footer_names_the_report_and_the_building_file():
    """The names of the two works and their publishers are source vocabulary."""
    assert [s.as_of for s in SOURCES] == ["31.12.2025", "31.12.2025"]
    # the annual report of the Amt für Wohnungswesen
    assert all(w in SOURCES[0].title for w in ("Jahresbericht", "Kommunale Wohnraumversorgung 2025", "Wohnungswesen"))
    # the Statistische Gebäudedatei, published on the Statistikportal
    assert all(w in SOURCES[1].title for w in ("Statistikportal Frankfurt", "Wohnungsbestand und Räume",
                                               "Gebäudedatei"))
    assert SOURCES[1].license == "dl-de/by-2-0, Stadt Frankfurt am Main"


def test_titles_carry_no_year_and_the_count_layer_counts_dwellings():
    """docs/texts.md, Map: legend: titles carry no as-of year, the legend note names it."""
    k = {x.id: x for x in CATALOG}
    assert not any(c.isdigit() for i in ("SH_SHARE", "SH_COUNT") for c in k[i].title)
    assert k["SH_COUNT"].unit == "Wohnungen"
    assert k["SH_SHARE"].legend_note.endswith(f", {k['SH_SHARE'].as_of}")


def test_social_housing_example_follows_the_spec():
    from pipeline.use_cases.social_housing.catalog import CALC_EXAMPLE_QUARTERS, social_housing_calc_example
    assert CALC_EXAMPLE_QUARTERS == {"SH_SHARE": "Bonames"}
    e = social_housing_calc_example("Bonames", 613, 3129.0, 19.59, T["de"])
    assert e.area == "Bonames"
    assert [(r.op, r.number) for r in e.rows] == [("", 613), ("÷", 3129), ("", 19.6)]
    assert all(r.text for r in e.rows)
    assert not any(r.estimate for r in e.rows)
    assert e.rows[-1].unit == "%" and e.rows[-1].decimals == 1 and e.rows[-1].total


def test_the_example_carries_the_rechnung_of_the_share():
    k = {x.id: x for x in CATALOG}
    assert k["SH_SHARE"].calc == ""
