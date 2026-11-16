import pandas as pd
from shapely.geometry import box

from pipeline.shared.core.checks import FAIL, OK, WARN
from pipeline.use_cases.flat_roofs.checks import (check_as_of, check_building_code, check_counts, check_funnel,
                                                  check_reference, check_unassigned, check_wall_strip)
from pipeline.use_cases.flat_roofs.model import Roof

F = {"candidates_m2": 1000.0, "not_housing_m2": 300.0, "very_low_m2": 50.0, "wall_m2": 100.0, "counted_m2": 550.0,
     "modules": 11.0}


def roof(building="a", use="31001_2000", area=500.0, height=6.4, wall=0.0, housing=True):
    return Roof(building, use, area, height, wall, False, housing, box(0, 0, 1, 1), 0.5, 0.5)


def gem(**kw):
    return pd.DataFrame({"gemarkung": ["A", "B"], "buildings": [10, 20], "parsed": [10, 20],
                         "delivered": ["2026-06-26", "2026-06-26"], **kw})


def test_check_counts():
    assert check_counts(gem()).status == OK
    c = check_counts(gem(parsed=[10, 19]))
    assert c.status == FAIL and "B" in c.text


def test_check_as_of():
    created = pd.Series(["2020", "2020", "2020", "2019"])
    c = check_as_of(gem(), created)
    assert c.status == OK and "26.6.2026" in c.text and "2020" in c.text
    assert check_as_of(gem(delivered=["2026-06-26", "2026-07-01"]), created).status == FAIL
    assert check_as_of(gem(), pd.Series(["2019", "2019", "2020"])).status == FAIL


def test_check_reference():
    ref = pd.DataFrame({"building": ["a", "b"], "function": ["31001_2000", "31001_2000"],
                        "area_m2": [500.0, 100.0], "height_m": [6.4, 5.0], "source": ["s", "s"]})
    assert check_reference([roof("a")], ref.iloc[:1]).status == OK
    c = check_reference([roof("a")], ref)
    assert c.status == FAIL and "b" in c.text
    assert check_reference([roof("a", area=502.0)], ref.iloc[:1]).status == FAIL
    assert check_reference([roof("a", height=6.6)], ref.iloc[:1]).status == FAIL
    assert check_reference([roof("a", use="31001_1000")], ref.iloc[:1]).status == FAIL


def table(*values):
    return pd.DataFrame({"id": [f"i{i}" for i in range(len(values))], "ROOF_FLAT": list(values)})


def test_check_funnel_ok_and_fail():
    assert check_funnel(F, table(300.0, 250.0), table(550.0), []).status == OK
    assert check_funnel({**F, "counted_m2": 560.0}, table(560.0), table(560.0), []).status == FAIL
    assert check_funnel({**F, "wall_m2": 90.0}, table(550.0), table(550.0), []).status == FAIL  # the strip counts
    assert check_funnel(F, table(300.0, 200.0), table(550.0), []).status == FAIL
    c = check_funnel(F, table(550.0), table(500.0), [roof("lost", area=50.0)])
    assert c.status == FAIL and "lost" in c.text


def test_check_unassigned():
    assert check_unassigned([roof()] * 5).status == OK
    c = check_unassigned([roof()] * 6)
    assert c.status == WARN and "6" in c.text


def test_check_wall_strip():
    c = check_wall_strip([roof("a", wall=50.0), roof("b"), roof("c", area=300.0, wall=300.0, housing=False)])
    assert c.status == OK and "1 counted" in c.text
    over = check_wall_strip([roof("a", wall=500.5)])
    assert over.status == FAIL and "a" in over.text
    assert check_wall_strip([roof("n", wall=-0.5)]).status == FAIL
    assert check_wall_strip([roof("e", wall=500.000001)]).status == OK  # float noise of the overlay


def test_check_building_code():
    """The 2,5 m of the Regel stand in the synopsis of Baupaket I (the old column says 3 m)."""
    new = "4In allen Fällen muss die Tiefe der \nAbstandsflächen mindestens 2,50 m betragen. \n"
    old = "4In allen Fällen muss die Tiefe der Abstandsflächen mindestens 3 m betragen."
    assert check_building_code(["Synopse", old + new]).status == OK
    c = check_building_code(["Synopse", old])
    assert c.status == FAIL and "2,50 m" in c.text
