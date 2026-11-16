from pathlib import Path

from pipeline import config


def test_inputs_live_in_the_repo():
    assert config.SOURCES == config.ROOT / "sources"
    assert config.CITY == config.SOURCES / "frankfurt"
    assert config.MONITORING_CSV == (config.CITY / "offices" / "Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv")
    assert config.GAZETTE_PDF.parent == config.CITY / "offices"


def test_every_path_lies_in_the_repo():
    paths = {k: v for k, v in vars(config).items() if isinstance(v, Path)}
    assert paths, "no paths found"
    outside = {k: str(v) for k, v in paths.items() if not v.is_relative_to(config.ROOT)}
    assert not outside, outside


def test_every_source_and_reference_file_of_the_config_exists():
    paths = [v for v in vars(config).values() if isinstance(v, Path)
             and (config.SOURCES in v.parents or config.REFERENCE in v.parents) and v.suffix]
    missing = [str(p) for p in paths if not p.exists()]
    assert len(paths) > 20 and not missing, missing


def test_every_database_extract_of_the_config_exists():
    tables = {**config.ZENSUS_TABLES, **config.REGIONAL_TABLES}
    assert len(tables) == 18
    assert not [str(p) for p in tables if not p.exists() or config.SOURCES not in p.parents]


def test_the_map_keeps_its_file_name():
    assert config.MAP_NAME == "sozialraum-frankfurt.html"


def test_downloads_include_the_2011_grid():
    assert config.DOWNLOADS["zensus2011_dwellings.zip"] == (
        "https://www.destatis.de/static/DE/zensus/2011_gitterdaten/Wohnungen_im_100_Meter-Gitter.zip")
