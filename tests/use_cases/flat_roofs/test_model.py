import pandas as pd
import pytest
from shapely.geometry import Point, box

from pipeline.shared.geography.model import Area
from pipeline.use_cases.flat_roofs import model
from pipeline.use_cases.flat_roofs.model import find_roofs, funnel, area_values


def part(building, x0, y0, w, h, height, flat=True, excluded=False, use="31001_2000"):
    geom = box(x0, y0, x0 + w, y0 + h)
    return {"building": building, "use": use, "excluded": excluded, "flat": flat, "height_m": height,
            "ground_m2": geom.area, "gemarkung": "G", "created": "2020", "geometry": geom}


def frame(*rows):
    return pd.DataFrame(list(rows))


def one(*rows, zones=None):
    return find_roofs(frame(*rows), [box(-1e6, -1e6, 1e6, 1e6)] if zones is None else zones)


def test_low_flat_parts_add_up_per_building():
    roofs = one(part("a", 0, 0, 12, 10, 4.0), part("a", 20, 0, 9, 10, 4.0))
    assert len(roofs) == 1 and roofs[0].area_m2 == pytest.approx(210.0)
    assert roofs[0].geom.area == pytest.approx(210.0)
    assert roofs[0].building == "a" and roofs[0].height_m == 4.0 and roofs[0].use == "31001_2000"


def test_bounds_of_height_and_area():
    assert len(one(part("a", 0, 0, 20, 10, 2.5))) == 1
    assert one(part("a", 0, 0, 20, 10, 2.4)) == []
    assert one(part("a", 0, 0, 20, 10, 8.0)) == []
    assert len(one(part("a", 0, 0, 20, 10, 7.99))) == 1
    assert one(part("a", 0, 0, 19.99, 10, 4.0)) == []
    assert one(part("a", 0, 0, 20, 10, 4.0, flat=False)) == []
    assert one(part("a", 0, 0, 20, 10, None)) == []


def test_excluded_function_is_no_roof():
    assert one(part("a", 0, 0, 20, 10, 4.0, excluded=True)) == []


def test_a_wall_more_than_3_m_higher_keeps_a_strip_of_2_5_m_free():
    # a 20 x 10 m roof, the wall along its long side: 2.5 x 20 = 50 m² stay free
    roofs = one(part("a", 0, 0, 20, 10, 4.0), part("n", 0, 10, 20, 10, 7.1, flat=False))
    assert [r.building for r in roofs] == ["a"]
    r = roofs[0]
    assert r.wall_m2 == pytest.approx(50.0, abs=0.01) and r.usable_m2 == pytest.approx(150.0, abs=0.01)
    assert r.area_m2 == pytest.approx(200.0) and r.counts and r.reason == ""


def test_a_part_more_than_1_m_away_gives_no_strip():
    r = one(part("a", 0, 0, 20, 10, 4.0), part("n", 0, 11.1, 20, 10, 7.1, flat=False))[0]
    assert r.wall_m2 == 0.0 and r.usable_m2 == r.area_m2
    near = one(part("a", 0, 0, 20, 10, 4.0), part("n", 0, 10.9, 20, 10, 7.1, flat=False))[0]
    assert near.wall_m2 == pytest.approx(2.5 * 20 - 0.9 * 20, abs=0.01)  # the strip counts from the wall


def test_a_part_exactly_3_m_higher_gives_no_strip():
    r = one(part("a", 0, 0, 20, 10, 4.0), part("n", 0, 10, 20, 10, 7.0, flat=False))[0]
    assert r.wall_m2 == 0.0


def test_a_taller_part_of_the_same_building_gives_a_strip_only_where_it_touches():
    touching = one(part("a", 0, 0, 20, 10, 4.0), part("a", 0, 10, 20, 10, 7.5, flat=False))[0]
    assert touching.wall_m2 == pytest.approx(50.0, abs=0.01)
    apart = one(part("a", 0, 0, 20, 10, 4.0), part("a", 0, 12, 20, 10, 7.5, flat=False))[0]
    assert apart.wall_m2 == 0.0


def test_the_strip_scales_with_the_area_of_the_extract():
    # the area of a roof comes from ground_m2 of the extract; the strip takes its share of the geometry
    row = part("a", 0, 0, 20, 10, 4.0)
    row["ground_m2"] = 210.0
    r = one(row, part("n", 0, 10, 20, 10, 7.1, flat=False))[0]
    assert r.area_m2 == 210.0 and r.wall_m2 == pytest.approx(210.0 * 50 / 200, abs=0.01)


def test_walls_on_two_sides_overlap_once():
    r = one(part("a", 0, 0, 20, 10, 4.0), part("n", 0, 10, 20, 10, 9.0, flat=False),
            part("m", 20, 0, 10, 10, 9.0, flat=False))[0]
    assert r.wall_m2 == pytest.approx(50.0 + 2.5 * 10 - 2.5 * 2.5, abs=0.01)


def test_very_low_below_3_2():
    assert one(part("a", 0, 0, 20, 10, 3.1))[0].reason == "very_low"
    assert one(part("a", 0, 0, 20, 10, 3.2))[0].counts


def test_any_housing_zone_wins():
    zones = [box(100, 100, 110, 110), box(9, 4, 11, 6)]
    roof = one(part("a", 0, 0, 20, 10, 4.0), zones=zones)[0]
    assert roof.housing and roof.counts
    assert not one(part("a", 0, 0, 20, 10, 4.0), zones=[box(100, 100, 110, 110)])[0].housing
    assert not one(part("a", 0, 0, 20, 10, 4.0), zones=[])[0].housing


def test_reason_order_and_counts():
    # outside housing zone and very low at once: the zone is named first. A wall strip is no reason.
    zones = [box(-1, -1, 21, 11)]
    rows = [part("a", 0, 0, 20, 10, 3.0), part("n", 0, 10, 20, 5, 9.0, flat=False)]
    roof = find_roofs(frame(*rows), zones)[0]
    assert roof.very_low and roof.reason == "very_low" and not roof.counts and roof.wall_m2 > 0
    roof = find_roofs(frame(*rows), [])[0]
    assert roof.reason == "zone"
    walled = find_roofs(frame(part("a", 0, 0, 20, 10, 4.0), rows[1]), zones)[0]
    assert walled.reason == "" and walled.counts and walled.wall_m2 > 0


def test_funnel_closes():
    zones = [box(-1, -1, 100, 100)]
    rows = [part("count", 0, 0, 20, 10, 4.0),                                      # 200
            part("wall", 0, 30, 20, 15, 4.0), part("wall", 0, 45, 20, 5, 9.0, flat=False),   # 300, 50 strip
            part("low", 0, 60, 30, 10, 3.0), part("ln", 0, 70, 30, 5, 9.0, flat=False),       # 300 very low
            part("out", 200, 0, 40, 10, 4.0)]                                      # 400 not housing
    roofs = find_roofs(frame(*rows), zones)
    f = funnel(roofs)
    assert set(f) == {"candidates_m2", "not_housing_m2", "very_low_m2", "wall_m2", "counted_m2", "modules"}
    assert f["candidates_m2"] == pytest.approx(1200.0)
    assert f["not_housing_m2"] == pytest.approx(400.0)
    assert f["very_low_m2"] == pytest.approx(300.0)
    assert f["wall_m2"] == pytest.approx(50.0, abs=0.01)  # the strip of the very low roof is not subtracted twice
    assert f["counted_m2"] == pytest.approx(450.0, abs=0.01)
    assert f["candidates_m2"] - f["not_housing_m2"] - f["very_low_m2"] - f["wall_m2"] == pytest.approx(f["counted_m2"])
    assert f["modules"] == pytest.approx(f["counted_m2"] * model.MODULE_SHARE / model.MODULE_M2)


def test_constants():
    assert (model.HEIGHT_MIN_M, model.HEIGHT_MAX_M, model.MIN_ROOF_M2, model.NEIGHBOUR_GAP_M, model.TALLER_BY_M,
            model.WALL_GAP_M, model.VERY_LOW_M, model.MODULE_SHARE, model.MODULE_M2, model.SIMPLIFY_M) == (
        2.5, 8.0, 200.0, 1.0, 3.0, 2.5, 3.2, 0.5, 25.0, 1.0)


def test_area_values_and_unassigned():
    zones = [box(-1e6, -1e6, 1e6, 1e6)]
    rows = [part("a", 0, 0, 20, 10, 4.0),            # district d1, quarter q1
            part("b", 100, 0, 20, 15, 4.0),          # district d1, no quarter
            part("c", 300, 0, 20, 10, 4.0),          # district d2, quarter q2
            part("d", 500, 0, 20, 10, 4.0),          # no district
            part("e", 600, 0, 20, 10, 3.0),          # very low, in no area: does not count
            part("w", 300, 10, 20, 10, 9.0, flat=False)]  # a wall along c: 50 m² of c stay free
    roofs = find_roofs(frame(*rows), zones)
    d1, d2, d3 = (Area("d1", "D1", "q1", "s", box(0, -10, 200, 20)), Area("d2", "D2", "q2", "s", box(250, -10, 350, 20)),
                  Area("d3", "D3", "q2", "s", box(900, 0, 910, 10)))
    q1, q2 = Area("q1", "Q1", "", "", box(0, -10, 50, 20)), Area("q2", "Q2", "", "", box(250, -10, 350, 20))
    districts, quarters, outside, no_quarter = area_values(roofs, [d1, d2, d3], [q1, q2])
    assert districts.set_index("id")["ROOF_FLAT"].round(2).to_dict() == {"d1": 500.0, "d2": 150.0, "d3": 0.0}
    assert quarters.set_index("id")["ROOF_FLAT"].round(2).to_dict() == {"q1": 200.0, "q2": 150.0}
    assert sorted(r.building for r in outside) == ["d", "e"]
    assert [r.building for r in no_quarter] == ["b"]
