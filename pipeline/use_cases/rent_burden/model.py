"""Net wage of a single full-time employee and the types of its rules. The rules of each survey day are typed in
`sources.py`. Steuerklasse I, no children (childless surcharge of the care insurance), no church tax, statutory health
insurance with the average Zusatzbeitrag. The wage tax follows the Programmablaufplan (PAP) of the Bundesministerium
der Finanzen: annual wage = 12 × monthly wage, minus Werbungskosten-Pauschbetrag, Sonderausgaben-Pauschbetrag (36 €)
and Vorsorgepauschale (§ 39b EStG), tariff of § 32a EStG, Soli with Freigrenze and Milderungszone (§ 4 SolZG).
Figure S1 (`wage_table`, `wage_facts`, `wage_view`): the warm rent of one flat against the net wage of the three model
persons of the catalog; `wage_table` counts every survey year, facts and view the latest one. Figure S2
(`group_table`, `low_income_facts`, `bars_view`): the warm rent against the household income of adult tenants per
income group of the use case `survey`, split into the burden classes of the catalog. Pure."""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from pipeline.shared.core import palette
from pipeline.shared.core.calc_example import CalcExample, Row, example_payload
from pipeline.shared.core.colours import contrast, text_on
from pipeline.shared.core.stats import weighted_median
from pipeline.shared.core.texts import Texts
from pipeline.use_cases.rent_burden.catalog import (CALC_CONTRACT, CALC_PERSON, CLASS_COLOURS, CLASSES, CONTRACTS,
                                                    FLAT_M2, PERSONS)
from pipeline.use_cases.survey.model import (BREAKDOWN_IDS, INCOME_LIMITS, MIN_CASES, OPEN_LOW, burden_ratios,
                                             round_half_up)


@dataclass(frozen=True)
class Tariff:
    """Income tax tariff of § 32a EStG for one year."""
    gfb: float  # Grundfreibetrag
    z1: float  # upper end of the first progression zone
    a1: float  # (a1 · y + 1400) · y
    z2: float  # upper end of the second progression zone
    a2: float  # (a2 · z + 2397) · z + c2
    c2: float
    c3: float  # 0.42 · x − c3 up to 277,826 € (2025; the 45 % zone is out of reach here)


@dataclass(frozen=True)
class WageRules:
    """Tax and contribution rules of one survey day for a single employee (Steuerklasse I, no children)."""
    tariff: Tariff
    werbungskosten: float  # Arbeitnehmer-Pauschbetrag
    rv_share_vsp: float  # part of the pension contribution in the Vorsorgepauschale
    soli_free: float  # Freigrenze of the annual wage tax
    soli_slope: float  # Milderungszone
    rv: float  # employee rate, pension insurance
    av: float  # employee rate, unemployment insurance
    kv_zusatz: float  # average Zusatzbeitrag (whole rate)
    kv_zusatz_employee_alone: bool
    pv: float  # employee rate of the care insurance incl. the childless surcharge
    ceiling_rv: float  # €/month, also unemployment insurance
    ceiling_kv: float  # €/month, also care insurance


def full_time(hourly: float) -> float:
    """Monthly wage of 40 hours a week: hourly × 40 × 52 ÷ 12."""
    return hourly * 40 * 52 / 12


def _kv_employee_rate(rules: WageRules) -> float:
    """General rate 14.6 % half, plus the Zusatzbeitrag (whole until 2018, half from 2019)."""
    return 0.073 + (rules.kv_zusatz if rules.kv_zusatz_employee_alone else rules.kv_zusatz / 2)


def contributions(wage: float, rules: WageRules) -> float:
    """Employee contributions per month: pension, unemployment, health, care."""
    up_rv, up_kv = min(wage, rules.ceiling_rv), min(wage, rules.ceiling_kv)
    return up_rv * (rules.rv + rules.av) + up_kv * (_kv_employee_rate(rules) + rules.pv)


def tariff(x: float, t: Tariff) -> float:
    """Annual income tax of § 32a EStG for a taxable income x (whole euros), rounded down."""
    if x <= t.gfb:
        return 0.0
    if x <= t.z1:
        y = math.floor((x - t.gfb) / 10000 * 1e6) / 1e6
        return math.floor((t.a1 * y + 1400) * y)
    if x <= t.z2:
        z = math.floor((x - t.z1) / 10000 * 1e6) / 1e6
        return math.floor((t.a2 * z + 2397) * z + t.c2)
    return math.floor(0.42 * x - t.c3)


def soli_of(tax: float, rules: WageRules) -> float:
    """Solidaritätszuschlag on an annual tax: none up to the Freigrenze, then 5.5 % at most the Milderungszone."""
    return 0.0 if tax <= rules.soli_free else min(0.055 * tax, (tax - rules.soli_free) * rules.soli_slope)


def _vorsorgepauschale(annual: float, rules: WageRules) -> float:
    """§ 39b EStG as the PAP computes it: pension part plus the larger of 12 % (at most 1,900 €)
    and health and care."""
    vsp1 = min(annual, 12 * rules.ceiling_rv) * rules.rv * rules.rv_share_vsp
    vsp2 = min(0.12 * annual, 1900)
    # the PAP takes the reduced general rate (14.0 %, half 7.0 %) for the Vorsorgepauschale
    kv = 0.07 + (rules.kv_zusatz if rules.kv_zusatz_employee_alone else rules.kv_zusatz / 2)
    vsp3 = min(annual, 12 * rules.ceiling_kv) * (kv + rules.pv)
    return math.ceil(vsp1 + max(vsp2, vsp3))


def income_tax(wage: float, rules: WageRules) -> tuple[float, float]:
    """Lohnsteuer and Soli per month, rounded down to cents like the PAP."""
    annual = 12 * wage
    zve = math.floor(annual - rules.werbungskosten - 36 - _vorsorgepauschale(annual, rules))
    tax = tariff(max(zve, 0), rules.tariff)
    return math.floor(tax / 12 * 100) / 100, math.floor(soli_of(tax, rules) / 12 * 100) / 100


def net(wage: float, rules: WageRules) -> float:
    """Net monthly wage: gross minus employee contributions, Lohnsteuer and Soli."""
    lohnsteuer, soli = income_tax(wage, rules)
    return wage - contributions(wage, rules) - lohnsteuer - soli


# --- S1, the wage example ---

def _wage_of(person: str, year: int, wages: dict[int, float], rules: dict[int, WageRules],
              mindestlohn: dict[int, float]) -> float:
    """Gross monthly wage: the Mindestlohn full time, the median of the residents, or the pension ceiling."""
    if person == "mindestlohn":
        return full_time(mindestlohn[year])
    return wages[year] if person == "median" else rules[year].ceiling_rv


def wage_table(rents: pd.DataFrame, nebenkosten: dict[int, float], wages: dict[int, float],
               rules: dict[int, WageRules], mindestlohn: dict[int, float], years: tuple[int, ...],
               m2: float) -> pd.DataFrame:
    """One row per survey year, person and contract: `warm_rent` = (`cold_m2`, the net cold rent of the Mietspiegel, +
    `costs_m2`, the `nebenkosten`, both € per m² and month) × `m2`, `gross` and `net` wage per month with the parts
    between them (`contributions`, `wage_tax`, `soli`), `share` = warm rent ÷ net × 100, `left` = net −
    warm rent, `left_real` = left × 100 ÷ prices_index (€ of the first year). `rents` has the columns year, new, old,
    prices_index (the rents table of new_construction); `mindestlohn` is € per hour. Stops, naming year and input, if
    a year lacks a rent, the price index, Nebenkosten, a wage, the Mindestlohn or rules, and if the price index of the
    first year is not 100."""
    r = rents.set_index("year")
    inputs = {"Nebenkosten": nebenkosten, "median wage": wages, "Mindestlohn": mindestlohn, "rules": rules}
    for year in years:
        for column in ("new", "old", "prices_index"):
            if year not in r.index or pd.isna(r.loc[year, column]):
                raise ValueError(f"wage table: no {'rent' if column != 'prices_index' else 'price index'} "
                                 f"({column}) for {year}")
        for name, values in inputs.items():
            if year not in values:
                raise ValueError(f"wage table: no {name} for {year}")
    first = min(years)
    if abs(r.loc[first, "prices_index"] - 100) > 1e-9:
        raise ValueError(f"wage table: the price index of {first} is {r.loc[first, 'prices_index']}, not 100")
    rows = []
    for year in years:
        for person in PERSONS:
            wage = _wage_of(person, year, wages, rules, mindestlohn)
            pay = net(wage, rules[year])
            wage_tax, soli = income_tax(wage, rules[year])
            for contract in CONTRACTS:
                cold = float(r.loc[year, contract])
                warm = (cold + nebenkosten[year]) * m2
                left = pay - warm
                rows.append({"year": year, "person": person, "contract": contract, "cold_m2": cold,
                             "costs_m2": nebenkosten[year], "warm_rent": warm, "gross": wage,
                             "contributions": contributions(wage, rules[year]), "wage_tax": wage_tax, "soli": soli,
                             "net": pay, "share": 100 * warm / pay, "left": left,
                             "left_real": left * 100 / float(r.loc[year, "prices_index"])})
    return pd.DataFrame(rows)


def wage_facts(table: pd.DataFrame, mietspiegel_table: pd.DataFrame, year: int) -> dict:
    """The numbers behind title and ⓘ of S1 (catalog WAGE_TEXTS) in `year`, the year S1 shows; checks.py tests each
    statement. `factor`: lowest and highest share of the Mindestlohn ÷ share of the high wage over the contracts.
    `sensitivity`: lowest and highest share − the share with the Nebenkosten of the Mietspiegel (`mietspiegel_table`,
    the same wage_table with the other Nebenkosten) over the cells of `year`; `sensitivity_persons` the same per
    person. Stops if `year` is missing or the two tables hold other cells in it."""
    s, m = (t[t["year"] == year].set_index(["person", "contract"])["share"] for t in (table, mietspiegel_table))
    if s.empty:
        raise ValueError(f"wage facts: the table has no row of {year}")
    if set(s.index) != set(m.index):
        raise ValueError(f"wage facts: the table with the Mietspiegel Nebenkosten holds other cells in {year}")
    ratio = s.xs("mindestlohn", level="person") / s.xs("high", level="person")
    gap = s - m.reindex(s.index)
    by_person = gap.groupby(level="person")
    return {"year": year, "factor": (float(ratio.min()), float(ratio.max())),
            "sensitivity": (float(gap.min()), float(gap.max())),
            "sensitivity_persons": {p: (float(by_person.min()[p]), float(by_person.max()[p])) for p in PERSONS}}


# The red block of the warm rent and its text (docs/design.md, View Miete); wage_view stops if the text contrasts less
# with the block than MIN_CONTRAST.
WAGE_COLOUR = palette.PUBLIC


def _percent(value: float, t: Texts) -> str:
    return "~" + t.number(value, 0, "%")


def _euro(value: float, t: Texts) -> str:
    return "~" + t.number(value, 0, "€")


def net_sum(row: pd.Series, texts: dict, hourly: float, t: Texts) -> dict:
    """Written sum of the net wage of one row of `wage_table` (docs/texts.md, Written sums): gross, minus contributions,
    Lohnsteuer and Soli, the net wage. A part that rounds to 0 is left out. `hourly`: the Mindestlohn per hour, named in
    the row of the gross wage. Every number is a model value („~“). `t`: the texts of the package in the language of
    `texts` (they format the number)."""
    parts = [("−", row[key], texts[key]) for key in ("contributions", "wage_tax", "soli") if round(row[key])]
    rows = (Row("", round(row["gross"]), 0, texts["gross"].format(hourly=t.number(hourly, 2, "€")), estimate=True,
                unit="€"),
            *(Row(op, round(value), 0, text, estimate=True, unit="€") for op, value, text in parts),
            Row("", round(row["net"]), 0, texts["net"], total=True, estimate=True, unit="€"))
    return example_payload(CalcExample("", rows, label=texts["label"]))


def share_sum(row: pd.Series, texts: dict, m2: float) -> dict:
    """Written sum of the share of one row of `wage_table`: net cold rent and Nebenkosten per m² (inputs, two
    decimals), × `m2`, the warm rent, ÷ the net wage, the share in whole percent. The results are model values („~“)."""
    rows = (Row("", round(row["cold_m2"], 2), 2, texts["cold"], unit="€"),
            Row("+", round(row["costs_m2"], 2), 2, texts["costs"], unit="€"),
            Row("×", m2, 0, texts["m2"]),
            Row("", round(row["warm_rent"]), 0, texts["warm"], total=True, estimate=True, unit="€"),
            Row("÷", round(row["net"]), 0, texts["net"], estimate=True, unit="€"),
            Row("", round(row["share"]), 0, texts["share"], total=True, estimate=True, unit="%"))
    return example_payload(CalcExample("", rows, label=texts["label"]))


def wage_view(table: pd.DataFrame, texts: dict, year: int, hourly: float, t: Texts) -> dict:
    """Payload of S1 (catalog WAGE_TEXTS), the wage bars of `year`: `title`, `lead` (what is left at the Mindestlohn
    and at the high wage, new contract), `info`, `source`, `link`, `explain`, `colour` and `ink` of the red block,
    `max_net` (the highest net wage: the full width of the plot), per contract in CONTRACTS order `id`, `name` (the
    switch), `rent` and `rent_text` and per person in PERSONS order `id`, `name`, `net`, `net_text`, `share_text`,
    `left_text` and `tip`; `aria_label` holds the title and every tip. `info` carries the two written sums of the
    Mindestlohn, new contract (`calc_examples`; `hourly`: its Mindestlohn per hour). Stops if `year` is missing, a
    share reaches 100 % (the block would leave its frame) or the warm rent of a contract differs between the persons
    (one block stands for all rows). `texts`: WAGE_TEXTS of one language, `t`: the texts of the package in the same
    language (they format the numbers)."""
    data = table[table["year"] == year].set_index(["contract", "person"])
    if data.empty:
        raise ValueError(f"wage view: the table has no row of {year}")
    ink = text_on(WAGE_COLOUR)
    if contrast(ink, WAGE_COLOUR) < MIN_CONTRAST:
        raise ValueError(f"wage view: the text on {WAGE_COLOUR} contrasts less than {MIN_CONTRAST}")
    contracts = []
    for contract in CONTRACTS:
        rows = []
        for person in PERSONS:
            r = data.loc[(contract, person)]
            if r["share"] >= 100:
                raise ValueError(f"wage view: {person} {contract} {year}: the warm rent is {r['share']:.1f} % of the "
                                 f"net wage, the block would leave its frame")
            rows.append({"id": person, "name": texts["names"][person], "net": float(r["net"]),
                         "net_text": texts["net_label"].format(net=_euro(r["net"], t)),
                         "share_text": _percent(r["share"], t),
                         "left_text": texts["left_label"].format(left=_euro(r["left"], t)),
                         "tip": texts["tip"].format(contract=texts["contracts"][contract], name=texts["names"][person],
                                                    warm_rent=_euro(r["warm_rent"], t), net=_euro(r["net"], t),
                                                    share=_percent(r["share"], t), left=_euro(r["left"], t))})
        rents = data.loc[contract, "warm_rent"]
        if rents.max() - rents.min() > 0.005:  # one block for all rows: the same flat, the same rent
            raise ValueError(f"wage view: {contract} {year}: the warm rent differs between the persons "
                             f"({rents.min():.2f} to {rents.max():.2f} €)")
        rent = float(rents.iloc[0])
        contracts.append({"id": contract, "name": texts["contracts"][contract], "rent": rent,
                          "rent_text": texts["rent_label"].format(rent=_euro(rent, t)), "rows": rows})
    lead = texts["lead"].format(left_low=_euro(data.loc[("new", "mindestlohn"), "left"], t),
                                left_high=_euro(data.loc[("new", "high"), "left"], t))
    tips = [r["tip"] for c in contracts for r in c["rows"]]
    example = data.loc[(CALC_CONTRACT, CALC_PERSON)]
    info = {**texts["info"], "calc_examples": [net_sum(example, texts["calc_net"], hourly, t),
                                               share_sum(example, texts["calc_share"], FLAT_M2)]}
    return {**{key: texts[key] for key in ("title", "source", "link", "explain")}, "info": info, "lead": lead,
            "colour": WAGE_COLOUR, "ink": ink, "max_net": float(data["net"].max()), "contracts": contracts,
            "aria_label": " ".join([texts["title"] + "."] + tips)}


# --- S2, tenants by income group ---

POSITIONS = (0.4, 0.5, 0.6, 0.7)  # the income placed inside its closed class (0.5 = midpoint, the main case)
OPEN_LOW_VALUES = (600, 750, 800)  # the equivalised income of the open lowest class (750 €, the main case)
MIN_SEGMENT = 9  # a segment narrower than this many points holds no number (docs/design.md, Charts: 4 px room)
MIN_CONTRAST = 4.5  # nor one whose text contrasts less with its fill (WCAG AA)


def group_table(ratios: pd.DataFrame,
                classes: tuple[tuple[float, float | None], ...] = CLASSES) -> pd.DataFrame:
    """One row per group of BREAKDOWN_IDS (index): `share` (percent of the weight of all tenants), the weighted
    `median` ratio, per class of `classes` (lower bound, upper bound or None) `class_0` … the percent of the group's
    weight from the lower bound to under the upper, and the unweighted `cases`. The weights count adults. Stops if a
    group has fewer than MIN_CASES cases."""
    total = ratios["weight"].sum()
    rows = {}
    for group in BREAKDOWN_IDS:
        g = ratios[ratios["group"] == group]
        if len(g) < MIN_CASES:
            raise ValueError(f"group table: {group} has {len(g)} cases, fewer than {MIN_CASES}")
        w = g["weight"]
        row = {"share": 100 * w.sum() / total, "median": weighted_median(g["ratio"], w)}
        for i, (low, high) in enumerate(classes):
            inside = g["ratio"] >= low
            if high is not None:
                inside &= g["ratio"] < high
            row[f"class_{i}"] = 100 * w[inside].sum() / w.sum()
        rows[group] = {**row, "cases": len(g)}
    return pd.DataFrame.from_dict(rows, orient="index").rename_axis("group")


def group_bounds(ratios: pd.DataFrame) -> tuple[float, float]:
    """Percent of the adult tenants surely under the first income limit and at most under it: the bounds of the
    income class × the `scale` of `burden_ratios` against the limit. Surely: the upper bound lies at or under the
    limit; at most: the lower bound lies under it."""
    low, high = ratios["income_low"].fillna(0) * ratios["scale"], ratios["income_high"] * ratios["scale"]
    w, limit = ratios["weight"], INCOME_LIMITS[0]
    sure, sure_not = high.le(limit), low.ge(limit)
    return (float(100 * w[sure].sum() / w.sum()),
            float(100 * (w[sure].sum() + w[~sure & ~sure_not].sum()) / w.sum()))


def low_income_facts(respondents: pd.DataFrame) -> dict:
    """The numbers behind title, lead and ⓘ of S2 (catalog LOW_INCOME_TEXTS); checks.py tests each statement.
    `main`: group_table at the class midpoints. `medians` and `shares`: the median and the share of the lowest group
    with the income at each of POSITIONS in its closed class (`position`) and with each of OPEN_LOW_VALUES for the
    open lowest class (`open_low`). `bounds`: group_bounds."""
    ratios = burden_ratios(respondents)
    main = group_table(ratios)
    at_main = main.loc[BREAKDOWN_IDS[0]]

    def lowest(frame: pd.DataFrame) -> pd.Series:
        return group_table(frame).loc[BREAKDOWN_IDS[0]]

    # the midpoint and the fixed value of the open class are the main case
    rows = {"position": {p: at_main if p == 0.5 else lowest(burden_ratios(respondents, income_position=p))
                         for p in POSITIONS},
            "open_low": {v: at_main if v == OPEN_LOW["income"]
                         else lowest(burden_ratios(respondents, open_low_income=v)) for v in OPEN_LOW_VALUES}}
    return {"main": main,
            **{name: {kind: {key: float(row[column]) for key, row in by.items()} for kind, by in rows.items()}
               for name, column in (("medians", "median"), ("shares", "share"))},
            "bounds": group_bounds(ratios)}


def segment_text(value: float, colour: str, t: Texts) -> str | None:
    """The number inside a segment („~58 %“), or None where it does not fit: under MIN_SEGMENT points or under
    MIN_CONTRAST with `text_on`. The tooltip carries it then."""
    fits = value >= MIN_SEGMENT and contrast(colour, text_on(colour)) >= MIN_CONTRAST
    return _percent(value, t) if fits else None


def bars_view(facts: dict, mikrozensus: dict[str, float], texts: dict, example: dict, t: Texts) -> dict:
    """Payload of S2 (catalog LOW_INCOME_TEXTS): `title`, `lead` with the share of the lowest group, `info` with the
    Unsicherheit filled (the lowest median of `facts["medians"]` rounded down, the highest and the values of
    `mikrozensus`, see `read_mikrozensus_2018`, rounded half up), `source`, `link`, `key` (per class id, name,
    colour), `bars` (per group of BREAKDOWN_IDS: id, name, `value` the median, `label`, `share`, `share_text`, `tip`,
    and `segments` per class: id, name, `value` percent of the group, `text` or None, `text_colour`, `colour`, `tip`)
    and `aria_label` (the title and every tooltip). `info` carries `example`, the written sum of the map indicator
    LIF_RENT_BURDEN_RATIO, as its only sum (`calc_examples`). Stops if `mikrozensus` holds other classes than the
    texts name. `texts`: LOW_INCOME_TEXTS of one language, `t`: the texts of the package in the same language (they
    format the numbers)."""
    if set(mikrozensus) != set(texts["mikrozensus"]):
        raise ValueError(f"bars view: Mikrozensus classes {sorted(mikrozensus)}, the texts name "
                         f"{sorted(texts['mikrozensus'])}")
    main = facts["main"]
    columns = [c for c in main.columns if c.startswith("class_")]
    if not len(texts["classes"]) == len(CLASS_COLOURS) == len(columns):
        raise ValueError(f"bars view: {len(texts['classes'])} class names, {len(CLASS_COLOURS)} class colours, "
                         f"{len(columns)} class columns")
    medians = [v for by in facts["medians"].values() for v in by.values()]
    compared = ", ".join(f"{name} {t.number(round_half_up(mikrozensus[key], 1), 0, '%')}"
                         for key, name in texts["mikrozensus"].items())
    info = {**texts["info"], "uncertainty": texts["info"]["uncertainty"].format(
        low=math.floor(min(medians)), high=int(round_half_up(max(medians), 1)), mikrozensus=compared),
        "calc_examples": [example]}
    key = [{"id": f"class_{i}", "name": name, "colour": CLASS_COLOURS[i]} for i, name in enumerate(texts["classes"])]
    bars = [_bar(group, main.loc[group], texts, key, t) for group in BREAKDOWN_IDS]
    title = texts["title"]
    tips = [tip for bar in bars for tip in [bar["tip"], *(s["tip"] for s in bar["segments"])]]
    return {"title": title, "lead": texts["lead"].format(share=_percent(float(main.loc[BREAKDOWN_IDS[0], "share"]), t)),
            "info": info, "source": texts["source"], "link": texts["link"], "key": key, "bars": bars,
            "aria_label": " ".join([title + "."] + tips)}


def _bar(group: str, row: pd.Series, texts: dict, key: list[dict], t: Texts) -> dict:
    """One bar of S2: the median label and the share of the group, the segments of the classes in `key`."""
    name, median, share = texts["groups"][group], float(row["median"]), float(row["share"])
    segments = []
    for k in key:
        value = float(row[k["id"]])
        segments.append({"id": k["id"], "name": k["name"], "value": value, "text": segment_text(value, k["colour"], t),
                         "text_colour": text_on(k["colour"]), "colour": k["colour"],
                         "tip": texts["tip_segment"].format(group=name, value=_percent(value, t), name=k["name"])})
    return {"id": group, "name": name, "value": median, "label": texts["median_label"].format(median=_percent(median, t)),
            "share": share, "share_text": _percent(share, t),
            "tip": texts["tip_bar"].format(group=name, share=_percent(share, t), median=_percent(median, t)),
            "segments": segments}
