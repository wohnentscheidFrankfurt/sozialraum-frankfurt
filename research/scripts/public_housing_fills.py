# The fills of ABG and Nassauische Heimstätte: what the map loses without them, and what the new sites hold.
# The numbers behind research/2026-10-22-public-housing-fills.md. Reads the interim data of a build and reruns the
# step public_housing without writing.
# Call: .venv/bin/python -I research/scripts/public_housing_fills.py > research/results/public_housing_fills.txt
import pandas as pd

from pipeline import config
from pipeline.build import STEPS
from pipeline.engine.steps import Context, producers
from pipeline.engine.store import Store
from pipeline.shared.zensus.model import CLASSES
import pipeline.use_cases.public_housing.step as step

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 100)


def breaks(values):  # the quantile classes of the map (APP.classify in web/js/01_base.js), without merged breaks
    w = sorted(values)
    return [w[min(len(w) - 1, (i * len(w)) // 5)] for i in range(1, 5)]


def klass(x, b):
    return sum(x >= g for g in b)


q = pd.read_csv(config.INTERIM / "public_housing_quarters.csv").set_index("quarter")
s = pd.read_csv(config.INTERIM / "ownership_shares_by_quarter.csv").set_index("id")
q["total"] = s["OWN_PUBLIC_DWELLINGS"] / s["OWN_PUBLIC"] * 100
q["share"] = s["OWN_PUBLIC"]
q["half_points"] = q["public_half"] / q["total"] * 100
variants = {
    "A": q["abg_scaled"] + q["nh_scaled"],  # count 2011 × factor only
    "B": q["public_value"] - q["research_new"],  # without the research
}
print("Frankfurt:", q[["public_value", "abg_scaled", "nh_scaled", "abg_fill", "nh_fill", "new", "research_new",
                       "gap_municipal"]].sum().round(0).to_dict())
now = q["share"]
b_now = breaks(now)
for name, value in variants.items():
    share = value / q["total"] * 100
    q[f"d{name}"] = share - now
    b = breaks(share)
    moved = [n for n in q.index if klass(now[n], b_now) != klass(share[n], b)]
    ranks = zip(q.index, now.rank(ascending=False), share.rank(ascending=False))
    print(f"\nVariant {name}: {len(moved)} Stadtteile change the class: {', '.join(moved)}")
    print("  rank moves by more than 3:", [(n, int(a), int(r)) for n, a, r in ranks if abs(a - r) > 3])
print()
print(q[["total", "public_value", "share", "half_points", "dA", "dB"]].round(1).sort_values("dA").to_string())

# new sites (step 5 of the README): cells without public stock in 2011 and municipal in 2022
captured = {}
original = step.public_housing


def spy(cells, e11, e22, sites):
    captured.update(cells=cells, e22=e22.reindex(cells.index, fill_value=0.0))
    return original(cells, e11, e22, sites)


class ReadOnly:
    def __init__(self, store):
        self.store = store

    def read(self, dataset):
        return self.store.read(dataset)

    def write(self, *args, **kwargs):
        pass


step.public_housing = spy
step.run(Context(ReadOnly(Store(config.INTERIM, producers(STEPS))), config, log=lambda _: None))
c, e22 = captured["cells"], captured["e22"]
new = ((c["dw_municipal_2011"] + c["dw_state_2011"]) == 0) & (c["bld_municipal"] > 0)
t11 = c["dw_total_2011"]
hidden = t11 - c[[f"dw_{k}_2011" for k in CLASSES]].sum(axis=1)
m = e22["municipal"].where(new, 0.0)
sites = pd.DataFrame({"quarter": c["quarter"], "empty_2011": m.where(t11 == 0, 0.0),
                      "dwellings_2011": m.where(t11 > 0, 0.0),
                      "of_them_secrecy_2011": m.where((t11 > 0) & (hidden > 0), 0.0)}).groupby("quarter").sum()
print("\nNew sites: municipal dwellings 2022 in cells without public stock 2011")
print(sites.loc[sites.sum(axis=1) > 0].round(1).to_string())
print("Frankfurt:", sites.sum().round(0).to_dict())
