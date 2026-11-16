import pandas as pd

from pipeline.shared.zensus.checks import grid_checks


def test_grid_checks_names_and_status():
    cells = pd.DataFrame({"edge": [0, 0, 1], "pop": [600, 400, 3], "dwellings": [300, 200, 1]})
    checks = grid_checks(cells, {"pop_zensus_2022": 1000, "dwellings_zensus_2022": 500})
    assert [(c.name, c.status) for c in checks] == [("Grid: population", "OK"),
                                                    ("Grid: population in edge cells", "OK"),
                                                    ("Grid: dwellings", "OK")]
    assert grid_checks(cells, {"pop_zensus_2022": 2000, "dwellings_zensus_2022": 500})[0].status == "FAIL"


def test_dwellings_check_accepts_the_known_gap_to_the_table_and_flags_more():
    """The grid holds about 3 % fewer dwellings than the table (docs/data-rules.md, Traps of the Zensus grid): OK at
    390,491, not at 380,000."""
    reference = {"pop_zensus_2022": 1000, "dwellings_zensus_2022": 402826}
    for dwellings, status in ((390491, "OK"), (380000, "FAIL")):
        cells = pd.DataFrame({"edge": [0], "pop": [1000], "dwellings": [dwellings]})
        assert grid_checks(cells, reference)[2].status == status
