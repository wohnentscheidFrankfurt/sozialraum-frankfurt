import datetime

import openpyxl
import pytest

from pipeline import config
from pipeline.shared.readers.pdf import page_texts
from pipeline.use_cases.new_construction.catalog import SURVEY_DATES
from pipeline.use_cases.rent_burden.catalog import PERSONS
from pipeline.use_cases.rent_burden.model import Tariff, WageRules
from pipeline.use_cases.rent_burden.sources import (
    HESSEN_QUANTILES, MIETSPIEGEL_COSTS, MIKROZENSUS_2018, MINDESTLOHN, WAGE_RULES, read_bmf_reference,
    read_est_reference, read_hessen_quantiles, read_median_wage, read_mietspiegel_costs, read_mikrozensus_2018,
    read_nebenkosten)

YEAR_FILES = {2017: config.BA_WAGES_2017_XLSM}


@pytest.fixture(name="pages_of", scope="module")
def pages_of_fixture():
    cache = {}

    def pages_of(name: str) -> list[str]:
        if name not in cache:
            cache[name] = page_texts(getattr(config, name))
        return cache[name]
    return pages_of


@pytest.fixture(name="report_pages", scope="module")
def report_pages_fixture():
    return page_texts(config.HOUSING_MARKET_REPORT_2019_2020_PDF)


@pytest.fixture(name="hessen_pages", scope="module")
def hessen_pages_fixture():
    return page_texts(config.HSL_WAGE_DISTRIBUTION_PDF)


def test_nebenkosten_of_the_four_survey_years():
    got = {y: read_nebenkosten(config.BA_KDU_XLSX[y], y) for y in SURVEY_DATES}
    assert {y: (round(v["betriebskosten"], 2), round(v["heizkosten"], 2)) for y, v in got.items()} == {
        2017: (2.33, 0.86), 2021: (2.45, 0.86), 2023: (2.63, 1.41), 2025: (2.72, 1.39)}
    assert set(got[2017]) == {"betriebskosten", "heizkosten"}


def test_median_wage_2017_and_2025():
    assert round(read_median_wage(2017, YEAR_FILES, config.BA_WAGES_SERIES_XLSX)) == 3861
    assert round(read_median_wage(2025, YEAR_FILES, config.BA_WAGES_SERIES_XLSX)) == 5074
    assert round(read_median_wage(2021, YEAR_FILES, config.BA_WAGES_SERIES_XLSX)) == 4273
    assert round(read_median_wage(2023, YEAR_FILES, config.BA_WAGES_SERIES_XLSX)) == 4594


def test_a_year_without_wage_stops():
    with pytest.raises(ValueError, match="2019"):
        read_median_wage(2019, YEAR_FILES, config.BA_WAGES_SERIES_XLSX)


def test_an_html_page_saved_as_xlsx_stops(tmp_path):
    page = tmp_path / "kdu-06412-0-202506-xlsx.xlsx"
    page.write_text("<html><body>Zugriff verweigert</body></html>", encoding="utf-8")
    with pytest.raises(ValueError, match="kdu-06412-0-202506-xlsx.xlsx"):
        read_nebenkosten(page, 2025)
    with pytest.raises(ValueError, match="kdu-06412-0-202506-xlsx.xlsx"):
        read_median_wage(2025, YEAR_FILES, page)


def test_a_kdu_file_of_another_year_stops():
    """Each file holds June of its year (2017 as the text „Juni 2017“, later years as the date 1.6.)."""
    with pytest.raises(ValueError, match="kdu-06412-0-202106-xlsx.xlsx.*2025"):
        read_nebenkosten(config.BA_KDU_XLSX[2021], 2025)
    with pytest.raises(ValueError, match="kdu-06412-0-201706-xlsx.xlsx.*2021"):
        read_nebenkosten(config.BA_KDU_XLSX[2017], 2021)


def _kdu_head(path, region, month):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Tabelle 1b HH Miete"
    for row in (["Tabelle 1b: Wohn- und Wohnkostensituation"], [region], [month], ["Merkmal", "Insgesamt"]):
        ws.append(row)
    wb.save(path)


def test_a_kdu_file_of_another_region_or_month_stops(tmp_path):
    path = tmp_path / "kdu-06413-0-202506-xlsx.xlsx"
    _kdu_head(path, "Kreis Offenbach am Main, Stadt", datetime.datetime(2025, 6, 1))
    with pytest.raises(ValueError, match="kdu-06413-0-202506-xlsx.xlsx.*Frankfurt am Main"):
        read_nebenkosten(path, 2025)
    _kdu_head(path, "Kreis Frankfurt am Main, Stadt", datetime.datetime(2025, 12, 1))
    with pytest.raises(ValueError, match="kdu-06413-0-202506-xlsx.xlsx.*2025"):
        read_nebenkosten(path, 2025)


def test_a_missing_file_stops_and_says_it_does_not_exist(tmp_path):
    with pytest.raises(ValueError, match="kdu-06412-0-202606-xlsx.xlsx: the file does not exist"):
        read_nebenkosten(tmp_path / "kdu-06412-0-202606-xlsx.xlsx", 2026)


def test_a_workbook_without_the_sheet_stops():
    with pytest.raises(ValueError, match="Tabelle 1b HH Miete"):
        read_nebenkosten(config.BA_WAGES_SERIES_XLSX, 2025)


def test_mietspiegel_costs(pages_of):
    costs = read_mietspiegel_costs(pages_of, MIETSPIEGEL_COSTS)
    assert {y: round(v, 2) for y, v in costs.items()} == {2017: 2.36, 2021: 2.61, 2023: 2.66, 2025: 2.91}


def test_a_typed_value_missing_on_its_page_stops(pages_of):
    def broken(name: str) -> list[str]:
        pages = list(pages_of(name))
        if name == "MIETSPIEGEL_2022_REPORT_PDF":
            page = MIETSPIEGEL_COSTS[2021]["page"] - 1
            pages[page] = pages[page].replace("2,61", "2,16")
        return pages
    with pytest.raises(ValueError, match="2021.*2,61"):
        read_mietspiegel_costs(broken, MIETSPIEGEL_COSTS)


def test_a_missing_page_stops(pages_of):
    with pytest.raises(ValueError, match="2017"):
        read_mietspiegel_costs(lambda name: pages_of(name)[:3], MIETSPIEGEL_COSTS)


def test_hessen_quantiles_and_mikrozensus_stand_on_their_pages(hessen_pages, report_pages):
    assert read_hessen_quantiles(hessen_pages) == HESSEN_QUANTILES == {88: 7859, 89: 8074}
    assert read_mikrozensus_2018(report_pages) == MIKROZENSUS_2018 == {"under 900": 60.1, "1,500-2,000": 33.7}


def test_a_quantile_missing_on_its_page_stops(hessen_pages):
    pages = list(hessen_pages)
    pages[35] = pages[35].replace("7 859", "7 860").replace("7\xa0859", "7\xa0860")
    with pytest.raises(ValueError, match="88"):
        read_hessen_quantiles(pages)
    with pytest.raises(ValueError, match="page 36"):
        read_hessen_quantiles(pages[:10])


def test_a_mikrozensus_value_missing_on_its_page_stops(report_pages):
    pages = list(report_pages)
    pages[62] = pages[62].replace("60,1", "61,0")
    with pytest.raises(ValueError, match="Mikrozensus"):
        read_mikrozensus_2018(pages)
    with pytest.raises(ValueError, match="page 63"):
        read_mikrozensus_2018(pages[:10])


def test_bmf_reference_has_nine_wage_tax_rows_and_three_2017_rows():
    wage_tax = read_bmf_reference(config.BMF_WAGE_TAX_CSV)
    assert len(wage_tax) == 9 and set(y for y, _ in wage_tax) == {2021, 2023, 2025}
    assert wage_tax[(2025, "median")] == (5074.10, 817.16, 0.00)
    assert wage_tax[(2021, "high")] == (7100.00, 1759.83, 41.27)
    est = read_est_reference(config.BMF_WAGE_TAX_CSV)
    assert est == {14281: (1062.00, 18.00), 37894: (8024.00, 441.32), 65294: (18948.00, 1042.14)}


def test_a_broken_bmf_file_stops(tmp_path):
    path = tmp_path / "bmf.csv"
    path.write_text("kind,year,person,base,tax,soli,source\nlohnsteuer,2025,median,5074.10,817.16,0.00,x\n"
                    "lohnsteuer,2025,median,5074.10,817.16,0.00,x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="twice"):
        read_bmf_reference(path)
    path.write_text("kind,year,person,base,tax\nlohnsteuer,2025,median,5074.10,817.16\n", encoding="utf-8")
    with pytest.raises(ValueError, match="soli"):
        read_bmf_reference(path)
    path.write_text("kind,year,person,base,tax,soli,source\nlohnsteuer,2025,manager,9000.00,2000.00,0.00,x\n",
                    encoding="utf-8")
    with pytest.raises(ValueError, match="manager"):
        read_bmf_reference(path)


def test_the_bmf_reference_names_the_persons_of_the_catalog():
    """The CSV calls the person at the pension ceiling „ceiling“; the reader gives the name of PERSONS."""
    assert {person for _, person in read_bmf_reference(config.BMF_WAGE_TAX_CSV)} == set(PERSONS)


def test_every_survey_year_has_rules_mindestlohn_and_a_kdu_file():
    years = set(SURVEY_DATES)
    assert set(WAGE_RULES) == set(MINDESTLOHN) == set(config.BA_KDU_XLSX) == years
    assert set(MIETSPIEGEL_COSTS) == years
    assert all(isinstance(r, WageRules) and isinstance(r.tariff, Tariff) for r in WAGE_RULES.values())


def test_the_rules_keep_the_values_of_the_research():
    assert MINDESTLOHN == {2017: 8.84, 2021: 9.60, 2023: 12.00, 2025: 12.82}
    assert WAGE_RULES[2025].tariff.gfb == 12096 and WAGE_RULES[2025].ceiling_rv == 8050
    assert WAGE_RULES[2017].kv_zusatz_employee_alone and not WAGE_RULES[2021].kv_zusatz_employee_alone
