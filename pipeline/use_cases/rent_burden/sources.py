"""Sources of the view „Miete“: the Betriebskosten and Heizkosten of renting households in the Grundsicherung (Kosten
der Unterkunft, Bundesagentur für Arbeit), the median gross wage of full-time employees living in Frankfurt
(Entgeltstatistik of the BA), the Betriebskostenspiegel of the Frankfurter Mietspiegel (sensitivity), the quantiles of
the wage distribution in Hessen (HSL N I 9 j/25), the Mikrozensus values of the Wohnungsmarktbericht 2019/2020, the
legal rules of the net wage (typed constants with their law) and the reference values of the calculators of the
Bundesministerium der Finanzen (BMF)."""
from __future__ import annotations

import csv
import datetime
import re
import zipfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException

from pipeline.use_cases.rent_burden.model import Tariff, WageRules

KDU_SHEET = "Tabelle 1b HH Miete"
ACTUAL_BLOCK = "Laufende tatsächliche"  # the block of the actual costs; „Laufende anerkannte“ holds the recognised ones
RECOGNISED_BLOCK = "Laufende anerkannte"
KDU_REGION = "Kreis Frankfurt am Main, Stadt"  # the line of the region in the head of the sheet
KDU_MONTH = 6  # the head names the month: the text „Juni 2017“ in 2017, the date 1.6. of the year from 2021
MONTHS_DE = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
             "November", "Dezember")
WAGE_2017_SHEET = "16.2"
WAGE_SERIES_SHEET = "9.2"  # median by Wohnort, time series 31.12.2021 to 31.12.2025
REGION = "06412"  # Frankfurt am Main, Stadt (Amtlicher Regionalschlüssel)
FRANKFURT_2017 = "Frankfurt am Main"

# Betriebskostenspiegel of the Mietspiegel, €/m² and month, mean per item, as printed (PDF page, 1-based). Items:
# water, sewage, rain water, waste, street cleaning, Grundsteuer, insurance, common electricity, heating, warm water.
# 2017 prints rain water with sewage (no item of its own). Sums only in the reports of 2018 and 2022: mean of the
# billed cold costs („cold“) and that plus the mean of heating and warm water („cold_heat“). „config“ names the PDF
# in `pipeline/config.py`.
ITEMS = ("water", "sewage", "rain", "waste", "street", "grundsteuer", "insurance", "electricity", "heating",
         "warm_water")
MIETSPIEGEL_COSTS: dict[int, dict] = {
    2017: {"config": "MIETSPIEGEL_2018_REPORT_PDF", "page": 22,
           "items": (0.18, 0.15, 0.00, 0.25, 0.08, 0.22, 0.15, 0.04, 0.74, 0.19), "cold": 1.43, "cold_heat": 2.36},
    2021: {"config": "MIETSPIEGEL_2022_REPORT_PDF", "page": 32,
           "items": (0.21, 0.13, 0.03, 0.25, 0.06, 0.22, 0.17, 0.06, 0.70, 0.32), "cold": 1.59, "cold_heat": 2.61},
    2023: {"config": "MIETSPIEGEL_2024_REPORT_PDF", "page": 29,
           "items": (0.24, 0.15, 0.02, 0.26, 0.06, 0.25, 0.21, 0.06, 0.64, 0.30)},
    2025: {"config": "MIETSPIEGEL_2026_REPORT_PDF", "page": 39,
           "items": (0.21, 0.13, 0.02, 0.26, 0.06, 0.25, 0.30, 0.07, 0.74, 0.36)},
}
COST_BASE_YEAR = 2021  # the last printed sum; 2023 and 2025 move it by the own sum of the items

# table 2.2.4 of HSL N I 9 j/25 (PDF page 36): quantiles of the gross monthly wage of full-time employees in Hessen,
# April 2025. The pension ceiling of 2025 (8,050 €) lies between P88 and P89.
HESSEN_QUANTILES = {88: 7859, 89: 8074}
HESSEN_PAGE = 36
# figure 41 of the Wohnungsmarktbericht 2019/2020 (PDF page 63): Mietbelastung (Bruttokaltmiete ÷
# Haushaltsnettoeinkommen) in Frankfurt by household net income class, Mikrozensus 2018, mean, as printed, in the
# order of the figure (percent). The map uses the two classes of MIKROZENSUS_2018.
MIKROZENSUS_2018_PRINTED = {"under 900": 60.1, "900-1,500": 42.1, "1,500-2,000": 33.7, "2,000-3,200": 26.0,
                            "3,200-4,500": 21.9, "4,500-6,000": 18.8, "6,000-7,500": 15.4, "all": 29.1}
MIKROZENSUS_2018 = {key: MIKROZENSUS_2018_PRINTED[key] for key in ("under 900", "1,500-2,000")}
MIKROZENSUS_PAGE = 63

# Rules of the net wage on the survey day of the Mietspiegel: June 2017, 1.7.2021, 1.7.2023, 1.7.2025. Checked
# against the PAP XML of 2025 (https://www.bmf-steuerrechner.de/javax.faces.resource/daten/xmls/Lohnsteuer2025.xml.xhtml,
# lines 577–612, 1001–1049, 1121–1125, 1367–1391) and, for the older years, against the calculators of the BMF
# (reference/bmf_wage_tax.csv). Laws:
# - tariff: § 32a EStG in the version of the year (2017: Gesetz vom 20.12.2016; 2021: Zweites
#   Familienentlastungsgesetz; 2023: Inflationsausgleichsgesetz; 2025: Steuerfortentwicklungsgesetz);
# - Soli: § 3 and § 4 SolZG 1995 (Freigrenze 972 € and 20 % until 2020; from 2021 the raised Freigrenze and 11.9 %);
# - ceilings: Sozialversicherungs-Rechengrößenverordnung 2017, 2021, 2023, 2025 (pension insurance West until 2024);
# - average Zusatzbeitrag: Bekanntmachung des BMG for the year; paid by the employee alone until 2018, half from 2019;
# - care insurance: § 55 SGB XI (rates from 1.7.2023 by the Pflegeunterstützungs- und -entlastungsgesetz);
# - Werbungskosten-Pauschbetrag, Sonderausgaben-Pauschbetrag (36 €) and Vorsorgepauschale: § 9a, § 10c, § 39b EStG.
WAGE_RULES: dict[int, WageRules] = {
    2017: WageRules(Tariff(8820, 13769, 1007.27, 54057, 223.76, 939.57, 8475.44), 1000, 0.68, 972, 0.20,
                    0.0935, 0.015, 0.011, True, 0.01525, 6350, 4350),
    2021: WageRules(Tariff(9744, 14753, 995.21, 57918, 208.85, 950.96, 9136.63), 1000, 0.84, 16956, 0.119,
                    0.093, 0.012, 0.013, False, 0.01775, 7100, 4837.50),
    2023: WageRules(Tariff(10908, 15999, 979.18, 62809, 192.59, 966.53, 9972.98), 1230, 1.00, 17543, 0.119,
                    0.093, 0.013, 0.016, False, 0.023, 7300, 4987.50),
    2025: WageRules(Tariff(12096, 17443, 932.30, 68480, 176.64, 1015.13, 10911.92), 1230, 1.00, 19950, 0.119,
                    0.093, 0.013, 0.025, False, 0.024, 8050, 5512.50),
}
# €/hour on the survey day: Mindestlohnanpassungsverordnung of 2016 (8.84 € from 1.1.2017), Dritte (9.60 € from
# 1.7.2021), Mindestlohnerhöhungsgesetz (12.00 € from 1.10.2022), Vierte (12.82 € from 1.1.2025).
MINDESTLOHN: dict[int, float] = {2017: 8.84, 2021: 9.60, 2023: 12.00, 2025: 12.82}


@contextmanager
def _workbook(path: Path) -> Iterator[openpyxl.Workbook]:
    """The workbook of an Excel file, read only, values instead of formulas. A file that is no workbook (the BA
    answers with an HTML page for a missing file) stops with the file name, and so does a missing file."""
    if not path.is_file():
        raise ValueError(f"{path.name}: the file does not exist ({path})")
    if not zipfile.is_zipfile(path):
        raise ValueError(f"{path.name}: not an Excel file (xlsx is a zip file)")
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except (zipfile.BadZipFile, KeyError, InvalidFileException) as error:
        raise ValueError(f"{path.name}: cannot be read as an Excel file ({error})") from error
    try:
        yield wb
    finally:
        wb.close()


def _sheet_rows(path: Path, sheet: str) -> list[tuple]:
    with _workbook(path) as wb:
        if sheet not in wb.sheetnames:
            raise ValueError(f"{path.name}: sheet „{sheet}“ not found")
        return list(wb[sheet].iter_rows(values_only=True))


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _kdu_head(path: Path, rows: list[tuple], year: int) -> None:
    """Stops unless the head of the sheet (the rows above „Merkmal“) names KDU_REGION and June of `year`."""
    head = []
    for row in rows:
        cells = [x for x in row if x is not None]
        if cells and isinstance(cells[0], str) and cells[0].strip().startswith("Merkmal"):
            break
        head += cells
    regions = [" ".join(x.split()) for x in head if isinstance(x, str) and x.strip().startswith("Kreis")]
    if regions != [KDU_REGION]:
        raise ValueError(f"{path.name}: region {', '.join(regions) or 'none'}, needs „{KDU_REGION}“")
    months = [(x.year, x.month) for x in head if isinstance(x, datetime.datetime)]
    for x in head:
        found = re.fullmatch(r"(\w+) (\d{4})", x.strip()) if isinstance(x, str) else None
        if found and found[1] in MONTHS_DE:
            months.append((int(found[2]), MONTHS_DE.index(found[1]) + 1))
    if months != [(year, KDU_MONTH)]:
        raise ValueError(f"{path.name}: month {', '.join(f'{m}/{y}' for y, m in months) or 'none'}, needs "
                         f"{KDU_MONTH}/{year}")


def read_nebenkosten(path: Path, year: int) -> dict[str, float]:
    """€/m² and month of the actual running costs of renting households in the Grundsicherung (sheet „Tabelle 1b HH
    Miete“, block „Laufende tatsächliche Kosten der Unterkunft“, row „pro qm“ of the item, column Insgesamt):
    {"betriebskosten": …, "heizkosten": …}. Stops without the sheet, an item or a number, on a file that is no
    workbook, and if the head of the sheet names another region than Frankfurt am Main or another month than June of
    `year`."""
    rows = _sheet_rows(path, KDU_SHEET)
    _kdu_head(path, rows, year)
    block, item, out = None, None, {}
    for row in rows:
        cells = [x for x in row if x is not None]
        if not cells or not isinstance(cells[0], str):
            continue
        label = cells[0].strip()
        if label.startswith(ACTUAL_BLOCK):
            block = "actual"
        elif label.startswith(RECOGNISED_BLOCK):
            block = "recognised"
        elif label.startswith("dav."):
            item = ("grundmiete" if "Unterkunftskosten" in label else "betriebskosten" if "Betriebskosten" in label
                    else "heizkosten" if "Heizkosten" in label else None)
        elif label == "pro qm" and block == "actual" and item in ("betriebskosten", "heizkosten") and item not in out:
            if len(cells) < 2 or not _is_number(cells[1]):
                raise ValueError(f"{path.name}: no number in the row „pro qm“ of {item}")
            out[item] = float(cells[1])
    missing = {"betriebskosten", "heizkosten"} - set(out)
    if missing:
        raise ValueError(f"{path.name}: no row „pro qm“ of {', '.join(sorted(missing))} in the block „{ACTUAL_BLOCK}“")
    return out


def _wage_2017(path: Path, year: int) -> float:
    rows = _sheet_rows(path, WAGE_2017_SHEET)
    if not any(isinstance(r[0], str) and f"Stichtag 31.12.{year}" in r[0] for r in rows if r):
        raise ValueError(f"{path.name}: sheet {WAGE_2017_SHEET} has no „Stichtag 31.12.{year}“")
    head = next((r for r in rows if r and "Insgesamt (Wohnort)" in r), None)
    if head is None:
        raise ValueError(f"{path.name}: sheet {WAGE_2017_SHEET} has no column „Insgesamt (Wohnort)“")
    column = head.index("Insgesamt (Wohnort)")
    hits = [r for r in rows if r and isinstance(r[0], str) and r[0].startswith(FRANKFURT_2017)
            and str(r[1]).strip() == REGION]
    if len(hits) != 1 or not _is_number(hits[0][column]):
        raise ValueError(f"{path.name}: {len(hits)} rows of Frankfurt am Main ({REGION}) in sheet {WAGE_2017_SHEET}, "
                         f"or no number in „Insgesamt (Wohnort)“")
    return float(hits[0][column])


def _wage_series(path: Path, year: int) -> float:
    rows = _sheet_rows(path, WAGE_SERIES_SHEET)
    if not any(isinstance(r[0], str) and "nach dem Wohnort" in r[0] for r in rows if r):
        raise ValueError(f"{path.name}: sheet {WAGE_SERIES_SHEET} is not the table by Wohnort („nach dem Wohnort“)")
    head = next((r for r in rows if r and any(isinstance(x, datetime.datetime) for x in r)), None)
    columns = {x.year: i for i, x in enumerate(head or ()) if isinstance(x, datetime.datetime)
               and (x.month, x.day) == (12, 31)}
    if year not in columns:
        raise ValueError(f"{path.name}: no wage of 31.12.{year} (years {', '.join(map(str, sorted(columns)))})")
    hits = [r for r in rows if r and r[0] == REGION]
    if len(hits) != 1 or not _is_number(hits[0][columns[year]]):
        raise ValueError(f"{path.name}: {len(hits)} rows of {REGION} in sheet {WAGE_SERIES_SHEET}, or no number "
                         f"for 31.12.{year}")
    return float(hits[0][columns[year]])


def read_median_wage(year: int, year_files: dict[int, Path], series: Path) -> float:
    """Median gross monthly wage of full-time employees (Kerngruppe) living in Frankfurt (Wohnort) on 31.12. of
    `year`. A year in `year_files` comes from sheet 16.2 of that file (2017), any other year from sheet 9.2 of
    `series` (31.12.2021 to 31.12.2025). Stops on a year neither holds."""
    if year in year_files:
        return _wage_2017(year_files[year], year)
    return _wage_series(series, year)


def _decimal_on(page: str, value: float) -> bool:
    """The number with a decimal comma (two decimals) stands in the page as a number of its own."""
    return re.search(rf"(?<![\d,]){f'{value:.2f}'.replace('.', ',')}(?!\d)", page) is not None


def read_mietspiegel_costs(pages_of: Callable[[str], list[str]], costs: dict[int, dict]) -> dict[int, float]:
    """Betriebskosten plus heating and warm water per m² and month for every survey year of `costs`
    (MIETSPIEGEL_COSTS): the printed sum, or, where the report prints none (2023, 2025), the sum of 2021 moved by the
    own sum of the ten items (an estimate). `pages_of(config name)` returns the page texts of a PDF. Stops if a
    typed value (item or sum) does not stand on its page."""
    for year, entry in costs.items():
        pages = pages_of(entry["config"])
        if not 1 <= entry["page"] <= len(pages):
            raise ValueError(f"Mietspiegel {year}, {entry['config']}: no page {entry['page']} ({len(pages)} pages)")
        page = pages[entry["page"] - 1].replace("\xa0", " ")
        values = [v for v in entry["items"] if v] + [entry[k] for k in ("cold", "cold_heat") if k in entry]
        missing = [f"{v:.2f}".replace(".", ",") for v in values if not _decimal_on(page, v)]
        if missing:
            raise ValueError(f"Mietspiegel {year}, {entry['config']}, page {entry['page']}: "
                             f"{', '.join(missing)} not found")
    base = costs[COST_BASE_YEAR]
    return {year: entry["cold_heat"] if "cold_heat" in entry
            else base["cold_heat"] * sum(entry["items"]) / sum(base["items"]) for year, entry in costs.items()}


def _page(pages: list[str], number: int, source: str) -> str:
    if len(pages) < number:
        raise ValueError(f"{source}: no page {number} ({len(pages)} pages)")
    return re.sub(r"\s+", " ", pages[number - 1])


def read_hessen_quantiles(pages: list[str]) -> dict[int, int]:
    """The quantiles of HESSEN_QUANTILES, found on PDF page 36 of HSL N I 9 j/25 (table 2.2.4). Stops if a value is
    not on the page."""
    text = _page(pages, HESSEN_PAGE, "HSL N I 9 j/25")
    for quantile, value in HESSEN_QUANTILES.items():
        if re.search(rf"(?<!\d){f'{value:,}'.replace(',', ' ')}(?!\d)", text) is None:
            raise ValueError(f"HSL N I 9 j/25, page {HESSEN_PAGE}: P{quantile} {value} not found")
    return dict(HESSEN_QUANTILES)


def read_mikrozensus_2018(pages: list[str]) -> dict[str, float]:
    """The Mikrozensus values of MIKROZENSUS_2018, found on PDF page 63 of the Wohnungsmarktbericht 2019/2020
    (figure 41): the whole printed row in its order, so a swapped class does not pass. Stops if it is not on the
    page."""
    text = _page(pages, MIKROZENSUS_PAGE, "Wohnungsmarktbericht 2019/2020")
    row = " ".join(f"{v:.1f}%".replace(".", ",") for v in MIKROZENSUS_2018_PRINTED.values())
    if row not in text:
        raise ValueError(f"Wohnungsmarktbericht 2019/2020, page {MIKROZENSUS_PAGE}: Mikrozensus 2018 row „{row}“ "
                         f"not found")
    return dict(MIKROZENSUS_2018)


def _bmf_rows(path: Path, kind: str) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in ("kind", "year", "person", "base", "tax", "soli", "source") if c not in
                   (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path.name}: no columns {', '.join(missing)}")
        return [r for r in reader if r["kind"] == kind]


# the persons of the reference file and their names in PERSONS (catalog): the file names the gross of the high wage
BMF_PERSONS = {"mindestlohn": "mindestlohn", "median": "median", "ceiling": "high"}


def read_bmf_reference(path: Path) -> dict[tuple[int, str], tuple[float, float, float]]:
    """Wage tax and Soli per month of the Lohnsteuerrechner of the BMF: (year, person of PERSONS) -> (gross €/month,
    Lohnsteuer €/month, Soli €/month). Stops without a column, without rows, on a person not in BMF_PERSONS, or on a
    (year, person) twice."""
    out: dict[tuple[int, str], tuple[float, float, float]] = {}
    for r in _bmf_rows(path, "lohnsteuer"):
        if r["person"] not in BMF_PERSONS:
            raise ValueError(f"{path.name}: unknown person „{r['person']}“ (knows {', '.join(BMF_PERSONS)})")
        key = (int(r["year"]), BMF_PERSONS[r["person"]])
        if key in out:
            raise ValueError(f"{path.name}: {key[0]} {key[1]} twice")
        out[key] = (float(r["base"]), float(r["tax"]), float(r["soli"]))
    if not out:
        raise ValueError(f"{path.name}: no rows of the kind lohnsteuer")
    return out


def read_est_reference(path: Path) -> dict[int, tuple[float, float]]:
    """Income tax and Soli per year of the Einkommensteuerrechner of the BMF for 2017: taxable income € per year ->
    (Einkommensteuer €, Soli €). Stops without a column, without rows, or on a taxable income twice."""
    out: dict[int, tuple[float, float]] = {}
    for r in _bmf_rows(path, "est"):
        key = int(r["base"])
        if key in out:
            raise ValueError(f"{path.name}: taxable income {key} twice")
        out[key] = (float(r["tax"]), float(r["soli"]))
    if not out:
        raise ValueError(f"{path.name}: no rows of the kind est")
    return out
