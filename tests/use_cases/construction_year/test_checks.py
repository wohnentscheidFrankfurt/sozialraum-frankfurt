from pipeline.use_cases.construction_year.checks import check_construction_year
from pipeline.shared.core.checks import FAIL, OK

TABLE = {2011: {"pre1919": 67328, "1949_1978": 187254, "total": 365401},
         2022: {"pre1919": 66790, "1949_1978": 189598, "total": 402826}}
GRID_2011 = {"pre1919": 64223, "1949_1978": 185741, "total": 364048}
SHARES = {"pre1919": 16.45, "1949_1978": 47.57}  # city values of the build: class 2011 capped per cell ÷ dwellings 2022


def test_check_construction_year():
    """pipeline/use_cases/construction_year/README.md: grid against 4000W-1008, city shares against the
    table shares of 2022. The ⓘ names no compared numbers (docs/texts.md, Lines)."""
    checks = check_construction_year(GRID_2011, TABLE, SHARES)
    assert [c.status for c in checks] == [OK] * 5, [c.text for c in checks]
    assert "4000W-1008" in checks[0].name and not any("ⓘ" in c.name for c in checks)
    status = lambda cs, name: {c.name: c.status for c in cs}[name]
    grid = "Construction year: grid 2011 against 4000W-1008, "
    assert status(check_construction_year(GRID_2011 | {"pre1919": 60000}, TABLE, SHARES), grid + "pre1919") == FAIL
    too_low = check_construction_year(GRID_2011 | {"1949_1978": 181000}, TABLE, SHARES)
    assert status(too_low, grid + "1949_1978") == FAIL
    assert status(check_construction_year(GRID_2011 | {"total": 360000}, TABLE, SHARES), grid + "total") == FAIL
    share = "Construction year: city share against 4000W-1008 (2022), "
    # absolute tolerance 2.0 points: conversions since 2011 are missing in the estimate
    assert status(check_construction_year(GRID_2011, TABLE, SHARES | {"pre1919": 18.5}), share + "pre1919") == OK
    assert status(check_construction_year(GRID_2011, TABLE, SHARES | {"pre1919": 18.7}), share + "pre1919") == FAIL
