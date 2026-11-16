"""Publish the built map on GitHub Pages: https://snagel86.github.io/sozialraum-frankfurt/

Only the map goes online, as index.html in its own Git history under output/github-pages/ (git-ignored).
The page is public; search engines are asked to skip it, and the link is shared by hand.

Run after the build, by hand:  .venv/bin/python -I -m pipeline.publish
It is no step of the build: publishing pushes to GitHub, so it never runs with `pipeline.build`.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from pipeline import config

MAP = config.OUTPUT / config.MAP_NAME
REPORT = config.INTERIM / "check_report.md"
GITHUB_PAGES = config.GITHUB_PAGES
REMOTE = "https://github.com/snagel86/sozialraum-frankfurt.git"
URL = "https://snagel86.github.io/sozialraum-frankfurt/"
AUTHOR_NAME = "snagel86"
AUTHOR_EMAIL = "22589199+snagel86@users.noreply.github.com"
NOINDEX = '<meta name="robots" content="noindex">'


def problems(html: str) -> list[str]:
    """Reasons not to publish this file."""
    found = []
    if NOINDEX not in html:
        found.append(f"the map lacks {NOINDEX}")
    if "/Users/" in html:
        found.append("the map holds a local path ('/Users/')")
    return found


def warnings(report: str) -> list[str]:
    """Check and result of every WARN row of the check report. The build already stops on FAIL."""
    rows = [line.split("|") for line in report.splitlines() if line.startswith("| WARN |")]
    return [f"{r[2].strip()}: {r[3].strip()}" for r in rows]


def git(*args: str) -> str:
    # the gh login of the private account answers for github.com; the global helper stays untouched
    base = ["git", "-C", str(GITHUB_PAGES), "-c", "credential.helper=",
            "-c", "credential.helper=!gh auth git-credential", "-c", f"user.name={AUTHOR_NAME}",
            "-c", f"user.email={AUTHOR_EMAIL}"]
    return subprocess.run([*base, *args], check=True, capture_output=True, text=True).stdout


def main() -> int:
    html = MAP.read_text(encoding="utf-8")
    if found := problems(html):
        print("not published:", "; ".join(found))
        return 1
    for w in warnings(REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""):
        print("WARN", w)
    if not (GITHUB_PAGES / ".git").exists():
        GITHUB_PAGES.mkdir(exist_ok=True)
        git("init", "-q", "-b", "main")
        git("remote", "add", "origin", REMOTE)
    shutil.copyfile(MAP, GITHUB_PAGES / "index.html")
    (GITHUB_PAGES / ".nojekyll").touch()
    git("add", "index.html", ".nojekyll")
    if not git("status", "--porcelain"):
        print(f"unchanged: {URL}")
        return 0
    git("commit", "-q", "-m", "Update the map")
    git("push", "-q", "-u", "origin", "main")
    print(f"published: {URL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
