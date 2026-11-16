"""Do the 2026 zones match the 2024 zones? Three points per 2024 zone, asked for their 2026 zone (HVBG WMS).

  .venv/bin/python -I research/scripts/boris_2026_zone_match.py research/results/boris_2026_zone_match.csv
"""
import csv, random, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shapely.geometry import Point
sys.path.insert(0, ".")
from pipeline.shared.readers.gml import parse_features

mun = re.compile(r"<boris:BR_Gemeinde>.*?<boris:name>([^<]*)</boris:name>", re.S)
zones = []
for p in sorted(Path("sources/hessen/boris").glob("boris_*.gml")):
    for f in parse_features(p.read_text(encoding="utf-8")):
        m = mun.search(f.raw)
        if m and m.group(1).strip() == "Frankfurt am Main" and f.geom is not None:
            zones.append(f)
rng = random.Random(1)
points = []
for f in zones:
    g = f.geom
    pts = [g.representative_point()]
    x0, y0, x1, y1 = g.bounds
    tries = 0
    while len(pts) < 3 and tries < 200:
        tries += 1
        q = Point(rng.uniform(x0, x1), rng.uniform(y0, y1))
        if g.contains(q): pts.append(q)
    for k, q in enumerate(pts):
        points.append((f.props["bodenrichtwertNummer"], f.props["bodenrichtwert"], f.props.get("entwicklungszustand", ""),
                       f.props.get("art", ""), k, q.x, q.y))
URL = ("https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-maps.ows?language=ger&REQUEST=GetFeatureInfo"
       "&VERSION=1.1.1&SERVICE=WMS&LAYERS=hboris_feature&QUERY_LAYERS=hboris_feature&INFO_FORMAT=text/plain"
       "&SRS=EPSG:25832&BBOX={},{},{},{}&WIDTH=101&HEIGHT=101&X=50&Y=50&FEATURE_COUNT=5")
FIELDS = ("WNUM", "BRW", "STAG", "ENTW_KLART", "NUTA_KLART", "NUTA_FARB")

def ask(pt):
    x, y = pt[5], pt[6]
    for attempt in range(4):
        try:
            text = urllib.request.urlopen(URL.format(x - 0.5, y - 0.5, x + 0.5, y + 0.5), timeout=60).read().decode("utf-8", "replace")
            break
        except Exception:
            time.sleep(2 + attempt * 3)
    else:
        return pt + ("ERROR",) + ("",) * (len(FIELDS))
    feats = text.split("Feature ")[1:]
    vals = [tuple((re.search(rf"{k} = '([^']*)'", ft) or [None, ""])[1] for k in FIELDS) for ft in feats]
    joined = tuple(";".join(v[i] for v in vals) for i in range(len(FIELDS)))
    return pt + (str(len(vals)),) + joined

with ThreadPoolExecutor(4) as ex:
    rows = list(ex.map(ask, points))
with open(sys.argv[1], "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(("wnum24", "brw24", "entw24", "art24", "k", "x", "y", "hits") + tuple(k.lower() for k in FIELDS))
    w.writerows(rows)
print("zones", len(zones), "points", len(points))
