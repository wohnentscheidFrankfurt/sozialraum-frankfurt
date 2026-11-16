"""Survey „Leben in Frankfurt 2025“: the printed class of each survey area, shown on its districts (README). Pure module."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from pipeline.shared.core.areas import city_rows
from pipeline.shared.core.stats import weighted_median

CITY_ROW = "city"
SURVEY_IDS = ("LIF_RENT_BURDEN_RATIO", "LIF_ATTACHMENT")
BREAKDOWN_IDS = ("LIF_RENT_BURDEN_INCOME_LOW", "LIF_RENT_BURDEN_INCOME_MID", "LIF_RENT_BURDEN_INCOME_HIGH")
INCOME_LIMITS = (2000, 3200)  # household income in euros: below the first, below the second, else
MIN_CASES = 30  # unweighted cases of an area and group; fewer show no value
STEP = 5  # the breakdown is rounded to 5 points
# Fixed values of the open classes (euros): lowest class of rent, costs and income, highest class of each
OPEN_LOW = {"rent": 325, "costs": 75, "income": 750}
OPEN_HIGH = {"rent": 1700, "costs": 450, "income": 6000}


def survey_table(figures: dict[str, dict], area_names) -> pd.DataFrame:
    """Printed class per survey area (<ID> = upper end, <ID>_LOWER = lower end) and the printed city value."""
    rows = [{"survey_area": name} for name in area_names] + [{"survey_area": CITY_ROW}]
    for indicator, figure in figures.items():
        found = {area: bounds for bounds, areas in figure["classes"].items() for area in areas}
        unknown = sorted(set(found) - set(area_names))
        missing = sorted(set(area_names) - set(found))
        if unknown or missing:
            raise ValueError(f"{indicator}: survey areas unknown {unknown}, without class {missing}")
        for row in rows:
            lower, upper = found.get(row["survey_area"], (math.nan, figure["city"]))
            row[indicator], row[f"{indicator}_LOWER"] = float(upper), float(lower)
    return pd.DataFrame(rows)


def survey_by_district(survey: pd.DataFrame, district_areas: pd.DataFrame) -> pd.DataFrame:
    """district_areas: columns id, survey_area. Each district gets the row of its survey area."""
    return district_areas.merge(survey, on="survey_area", how="left").drop(columns="survey_area")


def survey_city(survey: pd.DataFrame) -> list[dict]:
    """The printed city values (published) and the city row of the income groups (computed from the microdata)."""
    city = survey.set_index("survey_area").loc[CITY_ROW]
    plain = lambda v: v.item() if hasattr(v, "item") else v  # numpy numbers cannot go into JSON
    published = [row for k in SURVEY_IDS for row in city_rows({k: plain(city[k])}, kind="published")]
    # not city_rows: it drops ids ending in _LOW and _HIGH as ends of a range
    return published + [{"indicator": k, "value": plain(city[k]), "kind": "computed"} for k in BREAKDOWN_IDS]


def _midpoint(frame: pd.DataFrame, kind: str, position: float = 0.5, open_low: float | None = None) -> pd.Series:
    """Value of a closed class at `position` between its ends (0.5 = midpoint); the lowest and the open class take
    their fixed value (`open_low` replaces the fixed value of the lowest class)."""
    low, high = frame[f"{kind}_low"], frame[f"{kind}_high"]
    mid = low + position * (high - low)
    mid = mid.where(low != 0, OPEN_LOW[kind] if open_low is None else open_low)
    return mid.where(high.notna() | low.isna(), OPEN_HIGH[kind])


def _household_size(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Persons and children; singles and couples have no children, a household of 1 or 2 without form counts adults."""
    form = frame["household_form"]
    persons = frame["persons"].where(frame["persons"].notna(), form.map({"single": 1.0, "couple": 2.0}))
    children = frame["children"].where(~form.isin(["single", "couple"]), 0.0)
    adults_only = children.isna() & persons.isin([1, 2]) & form.isna()
    return persons, children.where(~adults_only, 0.0)


def burden_ratios(respondents: pd.DataFrame, income_position: float = 0.5,
                  open_low_income: float | None = None) -> pd.DataFrame:
    """Complete tenants with warm rent, equivalence `scale`, household income, ratio (percent) and income group.
    `income_position` places the income of a closed class at low + position × (high − low), `open_low_income`
    replaces the fixed income of the open lowest class. Rent and costs always take their midpoint."""
    persons, children = _household_size(respondents)
    frame = respondents.assign(persons=persons, children=children)
    frame = frame[frame["tenant"]].copy()
    frame["warm_rent"] = _midpoint(frame, "rent") + _midpoint(frame, "costs")
    adults = (frame["persons"] - frame["children"]).clip(lower=1)
    frame["scale"] = 1 + 0.5 * (adults - 1) + 0.3 * frame["children"]
    frame["household_income"] = _midpoint(frame, "income", income_position, open_low_income) * frame["scale"]
    frame["ratio"] = 100 * frame["warm_rent"] / frame["household_income"]
    frame = frame[frame["ratio"].notna() & frame["weight"].notna()].copy()
    group = np.searchsorted(INCOME_LIMITS, frame["household_income"].to_numpy(), side="right")
    frame["group"] = np.array(BREAKDOWN_IDS)[group]
    return frame


def round_half_up(value: float, step: int = STEP) -> float:
    return float(step * math.floor(value / step + 0.5))


def _cell_median(cell: pd.DataFrame) -> float:
    median = weighted_median(cell["ratio"], cell["weight"])
    return math.nan if median is None else median


def income_breakdown(ratios: pd.DataFrame, area_names: list[str]) -> pd.DataFrame:
    """Weighted median ratio per survey area (and the city) and income group, rounded; NaN under MIN_CASES."""
    rows = []
    for area in [*area_names, CITY_ROW]:
        in_area = ratios if area == CITY_ROW else ratios[ratios["survey_area"] == area]
        row = {"survey_area": area}
        for group_id in BREAKDOWN_IDS:
            cell = in_area[in_area["group"] == group_id]
            row[group_id] = round_half_up(_cell_median(cell)) if len(cell) >= MIN_CASES else math.nan
        rows.append(row)
    return pd.DataFrame(rows)


def _bootstrap_medians(ratio: np.ndarray, weight: np.ndarray, draws: int, rng: np.random.Generator) -> np.ndarray:
    """Lower weighted median of `draws` resamples of one cell (vectorised `weighted_median`)."""
    picks = rng.integers(0, len(ratio), (draws, len(ratio)))
    values, weights = ratio[picks], weight[picks]
    order = np.argsort(values, axis=1, kind="stable")
    values, weights = np.take_along_axis(values, order, 1), np.take_along_axis(weights, order, 1)
    cumulative = np.cumsum(weights, axis=1) / weights.sum(axis=1, keepdims=True)
    return np.take_along_axis(values, (cumulative >= 0.5).argmax(axis=1)[:, None], 1)[:, 0]


def _half_width(cell: pd.DataFrame, draws: int, rng: np.random.Generator) -> float:
    """Half the 90 % bootstrap interval of the weighted median of one cell."""
    medians = _bootstrap_medians(cell["ratio"].to_numpy(float), cell["weight"].to_numpy(float), draws, rng)
    low, high = np.percentile(medians, [5, 95])
    return float((high - low) / 2)


def breakdown_half_widths(ratios: pd.DataFrame, area_names: list[str], draws: int = 400, seed: int = 1) -> dict:
    """Half widths of the 90 % bootstrap interval of the median per area and group with a value: the median over the
    areas of the lowest group ("typical"), its largest ("max_low") and the largest of the other groups ("max_upper")."""
    rng = np.random.default_rng(seed)
    widths: dict[str, list[float]] = {group_id: [] for group_id in BREAKDOWN_IDS}
    for area in area_names:
        for group_id in BREAKDOWN_IDS:
            cell = ratios[(ratios["survey_area"] == area) & (ratios["group"] == group_id) & (ratios["weight"] > 0)]
            if len(cell) >= MIN_CASES:
                widths[group_id].append(_half_width(cell, draws, rng))
    lowest, *upper = BREAKDOWN_IDS
    return {"typical": float(np.median(widths[lowest])), "max_low": max(widths[lowest]),
            "max_upper": max(w for group_id in upper for w in widths[group_id])}


def tenant_medians(ratios: pd.DataFrame) -> dict[str, float]:
    """Weighted median ratio of all tenants per survey area and for the city, not rounded."""
    medians = {area: _cell_median(cell) for area, cell in ratios.groupby("survey_area")}
    return {**medians, CITY_ROW: _cell_median(ratios)}


def area_weight_shares(respondents: pd.DataFrame) -> dict[str, float]:
    """Percent of the total weight per survey area."""
    weight = respondents.groupby("survey_area")["weight"].sum()
    return (100 * weight / weight.sum()).to_dict()


def example_household(ratios: pd.DataFrame) -> dict:
    """Tenants living alone with the income class 1,000-2,000: medians of rent and costs, the ratio of their sum."""
    singles = ratios[(ratios["persons"] == 1) & (ratios["income_low"] == 1000) & (ratios["income_high"] == 2000)]
    result = {}
    for kind in ("rent", "costs"):
        mid = _midpoint(singles, kind)
        median = weighted_median(mid, singles["weight"])
        in_class = singles[mid == median].iloc[0]
        result |= {kind: median, f"{kind}_low": int(in_class[f"{kind}_low"]), f"{kind}_high": int(in_class[f"{kind}_high"])}
    income = 1500.0
    return result | {"income": income, "income_low": 1000, "income_high": 2000,
                     "ratio": 100 * (result["rent"] + result["costs"]) / income}
