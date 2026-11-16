"""Checks of the view „Trend“. Pure module."""
from __future__ import annotations

from pipeline.shared.core.checks import FAIL, OK, Check, check_examples, check_same_values, check_tolerance
from pipeline.use_cases.ownership_history import catalog
from pipeline.use_cases.ownership_history.catalog import CHARTS


def check_class_sum(name: str, values: dict[str, int], tolerance: int = 10) -> Check:
    """The classes add up to the total; the Zensus anonymises every cell on its own."""
    parts = sum(v for k, v in values.items() if k != "total")
    return check_tolerance(f"Ownership 2011–2022: classes add up to the total, {name}", parts, values["total"],
                           absolute=tolerance)


def check_size_sums(name: str, values: dict[str, dict[str, int]], tolerance: int) -> Check:
    """The size classes of each ownership class add up to its total; the Zensus anonymises every cell on its own."""
    off = {k: sum(n for s, n in v.items() if s != "total") - v["total"] for k, v in values.items()}
    bad = [f"{k}: {d:+d}" for k, d in off.items() if abs(d) > tolerance]
    return Check(f"Ownership 2011–2022: size classes add up to the total, {name}", FAIL if bad else OK,
                 "; ".join(bad) or f"largest difference {max(abs(d) for d in off.values())}, allowed {tolerance}")


def check_history_headings(facts: dict, charts: dict) -> list[Check]:
    """Every statement in the headings, lead lines and tooltips of the four charts must still hold
    (README). Each rule names the phrase it guards and where it stands;
    a text that no longer holds the phrase fails too, so the texts cannot change without their check."""
    factor, share = facts["company_factor"], facts["share_before_2010"]
    grew = facts["company_growth"] > 0  # a ratio of two losses can look like growth
    b22, d22 = facts["company_building_share_2022"], facts["company_share_2022"]
    large11, large22 = facts["company_large_share_2011"], facts["company_large_share_2022"]
    bf, growth = facts["company_building_factor"], facts["large_growth_share"]
    # chart „houses“ shows both company classes: each must beat every other group
    per, other = facts["smallest_company_dwellings_per_building_2022"], facts["largest_other_dwellings_per_building_2022"]
    rules = [
        (f"Heading '{catalog.HOUSES_TITLE}'", "houses", "title", catalog.HOUSES_TITLE, per > other,
         f"dwellings per building 2022: smaller company class {per:.1f}, largest other group {other:.1f}; "
         f"the company class must be higher"),
        (f"Lead line '{catalog.HOUSES_LEAD_BUILDINGS}'", "houses", "lead", catalog.HOUSES_LEAD_BUILDINGS,
         round(100 * b22) == 8,
         f"building share 2022 = {100 * b22:.2f} %, must round to 8"),
        (f"Lead line '{catalog.HOUSES_LEAD_DWELLINGS}'", "houses", "lead", catalog.HOUSES_LEAD_DWELLINGS,
         round(100 * d22) == 19,
         f"dwelling share 2022 = {100 * d22:.2f} %, must round to 19"),
        (f"Heading '{catalog.ARROWS_TITLE}'", "arrows", "title", catalog.ARROWS_TITLE,
         1.95 <= factor <= 2.05, f"company dwellings 2022/2011 = {factor:.3f}, allowed 1.95 to 2.05"),
        (f"Lead line '{catalog.ARROWS_LEAD}'", "arrows", "lead", catalog.ARROWS_LEAD, 1.45 <= bf <= 1.55,
         f"company buildings 2022/2011 = {bf:.3f}, allowed 1.45 to 1.55"),
        (f"Heading '{catalog.SIZES_TITLE}'", "sizes", "title", catalog.SIZES_TITLE,
         0.30 <= large22 <= 0.36, f"company share in buildings with 13+ dwellings 2022 = {100 * large22:.1f} %, "
                                  f"allowed 30 to 36 %"),
        (f"Lead line '{catalog.SIZES_LEAD}'", "sizes", "lead", catalog.SIZES_LEAD, 0.15 <= large11 <= 0.18,
         f"company share in buildings with 13+ dwellings 2011 = {100 * large11:.1f} %, allowed 15 to 18 %"),
        (f"Tooltip '{catalog.SIZES_TIP}'", "sizes", "tip_large", catalog.SIZES_TIP, 0.62 <= growth <= 0.70,
         f"{facts['company_large_growth']} of {facts['company_dwelling_growth']} additional company dwellings in "
         f"buildings with 13+ dwellings ({100 * growth:.1f} %), allowed 62 to 70 %"),
        (f"Heading '{catalog.DECADES_TITLE}'", "decades", "title", catalog.DECADES_TITLE, grew and share >= 0.70,
         f"{facts['company_growth_before_2010']} of {facts['company_growth']} additional company buildings "
         f"built before 2010 ({100 * share:.0f} %), at least 70 %"),
        (f"Lead line '{catalog.DECADES_LEAD}'", "decades", "lead", catalog.DECADES_LEAD, grew and 0.72 <= share <= 0.78,
         f"share built before 2010 = {100 * share:.1f} %, allowed 72 to 78 %"),
    ]
    out = []
    for name, chart, field, phrase, holds, text in rules:
        if phrase not in charts[chart][field]:
            out.append(Check(name, FAIL, f"the {field} of chart '{chart}' no longer says '{phrase}'; adjust text and check together"))
        else:
            out.append(Check(name, OK if holds else FAIL, text))
    return out


def check_condo_rented(use: dict[int, dict[str, int]], about: str) -> Check:
    """„meist vermietet“ in the tooltip of the WEG: in every year more than half of the WEG dwellings are rented
    (table 4000W-2002, README)."""
    name = f"Tooltip WEG '{catalog.CONDO_RENTED}'"
    if catalog.CONDO_RENTED not in about:
        return Check(name, FAIL, f"the tooltip of the WEG no longer says '{catalog.CONDO_RENTED}'; "
                                 "adjust text and check together")
    shares = {y: v["rented"] / v["total"] for y, v in sorted(use.items())}
    return Check(name, OK if all(s > 0.5 for s in shares.values()) else FAIL,
                 "rented WEG dwellings: " + ", ".join(f"{y} {100 * s:.1f} %" for y, s in shares.items())
                 + "; more than 50 % in every year")


def history_checks(history: dict, buildings: dict, b_size: dict, d_size: dict, table: dict[str, int],
                   facts: dict, texts: dict[str, str], examples: list[dict]) -> list[Check]:
    """history: 4000W-1011; buildings: 3000G-2001 per year; b_size, d_size: 3000G-2007, 4000W-2013; table: 4000W-2002;
    texts: source key -> text of the sources of the examples in the tooltips."""
    out = []
    for y in sorted(history):
        out += [check_same_values(f"Ownership 2011–2022: 4000W-2013 equals 4000W-1011, {y}",
                                  {k: v["total"] for k, v in d_size[y].items()}, history[y]),
                check_same_values(f"Ownership 2011–2022: 3000G-2007 equals 3000G-2001, {y}",
                                  {k: v["total"] for k, v in b_size[y].items()},
                                  {k: v["total"] for k, v in buildings[y].items()}),
                check_size_sums(f"buildings {y}", b_size[y], tolerance=10),
                check_size_sums(f"dwellings {y}", d_size[y], tolerance=15)]
    out.append(check_same_values("Ownership 2011–2022: 4000W-1011 equals 4000W-2002 in 2022", history[2022], table))
    out += [check_class_sum(f"dwellings {y}", history[y]) for y in sorted(history)]
    out += [check_class_sum(f"buildings {y}", {k: v["total"] for k, v in buildings[y].items()})
            for y in sorted(buildings)]
    return out + check_history_headings(facts, CHARTS) + [
        check_examples("Ownership 2011–2022: examples in the tooltips stand in their sources", texts, examples)]
