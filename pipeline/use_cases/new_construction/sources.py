"""Sources of the view „Neubau“: the building statistic of the Hessisches Statistisches Landesamt (Regionaldatenbank
tables 31121-01-02-4, 31121-02-02-4 and 31121-03-02-4, report F II 2, tables 15, 17 and 19), its stock update
(Regionaldatenbank table 31231-02-01-4, reports F I 1, table 4), its population update (Regionaldatenbank table
12411-01-01-4, reports A I 2 of the 2nd half of 2022 and 2025) and answers of the Magistrat on subsidised new
dwellings. For the second block of the view (rents, prices and wages): the Mietspiegel of Frankfurt (the reports and
brochures of 2018, 2022, 2024 and 2026), the Verbraucherpreisindex of Hessen (report M I 2 j/25, table 3), the
Nominallohnindex of Hessen (press table of the HSL) and the Melderegister (persons per household)."""
from __future__ import annotations

import csv
import io
import re
from collections.abc import Callable
from pathlib import Path

import openpyxl

DWELLINGS = "WOHN01$QMU"  # content code: dwellings in new residential buildings, Wohnheime included
ALL_DWELLINGS = "WOHN02$QMU"  # content code: all completed dwellings
STOCK = "WOHNY1$QMU"  # content code: stock of dwellings in residential and non-residential buildings
POPULATION = "BEVSTD$QMU"  # content code: population (Hauptwohnsitz)
TABLE_15 = re.compile(r"15\.\s+Fertiggestellte Wohnungen im Wohn- und Nichtwohnbau in Hessen (\d{4})")
TABLE_17 = re.compile(r"17\.\s+Fertiggestellte Wohngebäude in Hessen (\d{4})")
TABLE_19 = re.compile(r"19\.\s+Fertiggestellte Nichtwohngebäude in Hessen (\d{4})")
FRANKFURT_ROW = 2
# table 4 of report F I 1: the heading starts on the left page and ends on the right page
TABLE_4 = re.compile(r"4\.\s+Bestand an Wohnungen in Wohn- und Nichtwohngebäuden in den")
TABLE_4_END = re.compile(r"hessischen Gemeinden am 31\.12\.(\d{4})")
TABLE_4_ROW = re.compile(r"\n412 000\nFrankfurt am Main, Stadt\n\s*(\d{1,3}(?: \d{3})*)\s*\n")
# title page of report F I 1: the Zensus base of the Fortschreibung („… Gebäude- und Wohnungszählung 2011“)
STOCK_BASE = re.compile(r"Ergebnisse auf Grundlage der Gebäude-\s+und\s+Wohnungszählung (\d{4})")
# title page of report A I 2: the day and the Zensus base of the Fortschreibung. 2022: „Die Bevölkerung der hessischen
# Gemeinden am 31. Dezember 2022“, „Basis Zensus 09. Mai 2011“; 2025: „Bevölkerung in Hessen am 31. Dezember 2025“,
# „auf Basis Zensus 15. Mai 2022“
POPULATION_DAY = re.compile(r"(?:Gemeinden|Hessen)\s+am\s+31\.\s+Dezember\s+(\d{4})")
POPULATION_BASE = re.compile(r"Fortschreibungsergebnisse\s+(?:auf\s+)?Basis\s+Zensus\s+\d{2}\.\s+\w+\s+(\d{4})")
# report A I 2: a row of Frankfurt with the total and two parts (male and female, or German and not German)
_NUMBER = r"\s*(\d{1,3}(?: \d{3})*)\s*\n"
POPULATION_ROW = re.compile(r"\n412(?:000)?\s*\nFrankfurt am Main, Stadt\s*\n" + _NUMBER * 3)
_CELL = re.compile(r"^(\d{1,3}( \d{3})*|—|–|-)$")
B12_TOTAL = 3626  # „insgesamt 3626 Wohnungen fertiggestellt“ (text of B 12/2024)
B12_FW1_TOTAL, B12_FW2_TOTAL = 1984, 1642  # „Zu 5.“ and „Zu 6.“ of B 12/2024: the column sums, they catch a swapped row
REGION = "06412"  # Frankfurt am Main, Stadt (Amtlicher Regionalschlüssel)
FINAL = "e"  # quality flag of a value of the Regionaldatenbank
B483_TOTALS = re.compile(r"Zu Frage 1\) Jahr Baufertigstellungen Wohnungen " + " ".join(
    f"{year} (\\d\\.\\d{{3}})" for year in range(2019, 2025)))  # „Zu Frage 1) … 2019 3.663 2020 4.349 …“
GERMAN_MONTHS = {name: number for number, name in enumerate(
    ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November",
     "Dezember"], 1)}
VPI_SOURCE = "HSL M I 2 j/25, table 3"
VPI_TABLE = "3. Verbraucherpreisindex in Hessen (mehrjährige Übersicht)"  # the heading stands after the rows
VPI_BASE = "2020 = 100"
_VPI_MONTH = re.compile(r"\d+,\d")
_VPI_CHANGE = re.compile(r"(?:[–−-]\s*)?\d+,\d|•")  # „– 0,2“ (en dash, space); „•“ in the first year
VPI_VALUES = 14  # 12 months, the yearly mean and the change against the year before
WAGE_SOURCE = "HSL wage table"
WAGE_SHEET = "nach Jahren und Quartalen"
WAGE_COLUMN = "Nominallohnindex"  # the header; the column below it names the base
WAGE_BASE = "2022 = 100"
HOUSEHOLD_SOURCE = "Melderegister households"
HOUSEHOLD_COLUMNS = ("Stadtbezirk", "Stadtteil", "Jahr", "Nation", "Anzahl Personen in Haushalten", "Anzahl Haushalte")
B12_ROW_DEVIATION = {2023: 1}  # the table prints Gesamt 177 for 90 + 86; FW 1 + FW 2 add up to the total of the text


def _cell(text: str) -> int:
    return 0 if text in ("—", "–", "-") else int(text.replace(" ", ""))


def _regional(text: str, name: str, content: str, column: str, key: str, time: str = "JAHR") -> dict[int, int]:
    """One value per year of a content of the Regionaldatenbank, the rows with `column` = `key`. The year comes from
    the column `time`: JAHR (a year) or STAG (a day, only 31.12.). Stops on a region other than Frankfurt, a value with
    a quality flag other than „e“, a day other than 31.12. or a year with two rows."""
    rows = [r for r in csv.DictReader(io.StringIO(text), delimiter=";") if r["content"] == content and r[column] == key]
    if not rows:
        raise ValueError(f"{name}: no rows of {content}")
    series: dict[int, int] = {}
    for r in rows:
        year = int(r[time][:4])
        if time == "STAG" and r[time] != f"{year}-12-31":
            raise ValueError(f"{name}: day {r[time]}, expected 31.12.")
        if r["region"] != REGION:
            raise ValueError(f"{name}: region {r['region']} in {year}, expected {REGION}")
        if r["quality"] != FINAL:
            raise ValueError(f"{name}: quality flag {r['quality']!r} in {year}, expected {FINAL!r}")
        if year in series:
            raise ValueError(f"{name}: {year} appears twice")
        series[year] = int(float(r["value"]))
    return series


def read_regional_series(text: str) -> dict[int, int]:
    """Dwellings in new residential buildings per year, row „Insgesamt“ (%TOTAL%) of the content WOHN01$QMU."""
    return _regional(text, "Regionaldatenbank 31121-01-02-4", DWELLINGS, "GEBWH1", "%TOTAL%")


def read_regional_all(text: str) -> dict[int, int]:
    """All completed dwellings per year (residential and non-residential buildings, all building measures), row
    „Insgesamt“ (%TOTAL%) of the content WOHN02$QMU."""
    return _regional(text, "Regionaldatenbank 31121-03-02-4", ALL_DWELLINGS, "WHGGR2", "%TOTAL%")


def read_regional_new_nonres(text: str) -> dict[int, int]:
    """Dwellings in new non-residential buildings per year, row „Nichtwohngebäude“ (WOHNNG) of the content
    WOHN01$QMU."""
    return _regional(text, "Regionaldatenbank 31121-02-02-4", DWELLINGS, "BAUF04", "WOHNNG")


def read_regional_stock(text: str) -> dict[int, int]:
    """Stock of dwellings in residential and non-residential buildings on 31.12. per year, row „Insgesamt“ (%TOTAL%)
    of the content WOHNY1$QMU."""
    return _regional(text, "Regionaldatenbank 31231-02-01-4", STOCK, "WHGGR1", "%TOTAL%", "STAG")


def read_regional_population(text: str) -> dict[int, int]:
    """Population with Hauptwohnsitz on 31.12. per year, row „Insgesamt“ (%TOTAL%) of the content BEVSTD$QMU."""
    return _regional(text, "Regionaldatenbank 12411-01-01-4", POPULATION, "GES", "%TOTAL%", "STAG")


def _table_page(pages: list[str], heading: re.Pattern[str], number: int) -> tuple[int, int]:
    """Index of the page that holds the table and its year. The table of contents names the table too; only the table
    page holds the row of Frankfurt."""
    hits = [(i, m) for i, p in enumerate(pages) for m in [heading.search(p)] if m and "Frankfurt am Main, Stadt" in p]
    if not hits:
        raise ValueError(f"HSL report: table {number} with the row „Frankfurt am Main, Stadt“ not found")
    return hits[0][0], int(hits[0][1].group(1))


def _left_value(page: str, number: int) -> int:
    """The first number after the row „2“, „Frankfurt am Main, Stadt“ on the left page of a table."""
    left = re.search(r"\n2\nFrankfurt am Main, Stadt\n\s*(\d{1,3}(?: \d{3})*)\s*\n", "\n" + page)
    if not left:
        raise ValueError(f"HSL report: row 2 „Frankfurt am Main, Stadt“ of table {number} not found")
    return _cell(left.group(1))


def _right_block(page: str, number: int, values: int) -> list[int]:
    """Row 2 of the right page of a table: `values` values per row and then the row number. Checks that row 1 and row 2
    end with their row numbers. Returns the values of row 2."""
    lines = [line.strip() for line in page.splitlines() if line.strip()]
    first = next((k for k, line in enumerate(lines) if _CELL.match(line)), None)
    tokens = lines[first:] if first is not None else []
    width = values + 1
    block = tokens[(FRANKFURT_ROW - 1) * width:FRANKFURT_ROW * width]
    if len(block) != width or block[values] != str(FRANKFURT_ROW) or tokens[values] != "1" \
            or not all(_CELL.match(t) for t in block[:values]):
        raise ValueError(f"HSL report: table {number}, row 2 has not {values} values followed by its row number")
    return [_cell(t) for t in block[:values]]


def read_table_15(pages: list[str]) -> tuple[int, int]:
    """Table 15 of the HSL report F II 2, all completed dwellings in residential and non-residential buildings: the
    first value of row 2 on the table page. Returns (year, dwellings) of Frankfurt."""
    pages = [p.replace("\xa0", " ") for p in pages]
    i, year = _table_page(pages, TABLE_15, 15)
    return year, _left_value(pages[i], 15)


def read_table_17(pages: list[str]) -> tuple[int, int, int]:
    """Table 17 of the HSL report F II 2: the left page holds the buildings per row, the next page six values per row
    and then the row number; the third value is the dwellings. Returns (year, buildings, dwellings) of Frankfurt."""
    pages = [p.replace("\xa0", " ") for p in pages]
    i, year = _table_page(pages, TABLE_17, 17)
    return year, _left_value(pages[i], 17), _right_block(pages[i + 1], 17, 6)[2]


def read_table_19(pages: list[str]) -> tuple[int, int]:
    """Table 19 of the HSL report F II 2, new non-residential buildings: the next page holds five values per row and
    then the row number; the fifth value is the dwellings. Returns (year, dwellings) of Frankfurt."""
    pages = [p.replace("\xa0", " ") for p in pages]
    i, year = _table_page(pages, TABLE_19, 19)
    return year, _right_block(pages[i + 1], 19, 5)[4]


def read_table_4(pages: list[str], base: int) -> tuple[int, int]:
    """Table 4 of the HSL report F I 1, the stock of dwellings in the Gemeinden on 31.12.: the first value of the row
    „412 000“, „Frankfurt am Main, Stadt“ on the left page; the right page ends the heading with the day. Stops unless
    the title names the Gebäude- und Wohnungszählung `base` as the base of the Fortschreibung. Returns (year, dwellings)
    of Frankfurt."""
    pages = [p.replace("\xa0", " ") for p in pages]
    bases = {int(m.group(1)) for p in pages for m in STOCK_BASE.finditer(p)}
    if not bases:
        raise ValueError("HSL report F I 1: no base „Ergebnisse auf Grundlage der Gebäude- und Wohnungszählung“ found")
    if bases != {base}:
        raise ValueError(f"HSL report F I 1: expected the base Gebäude- und Wohnungszählung {base}, the report names "
                         + " and ".join(map(str, sorted(bases))))
    hits = [(i, row, end) for i, p in enumerate(pages[:-1]) if TABLE_4.search(p)
            for row, end in [(TABLE_4_ROW.search("\n" + p), TABLE_4_END.search(pages[i + 1]))] if row and end]
    if not hits:
        raise ValueError("HSL report F I 1: table 4 with the row „412 000 Frankfurt am Main, Stadt“ not found")
    _, row, end = hits[0]
    return int(end.group(1)), _cell(row.group(1))


def read_population_report(pages: list[str], base: int) -> tuple[int, int]:
    """Report A I 2 of the HSL, the population of the Gemeinden on 31. Dezember: the rows „412“ or „412000“,
    „Frankfurt am Main, Stadt“ with the total and two parts. Stops unless the title page names the day („Gemeinden am“
    or „Hessen am 31. Dezember“) and the Zensus of `base` („Basis Zensus 09. Mai 2011“, „auf Basis Zensus 15. Mai
    2022“), if a row does not add up or two rows differ. Returns (year, population) of Frankfurt."""
    pages = [p.replace("\xa0", " ") for p in pages]
    title = pages[0] if pages else ""
    found = POPULATION_BASE.search(title)
    if not found:
        raise ValueError("HSL report A I 2: no base „Fortschreibungsergebnisse Basis Zensus“ on the title page")
    if int(found.group(1)) != base:
        raise ValueError(f"HSL report A I 2: expected „Basis Zensus“ of {base}, the report names {found.group(1)}")
    day = POPULATION_DAY.search(title)
    if not day:
        raise ValueError("HSL report A I 2: no day „am 31. Dezember“ on the title page")
    rows = [[_cell(v) for v in m.groups()] for p in pages for m in POPULATION_ROW.finditer("\n" + p)]
    if not rows:
        raise ValueError("HSL report A I 2: no row „412 Frankfurt am Main, Stadt“ with a total and two parts")
    wrong = [r for r in rows if r[0] != r[1] + r[2]]
    if wrong:
        raise ValueError(f"HSL report A I 2: the parts of Frankfurt do not add up: {wrong}")
    totals = {r[0] for r in rows}
    if len(totals) != 1:
        raise ValueError(f"HSL report A I 2: the totals of Frankfurt differ: {sorted(totals)}")
    return int(day.group(1)), totals.pop()


def read_b12(pages: list[str]) -> dict[int, tuple[int, int | None]]:
    """B 12/2024, answer to question 2: per year 2010–2023 FW 1, FW 2 and Gesamt, one cell per line. 2010 has no FW 2.
    Stops if a row does not add up (except the known deviation of 2023) or the sums of FW 1, FW 2 or both differ from
    the totals of the text."""
    lines = [line.strip() for line in "\n".join(pages).splitlines() if line.strip()]
    if "Gesamt" not in lines:
        raise ValueError("B 12/2024: table of question 2 not found")
    cells = lines[lines.index("Gesamt") + 1:]
    years, rows = list(range(2010, 2024)), {}
    for year in years:
        if str(year) not in cells:
            raise ValueError(f"B 12/2024: year {year} missing")
        start = cells.index(str(year)) + 1
        stop = cells.index(str(year + 1)) if year + 1 in years else start + 3
        values = [int(v) for v in cells[start:stop]]
        fw1, fw2, total = (values[0], None, values[1]) if len(values) == 2 else values
        if fw1 + (fw2 or 0) + B12_ROW_DEVIATION.get(year, 0) != total:
            raise ValueError(f"B 12/2024: {year} FW 1 {fw1} + FW 2 {fw2} is not Gesamt {total}")
        rows[year] = (fw1, fw2)
    if sum(a + (b or 0) for a, b in rows.values()) != B12_TOTAL:
        raise ValueError(f"B 12/2024: the years do not add up to {B12_TOTAL}")
    if sum(a for a, _ in rows.values()) != B12_FW1_TOTAL or sum(b or 0 for _, b in rows.values()) != B12_FW2_TOTAL:
        raise ValueError(f"B 12/2024: FW 1 and FW 2 do not add up to {B12_FW1_TOTAL} and {B12_FW2_TOTAL}")
    return rows


def _only_hit(pages: list[str], pattern: str, source: str, group: int | None = None) -> re.Match[str]:
    """The one hit of a pinned phrase. Spaces and line breaks count as one space. With `group`, only hits that fill
    the group count. Stops on no hit or on more than one."""
    text = re.sub(r"\s+", " ", " ".join(pages))
    hits = [m for m in re.finditer(pattern, text) if group is None or m.group(group)]
    if len(hits) != 1:
        raise ValueError(f"{source}: phrase {pattern!r} not found exactly once ({len(hits)} hits)")
    return hits[0]


def read_answer(pages: list[str], pattern: str, group: int) -> int:
    """One number from a pinned phrase of an answer of the Magistrat. Spaces and line breaks count as one space."""
    return int(_only_hit(pages, pattern, "answer of the Magistrat", group).group(group))


def read_decimal(pages: list[str], pattern: str, group: int, name: str) -> float:
    """One number with a German decimal comma from a pinned phrase of the source `name`. Spaces and line breaks count
    as one space. Stops unless the phrase is found exactly once and the group holds a number like „13,05“."""
    text = _only_hit(pages, pattern, name, group).group(group)
    if not re.fullmatch(r"\d+,\d+", text):
        raise ValueError(f"{name}: {text!r} is not a number with a decimal comma (phrase {pattern!r})")
    return float(text.replace(",", "."))


def read_survey_month(pages: list[str], pattern: str, name: str) -> tuple[int, int]:
    """(year, month) of a survey from a pinned phrase of the source `name` with the named groups `month` (digits or a
    German month name) and `year`. Stops unless the phrase is found exactly once and the month is a month."""
    hit = _only_hit(pages, pattern, name)
    month = hit.group("month")
    number = int(month) if month.isdigit() else GERMAN_MONTHS.get(month)
    if number is None or not 1 <= number <= 12:
        raise ValueError(f"{name}: month {month!r} is not a month (phrase {pattern!r})")
    return int(hit.group("year")), number


def read_rent_surveys(pages_of: Callable[[str], list[str]], sources: list[dict]) -> dict[int, dict]:
    """Per survey year of the Mietspiegel the mean net rent per m² of the new and of the older contracts and the survey
    month: {2017: {"new": 10.21, "old": 8.69, "month": (2017, 6)}, …}. `sources` is RENT_SOURCES; `pages_of(config
    name)` returns the page texts of that file. Stops on a year twice."""
    cache: dict[str, list[str]] = {}

    def pages(config_name: str) -> list[str]:
        if config_name not in cache:
            cache[config_name] = pages_of(config_name)
        return cache[config_name]

    surveys: dict[int, dict] = {}
    for source in sources:
        year, values, date = source["year"], source["values"], source["date"]
        if year in surveys:
            raise ValueError(f"Mietspiegel {year} appears twice")
        label = f"Mietspiegel {year}, {values['config']}"
        surveys[year] = {
            "new": read_decimal(pages(values["config"]), values["pattern"], values["new_group"], label),
            "old": read_decimal(pages(values["config"]), values["pattern"], values["old_group"], label),
            "month": read_survey_month(pages(date["config"]), date["pattern"],
                                       f"Mietspiegel {year}, {date['config']}")}
    return surveys


def read_report_growths(pages_of: Callable[[str], list[str]], growths: list[dict]) -> dict[int, dict]:
    """Per survey year the growth rates (percent) the report prints for the new and the older contracts against the
    survey before: {2021: {"new": 13.2, "old": 5.2}, …}. `growths` is REPORT_GROWTHS."""
    result: dict[int, dict] = {}
    for growth in growths:
        year = growth["year"]
        if year in result:
            raise ValueError(f"Mietspiegel {year}, growth appears twice")
        pages = pages_of(growth["config"])
        label = f"Mietspiegel {year}, growth against {growth['base']}, {growth['config']}"
        result[year] = {"new": read_decimal(pages, growth["pattern"], growth["new_group"], label),
                        "old": read_decimal(pages, growth["pattern"], growth["old_group"], label)}
    return result


def read_price_index(pages: list[str]) -> dict[tuple[int, int], float]:
    """Table 3 of the HSL report M I 2 j/25, the Verbraucherpreisindex of Hessen (2020 = 100) per year and month. Each
    value stands on its own line: a year, 12 months, the yearly mean, the change against the year before („– 0,2“, in
    the first year „•“). The heading stands after the rows. Stops unless one page holds the heading and the base, if a
    year row has not 12 months, a mean and a change, or a year appears twice. Returns {(year, month): index}."""
    pages = [p.replace("\xa0", " ") for p in pages]
    flat = [re.sub(r"\s+", " ", p) for p in pages]
    hits = [p for p, f in zip(pages, flat) if VPI_TABLE in f and VPI_BASE in f]
    if not hits:
        raise ValueError(f"{VPI_SOURCE}: table 3 not found (no page with „{VPI_TABLE}“ and „{VPI_BASE}“)")
    if len(hits) > 1:
        raise ValueError(f"{VPI_SOURCE}: table 3 found on {len(hits)} pages, expected one")
    lines = [line.strip() for line in hits[0].splitlines() if line.strip()]
    index: dict[tuple[int, int], float] = {}
    k = 0
    while k < len(lines):
        if not re.fullmatch(r"\d{4}", lines[k]):
            k += 1
            continue
        year, end = int(lines[k]), k + 1
        while end < len(lines) and _VPI_CHANGE.fullmatch(lines[end]):
            end += 1
        cells = lines[k + 1:end]
        if len(cells) != VPI_VALUES or not all(_VPI_MONTH.fullmatch(c) for c in cells[:13]):
            raise ValueError(f"{VPI_SOURCE}: year {year} has {len(cells)} values, expected 12 months, the mean and the "
                             f"change")
        if (year, 1) in index:
            raise ValueError(f"{VPI_SOURCE}: {year} appears twice")
        index.update({(year, month): float(cells[month - 1].replace(",", ".")) for month in range(1, 13)})
        k = end
    if not index:
        raise ValueError(f"{VPI_SOURCE}: no year rows")
    return index


def read_wage_index(path: Path) -> dict[tuple[int, int], float]:
    """The Nominallohnindex of Hessen (2022 = 100) per (year, quarter) from the sheet „nach Jahren und Quartalen“ of
    the press table of the HSL. The columns are found by their headers „Jahr“, „Quartal“ and „Nominallohnindex“ (the
    cell below names the base). A quarter row carries the year only on its 1st quarter („1. Quartal“, „2. Quartal“,
    …); a yearly row has no quarter. Stops without the sheet, a header or the base, on a quarter without a year, out of
    order or without a number, or a quarter twice."""
    source = f"{WAGE_SOURCE} {path.name}"
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        if WAGE_SHEET not in wb.sheetnames:
            raise ValueError(f"{source}: sheet „{WAGE_SHEET}“ not found")
        rows = list(wb[WAGE_SHEET].iter_rows(values_only=True))
    finally:
        wb.close()
    head = next((n for n, row in enumerate(rows) if any(str(c or "").startswith(WAGE_COLUMN) for c in row)), None)
    if head is None:
        raise ValueError(f"{source}: no column „{WAGE_COLUMN}“")
    columns = {str(c).strip(): i for i, c in enumerate(rows[head]) if c is not None}
    value = next(i for c, i in columns.items() if c.startswith(WAGE_COLUMN))
    if "Jahr" not in columns or "Quartal" not in columns:
        raise ValueError(f"{source}: no columns „Jahr“ and „Quartal“ next to „{WAGE_COLUMN}“")
    if head + 1 >= len(rows) or str(rows[head + 1][value] or "").strip() != WAGE_BASE:
        raise ValueError(f"{source}: column „{WAGE_COLUMN}“ without „{WAGE_BASE}“ below its header")
    index: dict[tuple[int, int], float] = {}
    year, last = None, 0
    for n, row in enumerate(rows[head + 2:], head + 3):
        label, cell = str(row[columns["Quartal"]] or "").strip(), row[columns["Jahr"]]
        quarter = re.fullmatch(r"([1-4])\. Quartal", label)
        if not quarter:
            if cell is not None and not label:  # a yearly row ends the quarters of the year before
                year, last = None, 0
            continue
        number = int(quarter.group(1))
        if cell is not None:
            year, last = int(cell), 0
        if year is None:
            raise ValueError(f"{source}: row {n}, „{label}“ without a year")
        if number != last + 1:
            raise ValueError(f"{source}: row {n}, „{label}“ of {year} follows quarter {last}")
        last = number
        if (year, number) in index:
            raise ValueError(f"{source}: {year} „{label}“ appears twice")
        if not isinstance(row[value], (int, float)) or isinstance(row[value], bool):
            raise ValueError(f"{source}: {year} „{label}“ has no number in „{WAGE_COLUMN}“ ({row[value]!r})")
        index[(year, number)] = float(row[value])
    if not index:
        raise ValueError(f"{source}: no quarters")
    return index


def read_household_size(text: str) -> dict[int, float]:
    """Persons per household of Frankfurt per year from the Melderegister table of the persons in households: the
    persons in households ÷ the households of the row Stadtbezirk, Stadtteil and Nation „insgesamt“ (from the counts,
    not from the rounded column). Stops without the columns or the row, on a year twice or without households."""
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    missing = [c for c in HOUSEHOLD_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"{HOUSEHOLD_SOURCE}: no columns {', '.join(missing)}")
    size: dict[int, float] = {}
    for r in reader:
        if not (r["Stadtbezirk"] == r["Stadtteil"] == r["Nation"] == "insgesamt"):
            continue
        year, persons, households = int(r["Jahr"]), int(r["Anzahl Personen in Haushalten"]), int(r["Anzahl Haushalte"])
        if year in size:
            raise ValueError(f"{HOUSEHOLD_SOURCE}: {year} appears twice in the row insgesamt")
        if households <= 0:
            raise ValueError(f"{HOUSEHOLD_SOURCE}: {year} has {households} households")
        size[year] = persons / households
    if not size:
        raise ValueError(f"{HOUSEHOLD_SOURCE}: no row with Stadtbezirk, Stadtteil and Nation insgesamt")
    return size


def read_b483_totals(pages: list[str]) -> dict[int, int]:
    """B 483/2025, answer to question 1: all completed dwellings per year 2019–2024 as the Magistrat gives them."""
    text = re.sub(r"\s+", " ", " ".join(pages))
    hits = list(B483_TOTALS.finditer(text))
    if len(hits) != 1:
        raise ValueError(f"B 483/2025: table of question 1 not found exactly once ({len(hits)} hits)")
    return {2019 + i: int(v.replace(".", "")) for i, v in enumerate(hits[0].groups())}
