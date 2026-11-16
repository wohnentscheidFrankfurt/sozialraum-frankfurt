from pipeline import config
from pipeline import publish as pp

GOOD = '<head><meta name="robots" content="noindex"></head><h1>Sozialraum Frankfurt</h1>'


def test_a_good_map_has_no_problems():
    assert pp.problems(GOOD) == []


def test_search_engines_must_skip_the_map():
    assert pp.problems(GOOD.replace('content="noindex"', 'content="all"')) == ["the map lacks <meta name=\"robots\" content=\"noindex\">"]


def test_no_local_traces():
    assert pp.problems(GOOD + "/Users/someone/x.csv") == ["the map holds a local path ('/Users/')"]


def test_commits_use_the_noreply_address():
    # the work address of the repo must not appear in a public history
    assert pp.AUTHOR_EMAIL.endswith("@users.noreply.github.com")


def test_warnings_lists_the_warn_rows_of_the_check_report():
    # docs/texts.md, ⓘ protocol: the Abgleich lives in the checks, so the WARN rows show before upload
    report = ("# Check report 2026-10-13\n\n| Status | Check | Result |\n|---|---|---|\n"
              "| WARN | Coops: x | 3.48 against 3.21 |\n| OK | Housing: y | fine |\n")
    assert pp.warnings(report) == ["Coops: x: 3.48 against 3.21"]
    assert pp.warnings("") == []  # Review Focus 5: no report yet


def test_paths_come_from_config():
    """pipeline/ builds paths only in config.py (docs/architecture.md, Module kinds and dependency rule)."""
    assert pp.MAP == config.OUTPUT / config.MAP_NAME
    assert pp.REPORT == config.INTERIM / "check_report.md"
    assert pp.GITHUB_PAGES == config.GITHUB_PAGES == config.OUTPUT / "github-pages"
