"""Every inner cell: all zones of 2026 at its centre (WMS), for a comparison with the built land values.

  .venv/bin/python -I research/scripts/boris_2026_cells.py research/results/boris_2026_cells.csv
"""
import csv, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
sys.path.insert(0, ".")
from pipeline import config
c = pd.read_csv("interim/cells_2022.csv", usecols=["cell_id", "x25832", "y25832", "edge", "pop"])
c = c[c.edge == 0]

def ask(row):
    cid, x, y = row
    u = config.BORIS_VALUES_URL.format(x0=x - .5, y0=y - .5, x1=x + .5, y1=y + .5)
    for a in range(4):
        try:
            text = urllib.request.urlopen(u, timeout=60).read().decode("utf-8", "replace"); break
        except Exception:
            time.sleep(3)
    else:
        return cid, "ERROR"
    out = []
    for part in text.split("Feature ")[1:]:
        f = dict(re.findall(r"(\w+) = '([^']*)'", part))
        out.append("|".join((f.get("WNUM", ""), f.get("BRW", ""), f.get("ENTW_KLART", ""), f.get("NUTA_FARB", ""))))
    return cid, ";".join(out)

with ThreadPoolExecutor(4) as ex:
    rows = list(ex.map(ask, zip(c.cell_id, c.x25832, c.y25832)))
with open(sys.argv[1], "w", newline="") as f:
    w = csv.writer(f); w.writerow(("cell_id", "zones")); w.writerows(rows)
print(len(rows), sum(r[1] == "ERROR" for r in rows))
