import pandas as pd

from pipeline.use_cases.ownership_cells.checks import check_assigned_total, check_unassigned
from pipeline.shared.zensus.model import CLASSES


def test_check_assigned_total():
    ownership = pd.DataFrame([{**{f"dw_{k}": 1.0 for k in CLASSES}, "dw_unassigned": 2.0}])
    assert check_assigned_total(ownership, 10).status == "OK"
    assert check_assigned_total(ownership, 12).status == "FAIL"
    assert check_assigned_total(ownership, 10).name == "Ownership: assigned plus unassigned"


def test_check_unassigned():
    c = check_unassigned(11533.4, 390491)
    assert c.status == "OK" and c.name == "Ownership: no ownership type"
    assert "11,533 of 390,491 dwellings (3.0 %)" in c.text and "allowed up to 5 %" in c.text
    assert check_unassigned(28778, 390491).status == "WARN"
    assert check_unassigned(0, 0).status == "OK"
