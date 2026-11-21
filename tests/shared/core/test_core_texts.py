"""The shared sentences of shared/core live in texts.de.yaml; the old constants and helpers are aliases over it."""
import pytest

from pipeline.shared.core import indicator
from pipeline.shared.core.indicator import CORE

KEYS = {"QUARTERS_RULE": "quarters_rule", "TIP_DWELLINGS_RULE": "tip_dwellings_rule",
        "TIP_DWELLINGS_UNCERTAINTY": "tip_dwellings_uncertainty", "TEST_2011": "test_2011",
        "FIELD_MIDPOINT": "field_midpoint", "FIELD_EDGE": "field_edge", "FIELD_SUM": "field_sum",
        "DASH_MEANING": "dash_meaning", "Z22": "z22", "Z22_AS_OF": "z22_as_of", "Z11_AS_OF": "z11_as_of",
        "ZENSUS_LICENSE": "zensus_license"}


@pytest.mark.parametrize("name", KEYS)
def test_aliases_match_core_texts(name):
    assert getattr(indicator, name) == CORE["de"][KEYS[name]]


def test_field_sum_holds_the_midpoint_sentence():
    assert indicator.FIELD_SUM.endswith(indicator.FIELD_MIDPOINT) and "{@" not in indicator.FIELD_SUM


def test_old_helpers_put_in_their_arguments():
    rounding = indicator.tooltip_rounding("<dwellings>", 7)
    assert rounding.count("<dwellings>") == 2 and rounding.count("7") == 3 and "{" not in rounding
    assert "<weight>" in indicator.field_mean("<weight>") and indicator.field_mean("x").endswith(indicator.FIELD_MIDPOINT)
    assert "{range_K} <unit>" in indicator.estimate_range("K", "<unit>")
    assert "{range_K} " + CORE["de"]["units.points"] in indicator.estimate_range("K")
    assert "{high_K} " + CORE["de"]["units.points"] in indicator.estimate_up_to("K")
    backtest = indicator.estimate_backtest("K", 4, 5)
    assert backtest.startswith(indicator.TEST_2011) and "In 4 von 5 " in backtest and "{high_K}" in backtest


def test_new_helpers_take_keys_of_the_callers_texts(tmp_path):
    from pipeline.shared.core import texts as texts_module
    from pipeline.shared.core.texts import package_texts
    folder = tmp_path / "pkg"
    folder.mkdir()
    (folder / "texts.de.yaml").write_text('vacant_dative: "<vacant>"\nrented_dative: "<rented>"\ndwellings: "<dwellings>"\n',
                                          encoding="utf-8")
    texts_module._CACHE.clear()
    t = package_texts(str(folder / "catalog.py"))["de"]
    assert indicator.tooltip_rounding(t, "vacant_dative", 10) == indicator.tooltip_rounding("<vacant>", 10)
    assert indicator.field_mean(t, "rented_dative") == indicator.field_mean("<rented>")
    assert indicator.estimate_range(t, "OWN_PUBLIC") == indicator.estimate_range("OWN_PUBLIC")
    assert indicator.estimate_range(t, "OWN_PUBLIC_DWELLINGS", "dwellings") == indicator.estimate_range(
        "OWN_PUBLIC_DWELLINGS", "<dwellings>")
    assert indicator.estimate_up_to(t, "OWN_COOP") == indicator.estimate_up_to("OWN_COOP")
    assert indicator.estimate_backtest(t, "OWN_STATE", 40, 45) == indicator.estimate_backtest("OWN_STATE", 40, 45)


def test_late_placeholders_survive():
    assert "{range_OWN_COOP}" in indicator.estimate_range(CORE["de"], "OWN_COOP")
    assert "{high_OWN_COOP}" in indicator.estimate_up_to(CORE["de"], "OWN_COOP")
