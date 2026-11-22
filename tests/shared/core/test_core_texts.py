"""The shared sentences of shared/core live in texts.de.yaml; the helpers fill the templates of that file."""
from pipeline.shared.core import indicator
from pipeline.shared.core.indicator import CORE

DE = CORE["de"]


def test_field_sum_holds_the_midpoint_sentence():
    assert DE["field_sum"].endswith(DE["field_midpoint"]) and "{@" not in DE["field_sum"]


def test_helpers_put_in_the_keys_of_the_callers_texts(tmp_path):
    from pipeline.shared.core import texts as texts_module
    from pipeline.shared.core.texts import package_texts
    folder = tmp_path / "pkg"
    folder.mkdir()
    (folder / "texts.de.yaml").write_text(
        'vacant_dative: "<vacant>"\nrented_dative: "<rented>"\ndwellings: "<dwellings>"\n', encoding="utf-8")
    texts_module._CACHE.clear()
    t = package_texts(str(folder / "catalog.py"))["de"]
    rounding = indicator.tooltip_rounding(t, "vacant_dative", 7)
    assert rounding.count("<vacant>") == 2 and rounding.count("7") == 3 and "{" not in rounding
    mean = indicator.field_mean(t, "rented_dative")
    assert "<rented>" in mean and mean.endswith(DE["field_midpoint"])
    assert "{range_K} <dwellings>" in indicator.estimate_range(t, "K", "dwellings")
    assert "{range_K} " + DE["units.points"] in indicator.estimate_range(t, "K")
    assert "{high_K} " + DE["units.points"] in indicator.estimate_up_to(t, "K")
    backtest = indicator.estimate_backtest(t, "K", 4, 5)
    assert backtest.startswith(DE["test_2011"]) and "In 4 von 5 " in backtest and "{high_K}" in backtest


def test_late_placeholders_survive():
    assert "{range_OWN_COOP}" in indicator.estimate_range(DE, "OWN_COOP")
    assert "{high_OWN_COOP}" in indicator.estimate_up_to(DE, "OWN_COOP")
