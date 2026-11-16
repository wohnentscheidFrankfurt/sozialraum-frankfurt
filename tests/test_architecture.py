"""Architecture rules (docs/architecture.md, Module kinds and dependency rule)."""
from __future__ import annotations

import ast
import importlib
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "pipeline"
WEB = ROOT / "web"
PURE_THIRD_PARTY = {"numpy", "pandas", "shapely", "pyproj"}
IO_MODULES = {"glob", "http", "io", "os", "pathlib", "shutil", "socket", "subprocess", "tempfile", "urllib",
              "zipfile"}
IO_ATTRIBUTES = {"read_bytes", "read_text", "to_csv", "to_json", "write_bytes", "write_text"}
TIERS = ("engine", "shared", "use_cases", "map")
# `from pipeline.shared.zensus import step` imports the module step, not a name of the package
SUBMODULES = {p.stem for p in PIPELINE.rglob("*.py") if p.name != "__init__.py"}
GERMAN = frozenset("""
    abbruch abdeckung abruf abschnitt abschnitte abw alle anteil anteile anzahl aus ausgabe ausserhalb aussen
    behalten bei belastung bericht bestand bezirk bezirke bindung boden brw daten datei dateien ebene ebenen
    eig eigentum einheit einwohner eins einzeln erfuellt ergaenze ergebnis erstellt erwartet ew faktor faktoren
    farbe farben fehlend fertig flaeche flaechen fuer geb gebaeude gebiet gebiete gemeinde gerundet gewicht
    gewichte gewichtet gezeigt gitter gross gruppe gruppen gueltig haken hole innen ist jahr jahre jahrgang
    kandidat kandidaten karte kennzahl kennzahlen klasse klassen klein kopf kriterien kriterium lade laden lage
    lauf leer leerstand leser lies links liste listen mit miete mieter milieu mittel nach namen neu nummer oben
    oder ohne ordner ortsbild paket pfad pfade pruefe pruefen pruefung pruefungen punkt punkte quelle quellen
    quote rand runde sauber schaetze schicht schichten schluessel schreibe schriften schutz schwelle seite seiten
    soll sonstige spalte spalten stadt stadtteil stadtteile stadtwert stadtwerte stimmen summe sw tabelle
    tausender teil teile titel treffer und unbekannt unten verfahren vergleich voll von vorlage vorlagen wahl
    wechsel wert werte whg wohnung wohnungen zahl zeile zeilen zelle zellen ziel zonen zugeordnet zwei
""".split())


# --- tiers (docs/architecture.md, Module kinds and dependency rule) ---

ROOT_FILES = {"__init__.py", "build.py", "config.py", "update_sources.py"}
# update_sources.py runs by hand: it downloads and writes the extracts, nothing more
UPDATE_SOURCES_IMPORTS = {"pipeline.config", "pipeline.engine.download", "pipeline.shared.zensus.sources",
                          "pipeline.shared.readers.citygml",  # the part rows of the LoD2 package
                          "pipeline.shared.readers.nas",  # the ALKIS extracts (parcels, buildings, land use)
                          # the geometry candidates and the cover classes of building gaps: they are measured here,
                          # once, because the height model and the orthophoto (several GB) do not go into sources/
                          "pipeline.use_cases.building_gaps.sources",
                          "pipeline.shared.readers.gml",  # the inner point of each BORIS zone
                          "pipeline.shared.readers.jsonstat"}  # the long CSV of each database table
SHARED_PACKAGES = ("core", "readers", "zensus", "geography")
MAP_PACKAGES = ("assembly", "checks", "html")
USE_CASES = tuple(sorted(d.name for d in (PIPELINE / "use_cases").iterdir() if d.is_dir() and d.name != "__pycache__"))
# What a tier may import from pipeline/. build.py and config.py are the tier "root"; build.py may import everything.
MAY_IMPORT = {"engine": {"engine"}, "shared": {"engine", "shared"}, "use_cases": {"engine", "shared", "use_cases"},
              "map": {"engine", "shared", "use_cases", "map"}}
# (importing module, imported module) as (tier, package, module) beyond MAY_IMPORT, each with its reason
TIER_EXCEPTIONS = {
    (("engine", "engine", "steps"), ("shared", "core", "checks")),  # write_checks stores Check rows
}
# the former infra/: sources may read with them; they import only shared/core and each other
READERS = {("shared", "core"), ("shared", "readers")}
READER_MODULES = {("engine", "download")}


def locate(parts) -> tuple[str, str, str]:
    """(tier, package, module) of a path below pipeline/ or of a dotted name without the leading `pipeline`.
    The engine is one package; build and config have the tier "root"."""
    parts = [p.removesuffix(".py") for p in parts]
    if not parts or parts[0] not in TIERS:
        return "root", "", parts[0] if parts else ""
    if parts[0] == "engine":
        return "engine", "engine", parts[1] if len(parts) > 1 else ""
    return parts[0], parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else ""


def package_folder(tier: str, package: str, pipeline: Path = PIPELINE) -> Path:
    return pipeline / tier / package


def package_module(tier: str, package: str) -> str:
    """Dotted name of a package, e.g. pipeline.use_cases.land."""
    return f"pipeline.{tier}.{package}"


def module_kind(path: Path, pipeline: Path = PIPELINE) -> str | None:
    tier, package, module = locate(path.relative_to(pipeline).parts)
    if (tier, package) == ("shared", "core"):
        return "pure"
    if (tier, package) == ("shared", "readers") or (tier, module) in READER_MODULES:
        return "infra"
    if tier in ("shared", "use_cases", "map") and module:
        # tables.py (readers of the Zensus database tables) follows the rules of sources.py; cells.py helps steps
        return {"model": "pure", "catalog": "pure", "checks": "pure", "sources": "sources", "tables": "sources",
                "step": "step", "cells": "step"}.get(module)
    return None


def _imports(tree: ast.AST, package: list[str]) -> list[str]:
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
            if node.level:
                base = package[: len(package) - node.level + 1]
                module = ".".join(base + ([node.module] if node.module else []))
            else:
                module = node.module
            # `from pipeline.shared.zensus import step` imports the module pipeline.shared.zensus.step,
            # `from pipeline import use_cases` (or `from .. import map`) imports a whole tier
            for alias in node.names:
                is_module = alias.name in SUBMODULES or (module == "pipeline" and alias.name in TIERS)
                names.append(f"{module}.{alias.name}" if is_module else module)
    return names


def _pipeline_imports(path: Path, pipeline: Path) -> list[tuple[str, tuple[str, str, str]]]:
    """(dotted name, place) of every import from pipeline/ in a module."""
    parts = path.relative_to(pipeline).parts
    out = []
    for name in _imports(ast.parse(path.read_text(encoding="utf-8")), ["pipeline", *parts[:-1]]):
        top, *rest = name.split(".")
        if top == "pipeline" and rest:
            out.append((name, locate(rest)))
    return out


def relative_imports(path: Path, pipeline: Path = PIPELINE) -> list[str]:
    """pipeline/ imports only absolute names; a relative import with a wrong depth would name another module."""
    where = "/".join(path.relative_to(pipeline).parts)
    return [f"{where}:{node.lineno}: from {'.' * node.level}{node.module or ''} import "
            + ", ".join(a.name for a in node.names)
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.ImportFrom) and node.level]


def rule_violations(path: Path, pipeline: Path = PIPELINE) -> list[str]:
    kind = module_kind(path, pipeline)
    if kind is None:
        return []
    parts = path.relative_to(pipeline).parts
    own = locate(parts)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for name in _imports(tree, ["pipeline", *parts[:-1]]):
        top, *rest = name.split(".")
        if top != "pipeline":
            if kind == "pure" and top not in PURE_THIRD_PARTY and (top not in sys.stdlib_module_names
                                                                    or top in IO_MODULES):
                out.append(f"{path.name}: pure module imports {name}")
            continue
        tier, package, module = locate(rest)
        if kind == "pure" and not ((tier, package) == ("shared", "core") or module in ("model", "catalog")):
            out.append(f"{path.name}: pure module imports {name}")
        if kind == "infra" and (tier, package) not in (("shared", "core"), ("shared", "readers")):
            out.append(f"{path.name}: infra imports {name}")
        if kind == "sources" and not ((tier, package) in READERS or (tier, module) in READER_MODULES
                                      or ((tier, package) == own[:2] and module == "model")):
            out.append(f"{path.name}: sources import {name}")
        if kind == "step" and module == "step" and (tier, package) != own[:2]:
            out.append(f"{path.name}: step imports another step: {name}")
    if kind == "pure":
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                if isinstance(f, ast.Name) and f.id == "open":
                    out.append(f"{path.name}: pure module calls open()")
                if isinstance(f, ast.Attribute) and (f.attr in IO_ATTRIBUTES or f.attr.startswith("read_")):
                    out.append(f"{path.name}: pure module calls .{f.attr}()")
    return out


def tier_violations(path: Path, pipeline: Path = PIPELINE) -> list[str]:
    """The folder of a module decides which tiers it may import (MAY_IMPORT, TIER_EXCEPTIONS)."""
    own = locate(path.relative_to(pipeline).parts)
    if own[0] == "root":
        return []
    where = "/".join(path.relative_to(pipeline).parts)
    return [f"{where}: {own[0]} imports {name}" for name, place in _pipeline_imports(path, pipeline)
            if place[0] not in MAY_IMPORT[own[0]] and (own, place) not in TIER_EXCEPTIONS]


def _parts(identifier: str) -> list[str]:
    return [p.lower() for p in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", identifier)]


def german_identifiers(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.alias) and node.asname:
            names.add(node.asname)
    return sorted(n for n in names if not n.isascii() or any(p in GERMAN for p in _parts(n)))


def english_modules(pipeline: Path = PIPELINE) -> list[Path]:
    return sorted(pipeline.rglob("*.py"))


def test_dependency_rule_holds():
    violations = [v for p in sorted(PIPELINE.rglob("*.py")) for v in rule_violations(p)]
    assert not violations, violations


def test_tiers_import_only_what_their_folder_allows():
    violations = [v for p in sorted(PIPELINE.rglob("*.py")) for v in tier_violations(p)]
    assert not violations, violations


def test_migrated_modules_have_english_identifiers():
    found = {str(p.relative_to(PIPELINE)): g for p in english_modules() if (g := german_identifiers(p))}
    assert not found, found


def test_update_sources_imports_only_config_download_the_grid_extracts_four_readers_and_the_building_gaps_sources():
    names = {name for name, _ in _pipeline_imports(PIPELINE / "update_sources.py", PIPELINE)}
    assert {n.rsplit(".", 1)[0] if n.rsplit(".", 1)[0] in UPDATE_SOURCES_IMPORTS else n for n in names} \
        <= UPDATE_SOURCES_IMPORTS, names


def test_layout():
    """pipeline/ holds build.py, config.py, update_sources.py and the four tiers."""
    top = {p.name for p in PIPELINE.iterdir() if p.name != "__pycache__"}
    assert top == ROOT_FILES | set(TIERS), sorted(top ^ (ROOT_FILES | set(TIERS)))


def test_every_package_lies_in_its_tier():
    expected = {("engine", "engine"), *(("shared", p) for p in SHARED_PACKAGES),
                *(("use_cases", u) for u in USE_CASES), *(("map", p) for p in MAP_PACKAGES)}
    tier_folders = {PIPELINE / t for t in TIERS if t != "engine"}
    found = {locate(p.parent.relative_to(PIPELINE).parts)[:2] for p in PIPELINE.rglob("__init__.py")
             if p.parent != PIPELINE and p.parent not in tier_folders}
    assert found == expected, sorted(found ^ expected)


def loose_modules(pipeline: Path = PIPELINE) -> list[str]:
    """Files in shared/, use_cases/ or map/ other than __init__.py; such a module would get no kind and no rule."""
    return sorted("/".join(f.relative_to(pipeline).parts) for t in TIERS if t != "engine" and (pipeline / t).is_dir()
                  for f in (pipeline / t).iterdir() if f.is_file() and f.name not in ("__init__.py", ".DS_Store"))


def test_tiers_hold_only_packages():
    assert loose_modules() == []


def test_every_folder_is_a_package():
    missing = [str(d.relative_to(PIPELINE)) for d in PIPELINE.rglob("*")
               if d.is_dir() and d.name != "__pycache__" and not (d / "__init__.py").exists()]
    assert not missing, missing


def test_every_module_of_a_package_has_its_kind():
    """A path that the checker does not understand would switch its rules off without a failure."""
    unknown = sorted(str(p.relative_to(PIPELINE)) for p in PIPELINE.rglob("*.py")
                     if p.name != "__init__.py" and p.parent != PIPELINE and module_kind(p) is None)
    assert unknown == ["engine/datasets.py", "engine/steps.py", "engine/store.py"]
    assert module_kind(PIPELINE / "engine" / "download.py") == "infra"


# --- the checker itself, on a synthetic tree ---

def _module(root: Path, relative: str, code: str) -> Path:
    path = root / "pipeline" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")
    return path


def test_locate():
    assert locate(["engine", "steps.py"]) == ("engine", "engine", "steps")
    assert locate(["shared", "zensus", "tables.py"]) == ("shared", "zensus", "tables")
    assert locate("use_cases.land.model".split(".")) == ("use_cases", "land", "model")
    assert locate(["config"]) == ("root", "", "config")


def test_module_kind(tmp_path):
    pipeline = tmp_path / "pipeline"
    kinds = {r: module_kind(_module(tmp_path, r, ""), pipeline) for r in
             ("shared/core/stats.py", "shared/readers/gml.py", "engine/download.py",
              "engine/steps.py", "use_cases/land/model.py", "use_cases/indicators/catalog.py",
              "use_cases/land/sources.py", "shared/zensus/tables.py", "shared/zensus/cells.py",
              "use_cases/land/step.py", "use_cases/land/checks.py", "config.py")}
    assert kinds == {"shared/core/stats.py": "pure", "shared/readers/gml.py": "infra", "engine/download.py": "infra",
                     "engine/steps.py": None, "use_cases/land/model.py": "pure",
                     "use_cases/indicators/catalog.py": "pure", "use_cases/land/sources.py": "sources",
                     "shared/zensus/tables.py": "sources", "shared/zensus/cells.py": "step",
                     "use_cases/land/step.py": "step", "use_cases/land/checks.py": "pure", "config.py": None}


def test_pipeline_has_no_relative_imports():
    found = [v for p in sorted(PIPELINE.rglob("*.py")) for v in relative_imports(p)]
    assert not found, found


def test_relative_imports_are_found(tmp_path):
    """A relative import with a wrong depth would still resolve to some name, so the rules could miss it."""
    p = tmp_path / "pipeline"
    code = "from pipeline.shared.core import stats\nfrom ..core import grid\nfrom . import model\n"
    assert relative_imports(_module(tmp_path, "use_cases/land/step.py", code), p) == [
        "use_cases/land/step.py:2: from ..core import grid", "use_cases/land/step.py:3: from . import model"]


def test_loose_modules_in_a_tier_folder(tmp_path):
    """shared/, use_cases/ and map/ hold only __init__.py and package folders."""
    p = tmp_path / "pipeline"
    _module(tmp_path, "shared/__init__.py", "")
    _module(tmp_path, "shared/zensus/step.py", "")
    _module(tmp_path, "map/__init__.py", "")
    assert loose_modules(p) == []
    _module(tmp_path, "use_cases/foo.py", "")
    _module(tmp_path, "shared/x.py", "")
    assert loose_modules(p) == ["shared/x.py", "use_cases/foo.py"]


def test_german_identifiers(tmp_path):
    code = ("ZELLEN_2022 = 1\nfoo_bar = 2\ndef lies_tabelle(seiten, cell_id):\n    for zeile in seiten:\n"
            "        rows = zeile\nclass Gebiet:\n    pass\ndef setzeKennzahl(x):\n    pass\n")
    assert german_identifiers(_module(tmp_path, "x/model.py", code)) == [
        "Gebiet", "ZELLEN_2022", "lies_tabelle", "seiten", "setzeKennzahl", "zeile"]


HOME_PATH = re.compile(r"Path\.home|expanduser|Desktop|/Wohnentscheid Frankfurt|[\"']~/|\bHOME\b")


def _code_files() -> list[Path]:
    return [*PIPELINE.rglob("*.py"), *(ROOT / "research" / "scripts").glob("*.py"), *(ROOT / "research" / "scripts").glob("*.mjs")]


def test_only_config_builds_home_paths():
    found = [p.name for p in _code_files() if p.name != "config.py" and HOME_PATH.search(p.read_text(encoding="utf-8"))]
    assert not found, found


def test_web_names_the_map():
    html = (WEB / "map.html").read_text(encoding="utf-8")
    assert "<title>Sozialraum Frankfurt</title>" in html
    header = html[html.index('<header id="header">'):html.index("</header>")]
    assert "<h1>Sozialraum Frankfurt</h1>" in header
    # the map is public on the website
    assert "öffentlich" not in html and "nicht weitergeben" not in html


def test_map_may_be_indexed():
    html = (WEB / "map.html").read_text(encoding="utf-8")
    assert 'name="robots"' not in html


# --- use cases (docs/architecture.md, Use-case packages) ---

REQUIRED_FILES = ("README.md", "model.py", "step.py")
# catalog.py only with indicators or texts, checks.py only with checks: a file with a docstring alone is dead weight
OPTIONAL_FILES = ("catalog.py", "checks.py")
README_SECTIONS = ("Shows", "Formula", "Why", "Inputs", "Output", "Checks", "Limits")
TABLE_READS = {("ownership_shares", "ownership_cells"), ("ownership_shares", "public_housing"),
               ("ownership_shares", "coops"), ("coops", "ownership_cells"), ("rent_burden", "new_construction"),
               ("rent_burden", "survey")}


def readme_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def has_content(path: Path) -> bool:
    """True if the module holds more than a docstring and imports."""
    return any(not (isinstance(node, (ast.Import, ast.ImportFrom))
                    or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)))
               for node in ast.parse(path.read_text(encoding="utf-8")).body)


def package_problems(folder: Path, package: str) -> list[str]:
    out = [f"{package}: {f} missing" for f in REQUIRED_FILES if not (folder / f).exists()]
    out += [f"{package}: {f} holds no code, delete it" for f in OPTIONAL_FILES
            if (folder / f).exists() and not has_content(folder / f)]
    if (folder / "README.md").exists():
        sections = readme_sections((folder / "README.md").read_text(encoding="utf-8"))
        out += [f"{package}: README section {s} missing" for s in README_SECTIONS if s not in sections]
    return out


def readme_indicator_problems(package: str, ids: list[str], readme: str) -> list[str]:
    shows = readme_sections(readme).get("Shows", "")
    return [f"{package}: README does not name {i}" for i in ids
            if re.search(rf"(?<![A-Z0-9_]){re.escape(i)}(?![A-Z0-9_])", shows) is None]


def readme_input_problems(package: str, needs: set[str], readme: str, datasets: set[str]) -> list[str]:
    named = set(re.findall(r"`([a-z0-9_]+)`", readme_sections(readme).get("Inputs", ""))) & datasets
    return ([f"{package}: README Inputs miss {d}" for d in sorted(needs - named)]
            + [f"{package}: README Inputs name {d}, the step does not need it" for d in sorted(named - needs)])


def cross_import_problems(path: Path, pipeline: Path = PIPELINE) -> list[str]:
    """A use case imports only `model` or `catalog` of another use case, and so does map/. shared/ imports no use
    case."""
    tier, own, _ = locate(path.relative_to(pipeline).parts)
    out = []
    for name, (target_tier, target, module) in _pipeline_imports(path, pipeline):
        if target_tier != "use_cases" or (tier, own) == ("use_cases", target):
            continue
        if tier == "shared":
            out.append(f"{own}/{path.name}: shared block imports use case {name}")
        elif tier in ("use_cases", "map") and module not in ("model", "catalog"):
            out.append(f"{own}/{path.name}: imports {name}; only model or catalog of another use case")
    return out


def _all_datasets() -> set[str]:
    from pipeline.engine import datasets
    return {v.name for v in vars(datasets).values() if isinstance(v, datasets.Dataset)}


def test_use_cases_have_their_files_and_readme_sections():
    problems = [p for u in sorted(USE_CASES) for p in package_problems(package_folder("use_cases", u), u)]
    assert not problems, problems


def test_readme_names_the_indicators_and_the_inputs():
    from pipeline.build import STEPS
    steps = {s.name: s for s in STEPS}
    problems = []
    for u in sorted(USE_CASES):
        readme = (package_folder("use_cases", u) / "README.md").read_text(encoding="utf-8")
        catalog = importlib.import_module(f"{package_module('use_cases', u)}.catalog")
        problems += readme_indicator_problems(u, [k.id for k in getattr(catalog, "INDICATORS", [])], readme)
        problems += readme_input_problems(u, {d.name for d in steps[u].needs}, readme, _all_datasets())
    assert not problems, problems


def test_indicator_ids_are_unique_over_the_packages():
    ids = [k.id for u in sorted(USE_CASES)
           for k in getattr(importlib.import_module(f"{package_module('use_cases', u)}.catalog"), "INDICATORS", [])]
    assert len(ids) == len(set(ids)), sorted({i for i in ids if ids.count(i) > 1})


def test_imports_between_use_cases():
    problems = [p for path in sorted(PIPELINE.rglob("*.py")) for p in cross_import_problems(path)]
    assert not problems, problems


def test_use_cases_read_tables_of_others_only_in_known_pairs():
    from pipeline.build import STEPS
    from pipeline.engine.steps import producers
    made = producers(STEPS)
    pairs = {(s.name, made[d.name]) for s in STEPS if s.name in USE_CASES for d in s.needs
             if made.get(d.name) in USE_CASES and made[d.name] != s.name}
    assert pairs <= TABLE_READS, pairs - TABLE_READS


def test_checker_finds_missing_files_and_sections(tmp_path):
    folder = tmp_path / "pipeline" / "use_cases" / "land"
    folder.mkdir(parents=True)
    (folder / "README.md").write_text("# land\n## Shows\nLAND_VALUE\n## Inputs\n`cells_2022`\n", encoding="utf-8")
    (folder / "catalog.py").write_text('"""Texts."""\nfrom __future__ import annotations\n', encoding="utf-8")
    (folder / "checks.py").write_text('"""Checks."""\ndef check_x():\n    return []\n', encoding="utf-8")
    problems = package_problems(folder, "land")
    assert "land: model.py missing" in problems and "land: README section Limits missing" in problems
    assert "land: catalog.py holds no code, delete it" in problems and "land: checks.py holds no code, delete it" not in problems
    assert "land: catalog.py missing" not in problems and "land: checks.py missing" not in problems


def test_checker_matches_indicator_ids_as_whole_words():
    """HOU_RENT is a prefix of HOU_RENTERS; naming the longer ID does not name the shorter one."""
    assert readme_indicator_problems("housing", ["HOU_RENT"], "## Shows\nHOU_RENTERS\n") == [
        "housing: README does not name HOU_RENT"]
    assert readme_indicator_problems("housing", ["HOU_RENT"], "## Shows\nHOU_RENT, HOU_RENTERS\n") == []


def test_checker_compares_readme_inputs_with_the_step():
    readme = "## Inputs\n`cells_2022`, `land_value_cells`, file `sources/x.csv`\n"
    assert readme_input_problems("land", {"cells_2022", "protection_cells"}, readme,
                                 {"cells_2022", "land_value_cells", "protection_cells"}) == [
        "land: README Inputs miss protection_cells",
        "land: README Inputs name land_value_cells, the step does not need it"]


def test_map_tier_kinds(tmp_path):
    p = tmp_path / "pipeline"
    assert module_kind(_module(tmp_path, "map/assembly/catalog.py", ""), p) == "pure"
    assert module_kind(_module(tmp_path, "map/html/sources.py", ""), p) == "sources"
    assert locate("map.html.model".split(".")) == ("map", "html", "model")


# (checker, path below pipeline/, code, expected problems) for the import rules of the checker
CHECKER_CASES = {
    "pure: core models and pandas are fine": (
        rule_violations, "use_cases/ownership/model.py",
        "from __future__ import annotations\nimport math\nimport pandas as pd\n"
        "from pipeline.shared.core.stats import x\nfrom pipeline.shared.zensus.model import CLASSES\n"
        "from .catalog import y\n", []),
    "pure: no I/O": (
        rule_violations, "use_cases/ownership/model.py",
        "import subprocess\nimport pandas as pd\nfrom pipeline import config\n"
        "from pipeline.engine.store import Store\ndef f(p):\n    open(p)\n    return pd.read_csv(p)\n",
        ["model.py: pure module imports subprocess", "model.py: pure module imports pipeline.config",
         "model.py: pure module imports pipeline.engine.store", "model.py: pure module calls open()",
         "model.py: pure module calls .read_csv()"]),
    "pure: imported modules count as modules": (
        rule_violations, "use_cases/indicators/model.py",
        "from pipeline.shared.zensus import model\nfrom . import catalog\nfrom pipeline.shared.core import stats\n",
        []),
    "sources: shared and the own model are fine": (
        rule_violations, "use_cases/land/sources.py",
        "import pymupdf\nfrom pipeline.shared.readers.gml import parse_features\n"
        "from pipeline.use_cases.land.model import Zone\nfrom pipeline.engine.download import download\n", []),
    "sources: store and another use case are not": (
        rule_violations, "use_cases/land/sources.py",
        "from pipeline.engine.store import Store\nfrom pipeline.use_cases.protection.model import Site\n",
        ["sources.py: sources import pipeline.engine.store",
         "sources.py: sources import pipeline.use_cases.protection.model"]),
    "sources: imported modules count as modules": (
        rule_violations, "use_cases/land/sources.py",
        "from pipeline.use_cases.land import model\nfrom pipeline.shared.readers import gml\n", []),
    "tables follow the rules of sources: ok": (
        rule_violations, "shared/zensus/tables.py",
        "import csv\nfrom pipeline.shared.zensus.model import CLASSES\n", []),
    "tables follow the rules of sources: store and a use case are not": (
        rule_violations, "shared/zensus/tables.py",
        "from pipeline.engine.store import Store\nfrom pipeline.use_cases.land.model import Zone\n",
        ["tables.py: sources import pipeline.engine.store",
         "tables.py: sources import pipeline.use_cases.land.model"]),
    "step: no import of another step": (
        rule_violations, "use_cases/ownership/step.py",
        "from pipeline.shared.zensus.step import run_zensus\nfrom pipeline.shared.zensus.sources import read_2011\n",
        ["step.py: step imports another step: pipeline.shared.zensus.step"]),
    "step: a module import of another step is found": (
        rule_violations, "use_cases/ownership/step.py",
        "from pipeline.shared.zensus import step\nfrom ...shared.zensus import step as other\n",
        ["step.py: step imports another step: pipeline.shared.zensus.step"] * 2),
    "infra: core is fine": (
        rule_violations, "shared/readers/gml.py", "from pipeline.shared.core.geometry import Feature\n", []),
    "infra: a reader may use another reader": (
        rule_violations, "shared/readers/html.py", "from pipeline.shared.readers.pdf import page_texts\n", []),
    "infra: download imports no reader (the engine tier forbids shared)": (
        tier_violations, "engine/download.py",
        "from pipeline.shared.readers.pdf import page_texts\nfrom pipeline.shared.core.stats import mean\n",
        ["engine/download.py: engine imports pipeline.shared.readers.pdf",
         "engine/download.py: engine imports pipeline.shared.core.stats"]),
    "infra: a reader does not import the config": (
        rule_violations, "shared/readers/gml.py", "from pipeline.config import CACHE\n",
        ["gml.py: infra imports pipeline.config"]),
    "infra: download does not import the config": (
        rule_violations, "engine/download.py", "from pipeline.config import CACHE\n",
        ["download.py: infra imports pipeline.config"]),
    "infra: a reader does not import another package of shared": (
        rule_violations, "shared/readers/gml.py", "from pipeline.shared.zensus.model import CLASSES\n",
        ["gml.py: infra imports pipeline.shared.zensus.model"]),
    "infra: download does not import another module of the engine": (
        rule_violations, "engine/download.py", "from pipeline.engine.steps import Step\n",
        ["download.py: infra imports pipeline.engine.steps"]),
    "tier: the engine imports engine and the Check": (
        tier_violations, "engine/steps.py",
        "from pipeline.engine.datasets import Dataset\nfrom pipeline.shared.core.checks import Check\n", []),
    "tier: the engine imports nothing else": (
        tier_violations, "engine/store.py",
        "from pipeline.engine.datasets import Dataset\nfrom pipeline.shared.core.checks import Check\n"
        "from pipeline import config\n",
        ["engine/store.py: engine imports pipeline.shared.core.checks",
         "engine/store.py: engine imports pipeline.config"]),
    "tier: shared imports no use case": (
        tier_violations, "shared/geography/sources.py",
        "from pipeline.engine.steps import Step\nfrom pipeline.use_cases.land.model import Zone\n",
        ["shared/geography/sources.py: shared imports pipeline.use_cases.land.model"]),
    "tier: shared does not import the config": (
        tier_violations, "shared/zensus/step.py", "from pipeline import config\n",
        ["shared/zensus/step.py: shared imports pipeline.config"]),
    "tier: a use case does not import the config": (
        tier_violations, "use_cases/land/step.py", "from pipeline import config\n",
        ["use_cases/land/step.py: use_cases imports pipeline.config"]),
    "tier: the root may import everything": (
        tier_violations, "config.py", "from pipeline.engine import steps\n", []),
    "tier: shared names a whole tier with `from pipeline import`": (
        tier_violations, "shared/zensus/step.py", "from pipeline import use_cases\n",
        ["shared/zensus/step.py: shared imports pipeline.use_cases"]),
    "tier: the engine names a whole tier with a relative import": (
        tier_violations, "engine/steps.py", "from .. import map\n", ["engine/steps.py: engine imports pipeline.map"]),
    "tier: the engine names a whole tier with `from pipeline import`": (
        tier_violations, "engine/steps.py", "from pipeline import map\n", ["engine/steps.py: engine imports pipeline.map"]),
    "tier: map may import the use cases": (
        tier_violations, "map/assembly/step.py", "from pipeline import use_cases\n", []),
    "tier: a use case may import the engine": (
        tier_violations, "use_cases/land/step.py", "from pipeline import engine\n", []),
    "tier: map imports model and catalog of a use case": (
        tier_violations, "map/html/step.py",
        "from pipeline.use_cases.land.model import Zone\nfrom pipeline.use_cases.land import catalog\n", []),
    "tier: a use case does not import map": (
        tier_violations, "use_cases/candidates/step.py", "from pipeline.map.assembly.model import join_area_table\n",
        ["use_cases/candidates/step.py: use_cases imports pipeline.map.assembly.model"]),
    "use cases: model and catalog of another use case": (
        cross_import_problems, "use_cases/public_housing/model.py",
        "from pipeline.use_cases.ownership_cells.model import GROUPS\n"
        "from pipeline.use_cases.ownership_cells import catalog\n", []),
    "use cases: not the sources or the step of another use case": (
        cross_import_problems, "use_cases/public_housing/step.py",
        "from pipeline.use_cases.ownership_cells.sources import x\n"
        "from pipeline.use_cases.ownership_cells import step\n",
        ["public_housing/step.py: imports pipeline.use_cases.ownership_cells.sources; only model or catalog of "
         "another use case",
         "public_housing/step.py: imports pipeline.use_cases.ownership_cells.step; only model or catalog of "
         "another use case"]),
    "use cases: shared imports no use case": (
        cross_import_problems, "shared/zensus/step.py", "from pipeline.use_cases.land.model import Zone\n",
        ["zensus/step.py: shared block imports use case pipeline.use_cases.land.model"]),
    "use cases: shared imports no whole tier of use cases": (
        cross_import_problems, "shared/zensus/step.py", "from pipeline import use_cases\n",
        ["zensus/step.py: shared block imports use case pipeline.use_cases"]),
    "use cases: map imports no step of a use case": (
        cross_import_problems, "map/assembly/step.py", "from pipeline.use_cases.land import step\n",
        ["assembly/step.py: imports pipeline.use_cases.land.step; only model or catalog of another use case"]),
    "use cases: map imports model and catalog of a use case": (
        cross_import_problems, "map/html/step.py",
        "from pipeline.use_cases.land.model import Zone\nfrom pipeline.use_cases.land import catalog\n", []),
}


@pytest.mark.parametrize("case", CHECKER_CASES)
def test_checker_finds_forbidden_imports(case, tmp_path):
    checker, relative, code, expected = CHECKER_CASES[case]
    assert checker(_module(tmp_path, relative, code), tmp_path / "pipeline") == expected



def test_only_render_profile_writes_the_area_tab():
    write = re.compile(r"tab-area[^\n]*(innerHTML|outerHTML|insertAdjacentHTML)")
    owners = []
    for js in sorted((ROOT / "web" / "js").glob("*.js")):
        text = js.read_text(encoding="utf-8")
        for m in write.finditer(text):
            start = text.rfind("\nAPP.", 0, m.start())
            owners.append((js.name, text[start + 1 : text.index(" ", start + 1)] if start >= 0 else ""))
    assert owners, "no writer of the area tab found"
    assert all(owner == "APP.renderProfile" for _, owner in owners), owners


def test_one_function_builds_the_overlay_checkboxes():
    markup = re.compile(r"<input[^\n]*data-overlay")
    owners = []
    for js in sorted((ROOT / "web" / "js").glob("*.js")):
        text = js.read_text(encoding="utf-8")
        for m in markup.finditer(text):
            start = text.rfind("\nAPP.", 0, m.start())
            owners.append((js.name, text[start + 1 : text.index(" ", start + 1)] if start >= 0 else ""))
    assert owners, "no overlay checkbox markup found"
    assert all(owner == "APP.overlayRows" for _, owner in owners), owners
    assert "data-overlay" not in (ROOT / "web" / "map.html").read_text(encoding="utf-8")
