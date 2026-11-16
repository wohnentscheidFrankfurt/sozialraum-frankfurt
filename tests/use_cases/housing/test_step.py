
import pandas as pd
import pytest

from pipeline import config
from pipeline.engine.datasets import (CELLS_2022, HOUSING_BY_DISTRICT, HOUSING_BY_QUARTER, HOUSING_CALC_EXAMPLES,
                                      HOUSING_CHECKS, HOUSING_CITY)
from pipeline.use_cases.housing import step
from pipeline.use_cases.housing.step import STEP

KM = "CRS3035RES1000mN3002000E4222000"


def _km_extract(path, column, rate):
    path.write_text(f"GITTER_ID_1km;x_mp_1km;y_mp_1km;{column};werterlaeuternde_Zeichen\n"
                    f"{KM};4222500;3002500;{rate};\n", encoding="utf-8")
    return path


def _run(tmp_path, run_step):
    """The step on three cells of one 1 km cell: two inner cells in Gallus and one edge cell."""
    ids = [f"CRS3035RES100mN3002{i}00E4222000" for i in range(3)]  # all in one 1 km cell
    cells = pd.DataFrame({
        "cell_id": ids, "edge": [0, 0, 1], "district": ["d1", "d2", None], "quarter": ["Gallus", "Gallus", None],
        "pop": [100, 300, 9], "dwellings": [50, 150, 100], "vacancy_rate": [0.0, 10.0, 0.0],
        "owner_rate": [20.0, None, 50.0], "rent_sqm": [10.0, 14.0, 99.0], "rented_dwellings": [40, 120, 9],
        "vacancy_rate_market": [2.0, None, 0.0],
        "vacancy_rate_dash": [0, 0, 1], "vacancy_rate_market_dash": [0, 1, 1]})
    # the 1 km rates: 12.5 % of 300 dwellings = 37.5 vacant; known 15 (cell 2); the edge cell takes the rest 22.5
    km = {"zensus_vacancy.zip": _km_extract(tmp_path / "v.csv", "Leerstandsquote", "12,5"),
          "zensus_vacancy_market.zip": _km_extract(tmp_path / "m.csv", "marktaktive_Leerstandsquote", "3,0")}
    store, _ = run_step(tmp_path, STEP, {CELLS_2022: cells}, ZENSUS_4000W=config.ZENSUS_4000W,
                        ZENSUS_4000W_0001=config.ZENSUS_4000W_0001, ZENSUS_4000W_0004=config.ZENSUS_4000W_0004,
                        CHECK_REFERENCE_CSV=config.CHECK_REFERENCE_CSV, GRID_KM_EXTRACTS=km)
    return store


def test_step_on_a_fake_store(tmp_path, run_step, monkeypatch):
    monkeypatch.setattr(step, "CALC_EXAMPLE_QUARTERS", dict.fromkeys(step.CALC_EXAMPLE_QUARTERS, "Gallus"))
    store = _run(tmp_path, run_step)
    d = store.read(HOUSING_BY_DISTRICT).set_index("id")
    assert list(d.index) == ["d1", "d2"] and d.loc["d1", "HOU_RENT"] == pytest.approx(10.0)
    q = store.read(HOUSING_BY_QUARTER).set_index("id")
    assert list(q.index) == ["Gallus"] and q.loc["Gallus", "HOU_RENT"] == pytest.approx(13.0)  # edge cell not counted
    city = {r["indicator"]: r for r in store.read(HOUSING_CITY)}
    # inner cells only; the edge cell took the rest of the 1 km cell, so the inner cells keep 15 of 200 dwellings
    assert city["HOU_VACANT_ALL"]["value"] == pytest.approx(7.5) and city["HOU_VACANT_ALL"]["kind"] == "computed"
    # market: 3 % of 300 = 9 vacant; known 1 (cell 1); the rest 8 over 250 dwellings of the dash cells (150 inner)
    assert city["HOU_VACANT_MARKET"]["value"] == pytest.approx(100 * (1 + 8 * 150 / 250) / 200)
    assert not [k for k in city if k.startswith("COV_") or k.endswith("_DWELLINGS")]  # no city value of a count
    assert d.loc["d1", "HOU_VACANT_ALL_DWELLINGS"] == pytest.approx(0.0)
    assert d.loc["d2", "HOU_VACANT_ALL_DWELLINGS"] == pytest.approx(15.0)
    assert q.loc["Gallus", "HOU_VACANT_ALL_DWELLINGS"] == pytest.approx(15.0)
    assert {"COV_HOU_RENT", "HOU_RENT"} <= set(d.columns)  # coverage is per area, in the check report
    assert store.read(HOUSING_CHECKS)


def test_step_writes_the_worked_examples(tmp_path, run_step, monkeypatch):
    monkeypatch.setattr(step, "CALC_EXAMPLE_QUARTERS", dict.fromkeys(step.CALC_EXAMPLE_QUARTERS, "Gallus"))
    store = _run(tmp_path, run_step)
    q = store.read(HOUSING_BY_QUARTER).set_index("id")
    examples = store.read(HOUSING_CALC_EXAMPLES)
    assert set(examples) == {"HOU_VACANT_ALL", "HOU_VACANT_MARKET", "HOU_RENTERS"}
    for kid, e in examples.items():
        assert e["area"] == "Gallus" and e["rows"][-1]["number"] == round(q.loc["Gallus", kid], 1), kid
    # all: 15 vacant in the fields, no „–“ cell inside; market: 1 in the fields + 4.8 in the inner „–“ cell
    assert [r["number"] for r in examples["HOU_VACANT_ALL"]["rows"]] == [15, 200, 7.5]
    assert [r["number"] for r in examples["HOU_VACANT_MARKET"]["rows"]] == [1, 5, 6, 200, 2.9]
    assert [r["number"] for r in examples["HOU_RENTERS"]["rows"]] == [50, 10, 40, 50, 80.0]


def test_step_fails_without_the_example_stadtteil(tmp_path, run_step):
    with pytest.raises(ValueError, match="no Stadtteil Innenstadt"):
        _run(tmp_path, run_step)
