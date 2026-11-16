import numpy as np
import pandas as pd
import shapely
from shapely.geometry import MultiPolygon, Polygon, box

from pipeline.shared.geography.model import Area
from pipeline.use_cases.building_gaps import model
from pipeline.use_cases.building_gaps.model import (GEOMETRY_STEPS, Gap, area_values, find_gaps, funnel, judge,
                                                     suitability)

X0, Y0 = 477000.0, 5550000.0


def rect(x, y, w, h):
    return box(X0 + x, Y0 + y, X0 + x + w, Y0 + y + h)


def parcel(gml_id, geom):
    return {"gml_id": gml_id, "kz": gml_id, "official_m2": geom.area, "created": "1990-01-01", "addresses": 1,
            "geometry": geom}


def building(gml_id, geom, main=True, function="1000"):
    return {"gml_id": gml_id, "function": function, "main": main, "geometry": geom}


def landuse(gml_id, geom, cls="Wohnbauflaeche", function="", housing=True, access=False):
    return {"gml_id": gml_id, "cls": cls, "function": function, "housing": housing, "access": access,
            "geometry": geom}


def street(x=-50, w=400):
    return landuse("street", rect(x, -10, w, 10), cls="Strassenverkehr", housing=False, access=True)


def housing(x=-50, w=400):
    return landuse("housing", rect(x, 0, w, 200))


def run(parcels, buildings=(), extra=(), with_housing=True):
    uses = [street()] + ([housing()] if with_housing else []) + list(extra)
    frame = lambda rows, cols: pd.DataFrame(list(rows), columns=cols)  # noqa: E731
    return find_gaps(
        frame(parcels, ["gml_id", "kz", "official_m2", "created", "addresses", "geometry"]),
        frame(buildings, ["gml_id", "function", "main", "geometry"]),
        frame(uses, ["gml_id", "cls", "function", "housing", "access", "geometry"]))


def test_main_building_drops_a_parcel_but_a_garage_does_not():
    parcels = [parcel("a", rect(0, 0, 40, 25)), parcel("b", rect(100, 0, 40, 25)), parcel("c", rect(200, 0, 40, 25))]
    buildings = [building("garage", rect(0, 0, 10, 6), main=False, function="2460"),
                 building("small", rect(100, 0, 5, 5)),  # 25 m2, limit max(20, 5 % of 1,000) = 50
                 building("big", rect(200, 0, 10, 6))]  # 60 m2
    gaps, counts = run(parcels, buildings)
    assert [g.gml_id for g in gaps] == ["a", "b"]
    assert counts["main_building"] == 1


def test_small_parcel_drops_below_300_m2():
    parcels = [parcel("a", rect(0, 0, 16, 18.7)), parcel("b", rect(100, 0, 16, 18.75))]  # 299.2 and 300 m2
    buildings = [building("wa", rect(-10, 0, 10, 18)), building("wb", rect(90, 0, 10, 18))]  # row neighbours
    gaps, counts = run(parcels, buildings)
    assert counts["small"] == 1
    assert [g.gml_id for g in gaps] == ["b"]


def test_use_share_below_80_percent_drops():
    parcels = [parcel("a", rect(0, 0, 40, 25)), parcel("b", rect(100, 0, 40, 25))]
    only = [landuse("h1", rect(0, 0, 40, 25)), landuse("h2", rect(100, 0, 31, 25)),
            landuse("x", rect(131, 0, 9, 25), cls="IndustrieUndGewerbe", housing=False)]
    gaps, counts = run(parcels, extra=only, with_housing=False)
    assert counts["use"] == 1
    assert [g.gml_id for g in gaps] == ["a"]


def test_narrow_parcel_drops():
    parcels = [parcel("a", rect(0, 0, 40, 14)), parcel("b", rect(100, 0, 40, 16))]
    gaps, counts = run(parcels)
    assert counts["narrow"] == 1
    assert [g.gml_id for g in gaps] == ["b"]


def test_front_counts_streets_but_not_a_parking_platz():
    parcels = [parcel("a", rect(0, 0, 40, 25)), parcel("b", rect(100, 0, 40, 25))]
    lots = [landuse("p", rect(90, -10, 60, 10), cls="Platz", function="5310", housing=False, access=False)]
    uses = [landuse("street", rect(-50, -10, 140, 10), cls="Strassenverkehr", housing=False, access=True),
            housing()] + lots
    gaps, counts = find_gaps(
        pd.DataFrame(parcels), pd.DataFrame(columns=["gml_id", "function", "main", "geometry"]), pd.DataFrame(uses))
    assert counts["front"] == 1
    assert [g.gml_id for g in gaps] == ["a"]
    assert abs(gaps[0].front_m - 40) < 0.1


def test_row_needs_5_m_of_neighbour_wall_free_needs_30_m_front():
    parcels = [
        parcel("row", rect(0, 0, 17, 60)), parcel("near", rect(100, 0, 17, 60)),
        parcel("far", rect(200, 0, 31, 40)), parcel("free", rect(300, 0, 28, 40))]
    buildings = [building("wall", rect(-10, 0, 10, 20)),  # touches 20 m of the parcel "row"
                 building("gap2", rect(88, 0, 10, 20)),  # 2 m away from "near"
                 building("gap2b", rect(190, 0, 8, 20)),  # 2 m away from "far": no wall, but 31 m front
                 building("wall28", rect(328, 0, 10, 20)),  # touches "free" (28 m front): a row gap
                 ]
    gaps, counts = run(parcels, buildings)
    by = {g.gml_id: g for g in gaps}
    assert set(by) == {"row", "far", "free"}
    assert by["row"].kind == "row" and by["row"].wall_m >= 20
    assert by["far"].kind == "free" and by["far"].wall_m == 0
    assert by["free"].kind == "row"
    assert counts["no_wall"] == 1  # "near": 17 m front, no wall


def test_front_does_not_count_the_side_edges():
    """The 1.5 m tolerance reaches 1.5 m up each side edge: the front is the street side alone."""
    gaps, _ = run([parcel("a", rect(0, 0, 20, 30)), parcel("corner", rect(100, 0, 20, 30))],
                  [building("wall", rect(-10, 0, 10, 20))],  # "a" is a row gap
                  extra=[landuse("side", rect(120, -10, 10, 100), cls="Strassenverkehr", housing=False, access=True)])
    by = {g.gml_id: g for g in gaps}
    assert abs(by["a"].front_m - 20) < 0.1
    assert abs(by["corner"].front_m - 50) < 0.1  # 20 m at the street and 30 m at the side street


def test_front_merges_the_pieces_of_a_collection():
    """The boundary in the access buffer can be a GeometryCollection (a corner touches the buffer at a point). The
    ring starts at a corner of the front, so the front comes in two pieces: they are merged before the cut."""
    near = shapely.GeometryCollection([shapely.LineString([(0, 0), (20, 0), (20, 1.5)]),
                                       shapely.LineString([(0, 1.5), (0, 0)]), shapely.Point(20, 30)])
    assert model._front(near) == 20.0  # 18.5 without the merge
    assert model._front(shapely.MultiLineString([[(0, 0), (20, 0), (20, 1.5)], [(0, 1.5), (0, 0)]])) == 20.0
    assert model._front(shapely.GeometryCollection([shapely.Point(1, 1)])) == 0.0


def test_a_parcel_without_a_free_side_short_of_30_m_drops():
    """28 m at the street read 31 m with the side edges: no wall, so it drops."""
    gaps, counts = run([parcel("p", rect(0, 0, 28, 40))])
    assert gaps == [] and counts["no_wall"] == 1


def test_counts_add_up():
    parcels = [parcel("a", rect(0, 0, 40, 25)), parcel("big", rect(100, 0, 40, 25)), parcel("s", rect(200, 0, 10, 10)),
               parcel("n", rect(300, 0, 14, 40))]
    gaps, counts = run(parcels, [building("b", rect(100, 0, 10, 6))])
    assert tuple(counts) == GEOMETRY_STEPS
    assert counts["parcels"] - sum(v for k, v in counts.items() if k != "parcels") == len(gaps) == 1


def test_multipolygon_parcel_is_measured():
    two = MultiPolygon([rect(0, 0, 20, 40), rect(20, 0, 20, 40)])  # touching: invalid as a MultiPolygon
    bow = Polygon([(X0 + 200, Y0), (X0 + 240, Y0 + 40), (X0 + 200, Y0 + 40), (X0 + 240, Y0)])  # self-crossing
    assert not shapely.is_valid(bow)
    gaps, counts = run([parcel("two", two), parcel("bow", bow)])
    by = {g.gml_id: g for g in gaps}
    assert set(by) == {"two", "bow"}
    assert abs(by["two"].area_m2 - 1600) < 1e-6
    assert abs(by["bow"].area_m2 - 800) < 1e-6
    assert by["bow"].front_m >= 40


def test_cover_shares_classifies_the_four_classes():
    from pipeline.use_cases.building_gaps.model import cover_shares, ndvi
    x0, y1 = 477000, 5550012
    ndom = np.zeros((12, 12), dtype=np.float32)
    green = np.zeros((12, 12))
    ndom[:6, :6] = 5  # north west: building (high, not green)
    ndom[:6, 6:] = 5
    green[:6, 6:] = 0.5  # north east: tree (high and green)
    green[6:, :6] = 0.5  # south west: green (low and green)
    # south east: open
    geom = rect(1, 1, 10, 10)
    r = cover_shares(geom, ndom, green, x0, y1)
    assert r["px"] == 100 and r["nan_share"] == 0
    assert (r["building"], r["tree"], r["green"], r["open"]) == (0.25, 0.25, 0.25, 0.25)
    cir = np.zeros((1, 2, 3))
    cir[0, 0] = (200, 100, 0)
    cir[0, 1] = (0, 0, 0)
    assert ndvi(cir).tolist() == [[100 / 300, 0.0]]


def test_nan_pixels_only_count_in_nan_share():
    from pipeline.use_cases.building_gaps.model import cover_shares
    x0, y1 = 477000, 5550012
    ndom = np.zeros((12, 12), dtype=np.float32)
    ndom[:, :6] = np.nan  # the west half has no tile
    r = cover_shares(rect(1, 1, 10, 10), ndom, np.zeros((12, 12)), x0, y1)
    assert r["px"] == 100 and r["nan_share"] == 0.5
    assert r["open"] == 1.0 and r["building"] == 0.0
    allnan = cover_shares(rect(1, 1, 10, 10), np.full((12, 12), np.nan, dtype=np.float32), np.zeros((12, 12)), x0, y1)
    assert allnan["nan_share"] == 1.0 and allnan["open"] == 0.0



VERDICT_COLUMNS = ["gml_id", "kz", "verdict", "reason", "note", "checked", "by"]


def gap(gml_id, x=10.0, y=10.0, area=400.0):
    return Gap(gml_id=gml_id, kz=gml_id, area_m2=area, front_m=20.0, wall_m=8.0, kind="row", created="1990-01-01",
               addresses=1, geom=box(x - 10, y - 10, x + 10, y + 10), x=x, y=y)


def cover_frame(**rows):
    base = {"px": 400, "building": 0.0, "tree": 0.0, "green": 0.0, "open": 1.0, "nan_share": 0.0,
            "flight": "2025-08-19"}
    data = {k: {**base, **v} for k, v in rows.items()}
    return pd.DataFrame.from_dict(data, orient="index").rename_axis("gml_id")


def verdict_frame(*rows):
    return pd.DataFrame([dict(zip(VERDICT_COLUMNS, r)) for r in rows], columns=VERDICT_COLUMNS, dtype=str)


def test_reason_follows_the_funnel_order():
    zone = box(0, 0, 100, 100)
    gaps = [gap(n) for n in ("a_zone", "b_nocover", "c_green", "d_built", "e_notopen", "f_noverdict", "g_not",
                             "h_site", "i_counts")]
    gaps[0] = gap("a_zone", x=500.0)  # outside the zone
    cover = cover_frame(a_zone={}, c_green={"tree": 0.3, "green": 0.3, "open": 0.4}, d_built={"building": 0.2, "open": 0.8},
                        e_notopen={"open": 0.4, "tree": 0.1, "green": 0.1, "building": 0.1}, f_noverdict={},
                        g_not={}, h_site={}, i_counts={})
    verdicts = verdict_frame(("g_not", "g_not", "not", "green", "", "2026-11-15", "aerial"),
                             ("h_site", "h_site", "site", "", "", "2026-11-15", "aerial"),
                             ("i_counts", "i_counts", "counts", "parking", "", "2026-11-15", "site"))
    out = {c.gap.gml_id: c for c in judge(gaps, [zone], cover, verdicts)}
    assert {k: c.reason for k, c in out.items()} == {
        "a_zone": "zone", "b_nocover": "no_cover", "c_green": "green", "d_built": "built", "e_notopen": "not_open",
        "f_noverdict": "no_verdict", "g_not": "not", "h_site": "site", "i_counts": ""}
    assert [k for k, c in out.items() if c.drawn] == ["h_site", "i_counts"]  # user, 15.11.: not without a verdict
    assert [k for k, c in out.items() if c.counts] == ["i_counts"]
    assert out["i_counts"].verdict["reason"] == "parking" and out["a_zone"].housing is False
    assert out["b_nocover"].cover is None and out["c_green"].cover["tree"] == 0.3


def test_not_judged_gap_is_not_drawn():
    """User, 15.11.: a gap judged not stays in the funnel and the checks, but the map does not draw it."""
    zone = box(0, 0, 100, 100)
    gaps = [gap("n"), gap("s"), gap("o"), gap("c"), gap("g")]
    cover = cover_frame(n={}, s={}, o={}, c={}, g={"tree": 0.6, "open": 0.4})
    verdicts = verdict_frame(("n", "n", "not", "square", "", "2026-11-15", "aerial"),
                             ("s", "s", "site", "", "", "2026-11-15", "aerial"),
                             ("c", "c", "counts", "parking", "", "2026-11-15", "aerial"))
    out = {c.gap.gml_id: c for c in judge(gaps, [zone], cover, verdicts)}
    assert out["n"].reason == "not" and not out["n"].drawn and out["n"].judgeable
    assert [k for k, c in out.items() if c.drawn] == ["s", "c"]  # o: no verdict yet (user, 15.11.)
    assert [k for k, c in out.items() if c.judgeable] == ["n", "s", "o", "c"]  # g: the cover filter drops it


def test_a_gap_without_a_valid_height_pixel_has_no_cover():
    """No valid nDOM pixel gives the shares 0: the gap must not drop silently as not_open."""
    gaps = [gap("all_nan"), gap("no_px"), gap("ok")]
    cover = cover_frame(all_nan={"open": 0.0, "nan_share": 1.0}, no_px={"px": 0, "open": 0.0, "nan_share": 0.0},
                        ok={})
    out = judge(gaps, [box(0, 0, 100, 100)], cover, verdict_frame())
    assert [c.reason for c in out] == ["no_cover", "no_cover", "no_verdict"]


def test_judge_takes_an_empty_verdict_frame():
    out = judge([gap("a")], [box(0, 0, 100, 100)], cover_frame(a={}), verdict_frame())
    assert [c.reason for c in out] == ["no_verdict"]


def test_suitability_takes_the_largest_category():
    cases = [(300, "coop"), (364, "coop"), (365, "house_for_all"), (1269, "house_for_all"), (1270, "student"),
             (1999, "student"), (2000, "multi_family"), (5399, "multi_family"), (5400, "complex"), (9000, "complex")]
    assert [suitability(a) for a, _ in cases] == [k for _, k in cases]


def _mixed():
    zone = [box(0, 0, 100, 100)]
    gaps = [gap("a", x=500.0, area=400), gap("b", area=500), gap("c", area=600), gap("d", area=700),
            gap("e", area=800), gap("f", area=900), gap("g", area=1000), gap("h", area=1100), gap("i", area=1200),
            gap("j", x=50, area=1300)]
    cover = cover_frame(a={}, c={"tree": 0.6, "open": 0.4}, d={"building": 0.2, "open": 0.8}, e={"open": 0.3},
                        f={}, g={}, h={}, i={}, j={})
    verdicts = verdict_frame(("g", "g", "not", "other", "", "d", "aerial"), ("h", "h", "site", "", "", "d", "aerial"),
                             ("i", "i", "counts", "yard", "", "d", "aerial"),
                             ("j", "j", "counts", "storage", "", "d", "site"))
    return judge(gaps, zone, cover, verdicts)


def test_funnel_adds_up_to_the_counted_gaps():
    candidates = _mixed()
    geometry = {"parcels": 1000, "main_building": 700}
    f = funnel(geometry, candidates)
    assert f["parcels"] == 1000 and f["main_building"] == 700
    steps = [f[s] for s in model.CANDIDATE_STEPS]
    assert steps == [1, 1, 1, 1, 1, 1, 1, 1]
    assert f["counted"] == 2 and f["counted_m2"] == 1200 + 1300
    assert len(candidates) == sum(steps) + f["counted"]


def test_area_values_sum_counted_gaps_only():
    candidates = _mixed()
    d1, d2 = Area("d1", "D1", "q1", "s", box(0, 0, 100, 100)), Area("d2", "D2", "q2", "s", box(200, 0, 300, 100))
    q1 = Area("q1", "Q1", "", "", box(0, 0, 30, 100))  # j lies at x=50, outside q1 and q2
    q2 = Area("q2", "Q2", "", "", box(200, 0, 300, 100))
    dt, qt, outside, no_quarter = area_values(candidates, [d1, d2], [q1, q2])
    assert dt.columns.tolist() == ["id", "GAP_AREA"]
    assert dict(zip(dt["id"], dt["GAP_AREA"])) == {"d1": 1200 + 1300, "d2": 0}
    assert dict(zip(qt["id"], qt["GAP_AREA"])) == {"q1": 1200, "q2": 0}  # i at x=10 in q1; j in no quarter
    assert [c.gap.gml_id for c in outside] == []  # a (zone, x=500) is not drawn
    assert [c.gap.gml_id for c in no_quarter] == ["j"]


def test_unknown_verdict_does_not_count():
    gaps = [gap("a"), gap("b"), gap("c")]
    verdicts = verdict_frame(("a", "a", "", "", "", "d", "aerial"), ("b", "b", "yes", "", "", "d", "aerial"),
                             ("c", "c", "Counts", "", "", "d", "aerial"))
    out = judge(gaps, [box(0, 0, 100, 100)], cover_frame(a={}, b={}, c={}), verdicts)
    assert [c.reason for c in out] == ["no_verdict"] * 3 and not any(c.counts for c in out)
