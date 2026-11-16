# Why the overall rent burden differs between West and Mitte-West while the three income groups do not.
# Uses the functions of the map (pipeline/use_cases/survey), so the numbers are those of the map.
# Call from the repo root: .venv/bin/python -I research/scripts/rent_burden_west_mitte_west.py
# Prints per year and pooled: overall median, group shares, unrounded group medians; a composition counterfactual;
# a bootstrap of the 2025 difference of the overall medians.
import numpy as np
import pandas as pd

from pipeline import config as c
from pipeline.shared.core.stats import weighted_median
from pipeline.use_cases.survey import model
from pipeline.use_cases.survey.sources import read_microdata

GROUPS = {"LIF_RENT_BURDEN_INCOME_LOW": "<2000", "LIF_RENT_BURDEN_INCOME_MID": "2000-3200",
          "LIF_RENT_BURDEN_INCOME_HIGH": ">=3200"}
AREAS = ("West", "Mitte-West")


def describe(ratios: pd.DataFrame, area: str) -> str:
    s = ratios[ratios.survey_area == area]
    shares = {GROUPS[g]: round(100 * s.weight[s.group == g].sum() / s.weight.sum(), 1) for g in GROUPS}
    medians = {GROUPS[g]: round(weighted_median(s.ratio[s.group == g], s.weight[s.group == g]), 1) for g in GROUPS}
    return f"{area:11s} all {weighted_median(s.ratio, s.weight):5.1f}  n={len(s)}  shares {shares}  medians {medians}"


def with_mix_of(ratios: pd.DataFrame, area: str, mix_of: str) -> float:
    """Overall median of `area` after reweighting its groups to the group shares of `mix_of`."""
    s = ratios[ratios.survey_area == area].copy()
    t = ratios[ratios.survey_area == mix_of]
    for g in GROUPS:
        target = t.weight[t.group == g].sum() / t.weight.sum()
        s.loc[s.group == g, "weight"] *= target / s.weight[s.group == g].sum()
    return weighted_median(s.ratio, s.weight)


def main() -> None:
    per = {year: model.burden_ratios(read_microdata(path, year)) for year, path in c.SURVEY_MICRODATA.items()}
    per["pooled"] = pd.concat([per[2024], per[2025]])
    for key in (2025, 2024, "pooled"):
        print(f"== {key}")
        for area in AREAS:
            print(describe(per[key], area))
    pooled = per["pooled"]
    print(f"Mitte-West with the income mix of West: {with_mix_of(pooled, 'Mitte-West', 'West'):.1f}")
    print(f"West with the income mix of Mitte-West: {with_mix_of(pooled, 'West', 'Mitte-West'):.1f}")
    r = per[2025]
    west, mitte_west = r[r.survey_area == "West"], r[r.survey_area == "Mitte-West"]
    rng = np.random.default_rng(1)
    diffs = []
    for _ in range(1000):
        a = west.iloc[rng.integers(0, len(west), len(west))]
        b = mitte_west.iloc[rng.integers(0, len(mitte_west), len(mitte_west))]
        diffs.append(weighted_median(a.ratio, a.weight) - weighted_median(b.ratio, b.weight))
    low, mid, high = np.percentile(diffs, [5, 50, 95])
    print(f"2025 overall difference West - Mitte-West: median {mid:.1f}, 90 % interval {low:.1f} to {high:.1f}")


if __name__ == "__main__":
    main()
