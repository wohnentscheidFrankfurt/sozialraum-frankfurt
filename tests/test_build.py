import importlib
from pathlib import Path

import pytest

from pipeline import build
from pipeline.build import STEPS
from pipeline.engine.steps import Step, check_order


def test_steps_are_in_a_valid_order():
    check_order(STEPS)
    names = [s.name for s in STEPS]
    assert names[0] == "zensus" and names[-2:] == ["checks", "map"]  # a FAIL in the checks stops the map


def test_the_build_copies_nothing_outside_the_repo(monkeypatch):
    """The map goes online with pipeline/publish.py; the build copies nothing outside the repo."""
    from pipeline import config
    assert not hasattr(config, "TARGET") and not hasattr(build, "copy_to_target")
    with pytest.raises(SystemExit):
        build.main(["--no-copy"])


def test_the_build_never_publishes():
    """Publishing pushes to GitHub; it runs only by hand (python -I -m pipeline.publish), never as a step."""
    import ast
    tree = ast.parse(open(build.__file__, encoding="utf-8").read())
    names = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
    modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert "publish" not in names and "pipeline.publish" not in modules | names
    assert not [s.name for s in STEPS if "publish" in s.name]


def _fake_steps(log):
    return [Step("a", lambda ctx: log.append("a")), Step("b", lambda ctx: log.append("b"))]


def test_cli_runs_all_steps_in_order(monkeypatch):
    log = []
    monkeypatch.setattr(build, "STEPS", _fake_steps(log))
    build.main([])
    assert log == ["a", "b"]


def test_cli_runs_one_step(monkeypatch):
    log = []
    monkeypatch.setattr(build, "STEPS", _fake_steps(log))
    build.main(["--step", "b"])
    assert log == ["b"]


def test_cli_has_no_refresh(monkeypatch):
    """The build reads only sources/; pipeline/update_sources.py downloads."""
    monkeypatch.setattr(build, "STEPS", _fake_steps([]))
    with pytest.raises(SystemExit):
        build.main(["--refresh"])


def test_cli_rejects_an_unknown_step(monkeypatch):
    monkeypatch.setattr(build, "STEPS", _fake_steps([]))
    with pytest.raises(SystemExit):
        build.main(["--step", "x"])


def test_every_package_with_a_step_is_in_the_build():
    names = {s.name for s in STEPS}
    packages = sorted(p.parent for p in Path("pipeline").glob("*/*/step.py"))
    for folder in packages:
        module = importlib.import_module(".".join(folder.parts) + ".step")
        steps = [v for k, v in vars(module).items() if k.endswith("STEP")]
        assert steps and all(s.name in names for s in steps), folder
