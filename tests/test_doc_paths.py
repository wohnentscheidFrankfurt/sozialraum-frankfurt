"""Every repo path that the living docs name in backticks exists, and the layout keeps its shape
(docs/architecture.md, Layout)."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREFIXES = ("sources/", "research/", "docs/", "pipeline/", "reference/", "tests/", "tools/", "web/",
            "manual_layers/", "analyses/", "findings/")
SKIP = set("*<{…")
OLD_NAMES = "## Old folder names"  # this section of research/README.md lists paths that are gone on purpose


def living_docs(root: Path = ROOT) -> list[Path]:
    return sorted({root / "CLAUDE.md", root / "README.md", *root.glob("docs/*.md"), *root.glob("pipeline/**/README.md"),
                   *root.glob("research/README.md"),
                   *root.glob("sources/README.md")}
                  & set(root.rglob("*.md")))


def named_paths(text: str) -> list[str]:
    text = text.split(OLD_NAMES)[0]
    out = []
    for span in re.findall(r"`([^`\n]+)`", text):
        span = span.strip()
        if not span.startswith(PREFIXES) or SKIP & set(span):
            continue
        if not span.startswith("sources/"):  # source file names may hold spaces; others end at the first space
            span = span.split(" ")[0]
        out.append(re.sub(r":\d+(-\d+)?$", "", span.split("::")[0].rstrip(".,;:)")))
    return out


def missing_paths(root: Path = ROOT) -> list[str]:
    return [f"{doc.relative_to(root)}: {p}" for doc in living_docs(root)
            for p in named_paths(doc.read_text(encoding="utf-8"))
            if not (root / p).exists()]


def test_living_docs_name_existing_paths():
    assert not missing_paths(), missing_paths()


def test_checker_finds_a_missing_path(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("See `docs/a.md`, `docs/gone.md` and `sources/x/<file>`.\n"
                                            "## Old folder names\n`findings/` is now `research/`.\n", encoding="utf-8")
    assert missing_paths(tmp_path) == ["docs/a.md: docs/gone.md"]


def test_source_folders_have_plain_names():
    folders = [p.relative_to(ROOT / "sources").as_posix() for p in (ROOT / "sources").rglob("*") if p.is_dir()]
    bad = [f for f in folders if not re.fullmatch(r"[a-z0-9_]+(/[a-z0-9_]+)*", f)]
    assert not bad, bad


# sources/ by origin: who published a file and where it can be fetched again
# (docs/architecture.md, Layout)
def test_source_folders_follow_the_origin():
    named = re.findall(r"^## ([a-z0-9_/]+)$", (ROOT / "sources" / "README.md").read_text(encoding="utf-8"), re.M)
    assert named and all((ROOT / "sources" / n).is_dir() for n in named), named
    # every folder with files is a folder of sources/README.md or lies below one
    folders = {p.parent.relative_to(ROOT / "sources").as_posix() for p in (ROOT / "sources").rglob("*")
               if p.is_file() and not p.name.startswith(".") and p.parent != ROOT / "sources"}
    unnamed = [f for f in folders if not any(f == n or f.startswith(n + "/") for n in named)]
    assert not unnamed, unnamed
    # sources/ itself holds only this file and the dates of the downloads (pipeline/update_sources.py)
    assert {p.name for p in (ROOT / "sources").iterdir() if p.is_file() and not p.name.startswith(".")} \
        <= {"README.md", "fetched.csv"}


def test_every_source_file_exists_once():
    seen: dict[str, str] = {}
    twice = []
    for p in sorted((ROOT / "sources").rglob("*")):
        if p.is_file() and not p.name.startswith("."):  # .DS_Store and other files of the system
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if digest in seen:
                twice.append((seen[digest], p.relative_to(ROOT).as_posix()))
            seen.setdefault(digest, p.relative_to(ROOT).as_posix())
    assert not twice, twice


def test_code_names_no_spec():
    # \s: a reference may wrap. ".spec.mjs" is the suffix of a Playwright test file, not a spec.
    pattern = re.compile(r"\b(specs?|plans?)\s+20\d\d-|docs/(specs|plans)/|\bspecs?\b(?!\.mjs)|\baddend(um|a)\b",
                         re.IGNORECASE)
    files = [p for d in ("pipeline", "tests", "web", "research/scripts", "reference") for p in (ROOT / d).rglob("*")
             if p.suffix in {".py", ".js", ".mjs", ".css", ".html", ".md", ".csv"} and "node_modules" not in p.parts
             and p.name != "test_doc_paths.py"]
    found = [f"{p.relative_to(ROOT)}:{text.count(chr(10), 0, m.start()) + 1}" for p in files
             for text in [p.read_text(encoding="utf-8")] for m in pattern.finditer(text)]
    assert not found, found


def test_readme_pointers_have_a_readme():
    """A comment that points to "README" in a package of pipeline/ needs that README."""
    found = [f"{p.relative_to(ROOT)}" for p in (ROOT / "pipeline").rglob("*.py")
             if re.search(r"\(README\b|\bREADME[:)]", p.read_text(encoding="utf-8")) and not (p.parent / "README.md").exists()]
    assert not found, found


def test_every_readme_in_pipeline_is_a_living_doc():
    readmes = set((ROOT / "pipeline").rglob("README.md"))
    assert readmes and readmes <= set(living_docs()), sorted(readmes - set(living_docs()))


def unbreakable(line: str) -> bool:
    """One URL or one code span: no space to break the line at."""
    rest = re.sub(r"^([-*]|\d+\.)\s+", "", line.strip())
    return " " not in re.sub(r"`[^`]*`", "x", rest)


def long_lines(root: Path = ROOT, limit: int = 120) -> list[str]:
    """Prose lines of the living docs over the limit; tables, code blocks, headings and unbreakable lines may be
    longer."""
    out = []
    for doc in living_docs(root):
        code = False
        for number, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("```"):
                code = not code
            elif not code and len(line) > limit and not line.lstrip().startswith(("|", "#")) and not unbreakable(line):
                out.append(f"{doc.relative_to(root)}:{number}")
    return out


def test_living_docs_keep_lines_short():
    assert not long_lines(), long_lines()


def test_checker_finds_long_prose_lines(tmp_path):
    (tmp_path / "docs").mkdir()
    lines = [f"# {'h ' * 65}", f"| {'t ' * 65} |", "```", "c " * 65, "```", "word " * 25, ("word " * 24).strip(),
             f"  https://example.org/{'u' * 120}", f"- `{'c c' * 50}`"]
    (tmp_path / "docs" / "a.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert long_lines(tmp_path) == ["docs/a.md:6"]


POINTER = re.compile(r"`?docs/([\w-]+\.md)`?, ([^);\n]+)")


def headings(doc: Path) -> set[str]:
    return {m.strip() for m in re.findall(r"^#+ (.+)$", doc.read_text(encoding="utf-8"), re.M)}


def missing_sections(root: Path = ROOT) -> list[str]:
    """Every pointer "docs/<name>.md, <Section>" in code, tests, research scripts and the living docs names an existing
    heading of that file, at any level, case-sensitive. The section text runs until ")", ";" or the end of the line.
    A pointer may go on with ": " or ". " and prose, or name a heading that holds ": " itself ("Map: legend"). So the
    rule: the whole text, or the text before one of its ": " or ". ", is a heading. A trailing "." or "," does not
    count. A pointer to "Section: subsection" therefore passes when the section exists."""
    files = [p for d in ("pipeline", "web", "tests", "research/scripts") for p in (root / d).rglob("*")
             if p.suffix in {".py", ".js", ".mjs", ".css", ".html", ".md"} and "node_modules" not in p.parts
             and p.name != "test_doc_paths.py"]
    out = []
    for path in sorted(set(files) | set(living_docs(root))):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for name, section in POINTER.findall(line):
                doc = root / "docs" / name
                text = section.strip().rstrip(".,")
                cuts = [m.start() for m in re.finditer(r"[:.] ", text)] + [len(text)]
                options = {text[:i] for i in cuts}
                if not doc.exists() or not options & headings(doc):
                    out.append(f"{path.relative_to(root)}:{number}: docs/{name}, {text}")
    return out


def test_section_pointers_name_existing_headings():
    assert not missing_sections(), missing_sections()


def test_checker_finds_a_missing_section(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n## Map: legend\n### Lines\n", encoding="utf-8")
    (tmp_path / "pipeline").mkdir()
    (tmp_path / "pipeline" / "x.py").write_text(
        "# ok (docs/a.md, Lines)\n# ok (`docs/a.md`, Map: legend)\n# ok docs/a.md, Lines: the rest is prose.\n"
        "# ok docs/a.md, Map: legend: prose\n# bad (docs/a.md, Gone)\n# bad (docs/a.md, lines)\n"
        "# bad (docs/b.md, Lines)\n# ok (docs/a.md, A; docs/a.md, Lines)\n# ok docs/a.md, Lines. More prose.\n",
        encoding="utf-8")
    assert missing_sections(tmp_path) == ["pipeline/x.py:5: docs/a.md, Gone", "pipeline/x.py:6: docs/a.md, lines",
                                          "pipeline/x.py:7: docs/b.md, Lines"]


# research/ keeps a finding only while a file outside it names the finding (research/README.md, Keeping and removing)
CITING = ("CLAUDE.md", "README.md", "docs", "pipeline", "tests", "reference", "sources/README.md", "web")
TEXT = {".py", ".md", ".js", ".mjs", ".css", ".html", ".csv", ".json", ".txt"}
SITUATION = "## Data situation"


def findings(root: Path = ROOT) -> list[str]:
    """The dated Markdown files and dated folders at the top of research/."""
    return sorted(p.name for p in (root / "research").iterdir() if re.match(r"20\d\d-\d\d-\d\d-", p.name))


def texts(paths) -> str:
    files = [f for p in paths if p.exists() for f in ([p] if p.is_file() else sorted(p.rglob("*")))
             if f.is_file() and f.suffix in TEXT and "node_modules" not in f.parts and f.name != "test_doc_paths.py"]
    return "\n".join(f.read_text(encoding="utf-8") for f in files)


def names(text: str, name: str, folder: bool = False) -> bool:
    """True when the text holds the name as a whole: not as a part of a longer name. A folder needs its slash."""
    return re.search(r"(?<![\w.-])" + re.escape(name) + ("/" if folder else r"(?![\w-])"), text) is not None


def unnamed_findings(root: Path = ROOT) -> list[str]:
    """Findings that no living file names, neither directly nor through a script or result of research/ that a
    living file names, and that the section "Data situation" of research/README.md does not list. A finding named
    only by another finding counts as unnamed."""
    outside = texts(root / p for p in CITING)
    tools = [p for d in ("scripts", "results") for p in sorted((root / "research" / d).glob("*"))
             if names(outside, p.relative_to(root).as_posix())]
    readme = (root / "research" / "README.md").read_text(encoding="utf-8")
    situation = readme.split(SITUATION)[1].split("\n## ")[0] if SITUATION in readme else ""
    named = "\n".join((outside, texts(tools), situation))
    return [f for f in findings(root) if not names(named, f, folder=(root / "research" / f).is_dir())]


def test_every_finding_is_named():
    assert not unnamed_findings(), unnamed_findings()


def test_checker_finds_unnamed_findings(tmp_path):
    research = tmp_path / "research"
    for folder in ("scripts", "results", "2026-01-05-folder", "2026-01-11-e"):
        (research / folder).mkdir(parents=True)
    files = {
        "2026-01-01-kept.md": "See `research/2026-01-06-only-by-finding.md`.",
        "2026-01-02-chain.md": "", "2026-01-03-gone.md": "", "2026-01-04-situation.md": "",
        "2026-01-06-only-by-finding.md": "", "2026-01-07-by-result.md": "", "2026-01-08-by-lone-script.md": "",
        "2026-01-09-by-this-test.md": "", "2026-01-10-a.md": "",
        "scripts/s.py": "# research/2026-01-02-chain.md",
        "scripts/lone.py": "# research/2026-01-08-by-lone-script.md",  # no living file names this script
        "results/r.txt": "research/2026-01-07-by-result.md",
        "README.md": "`research/2026-01-03-gone.md`\n## Data situation\n\n- `research/2026-01-04-situation.md`\n\n"
                     "## Scripts\n`research/scripts/lone.py`",
    }
    for name, text in files.items():
        (research / name).write_text(text + "\n", encoding="utf-8")
    (tmp_path / "pipeline").mkdir()
    (tmp_path / "pipeline" / "README.md").write_text(
        "`research/2026-01-01-kept.md`, `research/scripts/s.py`, `research/results/r.txt`,\n"
        "`research/old-2026-01-10-a.md`, `research/2026-01-11-e-f.md`, `research/2026-01-05-folder.md`\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_doc_paths.py").write_text("# research/2026-01-09-by-this-test.md\n", encoding="utf-8")
    assert unnamed_findings(tmp_path) == ["2026-01-03-gone.md", "2026-01-05-folder", "2026-01-06-only-by-finding.md",
                                          "2026-01-08-by-lone-script.md", "2026-01-09-by-this-test.md",
                                          "2026-01-10-a.md", "2026-01-11-e"]
