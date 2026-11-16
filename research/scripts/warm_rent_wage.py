"""Warm rent against the net wage of three model persons, 2017 to 2025 (research of warm rent and income, S1).

Inputs per survey year of the Mietspiegel: the net cold rent of new and older contracts (`interim/` of the build),
the Betriebskosten and Heizkosten per m² of renting households in the Grundsicherung (Arbeitsagentur), the
Betriebskostenspiegel of the Mietspiegel (sensitivity) and the median gross wage of full-time employees living in
Frankfurt (Arbeitsagentur, Entgeltstatistik).

Call from the repo root (the build must exist; the result goes to research/results/warm_rent_wage.txt):
    .venv/bin/python -I research/scripts/warm_rent_wage.py
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import openpyxl
import pandas as pd
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from net_wage import CEILING_RV, MINDESTLOHN, full_time, net  # noqa: E402
from pipeline import config as c  # noqa: E402
from pipeline.shared.core.stats import weighted_median  # noqa: E402
from pipeline.use_cases.survey.model import burden_ratios  # noqa: E402
from pipeline.use_cases.survey.sources import read_microdata  # noqa: E402

SURVEY_YEARS = (2017, 2021, 2023, 2025)
BA = c.SOURCES / "arbeitsagentur"
KDU_FILES = {year: BA / f"kdu-06412-0-{year}06-xlsx.xlsx" for year in SURVEY_YEARS}
# 31.12. of a year -> file and sheet with the medians of Frankfurt (Arbeitsort, Wohnort)
WAGE_2016_2017 = {2016: BA / "entgelt-d-0-201612-xlsm.xlsm", 2017: BA / "entgelt-d-0-201712-xlsm.xlsm"}
WAGE_2021_2025 = BA / "entgelt-dwolk-0-202512-xlsx.xlsx"
RENTS_CSV = ROOT / "interim" / "new_construction_rents.csv"

# Betriebskostenspiegel of the Mietspiegel, €/m² and month, mean per item, as printed (PDF page, 1-based). Items:
# water, sewage, rain water, waste, street cleaning, Grundsteuer, insurance, common electricity, heating, warm water.
# 2017 prints rain water with sewage (no item of its own). Sums only in the reports of 2018 and 2022: mean of the
# billed cold costs („cold“) and that plus the mean of heating and warm water („cold_heat“).
ITEMS = ("water", "sewage", "rain", "waste", "street", "grundsteuer", "insurance", "electricity", "heating",
         "warm_water")
MIETSPIEGEL_COSTS = {
    2017: {"pdf": c.MIETSPIEGEL_2018_REPORT_PDF, "page": 22,
           "items": (0.18, 0.15, 0.00, 0.25, 0.08, 0.22, 0.15, 0.04, 0.74, 0.19), "cold": 1.43, "cold_heat": 2.36},
    2021: {"pdf": c.MIETSPIEGEL_2022_REPORT_PDF, "page": 32,
           "items": (0.21, 0.13, 0.03, 0.25, 0.06, 0.22, 0.17, 0.06, 0.70, 0.32), "cold": 1.59, "cold_heat": 2.61},
    2023: {"pdf": c.MIETSPIEGEL_2024_REPORT_PDF, "page": 29,
           "items": (0.24, 0.15, 0.02, 0.26, 0.06, 0.25, 0.21, 0.06, 0.64, 0.30)},
    2025: {"pdf": c.MIETSPIEGEL_2026_REPORT_PDF, "page": 39,
           "items": (0.21, 0.13, 0.02, 0.26, 0.06, 0.25, 0.30, 0.07, 0.74, 0.36)},
}

# Values of the data check of 1.11.2026 (BA tables read by hand); the readers must reproduce them.
EXPECTED_COSTS = {2017: (2.33, 0.86), 2021: (2.45, 0.86), 2023: (2.63, 1.41), 2025: (2.72, 1.39)}
EXPECTED_WAGE = {2017: 3861, 2025: 5074}


def de(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def check_mietspiegel_costs() -> None:
    """Every typed value of MIETSPIEGEL_COSTS stands on its PDF page."""
    for year, entry in MIETSPIEGEL_COSTS.items():
        text = pymupdf.open(entry["pdf"])[entry["page"] - 1].get_text()
        values = [v for v in entry["items"] if v] + [entry[k] for k in ("cold", "cold_heat") if k in entry]
        missing = [v for v in values if de(v) not in text]
        assert not missing, (year, missing)


def read_nebenkosten(path: Path) -> dict[str, float]:
    """€/m² of the actual running costs, renting households (table 1b), column Insgesamt."""
    sheet = openpyxl.load_workbook(path, read_only=True, data_only=True)["Tabelle 1b HH Miete"]
    out, block, item = {}, None, None
    for row in sheet.iter_rows(values_only=True):
        cells = [x for x in row if x is not None]
        if not cells or not isinstance(cells[0], str):
            continue
        label = cells[0].strip()
        if label.startswith("Laufende tatsächliche"):
            block = "actual"
        elif label.startswith("Laufende anerkannte"):
            block = "recognised"
        elif label.startswith("dav."):
            item = ("grundmiete" if "Unterkunftskosten" in label else
                    "betriebskosten" if "Betriebskosten" in label else "heizkosten")
        elif label == "pro qm" and block == "actual" and item and item not in out:
            out[item] = float(cells[1])
    assert set(out) == {"grundmiete", "betriebskosten", "heizkosten"}, (path.name, out)
    return out


def read_median_wage(year: int, place: str = "Wohnort") -> float:
    """Median gross monthly wage of full-time employees (Kerngruppe), Frankfurt, 31.12. of `year`."""
    if year in WAGE_2016_2017:
        sheet = openpyxl.load_workbook(WAGE_2016_2017[year], read_only=True, data_only=True)["16.2"]
        for row in sheet.iter_rows(values_only=True):
            if row and isinstance(row[0], str) and row[0].startswith("Frankfurt am Main"):
                cells = [x for x in row if x is not None]
                # name, key, Arbeitsort, 9 breakdowns, Wohnort
                return float(cells[2] if place == "Arbeitsort" else cells[-1])
        raise ValueError(f"Frankfurt not in 16.2 of {year}")
    sheet = openpyxl.load_workbook(WAGE_2021_2025, read_only=True, data_only=True)[
        "9.2" if place == "Wohnort" else "8.2"]
    for row in sheet.iter_rows(values_only=True):
        if row and row[0] == "06412" and (place == "Wohnort" or row[2] == "Insgesamt"):
            values = [x for x in row if isinstance(x, (int, float))]
            return float(values[year - 2021])
    raise ValueError(f"Frankfurt not in the time series ({year}, {place})")


def wage(year: int, basis: str = "year_end", place: str = "Wohnort") -> float | None:
    """The wage of a survey year: 31.12. of the year (main), or the mean with 31.12. of the year before
    ("mid_year", only where both exist: 2017, 2023, 2025)."""
    if basis == "year_end":
        return read_median_wage(year, place)
    if year == 2021:
        return None  # 31.12.2020 by Wohnort is not published
    return (read_median_wage(year - 1, place) + read_median_wage(year, place)) / 2


def read_rents() -> dict[int, dict[str, float]]:
    """Mietspiegel means, net cold rent €/m², new and older contracts, and the price and wage indices of the year
    (2017 = 100, VPI Hessen of the survey month, Nominallohnindex Hessen), as the build computed them."""
    with RENTS_CSV.open(encoding="utf-8") as f:
        return {int(r["year"]): {"new": float(r["new"]), "old": float(r["old"]), "prices": float(r["prices_index"]),
                                 "wages_hessen": float(r["wages_index"])}
                for r in csv.DictReader(f) if r["new"]}


RENTS = read_rents()
NEBENKOSTEN = {year: read_nebenkosten(KDU_FILES[year]) for year in SURVEY_YEARS}
FLAT_M2 = 55  # median class 50–60 m² of one-person tenant households, Leben in Frankfurt 2024+2025
PERSONS = ("mindestlohn", "median", "ceiling")
CONTRACTS = ("new", "old")


def mietspiegel_nebenkosten(year: int) -> float:
    """Betriebskosten plus heating and warm water, €/m², from the Mietspiegel: the printed sum (2017, 2021); for 2023
    and 2025 the sum of 2021 moved by the own sum of the ten items (an estimate)."""
    entry = MIETSPIEGEL_COSTS[year]
    if "cold_heat" in entry:
        return entry["cold_heat"]
    base = MIETSPIEGEL_COSTS[2021]
    return base["cold_heat"] * sum(entry["items"]) / sum(base["items"])


def nebenkosten(year: int, source: str = "ba") -> float:
    if source == "ba":
        return NEBENKOSTEN[year]["betriebskosten"] + NEBENKOSTEN[year]["heizkosten"]
    return mietspiegel_nebenkosten(year)


def gross_wage(person: str, year: int, basis: str = "year_end", place: str = "Wohnort") -> float | None:
    if person == "mindestlohn":
        return full_time(MINDESTLOHN[year])
    if person == "ceiling":
        return CEILING_RV[year]
    return wage(year, basis, place)


def share(person: str, contract: str, year: int, nebenkosten_source: str = "ba", m2: float = FLAT_M2,
          basis: str = "year_end", place: str = "Wohnort") -> dict | None:
    """Warm rent of the flat against the net wage of one person; what is left, also without inflation (€ of 2017)."""
    gross = gross_wage(person, year, basis, place)
    if gross is None:
        return None
    warm = (RENTS[year][contract] + nebenkosten(year, nebenkosten_source)) * m2
    pay = net(gross, year)
    left = pay - warm
    return {"warm_rent": warm, "gross": gross, "net": pay, "share": 100 * warm / pay, "left": left,
            "left_real": left * 100 / RENTS[year]["prices"]}


def share_table(title: str, **kwargs) -> list[str]:
    lines = [title, "person       contract " + " ".join(f"{y:>7}" for y in SURVEY_YEARS) + "   change"]
    for person in PERSONS:
        for contract in CONTRACTS:
            cells = [share(person, contract, y, **kwargs) for y in SURVEY_YEARS]
            values = [None if x is None else x["share"] for x in cells]
            change = values[-1] - values[0] if values[0] is not None else float("nan")
            lines.append(f"{person:12s} {contract:8s} " + " ".join("      -" if v is None else f"{v:6.1f}%"
                                                                 for v in values) + f"  {change:+6.1f}")
    return lines


def survey_new_singles() -> dict[str, float]:
    """Leben in Frankfurt 2024+2025: one-person tenant households in the flat for less than 5 years."""
    frames = []
    for year, path in c.SURVEY_MICRODATA.items():
        respondents = read_microdata(path, year)
        respondents["stay"] = pd.read_csv(path, sep=";", encoding="utf-8-sig", usecols=["FFdauliw_a"])["FFdauliw_a"]
        frames.append(respondents)
    ratios = burden_ratios(pd.concat(frames, ignore_index=True))
    group = ratios[(ratios["persons"] == 1) & (ratios["stay"] == 1)]
    return {"cases": len(group), "burden": weighted_median(group["ratio"], group["weight"]),
            "warm_rent": weighted_median(group["warm_rent"], group["weight"]),
            "all_burden": weighted_median(ratios["ratio"], ratios["weight"])}


HESSEN_DISTRIBUTION_PDF = c.SOURCES / "hessen" / "statistics" / "ni9_j25_2aa.pdf"
# table 2.2.4 (PDF page 36): quantiles of the gross monthly wage of full-time employees in Hessen, April 2025
HESSEN_QUANTILES_2025 = {50: 4471, 75: 6129, 80: 6646, 88: 7859, 89: 8074, 90: 8318}


def ceiling_position() -> list[str]:
    text = re.sub(r"\s+", " ", pymupdf.open(HESSEN_DISTRIBUTION_PDF)[35].get_text())
    for q, value in HESSEN_QUANTILES_2025.items():
        assert f"{value:,}".replace(",", " ") in text, (q, value)
    sheet = openpyxl.load_workbook(WAGE_2021_2025, read_only=True, data_only=True)["9.1"]
    row = next(r for r in sheet.iter_rows(values_only=True) if r and r[0] == "06412")
    counts = [x for x in row if isinstance(x, (int, float))]
    total, above_6000 = counts[0], counts[6]
    return [f"Frankfurt residents, full time, 31.12.2025: {above_6000:,} of {total:,} earn more than 6,000 € gross "
            f"({100 * above_6000 / total:.1f} %); the ceiling of {CEILING_RV[2025]:,.0f} € lies in this open class.",
            "Hessen, full time, April 2025 (N I 9 j/25, table 2.2.4): "
            + ", ".join(f"P{q} {v:,} €" for q, v in HESSEN_QUANTILES_2025.items())
            + f". The ceiling lies between P88 and P89 in Hessen."]


def bridge() -> list[str]:
    """2017 to 2025 in percent: why the share stays flat while the block of rents in Neubau shows rents outgrowing
    wages."""
    def g(a: float, b: float) -> str:
        return f"{100 * (b / a - 1):+.1f} %"
    warm = [(RENTS[y]["new"] + nebenkosten(y)) * FLAT_M2 for y in (2017, 2025)]
    return ["Growth 2017 to 2025:",
            f"  net cold rent, new contracts (Neubau block)      {g(RENTS[2017]['new'], RENTS[2025]['new'])}",
            f"  Betriebskosten + Heizkosten (BA)                 {g(nebenkosten(2017), nebenkosten(2025))}",
            f"  warm rent, new contract, 55 m²                   {g(*warm)}",
            f"  Nominallohnindex Hessen, gross (Neubau block)    {g(100, RENTS[2025]['wages_hessen'])}",
            f"  median gross wage, Frankfurt residents          {g(wage(2017), wage(2025))}",
            f"  median net wage, Frankfurt residents            {g(net(wage(2017), 2017), net(wage(2025), 2025))}",
            f"  prices (VPI Hessen, survey month)                {g(100, RENTS[2025]['prices'])}"]


def main() -> None:
    check_mietspiegel_costs()
    for year, (bk, heat) in EXPECTED_COSTS.items():
        got = NEBENKOSTEN[year]
        assert (round(got["betriebskosten"], 2), round(got["heizkosten"], 2)) == (bk, heat), (year, got)
    for year, value in EXPECTED_WAGE.items():
        assert round(wage(year)) == value, (year, wage(year))
    print("Inputs per survey year (€/m² and month; wage € gross per month, 31.12.)")
    print("year  rent_new rent_old  BA:grund  BA:betrieb BA:heiz  wage_wohnort wage_arbeitsort wage_mid_year")
    for year in SURVEY_YEARS:
        nk, mid = NEBENKOSTEN[year], wage(year, "mid_year")
        print(f"{year}  {RENTS[year]['new']:8.2f} {RENTS[year]['old']:8.2f}  {nk['grundmiete']:8.2f}  "
              f"{nk['betriebskosten']:10.2f} {nk['heizkosten']:7.2f}  {wage(year):12.0f} "
              f"{wage(year, place='Arbeitsort'):15.0f} {'-' if mid is None else f'{mid:.0f}':>13}")
    print("Mietspiegel Nebenkosten €/m² (2023, 2025 estimated):",
          ", ".join(f"{y} {mietspiegel_nebenkosten(y):.2f}" for y in SURVEY_YEARS))
    print()
    print(f"Warm rent of {FLAT_M2} m² in € and net wage in € (main case: BA Nebenkosten, wage 31.12. of the year)")
    for person in PERSONS:
        for contract in CONTRACTS:
            cells = [share(person, contract, y) for y in SURVEY_YEARS]
            print(f"  {person:12s} {contract:4s} " + "  ".join(
                f"{y}: {x['warm_rent']:5.0f} of {x['net']:5.0f}, left {x['left']:5.0f} (real {x['left_real']:5.0f})"
                for y, x in zip(SURVEY_YEARS, cells)))
    print()
    for line in share_table("Share of the net wage, main case"):
        print(line)
    for title, kwargs in [("Mietspiegel Nebenkosten", {"nebenkosten_source": "mietspiegel"}),
                          ("median at Arbeitsort", {"place": "Arbeitsort"}),
                          ("median at mid-year (2021: none)", {"basis": "mid_year"}),
                          ("flat 50 m²", {"m2": 50}), ("flat 60 m²", {"m2": 60})]:
        print()
        for line in share_table(f"Sensitivity: {title}", **kwargs):
            print(line)
    print()
    survey = survey_new_singles()
    print(f"Measured: published median burden of all tenants 29 % (reports 2024, 2025); own count "
          f"{survey['all_burden']:.1f} %. One-person tenant households, moved in less than 5 years ago "
          f"({survey['cases']} cases, 2024+2025): median burden {survey['burden']:.1f} %, median warm rent "
          f"{survey['warm_rent']:.0f} €. IWU (cross-check, Mikrozensus 2022 projected to 2024): Frankfurt 34 %, "
          f"moved in 2020 or later 37 %.")
    print()
    print(*bridge(), sep="\n")
    print()
    print(*ceiling_position(), sep="\n")


if __name__ == "__main__":
    main()
