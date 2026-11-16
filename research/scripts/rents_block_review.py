"""Review of the block of rents in the view „Neubau“ (research/2026-11-01-rents-block-review.md).

Growth of dwellings and population from several start years in four calculations (published, chained over the old
base of 2022, linear build-up of the Zensus correction, the city's Melderegister), the overcount that would turn the
heading, the drift of the stock after 2022, persons per household of the Melderegister from every base year, and a
rough estimate of the sampling error of the Mietspiegel means 2017 to 2025.

Call from the repo root:
    .venv/bin/python -I research/scripts/rents_block_review.py interim \
        "sources/frankfurt/statistics/Demographische Kennzahlen (Stadtbezirke).xlsx" \
        sources/frankfurt/statistics/bevoelkerung_in_haushalten_stadtbezirke_.csv
"""
from __future__ import annotations

import csv
import re
import sys
from datetime import date
from pathlib import Path

import openpyxl

# 31.12.2022 on the old base (Zensus 2011): HSL reports F I 1 j/22, table 4 (PDF page 12), and A I 2 mit A II, A III,
# A V, 2nd half of 2022 (PDF page 33). The build reads both (pipeline/use_cases/new_construction/README.md, step 8, 9).
OLD_BASE_2022 = {"stock": 408_605, "population": 773_068}
ZENSUS_2011, END_2022 = date(2011, 5, 9), date(2022, 12, 31)
LAST = 2025

# Sampling error of the Mietspiegel means, a rough own estimate. The reports print none. Values as the reports print
# them (README of new_construction, Formula 12 and Limits):
# - relative spread of the net rent per m² of all contracts from the deciles, sd = (P90 − P10) ÷ 2.5631 (normal),
#   divided by the mean of all contracts: Gutachten 2022, table 65 (2021: P10 6.99, P90 14.31, mean 10.29) and
#   Dokumentation 2026, table 64 (2025: P10 7.89, P90 17.53, mean 12.28). The report of 2018 prints no deciles, so
#   2017 takes the relative spread of 2021. Each group gets the relative spread of all contracts.
# - cases of the group: 2017 43.5 % new and 56.5 % older of 3,537 (Gutachten 2018, page 23, weighted), 2025 1,965 new
#   and 1,585 older (Dokumentation 2026, table 62, unweighted).
# - design effect 1.5 (assumed, for the weights).
# - means: 2017 new 10.21, older 8.69; 2025 new 13.95, older 10.11; VPI Hessen June 2017 97.2, July 2025 121.5.
SPREAD = {2017: (14.31 - 6.99) / 2.5631 / 10.29, 2025: (17.53 - 7.89) / 2.5631 / 12.28}
CASES = {"new": {2017: 0.435 * 3537, 2025: 1965}, "old": {2017: 0.565 * 3537, 2025: 1585}}
MEANS = {"new": {2017: 10.21, 2025: 13.95}, "old": {2017: 8.69, 2025: 10.11}}
PRICES = {2017: 97.2, 2025: 121.5}
DESIGN_EFFECT = 1.5
Z95 = 1.96


def read_build(interim: Path) -> dict[str, dict[int, int]]:
    """Stock and population on 31.12. per year, as the build wrote them (new_construction_stock.csv)."""
    out: dict[str, dict[int, int]] = {"stock": {}, "population": {}}
    with open(interim / "new_construction_stock.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for key in out:
                out[key][int(row["year"])] = int(float(row[key]))
    return out


def read_register(xlsx: Path) -> dict[int, int]:
    """Einwohner/-innen of the Melderegister per year: the sum of the Stadtbezirk rows of each sheet."""
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    out = {}
    for ws in wb.worksheets:
        year, total = None, 0
        for row in ws.iter_rows(values_only=True):
            first = row[0]
            if isinstance(first, str) and first.startswith("Jahr ="):
                year = int(first.split("=")[1])
            elif isinstance(first, str) and re.match(r"^\d{3} ", first) and row[1] not in (None, "-", ""):
                total += int(str(row[1]).replace(".", ""))
        if year in out:
            raise SystemExit(f"year {year} twice in {xlsx}")
        out[year] = total
    return out


def read_households(path: Path) -> dict[int, tuple[int, int]]:
    """Persons in households and households of the Melderegister, row insgesamt, per year."""
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if {r["Stadtbezirk"].lower(), r["Stadtteil"].lower(), r["Nation"]} == {"insgesamt"}:
                out[int(r["Jahr"])] = (int(r["Anzahl Personen in Haushalten"]), int(r["Anzahl Haushalte"]))
    return out


def growths(series: dict[int, int], old_2022: int, start: int) -> tuple[float, float, float]:
    """Growth from 31.12. of start to 31.12. of LAST: published, chained over the old base of 2022, and with the
    Zensus correction built up evenly from the Zensus 2011 to 31.12.2022."""
    published = series[LAST] / series[start] - 1
    chained = old_2022 / series[start] * series[LAST] / series[2022] - 1
    share = (date(start, 12, 31) - ZENSUS_2011).days / (END_2022 - ZENSUS_2011).days
    linear = series[LAST] / (series[start] - (old_2022 - series[2022]) * share) - 1
    return published, chained, linear


def main(interim: str, register_xlsx: str, households_csv: str) -> None:
    build = read_build(Path(interim))
    register = read_register(Path(register_xlsx))
    households = read_households(Path(households_csv))
    stock, population = build["stock"], build["population"]

    print("Growth to 31.12.2025 (percent): dwellings published / chained / linear, population published / chained /")
    print("linear, Melderegister; margin = lowest dwellings minus highest population")
    for start in range(2011, 2020):
        d = growths(stock, OLD_BASE_2022["stock"], start)
        p = growths(population, OLD_BASE_2022["population"], start)
        r = register[LAST] / register[start] - 1 if start in register else None
        highest = max(p + ((r,) if r is not None else ()))
        print(f"{start}: dwellings {d[0]:7.2%} {d[1]:7.2%} {d[2]:7.2%} | population {p[0]:7.2%} {p[1]:7.2%} "
              f"{p[2]:7.2%} | register {'   n/a ' if r is None else f'{r:7.2%}'} | margin {min(d) - highest:+7.2%}")

    print("\nOvercount of the old Fortschreibung on 31.12.2017 that makes the population grow as fast as the dwellings")
    for label, growth in (("published", growths(stock, OLD_BASE_2022["stock"], 2017)[0]),
                          ("chained", growths(stock, OLD_BASE_2022["stock"], 2017)[1])):
        print(f"dwellings {label} {growth:.2%}: overcount {population[2017] - population[LAST] / (1 + growth):,.0f} "
              f"(31.12.2022: {OLD_BASE_2022['population'] - population[2022]:,})")

    years = (END_2022 - ZENSUS_2011).days / 365.25
    drift = (OLD_BASE_2022["stock"] - stock[2022]) / years
    print(f"\nStock: mean overcount per year from the Zensus 2011 to 31.12.2022: {drift:,.0f}; three years after 2022: "
          f"{3 * drift:,.0f} = {3 * drift / stock[LAST]:.2%} of 31.12.2025")

    print("\nMelderegister: persons per household, and persons in households against Einwohner/-innen")
    for year in sorted(households):
        persons, count = households[year]
        against = f"{persons / register[year] - 1:+6.2%}" if year in register else "   n/a"
        print(f"{year}: {persons / count:.4f} ({persons:,} / {count:,}); persons in households against Einwohner "
              f"{against}; change to {LAST}: {households[LAST][0] / households[LAST][1] / (persons / count) - 1:+6.2%}")

    print("\nMietspiegel 2017 to 2025, 95 % range of the index (rough own estimate, assumptions in the script)")
    for group, label in (("new", "new contracts"), ("old", "older contracts")):
        relative = [SPREAD[y] * (DESIGN_EFFECT / CASES[group][y]) ** 0.5 for y in (2017, LAST)]
        ratio = Z95 * sum(r * r for r in relative) ** 0.5
        index = 100 * MEANS[group][LAST] / MEANS[group][2017]
        real = index / (PRICES[LAST] / PRICES[2017])
        print(f"{label}: in Euro {index:.1f} ± {index * ratio:.1f}, without inflation {real:.1f} ± {real * ratio:.1f} "
              f"(relative standard error of the means {relative[0]:.2%} and {relative[1]:.2%})")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
