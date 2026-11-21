"""Loader of the language files `texts.<lang>.yaml` that lie next to the modules of a package.

A file holds nested mappings; every leaf is a text. A text holds `{name}` placeholders (filled by code or by the
build) and `{@key}` / `{@core.key}` references (resolved here: same file, or the core file of this folder).
The files are part of the code: they are read once and cached.
"""
from __future__ import annotations

import datetime
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

import yaml

from pipeline.shared.core.numbers import format_number, format_range

LANGUAGES: tuple[str, ...] = ("de",)
SOURCE_LANGUAGE = "de"
CORE_FOLDER = Path(__file__).parent
_PLACEHOLDER = re.compile(r"\{(\w+)\}")
_REFERENCE = re.compile(r"\{@([^{}]+)\}")
_CACHE: dict[tuple, dict[str, "Texts"]] = {}
T = TypeVar("T")


def _flatten(node: object, prefix: str, file: Path, out: dict[str, str]) -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            _flatten(value, f"{prefix}.{key}" if prefix else str(key), file, out)
    elif isinstance(node, str):
        out[prefix] = node
    else:
        raise ValueError(f"{file.name}: {prefix}: a text must be a string, found {node!r}; put it in quotes")


def _read(file: Path) -> dict[str, str]:
    if not file.is_file():
        raise FileNotFoundError(f"language file missing: {file}")
    out: dict[str, str] = {}
    _flatten(yaml.safe_load(file.read_text(encoding="utf-8")) or {}, "", file, out)
    return out


def _resolve(raw: dict[str, str], core: dict[str, str] | None, file: Path) -> dict[str, str]:
    """Replace every `{@key}`; `core` is the resolved core file (None inside the core file itself)."""
    done: dict[str, str] = {}

    def resolve(key: str, stack: tuple[str, ...]) -> str:
        if key in done:
            return done[key]
        if key in stack:
            raise ValueError(f"{file.name}: reference cycle {' -> '.join((*stack, key))}")

        def replace(match: re.Match) -> str:
            ref = match.group(1)
            if ref.startswith("core."):
                if core is None or ref[5:] not in core:
                    raise KeyError(f"{file.name}: {key}: unknown reference {{@{ref}}}")
                return core[ref[5:]]
            if ref not in raw:
                raise KeyError(f"{file.name}: {key}: unknown reference {{@{ref}}}")
            return resolve(ref, (*stack, key))

        done[key] = _REFERENCE.sub(replace, raw[key])
        return done[key]

    for key in raw:
        resolve(key, ())
    return done


@dataclass(frozen=True)
class Texts:
    lang: str
    _data: dict[str, str] = field(repr=False, compare=False)
    _core: dict[str, str] = field(repr=False, compare=False)

    def __getitem__(self, key: str) -> str:
        if key in self._data:
            return self._data[key]
        if key.startswith("core.") and key[5:] in self._core:
            return self._core[key[5:]]
        raise KeyError(f"no text {key!r} ({self.lang})")

    def keys(self) -> list[str]:
        return list(self._data)

    def tree(self, prefix: str) -> dict:
        """The nested mapping under a prefix, leaves resolved."""
        head = prefix + "."
        out: dict = {}
        for key, text in self._data.items():
            if key.startswith(head):
                *path, leaf = key[len(head):].split(".")
                node = out
                for part in path:
                    node = node.setdefault(part, {})
                node[leaf] = text
        if not out:
            raise KeyError(f"no texts under {prefix!r} ({self.lang})")
        return out

    def fill(self, key: str, **values: object) -> str:
        """The text with only the named placeholders filled; the others stay for the build."""
        return _PLACEHOLDER.sub(lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0), self[key])

    def number(self, value: float, decimals: int, unit: str = "") -> str:
        return format_number(value, decimals, unit, self.lang)

    def number_range(self, low: float, high: float, decimals: int = 1) -> str:
        return format_range(low, high, decimals, self.lang)

    def month(self, month: int) -> str:
        try:
            return self._core[f"months.{month}"]
        except KeyError:
            raise KeyError(f"no month {month} in the core texts ({self.lang})") from None

    def date(self, day: datetime.date) -> str:
        if self.lang == "de":
            return f"{day.day}.{day.month}.{day.year}"
        return f"{day.day} {self.month(day.month)} {day.year}"


def package_texts(module_file: str, *, core_folder: Path | None = None,
                  languages: tuple[str, ...] | None = None) -> dict[str, Texts]:
    """One Texts per language, read from `texts.<lang>.yaml` next to `module_file` and cached per folder.
    `core_folder` and `languages` are for tests."""
    folder = Path(module_file).parent
    core_folder = core_folder or CORE_FOLDER
    langs = languages or LANGUAGES
    cache_key = (folder, core_folder, langs)
    if cache_key not in _CACHE:
        found = {}
        for lang in langs:
            file = folder / f"texts.{lang}.yaml"
            core_file = core_folder / f"texts.{lang}.yaml"
            if folder == core_folder:
                core = _resolve(_read(file), None, file)
                found[lang] = Texts(lang, core, core)
                continue
            core = _resolve(_read(core_file), None, core_file)
            found[lang] = Texts(lang, _resolve(_read(file), core, file), core)
        _CACHE[cache_key] = found
    return _CACHE[cache_key]


def per_language(build: Callable[[Texts], T], texts: dict[str, Texts]) -> dict[str, T]:
    return {lang: build(t) for lang, t in texts.items()}
