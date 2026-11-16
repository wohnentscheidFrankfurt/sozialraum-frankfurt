import re
from dataclasses import replace

import pandas as pd
import pytest

from pipeline.shared.core import palette
from pipeline.shared.core.colours import contrast, text_on
from pipeline.use_cases.new_construction.catalog import RENT_FROM, RENT_TO, SURVEY_DATES
from pipeline.use_cases.rent_burden.catalog import (CLASS_COLOURS, CLASSES, CONTRACTS, FLAT_M2, LOW_INCOME_TEXTS,
                                                    PERSONS, WAGE_TEXTS)
from pipeline.use_cases.rent_burden.model import (MIN_SEGMENT, OPEN_LOW_VALUES, POSITIONS, bars_view, contributions,
                                                  full_time, group_bounds, group_table, income_tax,
                                                  net, segment_text, tariff, wage_facts, wage_table, wage_view)
from pipeline.use_cases.rent_burden.sources import MIKROZENSUS_2018, MINDESTLOHN, WAGE_RULES
from pipeline.use_cases.survey.model import BREAKDOWN_IDS, MIN_CASES, OPEN_LOW, burden_ratios


def test_full_time_is_forty_hours_over_twelve_months():
    assert full_time(12.82) == pytest.approx(2222.13, abs=0.005)


def test_net_of_the_three_persons_2025():
    """Mindestlohn, median and pension ceiling; the values research/scripts/net_wage.py prints."""
    rules = WAGE_RULES[2025]
    assert round(net(2222.13, rules), 2) == 1605.01
    assert round(net(5074.10, rules), 2) == 3163.47
    assert round(net(8050.00, rules), 2) == 4702.50


def test_contributions_stop_at_the_ceilings():
    rules = WAGE_RULES[2025]
    assert contributions(rules.ceiling_rv, rules) == pytest.approx(1456.92, abs=0.005)
    assert contributions(20000, rules) == contributions(rules.ceiling_rv, rules)
    # between the two ceilings only the pension and unemployment part still grows
    low = contributions(rules.ceiling_kv, rules)
    assert contributions(rules.ceiling_kv + 1000, rules) - low == pytest.approx(1000 * (rules.rv + rules.av))


def test_soli_is_zero_below_the_freigrenze_and_mild_above():
    rules = WAGE_RULES[2025]
    assert income_tax(5074.10, rules) == (817.16, 0.0)
    tax, soli = income_tax(8050.00, rules)
    assert (tax, soli) == (1866.33, 24.25)
    assert soli < 0.055 * tax  # the Milderungszone: less than the full 5.5 %


def test_tariff_is_zero_up_to_the_grundfreibetrag_and_rises_above():
    t = WAGE_RULES[2025].tariff
    assert tariff(t.gfb, t) == 0.0
    assert 0 < tariff(t.gfb + 1000, t) < tariff(t.z1, t) < tariff(t.z2, t) < tariff(t.z2 + 1000, t)


def test_income_tax_of_a_negative_taxable_income_is_zero():
    assert income_tax(100, WAGE_RULES[2025]) == (0.0, 0.0)


def test_a_tariff_constant_moves_the_wage_tax():
    rules = WAGE_RULES[2021]
    off = replace(rules, tariff=replace(rules.tariff, c3=rules.tariff.c3 + 1))
    assert income_tax(7100.00, off)[0] != income_tax(7100.00, rules)[0]


# --- S1, the wage example ---

YEARS = tuple(SURVEY_DATES)


def table_of(inputs, nebenkosten=None):
    return wage_table(inputs["rents"], nebenkosten or inputs["ba"], inputs["wages"], WAGE_RULES, MINDESTLOHN, YEARS,
                      FLAT_M2)


def cell(table, person, contract, year):
    return table[(table["person"] == person) & (table["contract"] == contract) & (table["year"] == year)].iloc[0]


def test_wage_table_reproduces_the_finding(table):
    """research/results/warm_rent_wage.txt, main case."""
    assert len(table) == len(YEARS) * len(PERSONS) * len(CONTRACTS)
    assert {"year", "person", "contract", "warm_rent", "gross", "net", "share", "left", "left_real"} <= set(table)
    shares = {(p, c, y): round(float(cell(table, p, c, y)["share"]), 1)
              for p, c in (("mindestlohn", "new"), ("median", "new"), ("high", "new"), ("mindestlohn", "old"))
              for y in (RENT_FROM, RENT_TO)}
    assert shares == {("mindestlohn", "new", 2017): 65.6, ("mindestlohn", "new", 2025): 61.9,
                      ("median", "new", 2017): 31.3, ("median", "new", 2025): 31.4,
                      ("high", "new", 2017): 20.7, ("high", "new", 2025): 21.1,
                      ("mindestlohn", "old", 2017): 58.1, ("mindestlohn", "old", 2025): 48.7}
    median = cell(table, "median", "new", 2025)
    assert round(float(median["left_real"])) == 1736
    assert (round(float(median["warm_rent"])), round(float(median["net"])), round(float(median["left"]))) == (
        993, 3163, 2170)
    assert float(cell(table, "high", "old", 2025)["gross"]) == WAGE_RULES[2025].ceiling_rv
    assert float(cell(table, "mindestlohn", "old", 2025)["gross"]) == pytest.approx(full_time(MINDESTLOHN[2025]))


def test_wage_table_keeps_the_parts_of_the_calculation(table):
    """The written sums of the ⓘ: net cold rent and Nebenkosten per m², contributions, Lohnsteuer and Soli per month."""
    low = cell(table, "mindestlohn", "new", 2025)
    assert (float(low["cold_m2"]), round(float(low["costs_m2"]), 2)) == (13.95, 4.11)
    assert (round(float(low["contributions"]), 2), float(low["wage_tax"]), float(low["soli"])) == (478.87, 138.25, 0.0)
    assert float(cell(table, "high", "new", 2025)["soli"]) == 24.25
    parts = table["gross"] - table["contributions"] - table["wage_tax"] - table["soli"]
    assert (parts - table["net"]).abs().max() < 1e-9
    assert ((table["cold_m2"] + table["costs_m2"]) * FLAT_M2 - table["warm_rent"]).abs().max() < 1e-9


def test_wage_table_stops_on_a_year_without_nebenkosten(inputs):
    short = {y: v for y, v in inputs["ba"].items() if y != 2023}
    with pytest.raises(ValueError, match="2023.*Nebenkosten|Nebenkosten.*2023"):
        table_of(inputs, short)


def test_wage_table_stops_on_a_survey_year_without_rent(inputs):
    rents = inputs["rents"].assign(new=inputs["rents"]["new"].where(inputs["rents"]["year"] != 2021))
    with pytest.raises(ValueError, match="2021.*rent|rent.*2021"):
        wage_table(rents, inputs["ba"], inputs["wages"], WAGE_RULES, MINDESTLOHN, YEARS, FLAT_M2)


def test_wage_table_stops_if_the_prices_of_the_first_year_are_not_100(inputs):
    """left_real counts in euros of the first year („Preise von 2017“)."""
    rents = inputs["rents"].assign(prices_index=inputs["rents"]["prices_index"] * 1.01)
    with pytest.raises(ValueError, match="2017"):
        wage_table(rents, inputs["ba"], inputs["wages"], WAGE_RULES, MINDESTLOHN, YEARS, FLAT_M2)


def test_facts_count_the_latest_year(facts):
    assert facts["year"] == RENT_TO
    assert tuple(round(v, 2) for v in facts["factor"]) == (2.93, 2.93)
    assert not {"change", "base", "last"} & set(facts)


def test_facts_sensitivity_of_the_mietspiegel_nebenkosten(facts):
    """2025 (Mietspiegel 2026): the share with the Mietspiegel Nebenkosten lies 1.39 to 4.09 points lower; the
    Mindestlohn has the largest gap."""
    assert tuple(round(v, 2) for v in facts["sensitivity"]) == (1.39, 4.09)
    assert max(facts["sensitivity_persons"], key=lambda p: facts["sensitivity_persons"][p][1]) == "mindestlohn"
    assert facts["sensitivity_persons"]["median"][1] < facts["sensitivity_persons"]["mindestlohn"][0]


def test_facts_stop_if_the_two_tables_hold_other_cells(table, mietspiegel_table):
    drop = (mietspiegel_table["year"] == RENT_TO) & (mietspiegel_table["person"] == "median")
    with pytest.raises(ValueError, match="cells"):
        wage_facts(table, mietspiegel_table[~drop], RENT_TO)


def test_facts_stop_without_the_year(table, mietspiegel_table):
    with pytest.raises(ValueError, match=str(RENT_TO)):
        wage_facts(table[table["year"] != RENT_TO], mietspiegel_table[mietspiegel_table["year"] != RENT_TO], RENT_TO)


def euros(text):
    return [int(n.replace(".", "")) for n in re.findall(r"~(\d+(?:\.\d{3})*) €", text)]


def latest(table, person, contract):
    return cell(table, person, contract, RENT_TO)


def test_view_has_one_entry_per_contract_and_one_row_per_person(table):
    v = wage_view(table, WAGE_TEXTS, RENT_TO, MINDESTLOHN[RENT_TO])
    assert {k: v[k] for k in ("title", "source", "link", "explain")} == {
        k: WAGE_TEXTS[k] for k in ("title", "source", "link", "explain")}
    assert [c["id"] for c in v["contracts"]] == list(CONTRACTS)
    assert [c["name"] for c in v["contracts"]] == [WAGE_TEXTS["contracts"][c] for c in CONTRACTS]
    assert v["max_net"] == pytest.approx(4702.50, abs=0.01)  # the high wage fills the plot
    assert v["colour"] == palette.PUBLIC and contrast(v["ink"], v["colour"]) >= 4.5
    assert [c["rent"] for c in v["contracts"]] == [pytest.approx(993.07, abs=0.01), pytest.approx(781.87, abs=0.01)]
    for c in v["contracts"]:
        assert [r["id"] for r in c["rows"]] == list(PERSONS)
        assert [r["name"] for r in c["rows"]] == [WAGE_TEXTS["names"][p] for p in PERSONS]
        assert [r["net"] for r in c["rows"]] == [pytest.approx(float(latest(table, p, c["id"])["net"]))
                                                 for p in PERSONS]


def test_view_texts_are_the_table_values_of_the_latest_year(table):
    v = wage_view(table, WAGE_TEXTS, RENT_TO, MINDESTLOHN[RENT_TO])
    shares = {c["id"]: [r["share_text"] for r in c["rows"]] for c in v["contracts"]}
    assert shares == {"new": ["~62 %", "~31 %", "~21 %"], "old": ["~49 %", "~25 %", "~17 %"]}
    for c in v["contracts"]:
        rent = round(float(latest(table, PERSONS[0], c["id"])["warm_rent"]))
        assert euros(c["rent_text"]) == [rent]
        assert c["rent_text"] == WAGE_TEXTS["rent_label"].format(rent=f"~{rent} €")
        for r in c["rows"]:
            row = latest(table, r["id"], c["id"])
            assert euros(r["net_text"]) == [round(float(row["net"]))]
            assert euros(r["left_text"]) == [round(float(row["left"]))]
            assert r["net_text"].startswith(WAGE_TEXTS["net_label"].split("{")[0])
            assert r["left_text"].startswith(WAGE_TEXTS["left_label"].split("{")[0])
    assert "~612 €" in v["lead"] and "~3.709 €" in v["lead"] and "{" not in v["lead"]
    assert v["lead"].index("~612 €") < v["lead"].index("~3.709 €")  # Mindestlohn first, then the high wage


def test_view_tips_name_contract_person_and_numbers(table):
    v = wage_view(table, WAGE_TEXTS, RENT_TO, MINDESTLOHN[RENT_TO])
    tips = []
    for c in v["contracts"]:
        for r in c["rows"]:
            row = latest(table, r["id"], c["id"])
            assert c["name"] in r["tip"] and r["name"] in r["tip"] and r["share_text"] in r["tip"]
            assert euros(r["tip"]) == [round(float(row[k])) for k in ("warm_rent", "net", "left")]
            tips.append(r["tip"])
    assert len(tips) == len(CONTRACTS) * len(PERSONS)
    assert v["aria_label"].startswith(WAGE_TEXTS["title"]) and all(t in v["aria_label"] for t in tips)


def test_view_stops_at_a_share_of_100(table):
    """The red block would leave its frame: the rent reaches the wage."""
    full = table.copy()
    full.loc[(full["year"] == RENT_TO) & (full["person"] == "mindestlohn") & (full["contract"] == "old"), "share"] = 100.0
    with pytest.raises(ValueError, match="mindestlohn.*old"):
        wage_view(full, WAGE_TEXTS, RENT_TO, MINDESTLOHN[RENT_TO])


def test_view_stops_if_the_rent_differs_between_persons(table):
    """One block for all rows: the same flat costs every person the same rent."""
    other = table.copy()
    other.loc[(other["year"] == RENT_TO) & (other["person"] == "high") & (other["contract"] == "new"), "warm_rent"] += 1
    with pytest.raises(ValueError, match="new.*rent"):
        wage_view(other, WAGE_TEXTS, RENT_TO, MINDESTLOHN[RENT_TO])


def rows_of(example):
    return [(r["op"], r["number"], r["unit"], r["estimate"], r["total"]) for r in example["rows"]]


def test_view_info_has_the_two_sums_of_the_mindestlohn(table):
    """docs/texts.md, Written sums: the net wage and the share at the Mindestlohn, new contract, of the year shown."""
    v = wage_view(table, WAGE_TEXTS, RENT_TO, MINDESTLOHN[RENT_TO])
    assert {k: v["info"][k] for k in WAGE_TEXTS["info"]} == WAGE_TEXTS["info"]
    net_sum, share_sum = v["info"]["calc_examples"]
    t = WAGE_TEXTS["calc_net"], WAGE_TEXTS["calc_share"]
    assert (net_sum["label"], share_sum["label"]) == (t[0]["label"], t[1]["label"])
    # the Soli of the Mindestlohn rounds to 0: its row is left out
    assert rows_of(net_sum) == [("", 2222, "€", True, False), ("−", 479, "€", True, False), ("−", 138, "€", True, False),
                                ("", 1605, "€", True, True)]
    assert rows_of(share_sum) == [("", 13.95, "€", False, False), ("+", 4.11, "€", False, False),
                                  ("×", 55, "", False, False), ("", 993, "€", True, True),
                                  ("÷", 1605, "€", True, False), ("", 62, "%", True, True)]
    assert [r["decimals"] for r in share_sum["rows"]] == [2, 2, 0, 0, 0, 0]
    assert "12,82 €" in net_sum["rows"][0]["text"] and "{" not in net_sum["rows"][0]["text"]
    texts = [r["text"] for r in net_sum["rows"] + share_sum["rows"]]
    assert all(texts) and texts[6] == t[1]["m2"]


def test_view_sum_names_the_soli_where_it_counts(table):
    """The high wage pays Soli: as the example its sum would have five rows."""
    from pipeline.use_cases.rent_burden.model import net_sum
    rows = rows_of(net_sum(cell(table, "high", "new", RENT_TO), WAGE_TEXTS["calc_net"], 0.0))
    assert [r[:2] for r in rows] == [("", 8050), ("−", 1457), ("−", 1866), ("−", 24), ("", 4703)]


def test_view_stops_without_the_year(table):
    with pytest.raises(ValueError, match="2030"):
        wage_view(table, WAGE_TEXTS, 2030, MINDESTLOHN[RENT_TO])


# --- S2, tenants by income group ---

EXAMPLE = {"area": "einer Person", "label": "", "rows": [{"op": "", "number": 1, "decimals": 0, "text": "x",
                                                          "total": False, "estimate": False, "unit": "€"}]}


def bars_of(low_facts, mikrozensus=MIKROZENSUS_2018):
    return bars_view(low_facts, mikrozensus, LOW_INCOME_TEXTS, EXAMPLE)


def test_group_table_reproduces_the_finding(respondents):
    """research/2026-11-01-warm-rent-and-income.md, S2: tenants under 2,000 €, pooled, at the class midpoints."""
    table = group_table(burden_ratios(respondents), CLASSES)
    assert list(table.index) == list(BREAKDOWN_IDS)
    assert list(table.columns) == ["share", "median", "class_0", "class_1", "class_2", "class_3", "cases"]
    assert {g: tuple(round(float(v), 1) for v in row[:-1]) for g, row in table.iterrows()} == {
        "LIF_RENT_BURDEN_INCOME_LOW": (16.7, 53.3, 3.6, 16.4, 22.4, 57.6),
        "LIF_RENT_BURDEN_INCOME_MID": (23.6, 36.1, 27.7, 38.3, 18.8, 15.2),
        "LIF_RENT_BURDEN_INCOME_HIGH": (59.7, 23.9, 73.0, 20.7, 4.5, 1.8)}
    assert table["share"].sum() == pytest.approx(100)
    assert (table["cases"] >= MIN_CASES).all()


def test_group_table_stops_on_a_group_under_min_cases(respondents):
    ratios = burden_ratios(respondents)
    low = ratios[ratios["group"] == BREAKDOWN_IDS[0]]
    few = pd.concat([ratios[ratios["group"] != BREAKDOWN_IDS[0]], low.head(MIN_CASES - 1)])
    with pytest.raises(ValueError, match="LIF_RENT_BURDEN_INCOME_LOW"):
        group_table(few, CLASSES)


def test_bounds(respondents, low_facts):
    """By the class bounds × scale: surely under 2,000 € and at most, percent of the adult tenants."""
    assert tuple(round(v, 1) for v in group_bounds(burden_ratios(respondents))) == (14.2, 28.1)
    assert low_facts["bounds"] == group_bounds(burden_ratios(respondents))


def test_medians_of_the_sensitivities(low_facts):
    """The position of the income in its closed class and the value of the open lowest class move the median of the
    lowest group; the midpoint and 750 € are the main case."""
    medians = low_facts["medians"]
    assert tuple(medians["position"]) == POSITIONS and tuple(medians["open_low"]) == OPEN_LOW_VALUES
    assert [round(v, 1) for v in medians["position"].values()] == [55.4, 53.3, 51.6, 48.5]
    assert [round(v, 1) for v in medians["open_low"].values()] == [55.0, 53.3, 51.7]
    main = float(low_facts["main"].loc[BREAKDOWN_IDS[0], "median"])
    assert medians["position"][0.5] == medians["open_low"][OPEN_LOW["income"]] == pytest.approx(main)


def test_shares_of_the_sensitivities(low_facts):
    """The same sensitivities move the share of the lowest group a little; the main case is the share of the lead."""
    shares = low_facts["shares"]
    assert {k: tuple(v) for k, v in shares.items()} == {k: tuple(v) for k, v in low_facts["medians"].items()}
    assert [round(v, 1) for v in shares["position"].values()] == [16.7, 16.7, 16.2, 16.2]
    assert [round(v, 1) for v in shares["open_low"].values()] == [17.0, 16.7, 16.2]
    main = float(low_facts["main"].loc[BREAKDOWN_IDS[0], "share"])
    assert shares["position"][0.5] == shares["open_low"][OPEN_LOW["income"]] == pytest.approx(main)


def test_segments_add_up_to_100(low_facts):
    bars = bars_of(low_facts)["bars"]
    assert [b["id"] for b in bars] == list(BREAKDOWN_IDS)
    for bar in bars:
        assert [s["id"] for s in bar["segments"]] == [f"class_{i}" for i in range(len(CLASSES))]
        assert sum(s["value"] for s in bar["segments"]) == pytest.approx(100)
        assert all(s["value"] == pytest.approx(float(low_facts["main"].loc[bar["id"], s["id"]]))
                   for s in bar["segments"])


def test_a_segment_text_only_where_it_fits(low_facts):
    """docs/design.md, Charts: a number stands inside a bar only at a contrast of at least 4.5:1 and with room."""
    assert segment_text(50, "#777777") is None  # 4.48:1 with white, less with dark text
    assert segment_text(MIN_SEGMENT - 0.1, palette.COOP) is None
    assert segment_text(MIN_SEGMENT, palette.COOP) == "~9 %"
    for bar in bars_of(low_facts)["bars"]:
        for s in bar["segments"]:
            assert s["text_colour"] == text_on(s["colour"])
            fits = s["value"] >= MIN_SEGMENT and contrast(s["colour"], s["text_colour"]) >= 4.5
            assert (s["text"] is not None) == fits
            assert s["text"] is None or s["text"] == f"~{round(s['value'])} %"
    low = bars_of(low_facts)["bars"][0]["segments"]
    assert (low[0]["text"], low[3]["text"]) == (None, "~58 %")


def test_bars_view_fills_lead_and_uncertainty_from_the_facts(low_facts):
    v = bars_of(low_facts)
    assert {k: v[k] for k in ("title", "source", "link")} == {k: LOW_INCOME_TEXTS[k] for k in ("title", "source", "link")}
    assert "~17 %" in v["lead"] and "{" not in v["lead"]
    info = v["info"]
    assert list(info) == ["source", "as_of", "calc", "rule", "uncertainty", "calc_examples"]
    assert info["calc_examples"] == [EXAMPLE]  # the sum of the map indicator LIF_RENT_BURDEN_RATIO, as it comes
    assert {k: info[k] for k in ("source", "as_of", "calc", "rule")} == {
        k: LOW_INCOME_TEXTS["info"][k] for k in ("source", "as_of", "calc", "rule")}
    assert "48 und 55 %" in info["uncertainty"] and "{" not in info["uncertainty"]
    assert re.findall(r"(\d+) %", info["uncertainty"])[-2:] == ["60", "34"]  # Mikrozensus 60.1 and 33.7
    other = {**low_facts, "medians": {"position": {0.4: 56.0, 0.7: 47.9}, "open_low": {600: 50.0}}}
    assert "47 und 56 %" in bars_of(other)["info"]["uncertainty"]
    # the lower end rounds down, the upper end half up (the real 55.4 stays 55)
    for highest, text in ((55.6, "47 und 56 %"), (55.5, "47 und 56 %"), (55.4, "47 und 55 %")):
        other = {**low_facts, "medians": {"position": {0.4: highest, 0.7: 47.9}, "open_low": {600: 50.0}}}
        assert text in bars_of(other)["info"]["uncertainty"], highest
    assert "61 %" in bars_of(low_facts, {**MIKROZENSUS_2018, "under 900": 60.5})["info"]["uncertainty"]


def test_bars_view_labels_and_tips_carry_the_table_values(low_facts):
    v = bars_of(low_facts)
    main = low_facts["main"]
    assert [b["name"] for b in v["bars"]] == [LOW_INCOME_TEXTS["groups"][g] for g in BREAKDOWN_IDS]
    low = v["bars"][0]
    assert (low["value"], low["share"]) == (float(main.loc[BREAKDOWN_IDS[0], "median"]),
                                            float(main.loc[BREAKDOWN_IDS[0], "share"]))
    assert (low["label"], low["share_text"]) == ("Median ~53 %", "~17 %")
    assert low["tip"].startswith(low["name"]) and "~17 %" in low["tip"] and "~53 %" in low["tip"]
    top = low["segments"][3]
    assert top["tip"].startswith(low["name"]) and "~58 %" in top["tip"]
    assert LOW_INCOME_TEXTS["classes"][3] in top["tip"]
    assert [b["label"] for b in v["bars"][1:]] == ["Median ~36 %", "Median ~24 %"]
    assert [(k["id"], k["name"], k["colour"]) for k in v["key"]] == [
        (f"class_{i}", LOW_INCOME_TEXTS["classes"][i], CLASS_COLOURS[i]) for i in range(len(CLASSES))]
    assert v["aria_label"].startswith(v["title"])
    assert all(t in v["aria_label"] for b in v["bars"] for t in [b["tip"], *(s["tip"] for s in b["segments"])])


def test_bars_view_stops_if_classes_names_and_colours_differ_in_number(low_facts):
    texts = {**LOW_INCOME_TEXTS, "classes": LOW_INCOME_TEXTS["classes"][:3]}
    with pytest.raises(ValueError, match="3 class names, 4 class colours, 4 class columns"):
        bars_view(low_facts, MIKROZENSUS_2018, texts, EXAMPLE)
    short = {**low_facts, "main": low_facts["main"].drop(columns="class_3")}
    with pytest.raises(ValueError, match="4 class names, 4 class colours, 3 class columns"):
        bars_view(short, MIKROZENSUS_2018, LOW_INCOME_TEXTS, EXAMPLE)


def test_bars_view_stops_on_other_mikrozensus_classes(low_facts):
    with pytest.raises(ValueError, match="Mikrozensus"):
        bars_of(low_facts, {"under 900": 60.1})
