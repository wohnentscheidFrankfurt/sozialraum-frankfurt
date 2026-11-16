import re
import openpyxl
import pytest

from pipeline import config
from pipeline.use_cases.new_construction.catalog import REPORT_GROWTHS, RENT_SOURCES
from pipeline.use_cases.new_construction.sources import (
    read_answer, read_b12, read_b483_totals, read_decimal, read_household_size, read_price_index, read_regional_all,
    read_regional_new_nonres, read_regional_series, read_population_report, read_regional_population,
    read_regional_stock, read_rent_surveys, read_report_growths, read_survey_month, read_table_4, read_table_15,
    read_table_17, read_table_19, read_wage_index)


def test_regional_series_reads_dwellings_per_year():
    s = read_regional_series(config.REGIONAL_COMPLETIONS_CSV.read_text(encoding="utf-8"))
    assert s[2011] == 1905 and s[2015] == 4076 and s[2022] == 2498 and s[2024] == 3463


def test_regional_series_stops_without_the_dwellings():
    text = "table;region;BAUF03;BAUF03_label;content;content_label;GEBWH1;GEBWH1_label;JAHR;JAHR_label;value;quality\n"
    with pytest.raises(ValueError, match="WOHN01"):
        read_regional_series(text)


HEAD = "table;region;BAUF03;BAUF03_label;content;content_label;GEBWH1;GEBWH1_label;JAHR;JAHR_label;value;quality\n"


def row(year, value="2000.0", region="06412", quality="e"):
    return f"31121-01-02-4;{region};BAUGEB01;W;WOHN01$QMU;;%TOTAL%;Insgesamt;{year};{year};{value};{quality}\n"


def test_regional_series_reads_clean_input():
    assert read_regional_series(HEAD + row(2011) + row(2012, "2100.0")) == {2011: 2000, 2012: 2100}


@pytest.mark.parametrize("rows, message", [
    (row(2011) + row(2012, quality="."), "quality"),
    (row(2011) + row(2012, region="06411"), "region"),
    (row(2011) + row(2011, "2100.0"), "twice"),
])
def test_regional_series_stops_on_broken_rows(rows, message):
    with pytest.raises(ValueError, match="31121-01-02-4.*" + message):
        read_regional_series(HEAD + rows)


ALL_HEAD = "table;region;content;content_label;WHGGR2;WHGGR2_label;JAHR;JAHR_label;value;quality\n"
NONRES_HEAD = "table;region;BAUF04;BAUF04_label;content;content_label;JAHR;JAHR_label;value;quality\n"


def all_row(year, value="4000.0", region="06412", quality="e", content="WOHN02$QMU"):
    return f"31121-03-02-4;{region};{content};;%TOTAL%;Insgesamt;{year};{year};{value};{quality}\n"


def nonres_row(year, value="20.0", region="06412", quality="e", content="WOHN01$QMU"):
    return f"31121-02-02-4;{region};WOHNNG;Nichtwohngebäude;{content};;{year};{year};{value};{quality}\n"


def test_regional_all_reads_all_dwellings_per_year():
    s = read_regional_all(config.REGIONAL_ALL_DWELLINGS_CSV.read_text(encoding="utf-8"))
    assert s[2011] == 2138 and s[2017] == 5122 and s[2024] == 4203
    assert sorted(s)[0] == 1995 and sorted(s)[-1] == 2024


def test_regional_new_nonres_reads_dwellings_per_year():
    s = read_regional_new_nonres(config.REGIONAL_NEW_NONRES_CSV.read_text(encoding="utf-8"))
    assert s[2011] == 20 and s[2020] == 330 and s[2024] == 17


def test_regional_readers_read_clean_input():
    assert read_regional_all(ALL_HEAD + all_row(2011) + all_row(2012, "4100.0")) == {2011: 4000, 2012: 4100}
    assert read_regional_new_nonres(NONRES_HEAD + nonres_row(2011) + nonres_row(2012, "5.0")) == {2011: 20, 2012: 5}


@pytest.mark.parametrize("reader, head, make, table", [
    (read_regional_all, ALL_HEAD, all_row, "31121-03-02-4"),
    (read_regional_new_nonres, NONRES_HEAD, nonres_row, "31121-02-02-4"),
])
@pytest.mark.parametrize("bad, message", [
    ({"quality": "."}, "quality"),
    ({"region": "06411"}, "region"),
    ({"content": "BAU015$QMU"}, "no rows"),
])
def test_regional_readers_stop_on_broken_rows(reader, head, make, table, bad, message):
    with pytest.raises(ValueError, match=table + ".*" + message):
        reader(head + make(2011) + make(2012, **bad) if message != "no rows" else head + make(2011, **bad))


@pytest.mark.parametrize("reader, head, make, table", [
    (read_regional_all, ALL_HEAD, all_row, "31121-03-02-4"),
    (read_regional_new_nonres, NONRES_HEAD, nonres_row, "31121-02-02-4"),
])
def test_regional_readers_stop_on_a_duplicate_year(reader, head, make, table):
    with pytest.raises(ValueError, match=table + ".*twice"):
        reader(head + make(2011) + make(2011, "4100.0"))


def test_table_17_of_both_reports(page_texts):
    assert read_table_17(page_texts(config.HSL_COMPLETIONS_2025_PDF)) == (2025, 238, 3463)
    assert read_table_17(page_texts(config.HSL_COMPLETIONS_2024_PDF)) == (2024, 262, 3463)


def test_table_17_stops_on_a_broken_row(page_texts):
    pages = page_texts(config.HSL_COMPLETIONS_2025_PDF)
    name = re.compile(r"Frankfurt\s+am\s+Main,\s+Stadt")  # the 2025 report uses non-breaking spaces
    assert sum(len(name.findall(p)) for p in pages) > 0
    broken = [name.sub("Frankfurt", p) for p in pages]
    with pytest.raises(ValueError, match="table 17"):
        read_table_17(broken)


def test_table_15_of_both_reports(page_texts):
    assert read_table_15(page_texts(config.HSL_COMPLETIONS_2025_PDF)) == (2025, 3772)
    assert read_table_15(page_texts(config.HSL_COMPLETIONS_2024_PDF)) == (2024, 4203)


def test_table_19_of_both_reports(page_texts):
    assert read_table_19(page_texts(config.HSL_COMPLETIONS_2025_PDF)) == (2025, 18)
    assert read_table_19(page_texts(config.HSL_COMPLETIONS_2024_PDF)) == (2024, 17)


@pytest.mark.parametrize("reader, number", [(read_table_15, 15), (read_table_19, 19)])
def test_tables_15_and_19_stop_without_the_row_of_frankfurt(reader, number, page_texts):
    pages = page_texts(config.HSL_COMPLETIONS_2025_PDF)
    name = re.compile(r"Frankfurt\s+am\s+Main,\s+Stadt")  # the 2025 report uses non-breaking spaces
    assert sum(len(name.findall(p)) for p in pages) > 0
    broken = [name.sub("Frankfurt", p) for p in pages]
    with pytest.raises(ValueError, match=f"table {number}"):
        reader(broken)


def test_table_19_stops_when_a_value_of_row_2_is_missing(page_texts):
    pages = page_texts(config.HSL_COMPLETIONS_2025_PDF)
    old = re.compile(r"\n\s*18\s*\n(?=\s*2\s*\n)")  # the dwellings of Frankfurt, right before its row number
    assert sum(len(old.findall(p.replace("\xa0", " "))) for p in pages) == 1
    broken = [old.sub("\n", p.replace("\xa0", " ")) for p in pages]
    with pytest.raises(ValueError, match="table 19"):
        read_table_19(broken)


def test_b12_reads_both_programmes(page_texts):
    b = read_b12(page_texts(config.SUBSIDISED_B12_PDF))
    assert b[2010] == (126, None) and b[2011] == (83, 82) and b[2015] == (431, 67) and b[2023] == (90, 86)
    assert sorted(b) == list(range(2010, 2024))


def test_b12_stops_when_a_row_does_not_add_up(page_texts):
    cell = "\n2015 \n431 \n"  # the FW 1 cell of 2015: the row 2015 reads 431, 67, 498
    pages = page_texts(config.SUBSIDISED_B12_PDF)
    assert sum(p.count(cell) for p in pages) == 1
    with pytest.raises(ValueError, match="B 12/2024"):
        read_b12([p.replace(cell, "\n2015 \n432 \n") for p in pages])


def test_b12_stops_when_fw_1_and_fw_2_are_swapped_in_a_row(page_texts):
    # 2015 reads FW 1 431, FW 2 67, Gesamt 498: swapped, every row sum and the grand total still hold
    pages = page_texts(config.SUBSIDISED_B12_PDF)
    old, new = "\n2015 \n431 \n67 \n", "\n2015 \n67 \n431 \n"
    assert sum(p.count(old) for p in pages) == 1
    with pytest.raises(ValueError, match="FW 1"):
        read_b12([p.replace(old, new) for p in pages])


def test_answer_reads_a_pinned_phrase(page_texts):
    pages = page_texts(config.ANSWER_F_9_2026_PDF)
    assert read_answer(pages, r"Im Förderweg 2 wurden (\d+) Wohneinheiten fertiggestellt", 1) == 346


def test_answer_stops_without_the_phrase():
    with pytest.raises(ValueError, match="not found"):
        read_answer(["kein Text"], r"Förderweg 2: (\d+) WE", 1)


def test_b483_totals_read_the_answer_to_question_1(page_texts):
    assert read_b483_totals(page_texts(config.ANSWER_B_483_2025_PDF)) == {
        2019: 3663, 2020: 4349, 2021: 3914, 2022: 2951, 2023: 3661, 2024: 4203}


def test_b483_totals_stop_without_the_phrase():
    with pytest.raises(ValueError, match="not found"):
        read_b483_totals(["Zu Frage 1) Jahr Baufertigstellungen Wohnungen 2019 3.663"])


def test_regional_stock_reads_the_stock_per_year():
    s = read_regional_stock(config.REGIONAL_STOCK_CSV.read_text(encoding="utf-8"))
    assert (s[2011], s[2015], s[2021], s[2022], s[2024]) == (366541, 380510, 406003, 404227, 411592)
    assert sorted(s) == list(range(2011, 2025))


STOCK_HEAD = ("table;region;content;content_label;WHGGR1;WHGGR1_label;STAG;STAG_label;value;quality;GEBGR1;"
              "GEBGR1_label\n")


def stock_row(year, value="366541.0", region="06412", quality="e", day="12-31"):
    return f"31231-02-01-4;{region};WOHNY1$QMU;;%TOTAL%;Insgesamt;{year}-{day};31.12.{year};{value};{quality};;\n"


def test_regional_stock_reads_clean_input():
    assert read_regional_stock(STOCK_HEAD + stock_row(2011) + stock_row(2012, "368933.0")) == {2011: 366541,
                                                                                               2012: 368933}


@pytest.mark.parametrize("rows, message", [
    (stock_row(2011) + stock_row(2012, quality="."), "quality"),
    (stock_row(2011) + stock_row(2012, region="06411"), "region"),
    (stock_row(2011) + stock_row(2011, "368933.0"), "twice"),
    (stock_row(2011) + stock_row(2012, day="06-30"), "31.12."),
    (stock_row(2011).replace("%TOTAL%", "WHGRME01"), "no rows"),
])
def test_regional_stock_stops_on_broken_rows(rows, message):
    with pytest.raises(ValueError, match="31231-02-01-4.*" + message):
        read_regional_stock(STOCK_HEAD + rows)


def test_table_4_of_the_report_2025(page_texts):
    assert read_table_4(page_texts(config.HSL_STOCK_2025_PDF), 2022) == (2025, 415359)


def test_table_4_of_the_report_2022_on_the_old_base(page_texts):
    # F I 1 j/22 (July 2023), PDF page 12: the last Fortschreibung on the Gebäude- und Wohnungszählung 2011
    assert read_table_4(page_texts(config.HSL_STOCK_2022_OLD_BASE_PDF), 2011) == (2022, 408605)


def test_table_4_stops_on_a_report_of_another_base(page_texts):
    with pytest.raises(ValueError, match="Wohnungszählung 2011.*2022"):
        read_table_4(page_texts(config.HSL_STOCK_2025_PDF), 2011)
    with pytest.raises(ValueError, match="Wohnungszählung 2022.*2011"):
        read_table_4(page_texts(config.HSL_STOCK_2022_OLD_BASE_PDF), 2022)


def test_table_4_stops_without_the_heading_or_the_row(page_texts):
    pages = page_texts(config.HSL_STOCK_2025_PDF)
    with pytest.raises(ValueError, match="table 4"):
        read_table_4([p.replace("4. Bestand an Wohnungen", "4. Wohnungen") for p in pages], 2022)
    with pytest.raises(ValueError, match="table 4"):
        read_table_4([p.replace("hessischen Gemeinden am 31.12.", "hessischen Gemeinden") for p in pages], 2022)
    with pytest.raises(ValueError, match="table 4"):
        read_table_4([re.sub(r"Frankfurt\s+am\s+Main,\s+Stadt", "Frankfurt", p) for p in pages], 2022)


TITLE = "Ergebnisse auf Grundlage der Gebäude- und Wohnungszählung 2022 \n(Stand 15. Mai 2022)\n"


def test_table_4_reads_a_small_fake_text():
    left = ("4. Bestand an Wohnungen in Wohn- und Nichtwohngebäuden in den\n"
            "412 000\nFrankfurt am Main, Stadt\n 415 359  \n")
    right = "hessischen Gemeinden am 31.12.2025 nach Anzahl der Räume\n"
    assert read_table_4([TITLE, left, right], 2022) == (2025, 415359)
    with pytest.raises(ValueError, match="table 4"):
        read_table_4([TITLE, left.replace(" 415 359", " —"), right], 2022)
    with pytest.raises(ValueError, match="no base"):
        read_table_4(["Inhalt", left, right], 2022)
    with pytest.raises(ValueError, match="2011.*2022"):
        read_table_4([TITLE, TITLE.replace("2022 ", "2011 "), left, right], 2022)


def test_regional_population_reads_the_population_per_year():
    p = read_regional_population(config.REGIONAL_POPULATION_CSV.read_text(encoding="utf-8"))
    assert sorted(p) == list(range(1995, 2026))
    # checked against the Regionaldatenbank by hand on 25.10.2026
    assert {y: p[y] for y in (2011, 2015, 2021, 2022, 2025)} == {2011: 676533, 2015: 732688, 2021: 759224,
                                                                  2022: 747389, 2025: 760656}


POPULATION_HEAD = "table;region;content;content_label;GES;GES_label;STAG;STAG_label;value;quality\n"


def population_row(year, value="676533.0", key="%TOTAL%", region="06412", quality="e", day="12-31"):
    return f"12411-01-01-4;{region};BEVSTD$QMU;;{key};Insgesamt;{year}-{day};31.12.{year};{value};{quality}\n"


def test_regional_population_takes_the_total_only():
    rows = population_row(2011) + population_row(2011, "330000.0", "GESM") + population_row(2012, "687775.0")
    assert read_regional_population(POPULATION_HEAD + rows) == {2011: 676533, 2012: 687775}


@pytest.mark.parametrize("rows, message", [
    (population_row(2011) + population_row(2012, quality="."), "quality"),
    (population_row(2011) + population_row(2012, region="06411"), "region"),
    (population_row(2011) + population_row(2011, "687775.0"), "twice"),
    (population_row(2011) + population_row(2012, day="06-30"), "31.12."),
    (population_row(2011, key="GESW"), "no rows"),
])
def test_regional_population_stops_on_broken_rows(rows, message):
    with pytest.raises(ValueError, match="12411-01-01-4.*" + message):
        read_regional_population(POPULATION_HEAD + rows)


def test_population_report_of_2022_on_the_old_base(page_texts):
    # A I 2 mit A II, A III, A V, 2. Halbjahr 2022 (June 2023), PDF pages 33, 36 and 43: the last Fortschreibung on
    # the Zensus 2011
    assert read_population_report(page_texts(config.HSL_POPULATION_2022_OLD_BASE_PDF), 2011) == (2022, 773068)


def test_population_report_of_2025_on_the_new_base(page_texts):
    # A I 2 mit A II, A III, A V, 2. Halbjahr 2025 (July 2026), PDF pages 28 and 35: rows „412000“, German and not
    # German
    assert read_population_report(page_texts(config.HSL_POPULATION_2025_PDF), 2022) == (2025, 760656)


POPULATION_TITLE = ("Die Bevölkerung der hessischen\nGemeinden am 31. Dezember 2022\n"
                    "Fortschreibungsergebnisse Basis Zensus 09. Mai 2011\n")
POPULATION_ROW = "412 \nFrankfurt am Main, Stadt\n 773 068  \n 380 566  \n 392 502  \n 248,3 \n"
POPULATION_ROW_2 = "412000 \nFrankfurt am Main, Stadt\n 773 068  \n 534 096  \n 238 972  \n248,3 \n"


# the title page of 2025 says „Bevölkerung in Hessen am …“ and „auf Basis Zensus“
POPULATION_TITLE_2025 = ("Bevölkerung in Hessen am 31. Dezember 2025\nund Bevölkerungsbewegungen im Jahr 2025\n"
                         "nach Gemeinden\n(endgültige Ergebnisse)\nFortschreibungsergebnisse auf Basis Zensus 15. Mai "
                         "2022\n")
POPULATION_ROW_2025 = "412000 \nFrankfurt am Main, Stadt\n 760 656  \n 535 235  \n 225 421  \n 248,3  \n"


def test_population_report_reads_a_small_fake_text():
    assert read_population_report([POPULATION_TITLE, POPULATION_ROW, POPULATION_ROW_2], 2011) == (2022, 773068)
    assert read_population_report([POPULATION_TITLE_2025, POPULATION_ROW_2025], 2022) == (2025, 760656)


@pytest.mark.parametrize("pages, message", [
    ([POPULATION_TITLE_2025, POPULATION_ROW_2025], "Basis Zensus.*2011"),  # another base asked for, see the test
    ([POPULATION_TITLE_2025.replace("auf Basis Zensus 15. Mai", "auf Basis Zensus"), POPULATION_ROW_2025], "no base"),
    ([POPULATION_TITLE_2025.replace("31. Dezember", "30. Juni"), POPULATION_ROW_2025], "31. Dezember"),
    ([POPULATION_TITLE_2025, POPULATION_ROW_2025.replace("225 421", "225 422")], "add up"),
])
def test_population_report_of_2025_stops_on_drift(pages, message):
    with pytest.raises(ValueError, match="A I 2.*" + message):
        read_population_report(pages, 2011 if message.endswith("2011") else 2022)


@pytest.mark.parametrize("pages, message", [
    ([POPULATION_TITLE, POPULATION_ROW], "Basis Zensus.*2022"),  # another base asked for, see the test
    ([POPULATION_TITLE.replace("Basis Zensus 09. Mai 2011", "Basis Zensus"), POPULATION_ROW], "no base"),
    ([POPULATION_TITLE.replace("31. Dezember", "30. Juni"), POPULATION_ROW], "31. Dezember"),
    ([POPULATION_TITLE, POPULATION_ROW.replace("Frankfurt am Main", "Frankfurt")], "Frankfurt am Main, Stadt"),
    ([POPULATION_TITLE, POPULATION_ROW.replace("392 502", "392 503")], "add up"),
    ([POPULATION_TITLE, POPULATION_ROW, POPULATION_ROW_2.replace("773 068", "773 069").replace("238 972", "238 973")],
     "differ"),
])
def test_population_report_stops_on_drift(pages, message):
    with pytest.raises(ValueError, match="A I 2.*" + message):
        read_population_report(pages, 2022 if message.endswith("2022") else 2011)


def test_population_report_stops_on_a_report_of_the_dwellings(page_texts):
    with pytest.raises(ValueError, match="A I 2"):
        read_population_report(page_texts(config.HSL_STOCK_2022_OLD_BASE_PDF), 2011)


def test_rent_surveys_read_the_reports(page_texts):
    assert read_rent_surveys(lambda n: page_texts(getattr(config, n)), RENT_SOURCES) == {
        2017: {"new": 10.21, "old": 8.69, "month": (2017, 6)},
        2021: {"new": 11.56, "old": 9.14, "month": (2021, 7)},
        2023: {"new": 13.05, "old": 9.43, "month": (2023, 7)},
        2025: {"new": 13.95, "old": 10.11, "month": (2025, 7)}}


def test_report_growths(page_texts):
    assert read_report_growths(lambda n: page_texts(getattr(config, n)), REPORT_GROWTHS) == {2021: {"new": 13.2, "old": 5.2},
                                                           2025: {"new": 6.9, "old": 7.2}}


def test_price_index_months(page_texts):
    index = read_price_index(page_texts(config.HSL_PRICES_PDF))
    assert index[(2017, 6)] == 97.2 and index[(2021, 7)] == 103.1 and index[(2023, 7)] == 116.6
    assert index[(2025, 7)] == 121.5 and index[(2022, 7)] == 109.9
    for year in range(2017, 2026):
        assert [m for y, m in index if y == year] == list(range(1, 13))


def test_wage_index_quarters():
    index = read_wage_index(config.HSL_WAGES_XLSX)
    assert index[(2017, 2)] == 93.6 and index[(2017, 3)] == 84.0
    assert index[(2025, 2)] == 120.1 and index[(2025, 3)] == 110.9


def test_household_size():
    size = read_household_size(config.HOUSEHOLDS_CSV.read_text(encoding="utf-8"))
    assert size[2017] == 768537 / 416615 and size[2025] == 786325 / 426293


PHRASE = r"Mittelwert von (\d+,\d+) €/m²"


def test_decimal_reads_a_german_number_across_line_breaks():
    assert read_decimal(["Der Mittelwert\nvon 13,05  €/m² auf"], r"Mittelwert von (\d+,\d+)\s+€/m²", 1, "x") == 13.05


@pytest.mark.parametrize("pages, count", [
    (["nichts"], 0), (["Mittelwert von 1,00 €/m²", "Mittelwert von 2,00 €/m²"], 2)])
def test_decimal_stops_unless_the_phrase_is_found_once(pages, count):
    with pytest.raises(ValueError, match=rf"Mietspiegel 2021.*Mittelwert von.*\({count} hits\)"):
        read_decimal(pages, PHRASE, 1, "Mietspiegel 2021")


MONTH_PATTERN = r"Stich\w+ war der (?:(?P<day>\d{2})\.)?(?P<month>[A-Za-zä]+|\d{2})\.?\s?(?P<year>\d{4})"


@pytest.mark.parametrize("text, expected", [
    ("Stichmonat war der Juni 2017", (2017, 6)), ("Stichtag war der 01.07.2021", (2021, 7)),
    ("Stichmonat war der März 2018", (2018, 3))])
def test_survey_month_reads_digits_and_german_names(text, expected):
    assert read_survey_month([text], MONTH_PATTERN, "x") == expected


@pytest.mark.parametrize("text, message", [
    ("Stichmonat war der Junius 2017", "month"), ("Stichtag war der 01.13.2021", "month"), ("nichts", "0 hits")])
def test_survey_month_stops_on_drift(text, message):
    with pytest.raises(ValueError, match="Brochure 2022.*" + message):
        read_survey_month([text], MONTH_PATTERN, "Brochure 2022")


def test_rent_surveys_stop_on_a_missing_phrase(page_texts):
    sources = [{**RENT_SOURCES[1], "values": {**RENT_SOURCES[1]["values"], "pattern": "Gibt es nicht (\\d+,\\d+)"}}]
    with pytest.raises(ValueError, match="Mietspiegel 2021.*MIETSPIEGEL_2022_REPORT_PDF.*Gibt es nicht"):
        read_rent_surveys(lambda n: page_texts(getattr(config, n)), sources)


def test_report_growths_stop_on_a_missing_phrase(page_texts):
    growths = [{**REPORT_GROWTHS[0], "pattern": "Gibt es nicht (\\d+,\\d+) (\\d+,\\d+)"}]
    with pytest.raises(ValueError, match="Mietspiegel 2021.*Gibt es nicht"):
        read_report_growths(lambda n: page_texts(getattr(config, n)), growths)


def _vpi_page(rows: list[tuple[int, list[str]]]) -> str:
    head = "Jan.\nFeb.\nMärz\nJahres-\ndurchschnitt\nJährliche \nVeränderung\nin Prozent\n"
    body = "".join(f"{y}\n" + "".join(f"{v}  \n" for v in cells) for y, cells in rows)
    return head + body + "3. Verbraucherpreisindex in Hessen (mehrjährige Übersicht)\nJahr \n2020 = 100\n- 18 -\n"


VPI_YEAR = [f"9{m},{m % 10}" for m in range(1, 10)] + ["100,1", "100,2", "100,3"] + ["97,0", "1,4"]


def test_price_index_reads_a_small_fake_page():
    page = _vpi_page([(1968, VPI_YEAR[:-1] + ["•"]), (2017, VPI_YEAR), (2018, VPI_YEAR[:-1] + ["– 0,2"])])
    index = read_price_index(["Deckblatt", page])
    assert index[(2017, 1)] == 91.1 and index[(2017, 12)] == 100.3 and index[(2018, 6)] == 96.6 and len(index) == 36


@pytest.mark.parametrize("rows", [
    [(2017, VPI_YEAR[:11] + VPI_YEAR[12:])],  # 11 months
    [(2017, VPI_YEAR[:12] + [VPI_YEAR[13]])],  # no mean
    [(2017, VPI_YEAR[:13])],  # no change
    [(2017, VPI_YEAR + ["1,0"])],  # one value too many
    [(2017, VPI_YEAR), (2018, VPI_YEAR[1:])],  # 11 months in the second year
])
def test_price_index_stops_on_a_broken_year_row(rows):
    with pytest.raises(ValueError, match="M I 2.*table 3.*(2017|2018)"):
        read_price_index([_vpi_page(rows)])


def test_price_index_stops_on_a_year_twice():
    with pytest.raises(ValueError, match="M I 2.*table 3.*2017 appears twice"):
        read_price_index([_vpi_page([(2017, VPI_YEAR), (2017, VPI_YEAR)])])


def test_price_index_stops_without_table_3():
    with pytest.raises(ValueError, match="M I 2.*table 3 not found"):
        read_price_index(["Verbraucherpreisindex in Hessen nach Verwendungszwecken"])


def _wage_book(path, header="Nominallohnindex1)", base="2022 = 100", sheet="nach Jahren und Quartalen"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(["Entwicklung des Reallohn-, Nominallohn- und Verbraucherpreisindex"])
    ws.append(["Jahr", "Quartal", "Reallohnindex1)", None, header, None])
    ws.append([None, None, "2022 = 100", "Veränderung", base, "Veränderung"])
    ws.append([2017, None, 102.3, 1.6, 90.4, 3])
    ws.append([2017, "1. Quartal", 99.9, 0.7, 87.5, 2.2])
    ws.append([None, "2. Quartal", 106, 1.8, 93.6, 3.2])
    ws.append([None, "3. Quartal", 94.5, 0.9, 84, 2.3])
    ws.append([2018, "1. Quartal", 100.8, 0.9, 89.3, 2.1])
    ws.append([None, "2. Quartal", 107.9, 1.8, 96.7, 3.3])
    ws.append([None, None, None, None, None, None])
    ws.append(["________"])
    wb.save(path)
    return path


def test_wage_index_reads_a_small_fake_sheet(tmp_path):
    assert read_wage_index(_wage_book(tmp_path / "w.xlsx")) == {
        (2017, 1): 87.5, (2017, 2): 93.6, (2017, 3): 84.0, (2018, 1): 89.3, (2018, 2): 96.7}


@pytest.mark.parametrize("kwargs, message", [
    ({"header": "Bruttoverdienste"}, "Nominallohnindex"), ({"base": "2015 = 100"}, "2022 = 100"),
    ({"sheet": "nach Jahren"}, "nach Jahren und Quartalen")])
def test_wage_index_stops_on_drift(tmp_path, kwargs, message):
    with pytest.raises(ValueError, match="HSL wage table.*" + message):
        read_wage_index(_wage_book(tmp_path / "w.xlsx", **kwargs))


def test_wage_index_stops_on_a_quarter_out_of_order(tmp_path):
    path = _wage_book(tmp_path / "w.xlsx")
    wb = openpyxl.load_workbook(path)
    wb.active["B6"] = "3. Quartal"  # 1st, 3rd, 3rd quarter of 2017
    wb.save(path)
    with pytest.raises(ValueError, match="HSL wage table.*3. Quartal.*follows quarter 1"):
        read_wage_index(path)


def test_wage_index_stops_on_a_value_that_is_no_number(tmp_path):
    path = _wage_book(tmp_path / "w.xlsx")
    wb = openpyxl.load_workbook(path)
    wb.active["E6"] = "x"
    wb.save(path)
    with pytest.raises(ValueError, match="HSL wage table.*2017.*2. Quartal.*no number"):
        read_wage_index(path)


def test_wage_index_stops_on_a_quarter_without_a_year(tmp_path):
    path = _wage_book(tmp_path / "w.xlsx")
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    ws["A5"] = None  # the 1st quarter row lost its year; the yearly row before it carries no year to the quarters
    wb.save(path)
    with pytest.raises(ValueError, match="HSL wage table.*1. Quartal.*without a year"):
        read_wage_index(path)


HOUSEHOLD_HEAD = ("Stadtbezirk;Stadtteil;Jahr;Nation;Anzahl Personen in Haushalten;Anzahl Haushalte;"
                  "Personen pro Haushalt\r\n")
HOUSEHOLD_ROWS = ("010;Altstadt;2017;insgesamt;3713;2385;1,6\r\ninsgesamt;insgesamt;2017;deutsch;500;300;1,7\r\n"
                  "insgesamt;insgesamt;2017;insgesamt;768537;416615;1,8\r\n")


def test_household_size_reads_a_small_fake_file():
    assert read_household_size(HOUSEHOLD_HEAD + HOUSEHOLD_ROWS) == {2017: 768537 / 416615}


@pytest.mark.parametrize("text, message", [
    (HOUSEHOLD_HEAD + HOUSEHOLD_ROWS.replace("2017;insgesamt;7", "2017;ausländisch;7"), "no row"),
    (HOUSEHOLD_HEAD + HOUSEHOLD_ROWS + HOUSEHOLD_ROWS.splitlines()[2] + "\r\n", "twice"),
    (HOUSEHOLD_HEAD + HOUSEHOLD_ROWS.replace("416615", "0"), "households")])
def test_household_size_stops_on_drift(text, message):
    with pytest.raises(ValueError, match="Melderegister.*" + message):
        read_household_size(text)
