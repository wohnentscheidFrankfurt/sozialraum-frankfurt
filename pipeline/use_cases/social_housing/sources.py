"""Annual report "Kommunale Wohnraumversorgung" of the Amt für Wohnungswesen: table 1.2 per quarter.
Dwelling stock of the city (Statistische Gebäudedatei) per quarter: the base of the share."""
from __future__ import annotations

import re
from pathlib import Path

import openpyxl

HEADING_STOCK = r"1\.2\.\s+Bestand an Wohnungen nach Stadtteil"
_NUMBER = re.compile(r"^(\d{1,3}(\.\d{3})*|-)$")


def read_table(pages: list[str], heading: str, columns: int) -> dict[str, list[int]]:
    """Quarter table: one cell per text line, "-" means 0. Last hit of the heading, because the first one is in the
    table of contents. Stops if values are missing or the rows do not add up to the row "Gesamt"."""
    hits = [p for p in pages if re.search(heading, p)]
    if not hits:
        raise ValueError(f"table not found: {heading}")
    lines = [line.strip() for line in hits[-1].splitlines() if line.strip()]
    if "Altstadt" not in lines:
        raise ValueError(f"table without row Altstadt: {heading}")
    table: dict[str, list[int]] = {}
    name, values = None, []
    for line in lines[lines.index("Altstadt"):]:
        if _NUMBER.match(line):
            values.append(0 if line == "-" else int(line.replace(".", "")))
            if name == "Gesamt" and len(values) == columns:
                break
            continue
        if name is not None:
            table[name] = values
        name, values = line, []
    table[name] = values
    if "Gesamt" not in table:
        raise ValueError(f"row Gesamt missing: {heading}")
    wrong = [n for n, v in table.items() if len(v) != columns]
    if wrong:
        raise ValueError(f"rows with a wrong number of values: {wrong}")
    sums = [sum(v[i] for n, v in table.items() if n != "Gesamt") for i in range(columns)]
    if sums != table["Gesamt"]:
        raise ValueError(f"sum {sums} does not match Gesamt {table['Gesamt']}: {heading}")
    return table


def check_report_year(pages: list[str], year: str) -> None:
    """The catalog and the map name the year of the report. A new annual report stops here instead of appearing
    silently under the old year: the page of table 1.2 (last hit of the heading) says „Jahresbericht <year>“."""
    hits = [p for p in pages if re.search(HEADING_STOCK, p)]
    if not hits or not re.search(rf"Jahresbericht\s+{year}\b", hits[-1]):
        raise ValueError(f"New annual report? The page of table 1.2 does not say „Jahresbericht {year}“. Update the "
                         "as-of date and the source of the annual report in the catalog and in the list of sources of "
                         "the map (README, section New annual report).")


# the city counts Flughafen with Sachsenhausen-Süd, as the map does
STOCK_AIRPORT_ROW = "Sachsenhausen-Süd (inkl. Flughafen)"


def read_dwelling_stock(path: Path, year: int) -> dict[str, int]:
    """"Wohnungen insgesamt" per quarter on 31.12. of the year, dormitories included. One sheet per year, rows
    "01 - Altstadt" … and "Gesamt". Stops without the year or if the rows do not add up to "Gesamt"."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheets = [list(ws.iter_rows(values_only=True)) for ws in wb.worksheets]
    rows = next((r for r in sheets if any(row and row[0] == f"Jahr = {year}" for row in r)), None)
    if rows is None:
        raise ValueError(f"dwelling stock: no sheet for {year}")
    number = lambda v: int(str(v).replace(".", ""))
    stock, total = {}, None
    for row in rows:
        label = str(row[0] or "")
        if re.match(r"^\d{2} - ", label):
            stock[label.split(" - ", 1)[1].strip()] = number(row[1])
        elif label == "Gesamt":
            total = number(row[1])
    if total is None or sum(stock.values()) != total:
        raise ValueError(f"dwelling stock {year}: quarters add up to {sum(stock.values())}, Gesamt {total}")
    return stock
