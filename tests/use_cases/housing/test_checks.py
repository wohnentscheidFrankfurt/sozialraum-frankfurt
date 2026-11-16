from pipeline.shared.core.checks import OK, WARN
from pipeline.use_cases.housing.checks import (check_city_tables, check_vacancy_4000w, check_vacancy_city,
                                                 check_vacancy_count, check_vacancy_km)


def test_check_vacancy_4000w():
    c = check_vacancy_4000w(2.66, {"vacant": 12893, "occupied_and_vacant": 402393})
    assert c.status == OK and c.name == "Vacancy: city value against 4000W"
    assert "grid 2.66 %, table 4000W 3.20 % (12,893 of 402,393 dwellings), allowed ± 1 point" in c.text
    assert check_vacancy_4000w(1.9, {"vacant": 12893, "occupied_and_vacant": 402393}).status == WARN
    assert "allowed ± 2 points" in check_vacancy_4000w(2.66, {"vacant": 12893, "occupied_and_vacant": 402393}, 2).text


def test_check_city_tables_against_the_zensus_tables():
    checks = check_city_tables({"HOU_RENTERS": 79.92, "HOU_RENT": 10.583}, owner_rate=20.1, rent=10.58)
    assert [(c.name, c.status) for c in checks] == [
        ("Housing: Mieteranteil against 4000W-0001", "OK"), ("Housing: Miete im Bestand against 4000W-0004", "OK")]


def test_check_city_tables_fail_beyond_2_percent():
    checks = check_city_tables({"HOU_RENTERS": 82.0, "HOU_RENT": 10.0}, owner_rate=20.1, rent=10.9)
    assert [c.status for c in checks] == ["FAIL", "FAIL"]


KM = {"vacancy_market_km_2022": 1.83, "vacancy_all_km_2022": 3.08}


def test_check_vacancy_km():
    """The comparison with the 1-km grid is a check, not a line of the ⓘ (docs/data-rules.md, Checks); the filled
    rates lie close to it."""
    c = check_vacancy_km({"HOU_VACANT_MARKET": 1.84, "HOU_VACANT_ALL": 3.08}, KM)
    assert c.status == OK and c.name == "Vacancy: city values against the 1-km grid"
    assert "HOU_VACANT_MARKET 1.84 % against 1.83 %" in c.text and "allowed ± 0.2 points" in c.text
    assert check_vacancy_km({"HOU_VACANT_MARKET": 1.43, "HOU_VACANT_ALL": 3.08}, KM).status == WARN
    assert check_vacancy_km({"HOU_VACANT_MARKET": 1.84, "HOU_VACANT_ALL": 2.66}, KM).status == WARN


def test_check_vacancy_city_against_the_table_value():
    c = check_vacancy_city(3.08, 3.1)
    assert c.status == OK and c.name == "Vacancy: city value against WHG009"
    assert "grid 3.08 %, table WHG009 3.10 %, allowed ± 0.15 points" in c.text
    assert check_vacancy_city(2.66, 3.1).status == WARN
    assert check_vacancy_city(3.30, 3.1).status == WARN


def test_check_vacancy_count_warns_beyond_10_percent():
    ok = check_vacancy_count(12016.0, {"vacant": 12893, "occupied_and_vacant": 402393})  # -6.8 %
    assert ok.status == OK and ok.name == "Vacancy: city count against 4000W"
    assert "12,016" in ok.text and "12,893" in ok.text
    assert check_vacancy_count(11000.0, {"vacant": 12893, "occupied_and_vacant": 402393}).status == WARN
    assert check_vacancy_count(14200.0, {"vacant": 12893, "occupied_and_vacant": 402393}).status == WARN
