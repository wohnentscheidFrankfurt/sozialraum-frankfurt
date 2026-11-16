"""Checks of the building gaps: the delivery date, reference parcels, the cover extract, the hand verdicts, the known
cases of the user, the funnel and the suitability examples. Pure module."""
from __future__ import annotations

import re

import pandas as pd

from pipeline.shared.core.checks import FAIL, OK, WARN, Check
from pipeline.shared.core.indicator import format_de
from pipeline.use_cases.building_gaps.catalog import ALKIS_AS_OF, DOP_AS_OF, SUITABILITY_TEXT, german_date
from pipeline.use_cases.building_gaps.model import (BY, CANDIDATE_STEPS, COUNT_REASONS, GEOMETRY_STEPS, HIGH_M,
                                                    MIN_AREA_M2, NAN_WARN, NDVI_GREEN, NOT_REASONS, SUITABILITY,
                                                    VERDICTS, Candidate, Gap)

AREA_TOLERANCE_M2 = 1.0  # a reference parcel: geometry against the official area, at least ...
AREA_TOLERANCE_SHARE = 0.005  # ... or this share of the official area (the official area is older than the geometry)
SUM_TOLERANCE_M2 = 1.0  # the area sums against the funnel
UNASSIGNED_WARN = 5  # more drawn gaps than this in no district give WARN
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def check_as_of(meta: dict[str, str]) -> Check:
    """The portion date of the NAS delivery is the date the texts name (ALKIS_AS_OF)."""
    name = "Building gaps: ALKIS delivery date"
    found = german_date(meta.get("portion_date", ""))
    return Check(name, OK if found == ALKIS_AS_OF else FAIL,
                 f"delivery {found or 'missing'} (the texts say {ALKIS_AS_OF})")


def check_parcels(parcels: pd.DataFrame, reference: pd.DataFrame) -> Check:
    """Parcels read by hand in the raw NAS: Kennzeichen equal, and the area of the extract's geometry within
    max(AREA_TOLERANCE_M2, AREA_TOLERANCE_SHARE) of the official area."""
    name = "Building gaps: reference parcels against the raw NAS"
    by_id = {r.gml_id: r for r in parcels.itertuples()}
    bad = []
    for ref in reference.itertuples():
        p = by_id.get(ref.gml_id)
        if p is None:
            bad.append(f"{ref.gml_id}: not in the extract")
            continue
        area = float(p.geometry.area)
        tolerance = max(AREA_TOLERANCE_M2, AREA_TOLERANCE_SHARE * ref.official_m2)
        if p.kz != ref.kz or abs(area - ref.official_m2) > tolerance:
            bad.append(f"{ref.gml_id}: {p.kz}, {area:.1f} m²; expected {ref.kz}, {ref.official_m2:.1f} m²")
    return Check(name, FAIL if bad else OK, "; ".join(bad) or f"{len(reference)} parcels equal")


def _threshold_problems(meta: dict[str, str]) -> list[str]:
    out = []
    for key, value in (("cover_high_m", HIGH_M), ("cover_ndvi_green", NDVI_GREEN)):
        try:
            same = float(meta[key]) == value
        except (KeyError, ValueError):
            same = False
        if not same:
            out.append(f"{key} {meta.get(key, 'missing')} in the cover file, {value} in model.py")
    return out


def check_cover(gaps: list[Gap], cover: pd.DataFrame, meta: dict[str, str]) -> Check:
    """Every gap has its cover row and a valid height pixel, and the file was measured with the thresholds of
    model.py (meta: alkis_meta.csv); each is a FAIL (run update_sources). The most common flight is DOP_AS_OF (FAIL;
    other flights are named), and a gap with more than NAN_WARN of its pixels without height gives WARN."""
    name = "Building gaps: cover of every gap"
    missing = [g.gml_id for g in gaps if g.gml_id not in cover.index]
    rows = cover.loc[[g.gml_id for g in gaps if g.gml_id in cover.index]]
    blind = sorted(rows.index[(rows["px"] == 0) | (rows["nan_share"] >= 1)])
    flights = rows["flight"].map(german_date)
    tally = flights.value_counts()
    # the text's date must reach the top count; a tie never resolves by the order of the strings
    leads = not len(tally) or tally.get(DOP_AS_OF, 0) == tally.max()
    most = DOP_AS_OF if leads else ", ".join(d or "no date" for d in tally.index[tally == tally.max()])
    problems = []
    if missing:
        problems.append(f"{len(missing)} gaps without cover, run update_sources: {', '.join(missing[:10])}")
    if blind:
        problems.append(f"{len(blind)} gaps without a valid height pixel, check the height packages and run "
                        f"update_sources: {', '.join(blind[:10])}")
    if thresholds := _threshold_problems(meta):
        problems.append("; ".join(thresholds) + ", run update_sources")
    if not leads:
        problems.append(f"most flights on {most}, the texts say {DOP_AS_OF}")
    others = sorted(f"{gml_id} ({d or 'no date'})" for gml_id, d in flights.items() if d != most)
    holes = sorted(f"{gml_id} ({share:.0%})" for gml_id, share in rows["nan_share"].items() if share > NAN_WARN)
    text = (f"{len(rows)} gaps measured, flight {most or 'none'}"
            + (f"; other flights: {', '.join(others)}" if others else "")
            + (f"; without height (over {NAN_WARN:.0%} of the pixels): {', '.join(holes)}" if holes else ""))
    if problems:
        return Check(name, FAIL, "; ".join(problems) + "; " + text)
    return Check(name, WARN if holes else OK, text)


def _row_problems(row: dict) -> list[str]:
    verdict, reason, by = row["verdict"], row["reason"], row["by"]
    out = []
    if verdict not in VERDICTS:
        out.append(f"verdict „{verdict}“")
    elif verdict == "counts" and reason not in COUNT_REASONS:
        out.append(f"reason „{reason}“ for counts")
    elif verdict == "not" and reason not in NOT_REASONS:
        out.append(f"reason „{reason}“ for not")
    elif verdict == "site" and reason not in ("", *COUNT_REASONS, *NOT_REASONS):
        out.append(f"reason „{reason}“")
    if verdict == "not" and reason == "other" and not row["note"].strip():
        out.append("other without note")
    if by not in BY:
        out.append(f"by „{by}“")
    if not _ISO_DATE.fullmatch(row["checked"]) or not german_date(row["checked"]):
        out.append(f"checked „{row['checked']}“")
    return out


def check_verdicts(candidates: list[Candidate], verdicts: pd.DataFrame) -> Check:
    """The hand verdicts: an unknown verdict, reason or by, a reason of the wrong side, a bad date, a second row of
    a parcel or a Kennzeichen other than the gap's (a gml_id typo) is a FAIL (it never counts silently). A gap past the cover filters without a verdict and a row of a
    parcel that is no such gap any more (stale, after a new delivery) give WARN. A row "not" is not stale: its gap is
    not drawn, but it is still a candidate."""
    name = "Building gaps: hand verdicts"
    rows = verdicts.to_dict("records")
    problems = [f"{r['gml_id']}: {', '.join(p)}" for r in rows if (p := _row_problems(r))]
    twice = sorted(verdicts["gml_id"][verdicts["gml_id"].duplicated()].unique())
    problems += [f"{g}: more than one row" for g in twice]
    kz = {c.gap.gml_id: c.gap.kz for c in candidates}
    problems += [f"{r['gml_id']}: kz {r['kz']}, the parcel is {kz[r['gml_id']]}" for r in rows
                 if r["gml_id"] in kz and r["kz"] != kz[r["gml_id"]]]
    judgeable = [c for c in candidates if c.judgeable]
    open_ = [c.gap.gml_id for c in judgeable if c.verdict is None]
    stale = sorted({r["gml_id"] for r in rows} - {c.gap.gml_id for c in judgeable})
    counted = sum(c.counts for c in candidates)
    text = f"{len(rows)} rows, {counted} gaps count, {len(open_)} gaps past the filters without a verdict"
    if stale:
        text += f"; stale rows of no candidate after the cover filters: {', '.join(stale)}"
    if problems:
        return Check(name, FAIL, "; ".join(problems) + "; " + text)
    return Check(name, WARN if open_ or stale else OK, text)


def check_known(gaps: list[Gap], candidates: list[Candidate], known: pd.DataFrame, parcel_ids: set[str]) -> Check:
    """Known cases of the user (reference/building_gaps_known.csv). expect: no_gap (no gap of the geometry rule),
    dropped (a gap the zone or cover filters take out), not:<reason> (a gap past the filters judged not, for this
    reason; the map does not draw it). A not:<reason> case that is not judged yet gives WARN, so does a no_gap case
    whose parcel is not in the extract any more (a new delivery: the case must be found again)."""
    name = "Building gaps: known cases"
    gap_ids = {g.gml_id for g in gaps}
    by_id = {c.gap.gml_id: c for c in candidates}
    bad, pending = [], []
    for k in known.itertuples():
        c = by_id.get(k.gml_id)
        if k.expect == "no_gap":
            if k.gml_id not in parcel_ids:
                pending.append(f"{k.gml_id}: not in the extract")
            elif k.gml_id in gap_ids:
                bad.append(f"{k.gml_id}: is a gap, expected no_gap")
        elif k.expect == "dropped":
            if c is None or c.judgeable:
                bad.append(f"{k.gml_id}: {'no gap' if c is None else c.reason or 'counts'}, expected dropped")
        elif k.expect.startswith("not:"):
            if c is None or not c.judgeable:
                bad.append(f"{k.gml_id}: {'no gap' if c is None else c.reason}, expected {k.expect}")
            elif c.verdict is None:
                pending.append(f"{k.gml_id}: not judged yet")
            elif (c.verdict["verdict"], c.verdict["reason"]) != ("not", k.expect[4:]):
                bad.append(f"{k.gml_id}: {c.verdict['verdict']} {c.verdict['reason']}, expected {k.expect}")
        else:
            bad.append(f"{k.gml_id}: unknown expect „{k.expect}“")
    text = "; ".join(bad) or f"{len(known)} cases as expected"
    if pending and not bad:
        text += "; " + "; ".join(pending)
    return Check(name, FAIL if bad else WARN if pending else OK, text)


def check_funnel(f: dict[str, float], by_district: pd.DataFrame, by_quarter: pd.DataFrame,
                 no_quarter: list[Candidate]) -> Check:
    """The parcels minus every step equal the counted gaps, and districts and quarters add up to the counted area."""
    name = "Building gaps: funnel and area sums"
    problems = []
    rest = f["parcels"] - sum(f[s] for s in (*GEOMETRY_STEPS[1:], *CANDIDATE_STEPS))
    if rest != f["counted"]:
        problems.append(f"funnel leaves {rest:.0f} parcels, counted {f['counted']:.0f}")
    for label, table in (("districts", by_district), ("quarters", by_quarter)):
        total = float(table["GAP_AREA"].sum())
        if abs(total - f["counted_m2"]) > SUM_TOLERANCE_M2:
            problems.append(f"{label} add up to {total:.1f} m², counted {f['counted_m2']:.1f} m²")
    if no_quarter:
        problems.append("in no quarter: " + ", ".join(c.gap.gml_id for c in no_quarter))
    return Check(name, FAIL if problems else OK, "; ".join(problems)
                 or f"{f['counted']:.0f} gaps, {f['counted_m2']:.1f} m² in districts and quarters")


def check_unassigned(outside: list[Candidate]) -> Check:
    """Drawn gaps in no district. A few at the city border are normal."""
    name = "Building gaps: drawn gaps in no district"
    return Check(name, WARN if len(outside) > UNASSIGNED_WARN else OK,
                 f"{len(outside)} drawn gaps in no district (WARN above {UNASSIGNED_WARN})")


def check_examples(examples: pd.DataFrame) -> Check:
    """Every suitability has its example (reference/building_gaps_examples.csv). Its area is the threshold of the
    model (the first one, MIN_AREA_M2, holds every gap, so its example may be larger), and the text names its area,
    its number and, where given, its residents („25 Menschen“)."""
    name = "Building gaps: suitability examples"
    thresholds = {key: area for area, key in SUITABILITY}
    rows = {r.category: r for r in examples.itertuples()}
    bad = [f"{key}: no example" for key in thresholds if key not in rows]
    for key, r in rows.items():
        threshold = thresholds.get(key)
        if threshold is None:
            bad.append(f"{key}: no suitability")
            continue
        if not (r.area_m2 == threshold or (threshold == MIN_AREA_M2 and r.area_m2 >= threshold)):
            bad.append(f"{key}: example {r.area_m2} m², threshold {threshold} m²")
        text = SUITABILITY_TEXT[key]
        if f"{format_de(r.area_m2, 0)} m²" not in text or not re.search(rf"(?<![\d.]){r.number}(?![\d.])", text):
            bad.append(f"{key}: the text does not name {r.number} and {format_de(r.area_m2, 0)} m²")
        if pd.notna(r.residents) and f"{int(r.residents)} Menschen" not in text:
            bad.append(f"{key}: the text does not name {int(r.residents)} Menschen")
    return Check(name, FAIL if bad else OK, "; ".join(bad) or f"{len(rows)} examples match the texts")
