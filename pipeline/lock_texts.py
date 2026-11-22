"""Staleness lock of the English texts, and the checks of a German/English pair (tests/test_texts_pairs.py).

Next to each `texts.en.yaml` lies `texts.en.lock`: one line per key, `<key> <hash>`, sorted. The hash is the first
10 hex digits of the SHA-1 of the German text of the key after its references are resolved. It records which
German text the English text translates. Run by hand after the English text changed:

    .venv/bin/python -I -m pipeline.lock_texts [<folder> ...]
"""
from __future__ import annotations

import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

from pipeline.shared.core.texts import CORE_FOLDER, SOURCE_LANGUAGE, raw_leaves, resolved_leaves

ROOT = Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "pipeline"
TARGET_LANGUAGE = "en"
_PLACEHOLDER = re.compile(r"\{(\w+)\}")
_NUMBER = re.compile(r"\d(?:[\d.,]*\d)?")


def _file(folder: Path, lang: str, ext: str = "yaml") -> Path:
    return folder / f"texts.{lang}.{ext}"


def packages(root: Path = PIPELINE, *, with_english: bool = False) -> list[Path]:
    """The folders below `root` with a German file; with `with_english` only those that also have an English one."""
    found = sorted(f.parent for f in root.rglob(f"texts.{SOURCE_LANGUAGE}.yaml"))
    return [f for f in found if not with_english or _file(f, TARGET_LANGUAGE).is_file()]


def missing_languages(folder: Path) -> list[str]:
    return [lang for lang in (SOURCE_LANGUAGE, TARGET_LANGUAGE) if not _file(folder, lang).is_file()]


def resolved(folder: Path, lang: str, core_folder: Path = CORE_FOLDER) -> dict[str, str]:
    """The texts of one language of a package, references resolved."""
    core_file = None if folder == core_folder else _file(core_folder, lang)
    return resolved_leaves(_file(folder, lang), core_file)


def key_problems(folder: Path, core_folder: Path = CORE_FOLDER) -> str:
    """Empty when both files hold the same keys; else the missing and extra keys of the English file."""
    german, english = set(raw_leaves(_file(folder, SOURCE_LANGUAGE))), set(raw_leaves(_file(folder, TARGET_LANGUAGE)))
    parts = []
    if german - english:
        parts.append(f"missing in {TARGET_LANGUAGE}: {', '.join(sorted(german - english))}")
    if english - german:
        parts.append(f"extra in {TARGET_LANGUAGE}: {', '.join(sorted(english - german))}")
    return "; ".join(parts)


def reference_problems(folder: Path, core_folder: Path = CORE_FOLDER) -> list[str]:
    """A `{@key}` that points nowhere or a cycle, in either file."""
    problems = []
    for lang in (SOURCE_LANGUAGE, TARGET_LANGUAGE):
        try:
            resolved(folder, lang, core_folder)
        except (KeyError, ValueError) as error:
            problems.append(f"{lang}: {error.args[0]}")
    return problems


def _pair(folder: Path, core_folder: Path) -> list[tuple[str, str, str]]:
    """(key, German text, English text) of the keys both files hold, references resolved."""
    german, english = resolved(folder, SOURCE_LANGUAGE, core_folder), resolved(folder, TARGET_LANGUAGE, core_folder)
    return [(key, german[key], english[key]) for key in german if key in english]


def placeholder_problems(folder: Path, core_folder: Path = CORE_FOLDER) -> list[str]:
    problems = []
    for key, de, en in _pair(folder, core_folder):
        a, b = set(_PLACEHOLDER.findall(de)), set(_PLACEHOLDER.findall(en))
        if a != b:
            problems.append(f"{key}: placeholders differ; only German {sorted(a - b)}, only English {sorted(b - a)}")
    return problems


def numbers(text: str) -> Counter[str]:
    """The numbers of a text as digits only, so `1.754`, `1,754` and `6,6`, `6.6` compare equal.
    Digits inside `{placeholders}` do not count."""
    return Counter(re.sub(r"\D", "", n) for n in _NUMBER.findall(_PLACEHOLDER.sub("", text)))


def number_problems(folder: Path, core_folder: Path, allowed: dict[str, str]) -> list[str]:
    """Keys whose two texts hold different numbers and have no reason in `allowed`."""
    return [f"{key}: numbers differ; German {sorted(numbers(de).elements())}, English {sorted(numbers(en).elements())}"
            for key, de, en in _pair(folder, core_folder) if key not in allowed and numbers(de) != numbers(en)]


def _hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def current_lock(folder: Path, core_folder: Path = CORE_FOLDER) -> dict[str, str]:
    """Key -> hash of the German text, for every key of the English file."""
    german = resolved(folder, SOURCE_LANGUAGE, core_folder)
    return {key: _hash(german[key]) for key in raw_leaves(_file(folder, TARGET_LANGUAGE)) if key in german}


def read_lock(folder: Path) -> dict[str, str]:
    file = _file(folder, TARGET_LANGUAGE, "lock")
    if not file.is_file():
        return {}
    return dict(line.split() for line in file.read_text(encoding="utf-8").splitlines() if line.strip())


def stale_keys(folder: Path, core_folder: Path = CORE_FOLDER) -> list[str]:
    """Keys whose German text differs from the one in the lock, or that the lock lacks."""
    lock = read_lock(folder)
    return sorted(key for key, digest in current_lock(folder, core_folder).items() if lock.get(key) != digest)


def write_lock(folder: Path, core_folder: Path = CORE_FOLDER) -> list[str]:
    """Rewrite the lock from the current German texts. Returns the keys whose hash changed (new keys included)."""
    changed = stale_keys(folder, core_folder)
    lock = current_lock(folder, core_folder)
    _file(folder, TARGET_LANGUAGE, "lock").write_text(
        "".join(f"{key} {lock[key]}\n" for key in sorted(lock)), encoding="utf-8")
    return changed


def main(argv: list[str] | None = None, *, core_folder: Path = CORE_FOLDER, root: Path = PIPELINE) -> int:
    args = sys.argv[1:] if argv is None else argv
    folders = [Path(a).resolve() for a in args] or packages(root, with_english=True)
    for folder in folders:
        if missing_languages(folder):
            print(f"{folder}: needs texts.{SOURCE_LANGUAGE}.yaml and texts.{TARGET_LANGUAGE}.yaml", file=sys.stderr)
            return 1
    for folder in folders:
        for key in write_lock(folder, core_folder):
            print(f"{folder.name}: {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
