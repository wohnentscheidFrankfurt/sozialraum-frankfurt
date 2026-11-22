"""View „Neubau“: all dwellings per year, split into new construction and conversions, and the subsidised part;
the stock of dwellings and the population on 31.12. per year; the index of stocks, rents, prices and wages (README).
Pure."""
from __future__ import annotations

import datetime

import pandas as pd

from pipeline.shared.core import palette
from pipeline.shared.core.calc_example import CalcExample, Row, example_payload
from pipeline.shared.core.texts import Texts
from pipeline.use_cases.new_construction.catalog import SURVEY_DATES, shown_date


def add_report_year(totals: dict[int, int], year: int, dwellings: int, last: int) -> dict[int, int]:
    """The total of the last year comes from the HSL report only. Stops if the report is of another year or the
    Regionaldatenbank has the last year already (then the report is not needed and the two must be compared)."""
    if year != last:
        raise ValueError(f"HSL report is of {year}, expected {last}")
    if last in totals:
        raise ValueError(f"Regionaldatenbank has {last} already; the report of {last} is no longer the only source")
    return {**totals, last: dwellings}


def series(new_res: dict[int, int], new_nonres: dict[int, int], all_dwellings: dict[int, int],
           subsidised: dict[int, tuple[int, int]], first: int, last: int, provisional_from: int) -> pd.DataFrame:
    """One row per year: all completed dwellings (HSL), new construction (residential plus non-residential new
    buildings, HSL), conversions as the rest, FW 1 and FW 2 (Magistrat), their sum and the share of new construction."""
    inputs = {"new residential": new_res, "new non-residential": new_nonres, "all dwellings": all_dwellings,
              "subsidised": subsidised}
    rows = []
    for year in range(first, last + 1):
        for name, values in inputs.items():
            if year not in values:
                raise ValueError(f"new construction: no value for {year} in {name}")
        fw1, fw2 = subsidised[year]
        new = new_res[year] + new_nonres[year]
        rows.append({"year": year, "all": all_dwellings[year], "new_res": new_res[year],
                     "new_nonres": new_nonres[year], "new": new, "conversions": all_dwellings[year] - new,
                     "fw1": fw1, "fw2": fw2, "subsidised": fw1 + fw2, "share": (fw1 + fw2) / new,
                     "provisional": year >= provisional_from})
    return pd.DataFrame(rows)


def facts(table: pd.DataFrame, years: int) -> dict:
    """The numbers behind heading and lead (catalog TEXTS); checks.py tests each statement."""
    t = table.set_index("year")
    last = int(t.index.max())
    before = t.loc[:last - 1, "share"]
    span = t.loc[last - years + 1:, "all"]
    return {"last_year": last, "share_last": float(t.loc[last, "share"]), "max_share_before": float(before.max()),
            "max_share_year": int(before.idxmax()), "mean": float(span.mean()),
            "first_year": int(span.index.min())}


def percent(share: float, t: Texts) -> str:
    """A share as the chart shows it: one decimal."""
    return t.number(100 * share, 1, "%")


def column_sum(row, texts: dict) -> dict:
    """Written sum of one column (docs/texts.md, Written sums): new construction in residential and non-residential
    buildings, conversions, all dwellings. Counts, no estimate."""
    t = texts
    rows = (Row("", int(row.new_res), 0, t["new_res"]), Row("+", int(row.new_nonres), 0, t["new_nonres"]),
            Row("", int(row.new), 0, t["new"], total=True), Row("+", int(row.conversions), 0, t["conversions"]),
            Row("", int(row.all), 0, t["all"], total=True))
    return example_payload(CalcExample("", rows, label=t["label"].format(year=int(row.year))))


def share_sum(row, texts: dict) -> dict:
    """Written sum of the share of one year: Förderweg 1 and 2, the subsidised dwellings (named provisional where the
    year is), ÷ new construction, the share in percent with one decimal as in the chart."""
    t = texts
    rows = (Row("", int(row.fw1), 0, t["fw1"]), Row("+", int(row.fw2), 0, t["fw2"]),
            Row("", int(row.subsidised), 0, t["subsidised_provisional" if row.provisional else "subsidised"],
                total=True),
            Row("÷", int(row.new), 0, t["new"]),
            Row("", round(100 * row.share, 1), 1, t["share"], total=True, unit="%"))
    return example_payload(CalcExample("", rows, label=t["label"].format(year=int(row.year))))


def view(table: pd.DataFrame, texts: dict, t: Texts) -> dict:
    """Payload of the view: texts and per year the numbers, finished as text of the language, and the tooltip. `info`
    carries the written sums of the column and of the share of the last year (`calc_examples`). texts: TEXTS of one
    language, t: the texts of the package in the same language (they format the numbers)."""
    years = []
    for r in table.itertuples():
        tip = texts["tip"].format(year=r.year, all=t.number(r.all, 0), new=t.number(r.new, 0),
                                  conversions=t.number(r.conversions, 0), subsidised=t.number(r.subsidised, 0),
                                  share=percent(r.share, t))
        if r.provisional:
            tip += " " + texts["provisional_note"]
        years.append({"year": int(r.year), "all": int(r.all), "new": int(r.new), "conversions": int(r.conversions),
                      "subsidised": int(r.subsidised), "provisional": bool(r.provisional),
                      "all_text": t.number(int(r.all), 0), "share_text": percent(r.share, t), "tip": tip})
    last = next(table[table["year"] == table["year"].max()].itertuples())
    info = {**texts["info"], "calc_examples": [column_sum(last, texts["calc_column"]),
                                               share_sum(last, texts["calc_share"])]}
    return {**{k: texts[k] for k in ("title", "lead", "key", "source", "color", "link")}, "info": info,
            "highlight": int(table["year"].max()), "max": int(table["all"].max()), "years": years}


def up_to_last_year(values: dict[int, int], last: int, name: str) -> dict[int, int]:
    """A series that comes from the Regionaldatenbank alone, the last year included. Stops if the last year is missing
    or a later year is there (then LAST_YEAR and the reports are due for an update)."""
    if last not in values:
        raise ValueError(f"{name}: no value for {last}")
    later = sorted(y for y in values if y > last)
    if later:
        raise ValueError(f"{name}: values after {last} for {', '.join(map(str, later))}; update LAST_YEAR")
    return values


def stock_series(stock: dict[int, int], population: dict[int, int], all_dwellings: dict[int, int], first: int,
                 last: int, breaks: tuple[int, ...]) -> pd.DataFrame:
    """One row per year: the stock and the population on 31.12. (HSL), the completed dwellings, the change of the stock
    to the year before and the outflow as the rest (completed − change). Change and outflow stay empty for the first
    year and for a year that starts a new base (`breaks`)."""
    inputs = {"stock": stock, "population": population, "all dwellings": all_dwellings}
    rows = []
    for year in range(first, last + 1):
        for name, values in inputs.items():
            if year not in values:
                raise ValueError(f"{name}: no value for {year}")
        change = None if year == first or year in breaks else stock[year] - stock[year - 1]
        rows.append({"year": year, "stock": stock[year], "population": population[year],
                     "completed": all_dwellings[year], "change": change,
                     "outflow": None if change is None else all_dwellings[year] - change})
    return pd.DataFrame(rows).astype({"change": "Int64", "outflow": "Int64"})


def up_to_year(table: pd.DataFrame, last: int) -> pd.DataFrame:
    """The rows of a yearly table up to `last`. The block of rents ends at its last survey year (catalog RENT_TO), the
    stock table at the last year of the columns; stock_facts takes the span of the block from the shorter table."""
    return table[table["year"] <= last]


SERIES = ("stock", "population")  # the two series of the chart, columns of stock_series and keys of the bridge


def stock_facts(table: pd.DataFrame, start: int, breaks: tuple[int, ...], bridge: dict[str, dict[int, int]]) -> dict:
    """The numbers behind heading and ⓘ of the block of rents about the dwellings and the population (catalog
    RENTS_TEXTS); checks.py tests each statement. The span runs from `start` to the last year. Per series: the
    published growth divides the two values. The chained growth multiplies the yearly factors; a break year counts
    with its value on the old base (`bridge`, the last Fortschreibung on the old Zensus). The base effect is the value
    of the break year minus its value on the old base. Stops if a break year has no value on the old base."""
    for name in SERIES:
        missing = [y for y in breaks if y not in bridge[name]]
        if missing:
            raise ValueError(f"{name}: no value on the old base for {', '.join(map(str, missing))}")
    t = table.set_index("year")
    last = int(t.index.max())
    brk = max(breaks)
    outflow = t["outflow"].dropna()
    f = {"last_year": last, "from_year": start, "break_year": brk, "mean_outflow": float(outflow.mean()),
         "outflow_last": None if last not in outflow.index else int(outflow[last]),
         "mean_outflow_other": float(outflow.drop(last, errors="ignore").mean())}
    for name in SERIES:
        values, old = t[name], bridge[name]
        chained = 1.0
        for year in range(start + 1, last + 1):
            chained *= (old[year] if year in breaks else values[year]) / values[year - 1]
        f |= {f"{name}_growth": float(values[last] / values[start] - 1), f"{name}_growth_chained": float(chained - 1),
              f"{name}_bridge": old[brk], f"{name}_base_effect": int(values[brk]) - old[brk]}
    return f


def year_prices(prices: dict[tuple[int, int], float], months: dict[int, int], first: int, last: int,
                default_month: int) -> dict[int, float]:
    """The price index (VPI Hessen) per year: in a survey year the value of the survey month (`months`: year → month),
    in every other year the value of `default_month`. Stops and names the first (year, month) without a value."""
    out = {}
    for year in range(first, last + 1):
        month = months.get(year, default_month)
        if (year, month) not in prices:
            raise ValueError(f"prices: no value for {year} month {month}")
        out[year] = prices[(year, month)]
    return out


def year_wages(wages: dict[tuple[int, int], float], quarters: tuple[int, int], first: int,
               last: int) -> dict[int, float]:
    """The wage index (Nominallohnindex Hessen) per year: the mean of the given quarters. Stops and names the first
    (year, quarter) without a value."""
    out = {}
    for year in range(first, last + 1):
        for quarter in quarters:
            if (year, quarter) not in wages:
                raise ValueError(f"wages: no value for {year} quarter {quarter}")
        out[year] = sum(wages[(year, q)] for q in quarters) / len(quarters)
    return out


def rents_table(stock: pd.DataFrame, surveys: dict[int, dict], prices: dict[int, float], wages: dict[int, float],
                first: int, last: int) -> pd.DataFrame:
    """One row per year of the index of stocks, rents, prices and wages. A `*_index` column is the value divided by the
    value of the first year × 100. Stock and population count on 31.12. (`stock_series`). Rents (`surveys`: the mean
    net rent per m² of the new and of the older contracts), prices and wages stand for the middle of the year. A rent
    exists in a survey year only (NaN in the others). A `*_real` column is the index divided by the price index × 100,
    so without inflation. The prices of a survey year are the VPI of its survey month (`year_prices`). Stops if the
    first or the last year has no survey or an input lacks a year."""
    t = stock.set_index("year")
    for year in (first, last):
        if year not in surveys:
            raise ValueError(f"rents: no survey for {year}")
    for name, values in (("stock", t["stock"]), ("prices", prices), ("wages", wages)):
        missing = [y for y in range(first, last + 1) if y not in values]
        if missing:
            raise ValueError(f"{name}: no value for {missing[0]}")
    rows = []
    for year in range(first, last + 1):
        survey = surveys.get(year, {})
        row = {"year": year, "stock": int(t.loc[year, "stock"]), "population": int(t.loc[year, "population"]),
               "stock_index": 100 * t.loc[year, "stock"] / t.loc[first, "stock"],
               "population_index": 100 * t.loc[year, "population"] / t.loc[first, "population"],
               "prices_index": 100 * prices[year] / prices[first], "wages_index": 100 * wages[year] / wages[first]}
        row["wages_real"] = 100 * row["wages_index"] / row["prices_index"]
        for name in ("new", "old"):
            rent = survey.get(name, float("nan"))
            row |= {name: rent, f"{name}_index": 100 * rent / surveys[first][name]}
            row[f"{name}_real"] = 100 * row[f"{name}_index"] / row["prices_index"]
        rows.append(row)
    columns = ["year", "stock", "population", "stock_index", "population_index", "prices_index", "wages_index",
               "wages_real", "new", "old", "new_index", "old_index", "new_real", "old_real"]
    return pd.DataFrame(rows)[columns]


def rents_facts(table: pd.DataFrame, sf: dict, households: dict[int, float], first: int, last: int) -> dict:
    """The numbers behind heading, lead and ⓘ of the block of rents (catalog RENTS_TEXTS); checks.py tests each
    statement. The growths of the stocks come from `sf` (`stock_facts` with `start` = `first`), the others are the
    index of the last year ÷ 100 − 1: rents of new and older contracts, prices, wages, and the rents and wages without
    inflation (`*_growth_real`). The size of a household is persons ÷ households of `households`: the lowest
    (`household_low`) and the highest (`household_high`) of all years from first to last. The base effect of the break
    year (the ⓘ names it) comes from `sf` too: `break_year`, and per stock series the value on the old base
    (`*_bridge`) and its difference to the value of the break year (`*_base_effect`). Stops if `sf` spans other years
    or `households` lacks a year from first to last."""
    if (sf["from_year"], sf["last_year"]) != (first, last):
        raise ValueError(f"stock facts span {sf['from_year']} to {sf['last_year']}, expected {first} to {last}")
    for year in range(first, last + 1):
        if year not in households:
            raise ValueError(f"households: no value for {year}")
    t = table.set_index("year")
    f = {key: sf[key] for key in ("stock_growth", "stock_growth_chained", "population_growth",
                                  "population_growth_chained", "break_year", "stock_bridge", "population_bridge",
                                  "stock_base_effect", "population_base_effect")}
    for key, column in (("new_growth", "new_index"), ("new_growth_real", "new_real"), ("old_growth", "old_index"),
                        ("old_growth_real", "old_real"), ("prices_growth", "prices_index"),
                        ("wages_growth", "wages_index"), ("wages_growth_real", "wages_real")):
        f[key] = float(t.loc[last, column] / 100 - 1)
    sizes = [households[year] for year in range(first, last + 1)]
    return f | {"household_low": min(sizes), "household_high": max(sizes)}


INK = "#1a1a1a"  # --text of web/map.css: the population line and the end labels of the data lines
GREY = "#6b6b6b"  # --grey of web/map.css: the end labels of the references and the key of the old base
# The drawing of each series (docs/design.md, View Neubau): kind, colour, colour of the end label (grey for a reference
# line), width in units of the svg and dash pattern (None: solid). The references are thin edges of a grey band, a
# scale, not data.
LINES = {
    "prices": ("reference", palette.REFERENCE_PRICES, GREY, 1.5, None),
    "wages": ("reference", palette.REFERENCE_WAGES, GREY, 1.5, "5 3"),
    "dwellings": ("data", palette.SUBSIDISED, INK, 2.5, None),
    "population": ("data", INK, INK, 2, None),
    "new": ("data", palette.RENT_NEW, INK, 3, None),
    "old": ("data", palette.RENT_OLD, INK, 2.5, None),
}
OLD_BASE_DASH = "1 4"  # the dotted segment to a hollow dot and the swatch of the old base in the key
BAND_BETWEEN = ("wages", "prices")  # the band fills the space between these two series (both have every year)
# Per chart the series in drawing order (the references first, they lie under everything) with the column of the
# rents_table they take. Without inflation the prices are the scale: always 100 (no column).
CHART_SERIES = {
    "nominal": (("prices", "prices_index"), ("wages", "wages_index"), ("dwellings", "stock_index"),
                ("population", "population_index"), ("new", "new_index"), ("old", "old_index")),
    "real": (("prices", None), ("wages", "wages_real"), ("new", "new_real"), ("old", "old_real")),
}
OLD_BASE_SERIES = (("dwellings", "stock"), ("population", "population"))  # series id, column of the stock table


def rents_view(table: pd.DataFrame, facts: dict, texts: dict, bridge: dict[str, dict[int, int]],
               breaks: tuple[int, ...], axes: dict[str, dict], t: Texts) -> dict:
    """Payload of the block of rents (catalog RENTS_TEXTS): `title`, `lead`, `info`, `source`, `link` and the two
    `charts` (`nominal`, `real`), see `rents_chart`. `old_base` (chart `nominal` only) holds the break year on the old base:
    per stock series the index value and the tooltip of its hollow dot. Stops if the break year lies outside the
    years, if `facts` and the table give different published growths, or if a value lies outside the axis of its
    chart. texts: RENTS_TEXTS of one language, t: the texts of the package in the same language (they format the
    numbers)."""
    data = table.set_index("year")
    first, last, brk = int(data.index.min()), int(data.index.max()), max(breaks)
    if not first < brk <= last:
        raise ValueError(f"break year {brk} lies outside {first + 1} to {last}")
    for name, column in (("stock", "stock_index"), ("population", "population_index")):
        if abs(data.loc[last, column] / 100 - 1 - facts[f"{name}_growth"]) > 1e-9:
            raise ValueError(f"{name}: the growth in the facts is not the one of the table")
    old = {sid: float(100 * bridge[name][brk] / data.loc[first, name]) for sid, name in OLD_BASE_SERIES}
    old_base = {"year": brk, **{sid: {"value": old[sid], "tip": (
        texts["tip_hollow"].format(date=t.date(datetime.date(brk, 12, 31)), old_base=texts["old_base"],
                                   value=t.number(old[sid], 1),
                                   label=texts["tip_" + sid], count=t.number(bridge[name][brk], 0)))}
        for sid, name in OLD_BASE_SERIES}}
    charts = [rents_chart(cid, data, texts, axes[cid], brk, old_base, t) for cid in CHART_SERIES]
    info = {**texts["info"], "calc_examples": [rent_sum(data, texts["calc_rent"], first, last)]}
    return {**{key: texts[key] for key in ("title", "lead")}, "info": info,
            **{key: texts[key] for key in ("source", "link")}, "charts": charts}


def rent_sum(t: pd.DataFrame, texts: dict, first: int, last: int) -> dict:
    """Written sum of the new contracts of `last` (`t` indexed by year): the rent per m² ÷ the rent of `first` × 100 =
    the index, ÷ the prices × 100 = without inflation; the two end values of their lines, one decimal."""
    r = t.loc[last]
    rows = (Row("", float(r["new"]), 2, texts["rent"].format(year=last), unit="€"),
            Row("÷", float(t.loc[first, "new"]), 2, texts["base"].format(first=first), unit="€"),
            Row("×", 100, 0, ""),
            Row("", round(float(r["new_index"]), 1), 1, texts["nominal"].format(first=first), total=True),
            Row("÷", round(float(r["prices_index"]), 1), 1, texts["prices"].format(year=last, first=first)),
            Row("×", 100, 0, ""),
            Row("", round(float(r["new_real"]), 1), 1, texts["real"], total=True))
    return example_payload(CalcExample("", rows, label=texts["label"].format(year=last)))


def rents_chart(cid: str, data: pd.DataFrame, texts: dict, axis: dict, brk: int, old_base: dict, t: Texts) -> dict:
    """One chart of the block: `id`, `title`, `explain`, `key` (the series ids of `end_order`, chart `nominal` then the
    old base; per entry id, name, kind `data`, `reference` or `old_base`, colour, width and `dash`; a data entry adds
    `dot`, whether its swatch has a dot (True when the series has dots in the chart); a reference entry adds `edge`,
    `top` for the reference with the higher last value and `bottom` for the other, and `band`, the colour of the
    band), `band` (`between` the two series it fills, `colour`), `axis` (min, max, ticks, tick_texts), `years`,
    `survey_years` (the years with a rent value), `series` in drawing order (id, name, kind, colour, ink, width,
    `dash`, `values` per year with None where a year has no value, `dots` the years that get a dot: the rents in
    their survey years, a stock or a reference none, `end_value_text` and `end_name` of the last year),
    `end_order` (the series ids by their last value, highest first; a tie keeps the drawing order: the order of the end
    labels), `tips` (per year head, rows [value_text, label, series id], note, and all as one `text`) and
    `aria_label` (the title and every tooltip). Chart `nominal` adds `break` (year, note), `old_base` and
    `old_base_note`. Stops if a series of the band lacks a value in a year or if a value lies outside the axis, and
    names chart, series and year. `data` is the rents_table indexed by year, `t` the texts of the package."""
    text, years = texts["charts"][cid], [int(y) for y in data.index]
    values = {sid: [100.0] * len(years) if column is None else [None if pd.isna(v) else float(v) for v in data[column]]
              for sid, column in CHART_SERIES[cid]}
    for sid in BAND_BETWEEN:
        for year, v in zip(years, values[sid]):
            if v is None:
                raise ValueError(f"{cid}: {sid} {year} has no value for the band")
    for sid, current in values.items():
        for year, v in zip(years, current):
            if v is not None and not axis["min"] <= v <= axis["max"]:
                raise ValueError(f"{cid}: {sid} {year} = {v:.1f} lies outside the axis {axis['min']} to {axis['max']}")
    end_order = sorted(values, key=lambda sid: -values[sid][-1])
    stocks = [sid for sid, _ in OLD_BASE_SERIES]
    lines, dots = [], {}
    for sid, current in values.items():
        kind, colour, ink, width, dash = LINES[sid]
        # a dot marks a survey day of the Mietspiegel: the rents have it in their survey years, a reference or a stock
        # (counted every year, on 31.12.) has none
        dots[sid] = [] if kind == "reference" or sid in stocks else [y for y, v in zip(years, current) if v is not None]
        lines.append({"id": sid, "name": text["key"][sid], "kind": kind, "colour": colour, "ink": ink, "width": width,
                      "dash": dash, "values": current, "dots": dots[sid], "end_value_text": t.number(current[-1], 1),
                      "end_name": texts["names"][sid]})
    top = next(sid for sid in end_order if LINES[sid][0] == "reference")
    key = []
    for sid in end_order:
        kind, colour, _, width, dash = LINES[sid]
        key.append({"id": sid, "name": text["key"][sid], "kind": kind, "colour": colour, "width": width, "dash": dash,
                    **({"edge": "top" if sid == top else "bottom", "band": palette.REFERENCE_BAND}
                       if kind == "reference" else {"dot": bool(dots[sid])})})
    if "old_base" in text["key"]:
        key.append({"id": "old_base", "name": text["key"]["old_base"], "kind": "old_base", "colour": GREY, "width": 2,
                    "dash": OLD_BASE_DASH})
    nominal = cid == "nominal"
    tips = [rents_tip(i, data.loc[year], values, years, texts, old_base if nominal and year == brk else None, t)
            for i, year in enumerate(years)]
    label = [text["title"] + "."] + [tip["text"] for tip in tips]
    chart = {"id": cid, "title": text["title"], "explain": text["explain"], "key": key,
             "band": {"between": list(BAND_BETWEEN), "colour": palette.REFERENCE_BAND},
             "axis": {"min": axis["min"], "max": axis["max"], "ticks": list(axis["ticks"]),
                      "tick_texts": [t.number(v, 0) for v in axis["ticks"]]},
             "years": years, "survey_years": [y for y, v in zip(years, values["new"]) if v is not None],
             "series": lines, "end_order": end_order, "tips": tips}
    if nominal:
        chart |= {"break": {"year": brk, "note": texts["break_note"]}, "old_base": old_base,
                  "old_base_note": texts["old_base_note"]}
        label += [old_base[sid]["tip"] for sid, _ in OLD_BASE_SERIES]
    return chart | {"aria_label": " ".join(label)}


def rents_tip(i: int, row: pd.Series, values: dict[str, list], years: list[int], texts: dict,
              old_base: dict | None, t: Texts) -> dict:
    """The tooltip of the year `years[i]`: head, rows [value_text, label, series id] and a note. The browser draws the
    swatch of a row in the colour, width and dash of its series. The stock rows (chart `nominal`) show the count in
    brackets. The rent rows exist in a survey year only: the new contracts with their euro value and the day of the
    survey, the older contracts with their euro value. In the break year `old_base` puts the index values on the old
    base in front of the note. `texts`: RENTS_TEXTS of one language, `t` the texts of the package."""
    year, rows = years[i], []

    def add(sid, label):
        rows.append([t.number(values[sid][i], 1), label, sid])

    survey = not pd.isna(row["new"])
    if "dwellings" in values:
        add("dwellings", texts["tip_count"].format(label=texts["tip_dwellings"], count=t.number(int(row["stock"]), 0)))
        add("population", texts["tip_count"].format(label=texts["tip_population"],
                                                     count=t.number(int(row["population"]), 0)))
    if survey:
        if year not in SURVEY_DATES:
            raise ValueError(f"rents: no survey date for {year}")
        add("new", texts["tip_rent_new"].format(label=texts["tip_new"], rent=t.number(row["new"], 2, "€"),
                                                date=shown_date(year, t)))
        add("old", texts["tip_rent_old"].format(label=texts["tip_old"], rent=t.number(row["old"], 2, "€")))
    add("prices", texts["tip_prices"])
    add("wages", texts["tip_wages"] if "dwellings" in values else texts["tip_wages_real"])
    note = texts["tip_survey"] if survey else texts["tip_no_survey"]
    if old_base is not None:
        note = texts["tip_note_old_base"].format(
            old_base=texts["tip_old_base"].format(dwellings=t.number(old_base["dwellings"]["value"], 1),
                                                  population=t.number(old_base["population"]["value"], 1)),
            note=note)
    head = texts["tip_head"].format(year=year, base=years[0])
    return {"year": year, "head": head, "rows": rows, "note": note,
            "text": texts["tip_text"].format(
                head=head, rows="; ".join(texts["tip_row"].format(value=value, label=label) for value, label, _ in rows),
                note=note)}
