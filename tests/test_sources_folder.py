from pathlib import Path

from pipeline import config


def test_every_file_in_sources_is_read_or_listed():
    read = {v.resolve() for v in vars(config).values() if isinstance(v, Path)}
    read |= {p.resolve() for d in (config.GRID_EXTRACTS, config.GRID_KM_EXTRACTS, config.SNAPSHOTS) for p in d.values()}
    read |= {p.resolve() for p in config.BORIS_DIR.glob("*.gml")}
    readme = (config.SOURCES / "README.md").read_text(encoding="utf-8")
    unexplained = [str(p.relative_to(config.SOURCES)) for p in sorted(config.SOURCES.rglob("*"))
                   if p.is_file() and p.name not in ("README.md", "fetched.csv")
                   and p.resolve() not in read and p.name not in readme]
    assert not unexplained, unexplained
