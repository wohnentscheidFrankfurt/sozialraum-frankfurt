"""Warm rent against household income of tenants under 2,000 € net (research of warm rent and income, S2).

Leben in Frankfurt 2024 and 2025 (microdata), the formula of the use case `survey`: warm rent = class midpoint of
the rent + class midpoint of the heating and other costs; household income = equivalised class midpoint × scale.
Per income group: the share of adult tenants (the weights count adults), the median burden and the shares in the
classes under 30, 30 to under 40, 40 to under 50, 50 % and more, each with a 90 % bootstrap interval. Then the
sensitivities, the Mikrozensus values the city published (Wohnungsmarktbericht 2019/2020) and the order of
magnitude of renting households in the Grundsicherung.

Call from the repo root (the result goes to research/results/low_income_burden.txt):
    .venv/bin/python -I research/scripts/low_income_burden.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipeline import config as c  # noqa: E402
from pipeline.shared.core.stats import weighted_median  # noqa: E402
from pipeline.use_cases.survey import model  # noqa: E402
from pipeline.use_cases.survey.sources import read_microdata  # noqa: E402

GROUPS = {"LIF_RENT_BURDEN_INCOME_LOW": "under 2,000", "LIF_RENT_BURDEN_INCOME_MID": "2,000 to 3,200",
          "LIF_RENT_BURDEN_INCOME_HIGH": "3,200 and more"}
CLASSES = ((0, 30, "under 30"), (30, 40, "30-40"), (40, 50, "40-50"), (50, np.inf, "50 and more"))
DRAWS, SEED = 400, 1

REPORT_PDF = c.CITY / "offices" / "Wohnungsmarktbericht 2019_2020.pdf"
# Mikrozensus, Mietbelastung = Bruttokaltmiete ÷ Haushaltsnettoeinkommen, Frankfurt (SK), mean, as printed
MZ_2018 = {"under 900": 60.1, "900-1,500": 42.1, "1,500-2,000": 33.7, "2,000-3,200": 26.0, "3,200-4,500": 21.9,
           "4,500-6,000": 18.8, "6,000-7,500": 15.4, "all": 29.1}  # figure 41, PDF page 63
MZ_CLASSES_2006_2014 = ("500-700", "700-900", "900-1,100", "1,100-1,300", "1,300-1,500", "1,500-2,000",
                        "2,000-3,200", "3,200-4,500", "4,500-6,000", "6,000-7,500", "7,500 and more", "all")
MZ_2006_2014 = {  # figure 40, PDF page 62; 0.0 = no value printed as 0,0 %
    2006: (46.9, 45.6, 40.0, 35.3, 31.7, 27.9, 21.8, 19.0, 15.9, 14.4, 11.8, 23.6),
    2010: (50.9, 45.2, 41.8, 37.4, 33.4, 28.8, 23.3, 19.0, 17.3, 0.0, 0.0, 23.3),
    2014: (49.0, 48.5, 45.5, 40.5, 35.9, 31.0, 23.1, 17.9, 13.8, 12.5, 8.6, 28.6)}
KDU_2025 = c.SOURCES / "arbeitsagentur" / "kdu-06412-0-202506-xlsx.xlsx"
ZENSUS_USE = c.SOURCES / "zensus" / "Zensus2022_4000W-2002_Frankfurt_2011_2022.csv"

# The scratch check of 1.11.2026, pooled; the own count must reproduce it.
EXPECTED_POOLED = {"under 2,000": (16.7, 53.3, 79.4, 57.3), "all": 29.4}


def respondents() -> pd.DataFrame:
    frames = []
    for year, path in c.SURVEY_MICRODATA.items():
        frame = read_microdata(path, year)
        extra = pd.read_csv(path, sep=";", encoding="utf-8-sig", usecols=["XDberuf_a"])
        frame["working"] = extra["XDberuf_a"].map({1: "berufstätig", 2: "nicht berufstätig"})
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def group_values(ratios: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Per income group: share of adult tenants, median burden, shares per burden class (all weighted, percent)."""
    out = {}
    total = ratios["weight"].sum()
    for gid, name in GROUPS.items():
        g = ratios[ratios["group"] == gid]
        w = g["weight"]
        row = {"share": 100 * w.sum() / total, "median": weighted_median(g["ratio"], w),
               "over 40": 100 * w[g["ratio"] > 40].sum() / w.sum(), "over 50": 100 * w[g["ratio"] > 50].sum() / w.sum()}
        for low, high, label in CLASSES:
            row[label] = 100 * w[(g["ratio"] >= low) & (g["ratio"] < high)].sum() / w.sum()
        out[name] = row
    return out


def bootstrap(ratios: pd.DataFrame) -> dict[str, dict[str, tuple[float, float]]]:
    """90 % interval of every value of group_values, resampling respondents."""
    rng = np.random.default_rng(SEED)
    draws = []
    for _ in range(DRAWS):
        sample = ratios.iloc[rng.integers(0, len(ratios), len(ratios))]
        draws.append(group_values(sample))
    return {name: {key: tuple(np.percentile([d[name][key] for d in draws], [5, 95])) for key in draws[0][name]}
            for name in GROUPS.values()}


def certainty(ratios: pd.DataFrame) -> tuple[float, float]:
    """Share of adult tenants surely under 2,000 € and in doubt, from the class bounds × scale."""
    adults = (ratios["persons"] - ratios["children"]).clip(lower=1)
    scale = 1 + 0.5 * (adults - 1) + 0.3 * ratios["children"]
    low, high = ratios["income_low"].fillna(0) * scale, ratios["income_high"] * scale
    w = ratios["weight"]
    sure, sure_not = high.le(2000), low.ge(2000)
    return 100 * w[sure].sum() / w.sum(), 100 * w[~sure & ~sure_not].sum() / w.sum()


def check_mikrozensus() -> None:
    text = re.sub(r"\s+", " ", pymupdf.open(REPORT_PDF)[62].get_text())
    assert " ".join(f"{v:.1f}%".replace(".", ",") for v in MZ_2018.values()) in text
    text = re.sub(r"\s+", " ", pymupdf.open(REPORT_PDF)[61].get_text())
    for year, values in MZ_2006_2014.items():
        assert " ".join(f"{v:.1f}%".replace(".", ",") for v in values) in text, year


def sgb2_tenant_households() -> int:
    sheet = openpyxl.load_workbook(KDU_2025, read_only=True, data_only=True)["Tabelle 1b HH Miete"]
    for row in sheet.iter_rows(values_only=True):
        cells = [x for x in row if x is not None]
        if cells and str(cells[0]).strip() == "Bestand BG mit laufenden anerkannten Kosten der Unterkunft":
            return int(cells[1])
    raise ValueError("row not found")


def rented_dwellings() -> int:
    use = pd.read_csv(ZENSUS_USE, sep=";")
    row = use[(use["WHGNZ2"] == "NUTZ-MIETE") & (use["GEBEG1"] == "%TOTAL%") & (use["STAG"] == "2022-05-15")
              & (use["content"] == "WHG002$ID0004")]  # count; WHG002$PO0004 is the percentage
    assert len(row) == 1, row
    return int(row["value"].iloc[0])


def table(values: dict, intervals: dict | None = None) -> list[str]:
    keys = ("share", "median", "over 40", "over 50", *(label for *_, label in CLASSES))
    lines = ["group           " + "".join(f"{k:>18}" for k in keys)]
    for name, row in values.items():
        cells = []
        for k in keys:
            lo_hi = f" ({intervals[name][k][0]:.0f}-{intervals[name][k][1]:.0f})" if intervals else ""
            cells.append(f"{row[k]:.1f}{lo_hi}".rjust(18))
        lines.append(f"{name:16s}" + "".join(cells))
    return lines


def main() -> None:
    check_mikrozensus()
    people = respondents()
    ratios = model.burden_ratios(people)
    pooled = group_values(ratios)
    low = pooled["under 2,000"]
    got = (round(low["share"], 1), round(low["median"], 1), round(low["over 40"], 1), round(low["over 50"], 1))
    assert got == EXPECTED_POOLED["under 2,000"], got
    assert round(weighted_median(ratios["ratio"], ratios["weight"]), 1) == EXPECTED_POOLED["all"]

    print("Burden = warm rent ÷ household net income, adult tenants (weights), percent; 90 % bootstrap intervals")
    for year in (2024, 2025):
        sub = ratios[ratios["year"] == year]
        print(f"\n{year} ({len(sub)} cases), median of all tenants {weighted_median(sub['ratio'], sub['weight']):.1f}")
        print(*table(group_values(sub)), sep="\n")
    print(f"\n2024+2025 pooled ({len(ratios)} cases), median of all tenants "
          f"{weighted_median(ratios['ratio'], ratios['weight']):.1f}")
    print(*table(pooled, bootstrap(ratios)), sep="\n")
    for name in GROUPS.values():
        g = ratios[ratios["group"] == [k for k, v in GROUPS.items() if v == name][0]]
        print(f"  {name}: {len(g)} cases, median warm rent {weighted_median(g['warm_rent'], g['weight']):.0f} €, "
              f"median household income {weighted_median(g['household_income'], g['weight']):.0f} €")
    sure, doubt = certainty(ratios)
    print(f"\nUnder 2,000 € by the class bounds: surely {sure:.1f} % of adult tenants, in doubt {doubt:.1f} %, "
          f"so {sure:.1f} to {sure + doubt:.1f} %.")

    print("\nSensitivity: open lowest class of the equivalised income (under 1,000 €)")
    for value in (600, 750, 800):
        saved = model.OPEN_LOW["income"]
        model.OPEN_LOW["income"] = value
        try:
            v = group_values(model.burden_ratios(people))["under 2,000"]
        finally:
            model.OPEN_LOW["income"] = saved
        print(f"  {value} €: share {v['share']:.1f}, median {v['median']:.1f}, over 40 {v['over 40']:.1f}, "
              f"50 and more {v['50 and more']:.1f}")

    print("\nSensitivity: position of the income inside its closed class (0.5 = midpoint, the main case); the "
          "groups are formed again")
    midpoint = model._midpoint
    for position in (0.4, 0.5, 0.6, 0.7):
        def placed(frame: pd.DataFrame, kind: str, position: float = position) -> pd.Series:
            value = midpoint(frame, kind)
            if kind != "income":
                return value
            low, high = frame["income_low"], frame["income_high"]
            closed = (low > 0) & high.notna()
            return value.where(~closed, low + position * (high - low))
        model._midpoint = placed
        try:
            v = group_values(model.burden_ratios(people))["under 2,000"]
        finally:
            model._midpoint = midpoint
        print(f"  {position:.1f}: share {v['share']:.1f}, median {v['median']:.1f}, over 40 {v['over 40']:.1f}, "
              f"50 and more {v['50 and more']:.1f}")

    w_household = ratios["weight"] / (ratios["persons"] - ratios["children"]).clip(lower=1)
    in_low = ratios["group"] == "LIF_RENT_BURDEN_INCOME_LOW"
    print(f"\nPer household instead of per adult (weight ÷ adults, an approximation): the group under 2,000 € holds "
          f"{100 * w_household[in_low].sum() / w_household.sum():.1f} % of the tenant households.")

    print("\nUnder 2,000 € by employment (XDberuf_a)")
    lowest = ratios[ratios["group"] == "LIF_RENT_BURDEN_INCOME_LOW"]
    for status, g in lowest.groupby("working", dropna=False):
        label = "no answer" if pd.isna(status) else status
        if len(g) < model.MIN_CASES:
            print(f"  {label}: {len(g)} cases, too few")
            continue
        w = g["weight"]
        print(f"  {label}: {len(g)} cases, {100 * w.sum() / lowest['weight'].sum():.1f} % of the group, median "
              f"{weighted_median(g['ratio'], w):.1f}, over 50 {100 * w[g['ratio'] > 50].sum() / w.sum():.1f}")

    print("\nMikrozensus, Mietbelastung = Bruttokaltmiete (no heating) ÷ household net income, Frankfurt, mean "
          "(Wohnungsmarktbericht 2019/2020, figures 40 and 41)")
    print("  2018: " + ", ".join(f"{k} {v:.1f}" for k, v in MZ_2018.items()))
    for year, values in MZ_2006_2014.items():
        print(f"  {year}: " + ", ".join(f"{k} {'-' if v == 0 else f'{v:.1f}'}"
                                       for k, v in zip(MZ_CLASSES_2006_2014, values)))

    sgb2, rented = sgb2_tenant_households(), rented_dwellings()
    assert rented == 312915, rented
    print(f"\nOrder of magnitude [unsicher]: {sgb2:,} renting households in the Grundsicherung (SGB II, June 2025) "
          f"against {rented:,} rented dwellings (Zensus 15.5.2022): {100 * sgb2 / rented:.1f} % of households. The "
          f"group under 2,000 € holds {low['share']:.1f} % of adult tenants (per household see above). Grundsicherung im Alter and Wohngeld come on top.")


if __name__ == "__main__":
    main()
