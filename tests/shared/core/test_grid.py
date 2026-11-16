import pytest

from pipeline.shared.core.grid import cell_center, km_cell, km_cell_corner


def test_cell_center_is_the_middle_of_the_cell():
    assert cell_center("CRS3035RES100mN3000600E4226700") == (4226750, 3000650)


def test_cell_center_rejects_foreign_ids():
    with pytest.raises(ValueError, match="unknown grid id"):
        cell_center("100mN26865")


def test_km_cell_floors_north_and_east_to_the_kilometre():
    assert km_cell("CRS3035RES100mN3002900E4222800") == "CRS3035RES1000mN3002000E4222000"
    assert km_cell("CRS3035RES100mN3002000E4222000") == "CRS3035RES1000mN3002000E4222000"


def test_km_cell_rejects_foreign_ids():
    with pytest.raises(ValueError, match="unknown grid id"):
        km_cell("CRS3035RES1000mN3002000E4222000")


def test_km_cell_corner_is_the_lower_left_corner():
    assert km_cell_corner("CRS3035RES1000mN3002000E4222000") == (4222000, 3002000)
    with pytest.raises(ValueError, match="unknown grid id"):
        km_cell_corner("CRS3035RES100mN3002900E4222800")
