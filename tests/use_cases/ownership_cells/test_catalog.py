from pipeline.use_cases.ownership_cells.catalog import ZENSUS_2022


def test_zensus_2022_source_names_both_grids():
    """The grids and the table are source vocabulary of the Zensus."""
    title = ZENSUS_2022["de"].title
    assert title.startswith("Zensus 2022 ") and "100-m-" in title and "1-km-Gitter" in title and "4000W" in title
