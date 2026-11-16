import pandas as pd

from pipeline.engine.datasets import CELLS_2011_BUILDINGS, CELLS_2011_DWELLINGS, CELLS_2022
from pipeline.shared.zensus import step

A, B = "CRS3035RES100mN3000600E4226700", "CRS3035RES100mN3000700E4226700"
HEAD = "Gitter_ID_100m,Gitter_ID_100m_neu,Merkmal,Auspraegung_Code,Auspraegung_Text,Anzahl,Anzahl_q\n"


def test_zensus_2011_reads_both_extracts_for_the_inner_cells(tmp_path, run_step):
    dwellings, buildings = tmp_path / "w.csv", tmp_path / "g.csv"
    dwellings.write_bytes((HEAD + f"x,{A},EIGENTUM,4,Kommune,40,0\nx,{B},EIGENTUM,4,Kommune,9,0\n").encode("latin-1"))
    buildings.write_bytes((HEAD + f"x,{A},EIGENTUM,4,Kommune,3,0\n").encode("latin-1"))
    cells = pd.DataFrame({"cell_id": [A, B], "edge": [0, 1]})  # B is an edge cell
    store, _ = run_step(tmp_path, step.ZENSUS_2011_STEP, {CELLS_2022: cells},
                        GRID_EXTRACTS={"zensus2011_dwellings.zip": dwellings, "zensus2011_buildings.zip": buildings})
    assert store.read(CELLS_2011_DWELLINGS)[["cell_id", "dw_municipal_2011"]].to_dict("records") == [
        {"cell_id": A, "dw_municipal_2011": 40}]
    assert store.read(CELLS_2011_BUILDINGS)["bld_municipal_2011"].tolist() == [3]
