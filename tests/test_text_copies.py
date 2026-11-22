"""A map text stands once in the repo. Tests check its rules, numbers and placeholders, not its wording
(docs/texts.md, Where texts live). The guard is a heuristic: it finds a literal of a test with 20 or more characters and
a German word or letter that stands in a map text. A short label without such a word passes it. It reads the Python tests
and the browser tests (tests/browser/**/*.mjs)."""
from __future__ import annotations

import ast
import importlib
import re
from dataclasses import asdict, is_dataclass
from pathlib import Path

from pipeline.shared.core.texts import raw_leaves, resolved_leaves

ROOT = Path(__file__).resolve().parent.parent
# the modules that hold the texts of the map, besides web/
TEXT_MODULES = ("pipeline/**/catalog.py", "pipeline/use_cases/*/model.py", "pipeline/shared/core/indicator.py",
                "pipeline/map/html/model.py")
# the language files: every leaf is a map text (YAML comments are none)
YAML_TEXTS = "pipeline/**/texts.{lang}.yaml"
MIN_LENGTH = 20
GERMAN = re.compile(r"[äöüÄÖÜß„“]|\b(und|der|die|das|den|dem|des|ein|eine|nicht|nur|mit|ohne|von|aus|ist|sind|im|an|"
                    r"auf|zu|zum|zur|für|bei|nach|bis|unter|je|wie|oder|als|auch|noch|wird|wurde|seit|vor)\b")
# an English literal counts only against the English files: code, comments and docstrings are English too
ENGLISH = re.compile(r"\b(the|and|of|in|on|is|are|to|for|with|from|by|not|only|or|as|at|per|its|their|than|under|"
                     r"above|below|was|were|has|have)\b", re.I)
# phrase -> reason; a test may repeat these. A literal is exempt when it holds little else (less than MIN_LENGTH).
ALLOWED = {
    "Nassauische Heimstätte": "proper name",
    "Sachsenhausen-Süd und Flughafen": "area name: two Stadtteile that the annual report counts together",
    "13 und mehr Wohnungen": "source vocabulary: a size class of the Zensus",
    "außerhalb Frankfurts": "source vocabulary: a row of the annual report Kommunale Wohnraumversorgung",
    "Wohnungsbestand und Räume": "source vocabulary: a table of the Statistikportal",
    "Entwicklung des Reallohn-, Nominallohn- und Verbraucherpreisindex": "source vocabulary: the HSL press table",
    "dl-de/by-2-0, Stadt Frankfurt am Main": "licence line of a source: the same words in German and English",
    "Eigentum je 100-m-Feld": "tools/dump_text.mjs selects by visible text by design: the dump must survive renames of ids",
}


def string_literals(path: Path):
    """(line, text) of every string literal of a Python file. ast.walk also reaches the literal parts of an
    f-string."""
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.lineno, node.value


BROWSER_SKIPPED = {"node_modules", "output"}
REGEX_AFTER = set("(,=>:[!&|?{};")  # a `>` ends `=>` or a comparison, never a division
REGEX_AFTER_WORD = {"return", "case", "typeof", "else", "await", "yield", "void", "delete", "in", "of", "do"}
IDENTIFIER = re.compile(r"[A-Za-z0-9_$]")


def js_literals(path: Path):
    """(line, text) of every string, template part and regex literal of a JavaScript file. Comments are skipped. A `/`
    starts a regex after an operator or bracket, after a keyword such as `return` or at the start of a line, otherwise
    it divides. An escaped quote is unescaped; any other backslash stays, so a pattern of a source is not taken for a
    text."""
    src = path.read_text(encoding="utf-8")
    n, i, line = len(src), 0, 1
    prev, word = "", ""  # the last character that is no space, and the word that ends there
    line_start = True
    braces: list[int] = []  # one entry per open ${ : the depth of { } inside it

    def template(i: int, line: int):
        """Read a template part from i up to ${ or the closing backtick; return (text, i, line, start line, opens)."""
        out, start = [], line
        while i < n:
            c = src[i]
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1] if src[i + 1] in "`$" else c + src[i + 1])
                line += src[i + 1] == "\n"
                i += 2
                continue
            if c == "`":
                return "".join(out), i + 1, line, start, False
            if c == "$" and src.startswith("${", i):
                return "".join(out), i + 2, line, start, True
            line += c == "\n"
            out.append(c)
            i += 1
        return "".join(out), i, line, start, False

    while i < n:
        c = src[i]
        if c == "\n":
            line, i, line_start = line + 1, i + 1, True
            continue
        if c.isspace():
            i += 1
            continue
        starts_line, line_start = line_start, False
        if src.startswith("//", i):
            while i < n and src[i] != "\n":
                i += 1
            continue
        if src.startswith("/*", i):
            end = src.find("*/", i + 2)
            end = n if end < 0 else end + 2
            line += src.count("\n", i, end)
            i = end
            continue
        if c in "\"'":
            out, j, start = [], i + 1, line
            while j < n and src[j] != c and src[j] != "\n":
                if src[j] == "\\" and j + 1 < n:
                    out.append(src[j + 1] if src[j + 1] in "\"'`" else src[j] + src[j + 1])
                    j += 2
                else:
                    out.append(src[j])
                    j += 1
            yield start, "".join(out)
            i, prev, word = j + 1, c, ""
            continue
        if c == "`" or (c == "}" and braces and braces[-1] == 0):
            if c == "}":
                braces.pop()
            text, i, new_line, start, opens = template(i + 1, line)
            yield start, text
            line = new_line
            if opens:
                braces.append(0)
                prev, word = "{", ""
            else:
                prev, word = "`", ""
            continue
        if c == "/" and (not prev or prev in REGEX_AFTER or word in REGEX_AFTER_WORD or starts_line):
            out, j, in_class = [], i + 1, False
            while j < n and src[j] != "\n" and (in_class or src[j] != "/"):
                if src[j] == "\\" and j + 1 < n:
                    out.append(src[j:j + 2])
                    j += 2
                    continue
                in_class = in_class and src[j] != "]" or src[j] == "["
                out.append(src[j])
                j += 1
            yield line, "".join(out)
            i, prev, word = j + 1, "/", ""
            continue
        if braces:
            braces[-1] += (c == "{") - (c == "}")
        if IDENTIFIER.match(c):
            word = word + c if IDENTIFIER.match(prev) else c
        else:
            word = ""
        prev = c
        i += 1


def text_modules(root: Path = ROOT) -> list[Path]:
    return sorted({p for pattern in TEXT_MODULES for p in root.glob(pattern)})


def yaml_leaves(root: Path = ROOT, lang: str = "de") -> list[tuple[str, str, str]]:
    """(file, key, text as written) of every leaf of the language files of one language. For the guards of words and
    gender."""
    files = sorted(root.glob(YAML_TEXTS.format(lang=lang)))
    return [(str(f.relative_to(root)), key, text) for f in files for key, text in raw_leaves(f).items()]


def yaml_texts(root: Path = ROOT, lang: str = "de") -> list[str]:
    """The leaves of the language files of one language, as written (references unresolved) and as the map shows them
    (references resolved, placeholders stay)."""
    core_file = root / "pipeline" / "shared" / "core" / f"texts.{lang}.yaml"
    out: list[str] = []
    for file in sorted(root.glob(YAML_TEXTS.format(lang=lang))):
        out += raw_leaves(file).values()
        out += resolved_leaves(file, core_file if core_file.is_file() and file != core_file else None).values()
    return out


def map_texts(root: Path = ROOT) -> list[str]:
    """The literals of the text modules, the leaves of the language files and the files of web/. A literal with a
    backslash is a pattern of a source."""
    texts = [s for p in text_modules(root) for _, s in string_literals(p) if "\\" not in s]
    texts += yaml_texts(root)
    return texts + [p.read_text(encoding="utf-8") for p in sorted((root / "web").rglob("*")) if p.suffix in (".html", ".js")]


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for v in value:
            yield from strings(v)
    elif is_dataclass(value) and not isinstance(value, type):
        yield from strings(asdict(value))


def finished_texts() -> list[str]:
    """The string values of the text modules after import: filled f-strings and joined constants too."""
    modules = [importlib.import_module(".".join(p.relative_to(ROOT).with_suffix("").parts)) for p in text_modules()]
    return [s for m in modules for v in vars(m).values() for s in strings(v) if "\\" not in s]


def is_copy(literal: str, texts: str, english: str = "") -> bool:
    """texts: the German map texts and the files of web/; english: the English language files."""
    text = literal.strip()
    rest = text
    for allowed in ALLOWED:
        rest = rest.replace(allowed, "")
    rest = re.sub(r"<[^>]*>", "", rest)  # the tags around an allowed phrase are no text
    if len(rest.strip()) < MIN_LENGTH or " " not in text or "\\" in text:
        return False
    return (GERMAN.search(text) is not None and text in texts) or (ENGLISH.search(text) is not None and text in english)


def browser_tests(root: Path = ROOT) -> list[Path]:
    """The JavaScript files of tests/browser/ without node_modules and output folders."""
    return sorted(p for p in (root / "tests" / "browser").rglob("*.mjs")
                  if not BROWSER_SKIPPED & set(p.relative_to(root).parts))


def literals_of_tests(root: Path = ROOT):
    """(file, line, literal) of every test module except this one, and of every browser test."""
    for p in sorted((root / "tests").rglob("*.py")):
        if p.name != "test_text_copies.py":
            yield from ((p, line, literal) for line, literal in string_literals(p))
    for p in browser_tests(root):
        yield from ((p, line, literal) for line, literal in js_literals(p))


def text_copies(root: Path = ROOT, finished: list[str] | None = None) -> list[str]:
    texts = "\0".join(map_texts(root) + (finished or []))
    english = "\0".join(yaml_texts(root, "en"))
    copies = sorted((p, line, literal) for p, line, literal in literals_of_tests(root) if is_copy(literal, texts, english))
    return [f"{p.relative_to(root)}:{line}: {literal.strip()[:80]}" for p, line, literal in copies]


def test_no_test_repeats_a_map_text():
    copies = text_copies(finished=finished_texts())
    assert not copies, "\n".join(copies)


def test_every_exception_is_still_needed():
    texts = "\0".join(map_texts() + finished_texts())
    used = {a for a in ALLOWED for _, _, literal in literals_of_tests() if a in literal}
    assert set(ALLOWED) == used and all(a in texts for a in ALLOWED)


def test_checker_finds_copies(tmp_path):
    (tmp_path / "pipeline" / "use_cases" / "a").mkdir(parents=True)
    (tmp_path / "pipeline" / "use_cases" / "a" / "catalog.py").write_text(
        'TITLE = "Die Mieten stiegen schneller als die Löhne"\nPATTERN = r"Mittelwert von (\\d+,\\d+) €/m² und mehr"\n'
        'NOTE = f"Stand {YEAR}: Nassauische Heimstätte und mehr, viel mehr"\n', encoding="utf-8")
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "map.html").write_text("<p>Ein Klick auf ein Gebiet zeigt seine Werte.</p>", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(
        'assert TITLE == "Die Mieten stiegen schneller als die Löhne"\n'  # a copy of the catalog
        'assert "Ein Klick auf ein Gebiet" in HTML\n'  # a copy of web/
        'assert "stiegen schneller" in TITLE\n'  # shorter than MIN_LENGTH
        'assert re.search(r"Mittelwert von (\\d+,\\d+) €/m² und mehr", page)\n'  # a pattern of a source
        'assert ": Nassauische Heimstätte" in NOTE\n'  # allowed: little else
        'assert TITLE == f"{X} Mieten stiegen schneller als die Löhne"\n'  # the literal part of an f-string
        'assert check.name == "Rents: the heading holds"\n'  # English
        'assert ": Nassauische Heimstätte und mehr, viel mehr" in NOTE\n'  # an allowed phrase in a longer copy
        'assert RULE == "Stand 2026, gefüllt aus Konstanten"\n',  # a finished text of a module
        encoding="utf-8")
    assert text_copies(tmp_path, ["Stand 2026, gefüllt aus Konstanten"]) == [
        "tests/test_a.py:1: Die Mieten stiegen schneller als die Löhne",
        "tests/test_a.py:2: Ein Klick auf ein Gebiet",
        "tests/test_a.py:6: Mieten stiegen schneller als die Löhne",
        "tests/test_a.py:8: : Nassauische Heimstätte und mehr, viel mehr",
        "tests/test_a.py:9: Stand 2026, gefüllt aus Konstanten"]


def test_checker_finds_copies_in_browser_tests(tmp_path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "map.html").write_text("<p>Ein Klick auf ein Gebiet zeigt seine Werte.</p>", encoding="utf-8")
    (tmp_path / "tests" / "browser" / "desktop").mkdir(parents=True)
    (tmp_path / "tests" / "browser" / "desktop" / "a.spec.mjs").write_text(
        'expect(text).toBe("Ein Klick auf ein Gebiet zeigt seine Werte.");\n'  # double quotes
        "expect(text).toBe('Ein Klick auf ein Gebiet zeigt seine Werte.');\n"  # single quotes
        "expect(text).toBe(`${x} Ein Klick auf ein Gebiet zeigt`);\n"  # the literal part of a template
        "expect(text).toMatch(/Ein Klick auf ein Gebiet zeigt/);\n"  # a regex literal
        "const ratio = a / b; const other = c / d; // Ein Klick auf ein Gebiet zeigt seine Werte.\n"  # division, comment
        "/* Ein Klick auf ein Gebiet zeigt seine Werte. */\n"  # a block comment
        'expect(check.name).toBe("Rents: the heading holds in every view");\n'  # English
        'expect(header).toBe("Nassauische Heimstätte");\n'  # allowed
        "list.filter((t) => /Ein Klick auf ein Gebiet zeigt/.test(t));\n"  # a regex after =>
        "const r = await /Ein Klick auf ein Gebiet zeigt/;\n"  # a regex after await
        "switch (k) { case /Ein Klick auf ein Gebiet zeigt/: break; }\n",  # a regex after case
        encoding="utf-8")
    (tmp_path / "tests" / "browser" / "node_modules" / "pkg").mkdir(parents=True)
    (tmp_path / "tests" / "browser" / "node_modules" / "pkg" / "b.mjs").write_text(
        'x("Ein Klick auf ein Gebiet zeigt seine Werte.");\n', encoding="utf-8")
    assert text_copies(tmp_path) == [
        "tests/browser/desktop/a.spec.mjs:1: Ein Klick auf ein Gebiet zeigt seine Werte.",
        "tests/browser/desktop/a.spec.mjs:2: Ein Klick auf ein Gebiet zeigt seine Werte.",
        "tests/browser/desktop/a.spec.mjs:3: Ein Klick auf ein Gebiet zeigt",
        "tests/browser/desktop/a.spec.mjs:4: Ein Klick auf ein Gebiet zeigt",
        "tests/browser/desktop/a.spec.mjs:9: Ein Klick auf ein Gebiet zeigt",
        "tests/browser/desktop/a.spec.mjs:10: Ein Klick auf ein Gebiet zeigt",
        "tests/browser/desktop/a.spec.mjs:11: Ein Klick auf ein Gebiet zeigt"]


def test_finds_a_copy_of_a_yaml_text(tmp_path):
    (tmp_path / "pipeline" / "use_cases" / "a").mkdir(parents=True)
    (tmp_path / "pipeline" / "use_cases" / "a" / "texts.de.yaml").write_text(
        '# Ein Kommentar ist kein Kartentext, auch nicht mit Umlauten.\n'
        'title: "Die Mieten stiegen schneller als die Löhne"\n'
        'rule: "{@title}, und das nicht nur im Zentrum der Stadt"\n', encoding="utf-8")
    (tmp_path / "web").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(
        'assert TITLE == "Die Mieten stiegen schneller als die Löhne"\n'  # a leaf
        'assert RULE == "Die Mieten stiegen schneller als die Löhne, und das nicht nur im Zentrum der Stadt"\n'  # resolved
        'assert X == "Ein Kommentar ist kein Kartentext, auch nicht mit Umlauten."\n', encoding="utf-8")  # a comment
    assert text_copies(tmp_path) == [
        "tests/test_a.py:1: Die Mieten stiegen schneller als die Löhne",
        "tests/test_a.py:2: Die Mieten stiegen schneller als die Löhne, und das nicht nur im Zentrum der Sta"]


def test_finds_a_copy_of_an_english_text(tmp_path):
    pkg = tmp_path / "pipeline" / "use_cases" / "a"
    pkg.mkdir(parents=True)
    (pkg / "texts.de.yaml").write_text('title: "Die Mieten stiegen schneller als die Löhne"\n', encoding="utf-8")
    (pkg / "texts.en.yaml").write_text('title: "Rents grew faster than wages in the city"\n'
                                       'rule: "{@title}, and not only in the centre"\n', encoding="utf-8")
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "map.js").write_text("// Rents grew faster than wages in the city\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(
        'assert TITLE == "Rents grew faster than wages in the city"\n'  # a leaf
        'assert RULE == "Rents grew faster than wages in the city, and not only"\n'  # resolved
        'assert check.name == "Rents: the heading holds in every view"\n'  # English, but no map text
        'assert X == "Die Mieten stiegen schneller als die Löhne"\n', encoding="utf-8")  # German
    assert text_copies(tmp_path) == [
        "tests/test_a.py:1: Rents grew faster than wages in the city",
        "tests/test_a.py:2: Rents grew faster than wages in the city, and not only",
        "tests/test_a.py:4: Die Mieten stiegen schneller als die Löhne"]
