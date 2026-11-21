import datetime

import pytest

from pipeline.shared.core import texts as texts_module
from pipeline.shared.core.texts import LANGUAGES, Texts, package_texts, per_language

MONTHS_EN = "\n".join(f'  "{i}": {n}' for i, n in enumerate(
    "January February March April May June July August September October November December".split(), 1))


def write(folder, text, lang="de"):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"texts.{lang}.yaml").write_text(text, encoding="utf-8")


def load(tmp_path, text, core="", lang="de"):
    write(tmp_path / "pkg", text, lang)
    write(tmp_path / "core", core or "x: leer\n", lang)
    texts_module._CACHE.clear()
    return package_texts(str(tmp_path / "pkg" / "catalog.py"), core_folder=tmp_path / "core",
                         languages=(lang,))[lang]


def test_languages():
    assert LANGUAGES == ("de",)


def test_reference_resolves_in_file_and_core(tmp_path):
    t = load(tmp_path, 'a: "Eins {@b}"\nb: "zwei"\nc: "{@core.x}!"\n', core='x: "drei"\n')
    assert t["a"] == "Eins zwei"
    assert t["c"] == "drei!"


def test_reference_cycle_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="cycle"):
        load(tmp_path, 'a: "{@b}"\nb: "{@a}"\n')


def test_unknown_reference_names_file_and_key(tmp_path):
    with pytest.raises(KeyError) as e:
        load(tmp_path, 'a: "{@missing}"\n')
    assert "texts.de.yaml" in str(e.value) and "missing" in str(e.value)


@pytest.mark.parametrize("value", ["no", "yes", "2025", "1.5", "null"])
def test_non_string_leaf_is_rejected(tmp_path, value):
    with pytest.raises(ValueError, match="my_key"):
        load(tmp_path, f"my_key: {value}\n")


def test_unknown_core_reference_names_file_and_key(tmp_path):
    with pytest.raises(KeyError) as e:
        load(tmp_path, 'a: "{@core.nothing}"\n')
    assert "texts.de.yaml" in str(e.value) and "core.nothing" in str(e.value)


def test_missing_core_file_names_path(tmp_path):
    texts_module._CACHE.clear()
    write(tmp_path / "pkg", 'a: "x"\n')
    with pytest.raises(FileNotFoundError, match="core.*texts.de.yaml"):
        package_texts(str(tmp_path / "pkg" / "catalog.py"), core_folder=tmp_path / "core", languages=("de",))


def test_missing_month_names_language(tmp_path):
    t = load(tmp_path, 'a: "x"\n', core='months:\n  "3": März\n')
    with pytest.raises(KeyError, match="de"):
        t.month(5)


def test_fill_runs_once_over_the_placeholders(tmp_path):
    t = load(tmp_path, 'k: "{x} und {y}"\n')
    assert t.fill("k", x="{y}", y="B") == "{y} und B"


def test_missing_file_names_path(tmp_path):
    texts_module._CACHE.clear()
    with pytest.raises(FileNotFoundError, match="texts.de.yaml"):
        package_texts(str(tmp_path / "none" / "catalog.py"), core_folder=tmp_path, languages=("de",))


def test_fill_is_partial(tmp_path):
    t = load(tmp_path, 'k: "{x} und {range_A}"\n')
    assert t.fill("k", x=3) == "3 und {range_A}"


def test_tree_keeps_nesting(tmp_path):
    t = load(tmp_path, 'a:\n  b: "1x"\n  c:\n    d: "{@a.b}!"\ne: "z"\n')
    assert t.tree("a") == {"b": "1x", "c": {"d": "1x!"}}
    assert sorted(t.keys()) == ["a.b", "a.c.d", "e"]


def test_per_language(tmp_path):
    t = load(tmp_path, 'a: "x"\n')
    assert per_language(lambda tx: tx["a"] + "y", {"de": t}) == {"de": "xy"}


def test_date_and_month_de_and_en(tmp_path):
    day = datetime.date(2026, 3, 15)
    de = load(tmp_path / "de", 'a: "x"\n', core='months:\n  "3": März\n')
    assert de.date(day) == "15.3.2026"
    assert de.month(3) == "März"
    en = load(tmp_path / "en", 'a: "x"\n', core=f"months:\n{MONTHS_EN}\n", lang="en")
    assert en.date(day) == "15 March 2026"
    assert en.number(18.44, 1, "%") == "18.4%"
    assert en.number_range(0.6, 8.8) == "0.6 to 8.8"


def test_real_core_file_has_german_months():
    texts_module._CACHE.clear()
    core = package_texts(texts_module.__file__)["de"]
    assert core.month(3) == "März" and core.month(12) == "Dezember"
    assert isinstance(core, Texts)
