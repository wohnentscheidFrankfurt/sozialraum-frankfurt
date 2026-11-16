# Scenarios of the Unsicherheit per ownership form: the numbers behind research/2026-10-12-uncertainty-of-ownership.md
# (old protocols: tag docs-history-2026-10-20 of the archive). Reads the interim data of a build.
# Call: .venv/bin/python -I research/scripts/uncertainty_scenarios.py interim > research/results/uncertainty_scenarios.txt
import json
import sys
from pathlib import Path

import pandas as pd

from pipeline import config as cf
from pipeline.use_cases.coops.model import HALF_ESTIMATED
from pipeline.use_cases.ownership_cells.model import GROUPS
from pipeline.use_cases.ownership_shares.model import HALF_POINTS
from pipeline.use_cases.public_housing.model import P90_CHANGE
from pipeline.shared.zensus.model import CLASSES
from pipeline.shared.zensus.tables import read_4000w

interim = Path(sys.argv[1])
read = lambda name: pd.read_csv(interim / name)
q = read("ownership_shares_by_quarter.csv").set_index("id")
ph = read("public_housing_quarters.csv").set_index("quarter")
co = read("coops_quarters.csv").set_index("quarter")
city = {r["indicator"]: r["value"] for r in json.loads((interim / "ownership_shares_city.json").read_text())}
table = read_4000w(cf.ZENSUS_4000W.read_text(encoding="utf-8-sig"))
known = ph["public_value"] / (q["OWN_PUBLIC"] / 100)  # every Stadtteil has ABG or NH dwellings
half = pd.DataFrame({"OWN_PUBLIC": 100 * ph["public_half"] / known, "OWN_COOP": 100 * co["coop_half"] / known,
                     **{g: pd.Series(h, index=q.index) for g, h in HALF_POINTS.items()}})

print("# 1. Half range per Stadtteil in percentage points: smallest, median, largest (value and range of the map)")
for g in half.columns:
    h = half[g].dropna().sort_values()
    picks = {"smallest": h.index[0], "median": h.index[len(h) // 2], "largest": h.index[-1]}
    row = "; ".join(f"{k} {n}: ±{h[n]:.2f}, {q.loc[n, g]:.1f} % ({q.loc[n, g + '_LOW']:.1f}–{q.loc[n, g + '_HIGH']:.1f})"
                    for k, n in picks.items())
    print(f"{g:14} {row}")

print("\n# 2. What sets the half range of ABG and NH (pipeline/use_cases/public_housing/README.md)")
# half range = max(16 % of the change, difference of the two variants) + unfilled secrecy gap 2011
stock = ph[["abg_scaled", "nh_scaled", "abg_fill", "nh_fill"]].sum(axis=1)
backtest = P90_CHANGE * (stock - ph["abg_2011"] - ph["nh_2011"] + ph["new"]).abs()
variants = (ph["abg_scaled"] + ph["nh_scaled"] - ph["public_additive"]).abs()
floor = variants > backtest
parts = pd.DataFrame({"backtest": backtest.where(~floor, 0.0), "variants": variants.where(floor, 0.0),
                      "gap": ph["gap_public"]})
print(f"Frankfurt: half ranges added up {ph['public_half'].sum():,.0f} = {P90_CHANGE:.0%} of the change "
      f"{parts['backtest'].sum():,.0f} + difference of the variants {parts['variants'].sum():,.0f} + secrecy gap 2011 "
      f"{parts['gap'].sum():,.0f} ({parts['gap'].sum() / ph['public_half'].sum():.0%})")
print(f"difference of the variants larger than {P90_CHANGE:.0%} of the change in {int(floor.sum())} of {len(ph)} "
      f"Stadtteile: " + ", ".join(sorted(ph.index[floor])))
print("secrecy gap smaller than the estimate part in: " + ", ".join(sorted(ph.index[ph["gap_public"] < ph["err_change"]])))
for n in half["OWN_PUBLIC"].nlargest(3).index:
    print(f"  {n}: value {ph.loc[n, 'public_value']:,.0f}, half {ph.loc[n, 'public_half']:,.0f} = "
          + " + ".join(f"{k} {v:,.0f}" for k, v in parts.loc[n].items()))

print(f"\n# 3. Genossenschaften: half range = {HALF_ESTIMATED:.0%} of the estimated part (gap 2011 + estimate 2022)")
estimated = (co["gap_2011"] + co["estimate_2022"]) / co["coop_value"].where(co["coop_value"] > 0)
print(f"estimated part of the value: Frankfurt {(co['gap_2011'] + co['estimate_2022']).sum() / co['coop_value'].sum():.0%}; "
      f"Stadtteile counted only: {int((estimated == 0).sum())}, without coop: {int(estimated.isna().sum())}")
for n in half["OWN_COOP"].nlargest(3).index:
    print(f"  {n}: value {co.loc[n, 'coop_value']:,.0f}, estimated {estimated[n]:.0%}, half {co.loc[n, 'coop_half']:,.0f}")

print("\n# 4. Basis of the half range: error of the estimate in 9 of 10 Stadtteile, backtest on 2011")
print(f"OWN_PUBLIC     {P90_CHANGE:.0%} on the estimated change (research/2026-10-10-abg-estimate-accuracy.md, E2), "
      "at least the difference of the two variants, plus the unfilled secrecy gap 2011 (both no backtest)")
print(f"OWN_COOP       {HALF_ESTIMATED:.0%} on the estimated part (research/results/formula_review.txt, backtest E0)")
for g, h in HALF_POINTS.items():
    print(f"{g:14} {h} points (research/results/formula_review.txt, round 2; the range holds the count in 40 of 45)")

print("\n# 5. Abgleich against Unsicherheit, Frankfurt: share of the map, share of table 4000W-2002, half range of the city")
total = sum(table[k] for k in CLASSES)
known_city = ph["public_value"].sum() / (city["OWN_PUBLIC"] / 100)
city_half = {"OWN_PUBLIC": 100 * ph["public_half"].sum() / known_city, "OWN_COOP": 100 * co["coop_half"].sum() / known_city,
             **HALF_POINTS}
for g, classes in GROUPS.items():
    expected = 100 * sum(table[k] for k in classes) / total
    diff = city[g] - expected
    print(f"{g:14} map {city[g]:5.2f} %, table {expected:5.2f} %, difference {diff:+.2f} points, half range ±{city_half[g]:.2f}"
          + ("  OUTSIDE" if abs(diff) > city_half[g] else ""))
print(f"denominator: map {known_city:,.0f} dwellings with an owner (grid), table {total:,} dwellings (sum of the "
      f"classes; the table prints {table['total']:,})")
print(f"in dwellings: ABG and NH map {ph['public_value'].sum():,.0f}, table {table['municipal']:,}; "
      f"Genossenschaften map {co['coop_value'].sum():,.0f}, table {table['coop']:,}")
