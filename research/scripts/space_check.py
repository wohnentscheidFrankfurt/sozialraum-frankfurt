# Wohnfläche je Bewohner: Zensus 2022 grid against the Zensus database (research/2026-10-12-living-space-grid.md).
# The grid mean, weighted by residents, should equal the table value. It lies about a fifth higher, also for Germany.
# Call: .venv/bin/python -I research/scripts/space_check.py cache
# Reads cache/zensus_space_per_resident.zip and cache/zensus_population.zip.
# The pipeline no longer downloads zensus_space_per_resident.zip (the map has no such layer). After a cache wipe fetch it by hand:
#   curl -L -o cache/zensus_space_per_resident.zip \
#     https://www.destatis.de/static/DE/zensus/gitterdaten/Durchschnittliche_Wohnflaeche_je_Bewohner_in_Gitterzellen.zip
# cache/zensus_population.zip is still a download of the pipeline.
import sys, zipfile

import pandas as pd

TABLE_GERMANY = 46.3  # 1000A-0004, Germany, 15.5.2022
TABLE_FRANKFURT = 38.3  # 1000A-0004, Frankfurt (sources/zensus/Zensus2022_1000A-0004_Frankfurt.csv)
HOUSEHOLD_AREA, HOUSEHOLD_SIZE = 73.7, 1.9  # 5000H-0002 and 5000H-0001, Frankfurt


def read(cache: str, zip_name: str, suffix: str) -> pd.DataFrame:
    with zipfile.ZipFile(f"{cache}/{zip_name}") as z:
        name = next(n for n in z.namelist() if n.endswith(suffix))
        return pd.read_csv(z.open(name), sep=";", dtype=str, encoding="latin-1")


def number(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")


cache = sys.argv[1]
for res in ("10km", "1km"):
    space = read(cache, "zensus_space_per_resident.zip", f"_{res}-Gitter.csv")
    pop = read(cache, "zensus_population.zip", f"_{res}-Gitter.csv")
    m = space.merge(pop, on=f"GITTER_ID_{res}")
    m["space"], m["pop"] = number(m["durchschnFlaechejeBew"]), number(m["Einwohner"])
    m = m.dropna(subset=["space", "pop"])
    grid = (m["space"] * m["pop"]).sum() / m["pop"].sum()
    print(f"Germany, {res} grid weighted by residents: {grid:.1f} m², table {TABLE_GERMANY} m², "
          f"grid / table {grid / TABLE_GERMANY:.3f}")
print(f"Frankfurt, table 1000A-0004: {TABLE_FRANKFURT} m²; household area / household size: "
      f"{HOUSEHOLD_AREA / HOUSEHOLD_SIZE:.1f} m²; map value 47.6 m² (100-m grid weighted by residents; tag docs-history-2026-10-20 of the archive)")
