from pipeline.shared.core.checks import FAIL, OK, WARN
from pipeline.use_cases.social_housing.checks import (check_social_housing, check_social_housing_monitoring,
                                                      check_social_housing_protocol, check_social_housing_totals)

REPORT_TEXT = ("Darüber hinaus beträgt das Reservoir an vertraglich gesicherten „zukünftig“ zum Erwerb von \n"
               "Belegungsrechten (Modell 2) vorgesehenen Wohnungen: \n2.294 Wohnungen \n")


def test_check_social_housing():
    info = {"SH_COUNT": 25610, "outside_stock": [362, 0, 49], "total_stock": [25972, 4224, 4867]}
    assert check_social_housing(info).status == OK
    assert check_social_housing({**info, "SH_COUNT": 25611}).status == FAIL


def test_check_social_housing_totals():
    """The build, not only the tests, holds the totals of the report and of the city's dwelling count."""
    info = {"total_stock": [25972, 4224, 4867], "dwellings_total": 430451}
    reference = {"sh_report_stock": 25972, "sh_dwellings_city": 430451}
    assert [c.status for c in check_social_housing_totals(info, reference)] == [OK, OK]
    assert [c.status for c in check_social_housing_totals({**info, "dwellings_total": 414063}, reference)] == [OK, FAIL]
    assert [c.status for c in check_social_housing_totals({**info, "total_stock": [25971, 0, 0]}, reference)] == [FAIL, OK]


def test_check_social_housing_protocol():
    """The numbers in the Regel lines of the ⓘ come from the report."""
    info = {"outside_stock": [362, 0, 49], "total_stock": [25972, 4224, 4867], "report_text": REPORT_TEXT}
    assert check_social_housing_protocol(info).status == OK
    assert check_social_housing_protocol({**info, "outside_stock": [361, 0, 49]}).status == FAIL
    assert check_social_housing_protocol({**info, "total_stock": [25972, 4224, 4900]}).status == FAIL


def test_check_social_housing_protocol_reads_the_contract_only_dwellings_from_the_report():
    """2.294 in the ⓘ against the sentence of the report, whatever the line breaks."""
    info = {"outside_stock": [362, 0, 49], "total_stock": [25972, 4224, 4867]}
    assert check_social_housing_protocol({**info, "report_text": REPORT_TEXT.replace("2.294", "2.300")}).status == FAIL
    assert check_social_housing_protocol({**info, "report_text": "nichts"}).status == FAIL
    assert check_social_housing_protocol({**info, "report_text": REPORT_TEXT.replace(" \n", " ")}).status == OK


def test_check_social_housing_monitoring():
    assert check_social_housing_monitoring(6.56, 7.0).status == OK
    assert check_social_housing_monitoring(4.9, 7.0).status == WARN
