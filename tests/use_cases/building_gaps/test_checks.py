import pandas as pd
from shapely.geometry import box

from pipeline.shared.core.checks import FAIL, OK, WARN
from pipeline.use_cases.building_gaps.catalog import SUITABILITY_TEXT as SUITABILITY_BY_LANGUAGE, T
from pipeline.use_cases.building_gaps.checks import (check_as_of, check_cover, check_examples, check_funnel,
                                                     check_known, check_parcels, check_unassigned, check_verdicts)
from pipeline.use_cases.building_gaps.model import Candidate, Gap

SUITABILITY_TEXT, TEXTS = SUITABILITY_BY_LANGUAGE["de"], T["de"]
COVER = {"px": 400, "building": 0.0, "tree": 0.0, "green": 0.1, "open": 0.9, "nan_share": 0.0, "flight": "2025-08-19"}
F = {"parcels": 100, "main_building": 40, "small": 20, "use": 10, "narrow": 5, "front": 5, "no_wall": 5, "zone": 3,
     "no_cover": 0, "green": 2, "built": 1, "not_open": 1, "not": 2, "site": 1, "no_verdict": 1, "counted": 4,
     "counted_m2": 2000.0}


def gap(gml_id="a", area=500.0, kz="060466171000090000__"):
    return Gap(gml_id, kz, area, 20.0, 6.0, "row", "1990-01-01", 1, box(0, 0, 20, 25), 10.0, 10.0)


def cand(gml_id="a", verdict=None, housing=True, cover=COVER, area=500.0):
    return Candidate(gap(gml_id, area), housing, cover, verdict)


KZ = "060466171000090000__"


def row(gml_id="a", verdict="counts", reason="parking", by="aerial", note="", checked="2026-11-15", kz=KZ):
    return {"gml_id": gml_id, "kz": kz, "verdict": verdict, "reason": reason, "note": note, "checked": checked,
            "by": by}


def frame(*rows):
    return pd.DataFrame(list(rows), columns=["gml_id", "kz", "verdict", "reason", "note", "checked", "by"])


def test_check_as_of():
    c = check_as_of({"portion_date": "2026-11-04", "parcels": "174650"})
    assert c.status == OK and "4.11.2026" in c.text
    assert check_as_of({"portion_date": "2026-12-01"}).status == FAIL
    assert check_as_of({}).status == FAIL


def test_check_parcels():
    parcels = pd.DataFrame({"gml_id": ["a", "b"], "kz": ["k1", "k2"],
                            "geometry": [box(0, 0, 20, 50), box(0, 0, 40, 100)]})  # 1,000 and 4,000 m²
    ref = pd.DataFrame({"gml_id": ["a", "b"], "kz": ["k1", "k2"], "official_m2": [1004.0, 4019.0], "source": "s"})
    assert check_parcels(parcels, ref).status == OK  # within 0,5 %
    assert check_parcels(parcels, ref.assign(official_m2=[1006.0, 4000.0])).status == FAIL
    small = pd.DataFrame({"gml_id": ["s"], "kz": ["k"], "geometry": [box(0, 0, 10, 10)]})
    one = pd.DataFrame({"gml_id": ["s"], "kz": ["k"], "official_m2": [101.0], "source": "s"})
    assert check_parcels(small, one).status == OK  # at least 1 m²
    assert check_parcels(small, one.assign(official_m2=[101.2])).status == FAIL
    c = check_parcels(parcels, ref.assign(kz=["k1", "x"]))
    assert c.status == FAIL and "b" in c.text
    assert check_parcels(parcels, ref.assign(gml_id=["a", "gone"])).status == FAIL


def cover(*rows):
    return pd.DataFrame([{"gml_id": g, **COVER, **kw} for g, kw in rows]).set_index("gml_id")


META = {"portion_date": "2026-11-04", "cover_high_m": "2.5", "cover_ndvi_green": "0.2"}


def test_check_cover():
    gaps = [gap("a"), gap("b"), gap("c")]
    assert check_cover(gaps, cover(("a", {}), ("b", {}), ("c", {})), META).status == OK
    other = check_cover(gaps, cover(("a", {}), ("b", {}), ("c", {"flight": "2023-07-07"})), META)
    assert other.status == OK and "7.7.2023" in other.text and "c" in other.text  # named, not a fault
    assert check_cover(gaps, cover(("a", {"flight": "2023-07-07"}), ("b", {"flight": "2023-07-07"}),
                                   ("c", {})), META).status == FAIL  # most flights differ from the text
    missing = check_cover(gaps, cover(("a", {}), ("b", {})), META)
    assert missing.status == FAIL and "update_sources" in missing.text
    tie = [gap("a"), gap("b")]  # one flight each: the text's date reaches the top count, in either order
    assert check_cover(tie, cover(("a", {}), ("b", {"flight": "2023-07-07"})), META).status == OK
    assert check_cover(tie, cover(("a", {"flight": "2023-07-07"}), ("b", {})), META).status == OK
    late = cover(("a", {"flight": "2026-01-01"}), ("b", {"flight": "2023-07-07"}))  # a tie without the text's date
    assert check_cover(tie, late, META).status == FAIL
    nan = check_cover(gaps, cover(("a", {}), ("b", {"nan_share": 0.2}), ("c", {})), META)
    assert nan.status == WARN and "b" in nan.text


def test_check_cover_fails_on_a_gap_without_a_valid_height_pixel():
    """A broken height package must not publish a wrong zero: a gap with no valid pixel is a FAIL, not a WARN."""
    gaps = [gap("a"), gap("b"), gap("c")]
    c = check_cover(gaps, cover(("a", {}), ("b", {"nan_share": 1.0}), ("c", {"px": 0, "nan_share": 0.0})), META)
    assert c.status == FAIL and "b" in c.text and "c" in c.text and "without a valid height pixel" in c.text


def test_check_cover_fails_when_the_thresholds_of_the_file_differ_from_the_model():
    """The cover file is measured by update_sources; a threshold changed in model.py since then needs a rerun."""
    rows = cover(("a", {}))
    assert check_cover([gap("a")], rows, {**META, "cover_high_m": "2.50"}).status == OK
    for meta in ({**META, "cover_high_m": "3.0"}, {**META, "cover_ndvi_green": "0.25"},
                 {"portion_date": "2026-11-04"}):
        c = check_cover([gap("a")], rows, meta)
        assert c.status == FAIL and "update_sources" in c.text, meta


def test_check_verdicts_ok_and_warns():
    candidates = [cand("a", row("a")), cand("b", row("b", "not", "square")), cand("c", row("c", "site", "")),
                  cand("d")]
    verdicts = frame(row("a"), row("b", "not", "square"), row("c", "site", ""))
    c = check_verdicts(candidates, verdicts)
    assert c.status == WARN and "1 gaps past the filters without a verdict" in c.text  # d
    assert check_verdicts(candidates[:3], verdicts).status == OK


def test_check_verdicts_warns_on_a_stale_row():
    """Review Focus 3: a parcel split in a new delivery: its row is stale, never an error."""
    c = check_verdicts([cand("a", row("a")), cand("new")], frame(row("a"), row("gone")))
    assert c.status == WARN and "stale" in c.text and "gone" in c.text
    # a row of a gap the cover filters drop is stale too
    dropped = cand("x", row("x"), cover={**COVER, "green": 0.9})
    assert "stale" in check_verdicts([dropped], frame(row("x"))).text


def test_check_verdicts_a_not_row_is_not_stale():
    """User, 15.11.: a gap judged not is no longer drawn, but its row still belongs to a candidate."""
    judged = cand("n", row("n", "not", "square"))
    assert not judged.drawn
    c = check_verdicts([judged], frame(row("n", "not", "square")))
    assert c.status == OK and "stale" not in c.text


def test_check_verdicts_fails_when_the_kz_of_a_row_differs_from_its_gap():
    """A gml_id typo that lands on another parcel shows in the Kennzeichen."""
    c = check_verdicts([cand("a", row("a", kz="060466171000100000__"))], frame(row("a", kz="060466171000100000__")))
    assert c.status == FAIL and "a" in c.text and "060466171000100000__" in c.text
    stale = check_verdicts([cand("a", row("a"))], frame(row("a"), row("gone", kz="x")))  # a stale row has no gap
    assert stale.status == WARN


def test_check_verdicts_fails_on_unknown_values():
    """Review Focus 5: an unknown verdict, reason or by, or a reason of the wrong side never counts silently."""
    for bad in (row(verdict="yes"), row(reason="garden"), row(by="drone"), row(reason="green"),
                row(verdict="not", reason="parking"), row(verdict="not", reason="other"), row(checked="15.11.2026")):
        c = check_verdicts([cand("a", bad)], frame(bad))
        assert c.status == FAIL, bad
        assert "a" in c.text
    assert check_verdicts([cand("a", row())], frame(row(), row())).status == FAIL  # one row per parcel
    assert check_verdicts([cand("a", row("a", "not", "other", note="Tankstelle"))],
                          frame(row("a", "not", "other", note="Tankstelle"))).status == OK


def known(*rows):
    return pd.DataFrame(list(rows), columns=["gml_id", "expect", "note"])


def test_check_known():
    gaps = [gap("drawn"), gap("dropped"), gap("judged")]
    parcels = {"drawn", "dropped", "judged", "none"}
    candidates = [cand("drawn"), cand("dropped", housing=False), cand("judged", row("judged", "not", "square"))]
    ok = known(("none", "no_gap", ""), ("dropped", "dropped", ""), ("judged", "not:square", ""))
    assert check_known(gaps, candidates, ok, parcels).status == OK
    gone = check_known(gaps, candidates, known(("gone", "no_gap", "")), parcels)
    assert gone.status == WARN and "gone: not in the extract" in gone.text  # never a silent pass
    for bad in (("drawn", "no_gap", ""), ("drawn", "dropped", ""), ("judged", "not:school", ""),
                ("none", "not:square", ""), ("drawn", "maybe", "")):
        c = check_known(gaps, candidates, known(bad), parcels)
        assert c.status == FAIL and bad[0] in c.text, bad
    pending = check_known(gaps, candidates, known(("drawn", "not:square", "")), parcels)
    assert pending.status == WARN and "drawn" in pending.text  # not judged yet
    # a gap judged not is no longer drawn (user, 15.11.): still no "dropped", still its not:<reason>
    assert not candidates[2].drawn
    assert check_known(gaps, candidates, known(("judged", "dropped", "")), parcels).status == FAIL


def table(*values):
    return pd.DataFrame({"id": [f"i{i}" for i in range(len(values))], "GAP_AREA": list(values)})


def test_check_funnel():
    assert check_funnel(F, table(1500.0, 500.0), table(2000.0), []).status == OK
    assert check_funnel({**F, "counted": 5}, table(2000.0), table(2000.0), []).status == FAIL
    assert check_funnel(F, table(1500.0), table(2000.0), []).status == FAIL
    assert check_funnel(F, table(2000.0), table(1999.0), []).status == OK  # 1 m²
    c = check_funnel(F, table(2000.0), table(1500.0), [cand("lost", row("lost"))])
    assert c.status == FAIL and "lost" in c.text


def test_check_unassigned():
    assert check_unassigned([cand()] * 5).status == OK
    c = check_unassigned([cand()] * 6)
    assert c.status == WARN and "6" in c.text


EXAMPLES = pd.DataFrame({"category": ["coop", "house_for_all", "student", "multi_family", "complex"],
                         "area_m2": [312, 365, 1270, 2000, 5400], "number": [9, 19, 177, 42, 67],
                         "residents": [25, None, None, None, None],
                         "unit": "u", "place": "p", "year": 2025, "source_url": "s", "quote": "q"})


def test_check_examples():
    assert check_examples(EXAMPLES, SUITABILITY_TEXT, TEXTS).status == OK
    threshold = EXAMPLES.assign(area_m2=[312, 365, 1300, 2000, 5400])
    assert check_examples(threshold, SUITABILITY_TEXT, TEXTS).status == FAIL
    under_minimum = EXAMPLES.assign(area_m2=[290, 365, 1270, 2000, 5400])
    assert check_examples(under_minimum, SUITABILITY_TEXT, TEXTS).status == FAIL
    c = check_examples(EXAMPLES.assign(number=[9, 19, 177, 43, 67]), SUITABILITY_TEXT, TEXTS)
    assert c.status == FAIL and "multi_family" in c.text  # the number of the text
    assert check_examples(EXAMPLES.iloc[:4], SUITABILITY_TEXT, TEXTS).status == FAIL  # every category has its example
    c = check_examples(EXAMPLES.assign(residents=[24, None, None, None, None]), SUITABILITY_TEXT, TEXTS)
    assert c.status == FAIL and "coop" in c.text and "24 Menschen" in c.text  # the residents of the text


def test_the_real_examples_match_the_texts_and_point_at_their_sources():
    """The sources of the suitability examples lie in sources/ (user, 15.11.); the CSV keeps the URLs too."""
    from pipeline import config
    examples = pd.read_csv(config.BUILDING_GAPS_EXAMPLES_CSV, dtype={"category": str})
    assert check_examples(examples, SUITABILITY_TEXT, TEXTS).status == OK
    assert all((config.SOURCES / f).is_file() for f in examples["file"]) and examples["source_url"].str.len().all()
