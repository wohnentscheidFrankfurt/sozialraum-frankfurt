"""The German and the English file of a package say the same: same keys, placeholders and numbers, and the
English text is not older than the German one (`pipeline/lock_texts.py`, docs/texts.md)."""
from __future__ import annotations

from pathlib import Path

import pytest

from pipeline import lock_texts as lt
from pipeline.shared.core.texts import CORE_FOLDER, LANGUAGES

# key -> reason: the English text writes a number differently (a word, a month name), so the digits differ
ALLOWED_NUMBERS: dict[str, str] = {}


def _write(folder: Path, lang: str, body: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"texts.{lang}.yaml").write_text(body, encoding="utf-8")


def _pair(tmp_path: Path, de: str, en: str, core_de: str = "shared: \"Shared.\"\n",
          core_en: str = "shared: \"Shared.\"\n") -> tuple[Path, Path]:
    """A core folder and a package folder, each with both languages."""
    core, pkg = tmp_path / "core", tmp_path / "pkg"
    _write(core, "de", core_de)
    _write(core, "en", core_en)
    _write(pkg, "de", de)
    _write(pkg, "en", en)
    return pkg, core


def test_packages_are_found_by_their_german_file(tmp_path):
    _pair(tmp_path, 'a: "x"\n', 'a: "x"\n')
    _write(tmp_path / "other", "de", 'a: "x"\n')
    assert [p.name for p in lt.packages(tmp_path)] == ["core", "other", "pkg"]
    assert [p.name for p in lt.packages(tmp_path, with_english=True)] == ["core", "pkg"]


# --- fixtures: each guard fails on a broken pair and passes on a fixed one ---

def test_missing_and_extra_keys_are_listed(tmp_path):
    pkg, core = _pair(tmp_path, 'a: "x"\nb:\n  c: "y"\n', 'a: "x"\nd: "z"\n')
    message = lt.key_problems(pkg, core)
    assert "b.c" in message and "missing" in message and "d" in message and "extra" in message
    _write(pkg, "en", 'a: "x"\nb:\n  c: "y"\n')
    assert lt.key_problems(pkg, core) == ""


def test_a_missing_language_file_is_reported(tmp_path):
    pkg, core = _pair(tmp_path, 'a: "x"\n', 'a: "x"\n')
    (pkg / "texts.en.yaml").unlink()
    assert lt.missing_languages(pkg) == ["en"]
    _write(pkg, "en", 'a: "x"\n')
    assert lt.missing_languages(pkg) == []


def test_placeholders_must_match_per_key(tmp_path):
    pkg, core = _pair(tmp_path, 'a: "{n} homes"\nb: "none"\n', 'a: "{n} homes {extra}"\nb: "none"\n')
    problems = lt.placeholder_problems(pkg, core)
    assert len(problems) == 1 and problems[0].startswith("a:") and "extra" in problems[0]
    _write(pkg, "en", 'a: "{n} dwellings"\nb: "none"\n')
    assert lt.placeholder_problems(pkg, core) == []


def test_placeholders_are_compared_after_references_resolve(tmp_path):
    pkg, core = _pair(tmp_path, 'a: "{@core.shared} {n}"\n', 'a: "{@core.shared} {n}"\n',
                      core_de='shared: "Of {k}."\n', core_en='shared: "Von {k}."\n')
    assert lt.placeholder_problems(pkg, core) == []
    _write(core, "en", 'shared: "Of {other}."\n')
    assert lt.placeholder_problems(pkg, core)


def test_an_unknown_reference_is_reported(tmp_path):
    pkg, core = _pair(tmp_path, 'a: "{@b}"\nb: "x"\n', 'a: "{@missing}"\nb: "x"\n')
    problems = lt.reference_problems(pkg, core)
    assert len(problems) == 1 and "en" in problems[0] and "missing" in problems[0]
    _write(pkg, "en", 'a: "{@b}"\nb: "x"\n')
    assert lt.reference_problems(pkg, core) == []


def test_a_changed_german_text_makes_the_lock_stale(tmp_path):
    pkg, core = _pair(tmp_path, 'a: "one"\nb: "two"\n', 'a: "one"\nb: "two"\n')
    assert lt.stale_keys(pkg, core) == ["a", "b"]  # no lock yet
    assert lt.write_lock(pkg, core) == ["a", "b"]  # new keys count as changed
    assert lt.stale_keys(pkg, core) == []
    _write(pkg, "de", 'a: "one changed"\nb: "two"\n')
    assert lt.stale_keys(pkg, core) == ["a"]
    assert lt.write_lock(pkg, core) == ["a"]  # the command names the keys whose hash changed
    assert lt.stale_keys(pkg, core) == []


def test_a_changed_core_sentence_makes_the_dependent_key_stale(tmp_path):
    pkg, core = _pair(tmp_path, 'a: "{@core.shared} Own."\nb: "plain"\n', 'a: "{@core.shared} Eigen."\nb: "plain"\n')
    lt.write_lock(pkg, core)
    _write(core, "de", 'shared: "Changed."\n')
    assert lt.stale_keys(pkg, core) == ["a"]


def test_the_lock_is_sorted_one_line_per_key_with_ten_hex_digits(tmp_path):
    pkg, core = _pair(tmp_path, 'b: "two"\na: "one"\n', 'b: "two"\na: "one"\n')
    lt.write_lock(pkg, core)
    lines = (pkg / "texts.en.lock").read_text(encoding="utf-8").splitlines()
    assert [line.split()[0] for line in lines] == ["a", "b"]
    assert all(len(line.split()[1]) == 10 for line in lines)
    assert lines[0].split()[1] == "fe05bcdcdc"  # sha1("one")[:10]


def test_the_command_takes_folders_and_defaults_to_every_package_with_english(tmp_path):
    pkg, core = _pair(tmp_path, 'a: "one"\n', 'a: "one"\n')
    assert lt.main([str(pkg)], core_folder=core, root=tmp_path) == 0
    assert (pkg / "texts.en.lock").is_file() and not (core / "texts.en.lock").exists()
    assert lt.main([], core_folder=core, root=tmp_path) == 0
    assert (core / "texts.en.lock").is_file()


def test_different_numbers_fail_and_equal_numbers_in_other_formats_pass(tmp_path):
    pkg, core = _pair(tmp_path, 'a: "1.754 homes, 6,6 %"\nb: "{n_5} of 5"\n', 'a: "1,754 homes, 7.6%"\nb: "{n_6} of 5"\n')
    problems = lt.number_problems(pkg, core, {})
    assert len(problems) == 1 and problems[0].startswith("a:")  # b: digits in {placeholders} are ignored
    _write(pkg, "en", 'a: "6.6% of 1,754 homes"\nb: "{n_6} of 5"\n')
    assert lt.number_problems(pkg, core, {}) == []


def test_a_number_written_as_a_word_needs_a_reason(tmp_path):
    pkg, core = _pair(tmp_path, 'a: "3 mal"\n', 'a: "three times"\n')
    assert lt.number_problems(pkg, core, {}) != []
    assert lt.number_problems(pkg, core, {"a": "written out"}) == []


# --- the repo: every package that has an English file ---

def _english_packages() -> list[Path]:
    return lt.packages(lt.PIPELINE, with_english=True)


def _ids(folders: list[Path]) -> list[str]:
    return [str(f.relative_to(lt.PIPELINE)) for f in folders]


@pytest.mark.skipif("en" not in LANGUAGES, reason="English files land with the phase 2 tasks")
def test_every_package_has_both_languages():
    missing = {str(f.relative_to(lt.PIPELINE)): m for f in lt.packages(lt.PIPELINE) if (m := lt.missing_languages(f))}
    assert not missing, missing


@pytest.mark.parametrize("folder", _english_packages(), ids=_ids(_english_packages()))
def test_same_keys(folder):
    assert lt.key_problems(folder, CORE_FOLDER) == ""


@pytest.mark.parametrize("folder", _english_packages(), ids=_ids(_english_packages()))
def test_same_placeholders(folder):
    assert lt.placeholder_problems(folder, CORE_FOLDER) == []


@pytest.mark.parametrize("folder", _english_packages(), ids=_ids(_english_packages()))
def test_references_resolve(folder):
    assert lt.reference_problems(folder, CORE_FOLDER) == []


@pytest.mark.parametrize("folder", _english_packages(), ids=_ids(_english_packages()))
def test_lock_is_fresh(folder):
    stale = lt.stale_keys(folder, CORE_FOLDER)
    name = folder.relative_to(lt.ROOT)
    assert not stale, [f"{key}: German text changed; update the English text, then run "
                       f"`python -m pipeline.lock_texts {name}`" for key in stale]


@pytest.mark.parametrize("folder", _english_packages(), ids=_ids(_english_packages()))
def test_same_numbers(folder):
    assert lt.number_problems(folder, CORE_FOLDER, ALLOWED_NUMBERS) == []
