"""Districts and quarters from the geodata in sources/ and the monitoring table in sources/."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from shapely.ops import unary_union

from pipeline.shared.core.geometry import Feature
from pipeline.shared.geography.model import Area, map_quarter_name
from pipeline.shared.readers.gml import parse_features


def _read(path: Path) -> list[Feature]:
    return parse_features(path.read_text(encoding="utf-8"))


def load_districts(gml: Path, monitoring_csv: Path) -> list[Area]:
    """114 analysis units: statistical districts joined as in the monitoring (column Einheit)."""
    stbz = {f.props["STBZ_ID"]: f.geom for f in _read(gml)}
    mon = pd.read_csv(monitoring_csv, dtype={"STBZ": str, "Einheit": str})
    areas = []
    for unit, g in mon.groupby("Einheit", sort=False):
        names = list(dict.fromkeys(n.strip() for n in g["Name"]))
        largest = g.loc[g["EW"].fillna(0).idxmax()]
        areas.append(Area(id=unit, name=" / ".join(names),
                          quarter=map_quarter_name(largest["Stadtteil"]),
                          survey_area=str(largest["Umfragebezirk"]),
                          geom=unary_union([stbz[s] for s in g["STBZ"]])))
    return areas


def load_quarters(gml: Path) -> list[Area]:
    """45 quarters: Sachsenhausen-Süd and Flughafen joined as at votemanager."""
    parts: dict[str, list] = {}
    for f in _read(gml):
        parts.setdefault(map_quarter_name(f.props["STT_NAME"]), []).append(f.geom)
    return [Area(id=n, name=n, quarter=n, survey_area="", geom=unary_union(g)) for n, g in parts.items()]
