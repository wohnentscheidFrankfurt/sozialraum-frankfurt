"""The check report: one table of all check results and the sections on plausibility (docs/architecture.md, Checks). Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.checks import RANK, Check, thousands

COVERAGE_COLUMNS = ("COV_HOU_RENTERS", "COV_HOU_RENT", "COV_HOU_VACANT_MARKET", "COV_HOU_VACANT_ALL")


def quarters_without_ownership(quarters: pd.DataFrame, limit: float = 80) -> list[str]:
    s = quarters[quarters["COV_OWN"] < limit].sort_values("COV_OWN")
    return [f"- {r['name']} ({r['id']}): {100 - r['COV_OWN']:.0f} % without ownership type" for _, r in s.iterrows()]


def plausibility(districts: pd.DataFrame, indicators: list[tuple[str, str]]) -> str:
    """indicators: (ID, title) of the numeric criteria on district level, in catalog order."""
    parts = ["## Plausibility (5 highest and 5 lowest districts)\n"]
    large = districts[districts["small"] == 0]
    for id_, title in indicators:
        if id_ not in large:
            continue
        s = large[["id", "name", id_]].dropna().sort_values(id_)
        high = ", ".join(f"{r['name']} ({r['id']}) {r[id_]:.1f}" for _, r in s.tail(5)[::-1].iterrows())
        low = ", ".join(f"{r['name']} ({r['id']}) {r[id_]:.1f}" for _, r in s.head(5).iterrows())
        parts.append(f"- **{title}** – highest: {high}; lowest: {low}")
    return "\n".join(parts) + "\n"


def low_coverage(districts: pd.DataFrame) -> list[str]:
    return [f"- {r['name']} ({r['id']}): {c} {r[c]:.0f} %" for _, r in districts.iterrows()
            for c in COVERAGE_COLUMNS if pd.notna(r[c]) and r[c] < 50]


def report_sections(unassigned: float, total: int, filled: float, filled_cells: int, districts: pd.DataFrame,
                    quarters: pd.DataFrame, indicators: list[tuple[str, str]]) -> list[str]:
    small = districts[districts["small"] == 1]
    return ["## Unassigned dwellings\n",
            f"- {thousands(round(unassigned))} of {thousands(total)} dwellings ({100 * round(unassigned) / total:.1f} %) have no "
            "ownership type, also not from Zensus 2011; the shares OWN_* refer to all dwellings; the four other groups "
            "take the unassigned ones in proportion.",
            f"- Filled from Zensus 2011: {thousands(round(filled))} dwellings in {filled_cells} cells without ownership "
            "type 2022.", "",
            "Stadtteile with less than 80 % assigned dwellings:",
            "\n".join(quarters_without_ownership(quarters)) or "- none", "",
            "## Small districts (under 1,000 residents)\n",
            "\n".join(f"- {r['name']} ({r['id']}): grid {r['POP']}, monitoring {r['POP_MONITORING']}" for _, r in small.iterrows())
            or "- none", "",
            "## Low coverage (under 50 % of the base has a value)\n",
            "\n".join(low_coverage(districts)) or "- none", "", plausibility(districts, indicators)]


def report(checks: list[Check], sections: list[str], date: str) -> str:
    rows = [f"# Check report {date}\n", "| Status | Check | Result |", "|---|---|---|"]
    for c in sorted(checks, key=lambda c: RANK[c.status]):
        rows.append(f"| {c.status} | {c.name} | {c.text.replace('|', '/')} |")
    return "\n".join(rows) + "\n\n" + "\n".join(sections)
