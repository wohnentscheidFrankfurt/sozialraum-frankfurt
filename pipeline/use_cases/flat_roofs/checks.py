"""Checks of the low flat roofs: the extract, its dates, the reference buildings, the funnel, the wall strip and the
building code behind it. Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.checks import FAIL, OK, WARN, Check
from pipeline.shared.core.numbers import format_number
from pipeline.use_cases.flat_roofs.catalog import LOD2_AS_OF, LOD2_CREATED_YEAR
from pipeline.use_cases.flat_roofs.model import WALL_GAP_M, Roof

AREA_TOLERANCE_M2 = 1.0  # reference area against the extract
HEIGHT_TOLERANCE_M = 0.1
SUM_TOLERANCE_M2 = 1.0  # the area sums against the funnel
STRIP_TOLERANCE_M2 = 0.01  # the wall strip against its roof: float noise of the geometry only
UNASSIGNED_WARN = 5  # more roofs than this in no district give WARN


def check_counts(gemarkungen: pd.DataFrame) -> Check:
    """Every Gemarkung of the extract holds all buildings of the delivery's list."""
    name = "Flat roofs: buildings read against the delivery list"
    bad = gemarkungen[gemarkungen["parsed"] != gemarkungen["buildings"]]
    if len(bad):
        return Check(name, FAIL, "; ".join(f"{r.gemarkung}: {r.parsed} of {r.buildings}" for r in bad.itertuples()))
    return Check(name, OK, f"{len(gemarkungen)} Gemarkungen, {int(gemarkungen['buildings'].sum()):,} buildings")


def check_as_of(gemarkungen: pd.DataFrame, created: pd.Series) -> Check:
    """One delivery date (LOD2_AS_OF) and the footprints mostly of LOD2_CREATED_YEAR: the ⓘ states both."""
    name = "Flat roofs: delivery date and year of the footprints"
    dates = sorted({f"{int(d[8:10])}.{int(d[5:7])}.{d[:4]}" for d in gemarkungen["delivered"]})
    year = created.astype(str).str[:4].mode().iloc[0]
    ok = dates == [LOD2_AS_OF] and year == LOD2_CREATED_YEAR
    return Check(name, OK if ok else FAIL, f"delivery {', '.join(dates)}, most footprints of {year} "
                 f"(the texts say {LOD2_AS_OF} and {LOD2_CREATED_YEAR})")


def check_reference(roofs: list[Roof], reference: pd.DataFrame) -> Check:
    """Buildings read by hand in the raw GML: area, height and function of the roof must match the extract."""
    name = "Flat roofs: reference buildings against the raw GML"
    by_building = {r.building: r for r in roofs}
    bad = []
    for ref in reference.itertuples():
        r = by_building.get(ref.building)
        if r is None:
            bad.append(f"{ref.building}: no roof")
        elif (abs(r.area_m2 - ref.area_m2) > AREA_TOLERANCE_M2 or abs(r.height_m - ref.height_m) > HEIGHT_TOLERANCE_M
              or r.use != ref.function):
            bad.append(f"{ref.building}: {r.area_m2:.1f} m², {r.height_m:.1f} m, {r.use}; expected "
                       f"{ref.area_m2:.1f} m², {ref.height_m:.1f} m, {ref.function}")
    return Check(name, FAIL if bad else OK, "; ".join(bad) or f"{len(reference)} buildings equal")


def check_funnel(f: dict[str, float], by_district: pd.DataFrame, by_quarter: pd.DataFrame,
                 no_quarter: list[Roof]) -> Check:
    """Candidates minus the roofs out of a housing zone, the very low roofs and the wall strips equal the counted area,
    and districts and quarters add up to it."""
    name = "Flat roofs: funnel and area sums"
    problems = []
    rest = f["candidates_m2"] - f["not_housing_m2"] - f["very_low_m2"] - f["wall_m2"]
    if abs(rest - f["counted_m2"]) > SUM_TOLERANCE_M2:
        problems.append(f"funnel leaves {rest:.1f} m², counted {f['counted_m2']:.1f} m²")
    for label, table in (("districts", by_district), ("quarters", by_quarter)):
        total = float(table["ROOF_FLAT"].sum())
        if abs(total - f["counted_m2"]) > SUM_TOLERANCE_M2:
            problems.append(f"{label} add up to {total:.1f} m², counted {f['counted_m2']:.1f} m²")
    if no_quarter:
        problems.append("in no quarter: " + ", ".join(r.building for r in no_quarter))
    return Check(name, FAIL if problems else OK,
                 "; ".join(problems) or f"counted {f['counted_m2']:.1f} m² in districts and quarters")


def check_unassigned(outside: list[Roof]) -> Check:
    """Roofs in no district drop out of the map. A few at the city border are normal."""
    name = "Flat roofs: roofs in no district"
    return Check(name, WARN if len(outside) > UNASSIGNED_WARN else OK,
                 f"{len(outside)} roofs in no district (WARN above {UNASSIGNED_WARN})")


def check_wall_strip(roofs: list[Roof]) -> Check:
    """The strip in front of taller walls is part of its roof: never below 0, never larger than the roof."""
    name = "Flat roofs: wall strip never larger than the roof"
    bad = [r for r in roofs if r.wall_m2 < -STRIP_TOLERANCE_M2 or r.wall_m2 > r.area_m2 + STRIP_TOLERANCE_M2]
    if bad:
        return Check(name, FAIL, "; ".join(f"{r.building}: strip {r.wall_m2:.1f} m², roof {r.area_m2:.1f} m²"
                                           for r in bad))
    counted = [r for r in roofs if r.counts and r.wall_m2 > 0]
    whole = sum(r.wall_m2 >= r.area_m2 - STRIP_TOLERANCE_M2 for r in counted)
    return Check(name, OK, f"{len(counted)} counted roofs with a strip, {whole} of them lose all of their area")


def check_building_code(pages: list[str]) -> Check:
    """The strip of WALL_GAP_M is the smallest Abstandsfläche of the HBO (§ 6 Abs. 5 Satz 4) in the version of
    Baupaket I. The synopsis of the ministry must still say so; its old column says 3 m."""
    name = "Flat roofs: HBO synopsis still says the wall strip"
    phrase = f"mindestens {format_number(WALL_GAP_M, 2)} m betragen"
    found = phrase in " ".join(" ".join(pages).split())
    return Check(name, OK if found else FAIL, f"„{phrase}“ {'found' if found else 'missing'} in the synopsis")
