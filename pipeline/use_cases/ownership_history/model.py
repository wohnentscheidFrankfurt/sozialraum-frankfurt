"""The view „Trend“: dwellings and buildings per owner group in both years (README).
Pure module."""
from __future__ import annotations

import math

import pandas as pd

from pipeline.use_cases.ownership_history.catalog import (BAR_ORDER, CHARTS, COMPANY_TITLE, GROUP_TEXTS,
                                                          HISTORY_SOURCE, SECTORS, SIZE_LABELS)
from pipeline.shared.core.colours import contrast, line_on, text_on
from pipeline.shared.core.checks import de_thousands
from pipeline.shared.core.indicator import fill
from pipeline.shared.zensus.model import SIZES

# Groups of the view "Trend" (README). The Nassauische Heimstätte
# is "state" in 2011 and "municipal" in 2022, so both form one group. The two company classes stay apart; "company"
# is their sum (COMPANY_CLASSES) for the lead lines and the charts „sizes“ and „decades“.
HISTORY_GROUPS = {"person": ["person"], "condo": ["condo"], "public": ["municipal", "state"],
                  "housing_company": ["housing_company"], "other_company": ["other_company"], "coop": ["coop"],
                  "nonprofit": ["nonprofit"]}
COMPANY_CLASSES = ["housing_company", "other_company"]

# "Große Häuser" = LARGE (sizes: pipeline.shared.zensus.model.SIZES)
LARGE = "13_plus"


def change_text(before: int, after: int) -> str | None:
    """The change from 2011 to 2022 in percent for the tooltips of the arrows, for example "+12 %" or "−3 %". The
    percent is rounded half up (as Math.round of the browser did), the sign follows the direction. A base of 0 has no
    change: None."""
    if before == 0:
        return None
    percent = math.floor(100 * (after - before) / before + 0.5)
    return ("+" if after >= before else "−") + de_thousands(abs(percent)) + " %"


def history_groups(dwellings: dict[int, dict[str, int]], buildings: dict[int, dict[str, dict[str, int]]]) -> pd.DataFrame:
    """Dwellings (4000W-1011) and buildings (totals of 3000G-2007) per group and year."""
    return pd.DataFrame([{"group": g, "year": y, "dwellings": int(sum(dwellings[y][k] for k in classes)),
                          "buildings": int(sum(buildings[y][k]["total"] for k in classes))}
                         for g, classes in HISTORY_GROUPS.items() for y in sorted(dwellings)])


def by_size(buildings: dict[int, dict[str, dict[str, int]]], dwellings: dict[int, dict[str, dict[str, int]]]) -> pd.DataFrame:
    """Buildings and dwellings per group, year and size; 'company' adds both company classes, 'all' holds every owner."""
    groups = HISTORY_GROUPS | {"company": COMPANY_CLASSES, "all": ["total"]}
    return pd.DataFrame([{"group": g, "year": y, "size": s,
                          "buildings": int(sum(buildings[y][k][s] for k in classes)),
                          "dwellings": int(sum(dwellings[y][k][s] for k in classes))}
                         for g, classes in groups.items() for y in sorted(dwellings) for s in SIZES])


def company_buildings_by_decade(decades: list[dict], buildings: dict[int, dict[str, dict[str, int]]]) -> pd.DataFrame:
    return pd.DataFrame([{**d, "year": y, "buildings": int(sum(buildings[y][k][d["decade"]] for k in COMPANY_CLASSES))}
                         for d in decades for y in sorted(buildings)])


def _with_company(groups: pd.DataFrame, column: str) -> pd.Series:
    """One column per (group, year), plus the group "company": the sum of both company classes."""
    v = groups.set_index(["group", "year"])[column]
    company = groups[groups["group"].isin(COMPANY_CLASSES)].groupby("year")[column].sum()
    return pd.concat([v, pd.Series({("company", y): n for y, n in company.items()})])


def history_facts(groups: pd.DataFrame, decades: pd.DataFrame, sizes: pd.DataFrame) -> dict:
    """The numbers behind the chart headings and lead lines (README). "company" is the sum of both company classes."""
    g = _with_company(groups, "dwellings")
    total = groups.groupby("year")["dwellings"].sum()
    wide = decades.pivot_table(index=["decade", "label", "first_year"], columns="year", values="buildings")
    change = wide[2022] - wide[2011]
    before = change[change.index.get_level_values("first_year") < 2010].sum()
    b = _with_company(groups, "buildings")
    b_total = groups.groupby("year")["buildings"].sum()
    z = sizes.set_index(["group", "year", "size"])["dwellings"]
    large_growth = int(z["company", 2022, LARGE] - z["company", 2011, LARGE])
    dwelling_growth = int(g["company", 2022] - g["company", 2011])
    extra = {"company_building_factor": float(b["company", 2022] / b["company", 2011]),
             "company_building_share_2022": float(b["company", 2022] / b_total[2022]),
             "company_large_share_2011": float(z["company", 2011, LARGE] / z["all", 2011, LARGE]),
             "company_large_share_2022": float(z["company", 2022, LARGE] / z["all", 2022, LARGE]),
             "company_large_growth": large_growth, "company_dwelling_growth": dwelling_growth,
             "large_growth_share": large_growth / dwelling_growth,
             "smallest_company_dwellings_per_building_2022": float(min(g[k, 2022] / b[k, 2022]
                                                                       for k in COMPANY_CLASSES)),
             "largest_other_dwellings_per_building_2022": float(max(g[k, 2022] / b[k, 2022] for k in HISTORY_GROUPS
                                                                    if k not in COMPANY_CLASSES))}
    return {"company_factor": float(g["company", 2022] / g["company", 2011]),
            "company_share_2022": float(g["company", 2022] / total[2022]),
            "company_growth": int(change.sum()), "company_growth_before_2010": int(before),
            "share_before_2010": float(before / change.sum())} | extra


def history_data(groups: pd.DataFrame, sizes: pd.DataFrame, decades: pd.DataFrame) -> dict:
    """Data and texts of the view "Trend" (README). The view only draws: shares, colours of labels and lines, and the
    filled tooltip come finished. A share is in percent and not rounded; the base is the sum of the groups of the year."""
    g = groups.set_index(["group", "year"])
    years = sorted(groups["year"].unique())
    z = sizes.set_index(["group", "year", "size"])["dwellings"]
    order = list(dict.fromkeys(decades.sort_values("first_year", kind="stable")["decade"]))
    d = decades.set_index(["decade", "year"])
    dw, bu = _with_company(groups, "dwellings"), _with_company(groups, "buildings")
    per_year = lambda f: {str(y): f(y) for y in years}
    count = lambda k, column: per_year(lambda y: int(g.loc[(k, y), column]))
    total = {c: {str(y): sum(int(g.loc[(k, y), c]) for k in BAR_ORDER) for y in years} for c in ("buildings", "dwellings")}
    share = lambda n, base: {y: 100 * n[y] / base[y] for y in n}
    out_groups = []
    for k, t in GROUP_TEXTS.items():
        buildings, values = count(k, "buildings"), count(k, "dwellings")
        out_groups.append({"id": k, **t, "values": values, "buildings": buildings,
                           "share": {"buildings": share(buildings, total["buildings"]),
                                     "values": share(values, total["dwellings"])},
                           "line_color": line_on(t["color"]), "label_color": text_on(t["color"]),
                           "label_contrast": contrast(t["color"], text_on(t["color"])), "company": k in COMPANY_CLASSES,
                           "change": {"buildings": change_text(buildings["2011"], buildings["2022"]),
                                      "values": change_text(values["2011"], values["2022"])}})
    out_sectors = []
    for k, t in SECTORS.items():
        n = {"buildings": {str(y): sum(int(g.loc[(m, y), "buildings"]) for m in t["groups"]) for y in years},
             "values": {str(y): sum(int(g.loc[(m, y), "dwellings"]) for m in t["groups"]) for y in years}}
        out_sectors.append({"id": k, **t, "count": {"values": n["values"]},
                            "share": {"buildings": share(n["buildings"], total["buildings"]),
                                      "values": share(n["values"], total["dwellings"])}})
    large = z["company", years[-1], LARGE] - z["company", years[0], LARGE]
    growth = dw["company", years[-1]] - dw["company", years[0]]
    sizes_chart = {k: v for k, v in CHARTS["sizes"].items() if k != "tip_large"} | {
        "tip_large_text": fill(CHARTS["sizes"]["tip_large"],
                               {"large": de_thousands(int(large)), "total": de_thousands(int(growth))})}
    return {"groups": out_groups,
            "company": {"title": COMPANY_TITLE, "values": per_year(lambda y: int(dw["company", y])),
                        "buildings": per_year(lambda y: int(bu["company", y]))},
            "bar_order": BAR_ORDER, "sectors": out_sectors,
            "sizes": [{"size": s, **SIZE_LABELS[s], "company": per_year(lambda y: int(z["company", y, s])),
                       "all": per_year(lambda y: int(z["all", y, s])),
                       "company_share": per_year(lambda y: 100 * int(z["company", y, s]) / int(z["all", y, s]))}
                      for s in SIZES],
            "decades": [{"label": d.loc[(k, years[0]), "label"], "first_year": int(d.loc[(k, years[0]), "first_year"]),
                         "values": {str(y): int(d.loc[(k, y), "buildings"]) for y in years}} for k in order],
            "source": HISTORY_SOURCE, "charts": CHARTS | {"sizes": sizes_chart}}
