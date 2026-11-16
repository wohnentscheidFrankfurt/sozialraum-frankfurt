# Single dataset "Leben in Frankfurt 2025": rent per m2 by landlord, lock-in when moving. Weighted with `weight`.
# Call: python lif.py <leben-in-frankfurt_2025.csv> [rent cap, default 1550]
# Area, rent, length of residence and age exist only in classes of the codebook; the class maps below use midpoints.
import sys, numpy as np, pandas as pd
df = pd.read_csv(sys.argv[1], sep=';', encoding='utf-8-sig', low_memory=False)
cols = ['weight','Umfragebezirk','FFdauliw_a','WOmieig_a','WOverm_a','WOmierh','WOflae_a','WOraeu_a','WOkami_a','XDhhform_a','XDhhgrabs_a','XDgebjahr_a','XDhhnek_a']
d = df[cols].copy()
for c in cols[2:]:
    d[c] = pd.to_numeric(d[c], errors='coerce'); d.loc[d[c] < 0, c] = np.nan
d['weight'] = pd.to_numeric(d['weight'].astype(str).str.replace(',', '.'), errors='coerce')
TOP_RENT = float(sys.argv[2]) if len(sys.argv) > 2 else 1550
area_m2 = {i: 25 + 10*(i-1) for i in range(1, 13)}; area_m2[1] = 25; area_m2[13] = 155
rent_by_class = {1: 350}; rent_by_class.update({i: 450 + 100*(i-2) for i in range(2, 12)}); rent_by_class[12] = TOP_RENT
d['m2'] = d.WOflae_a.map(area_m2); d['rent'] = d.WOkami_a.map(rent_by_class)
d['eur_m2'] = d.rent / d.m2
d['persons'] = np.where(d.XDhhform_a == 1, 1, np.where(d.XDhhform_a == 2, 2, d.XDhhgrabs_a))
d['rooms'] = d.WOraeu_a
d['under'] = (d.rooms - d.persons) >= 2
d['over'] = d.rooms < d.persons
LANDLORD = {1: 'individual/heirs', 2: 'public (ABG, NH)', 3: 'private company', 4: 'other incl. coop'}
TENURE = {1: '<5 y', 2: '5-15 y', 3: '>=15 y'}
AGE = {1: '18-29', 2: '30-39', 3: '40-49', 4: '50-59', 5: '60-69', 6: '70-79'}
# wq = weighted quantile, wmean = weighted mean, wshare = weighted share in percent
def wq(x, w, q=.5):
    m = x.notna() & w.notna(); x, w = x[m].values, w[m].values
    if len(x) == 0: return np.nan
    o = np.argsort(x); x, w = x[o], w[o]; c = np.cumsum(w) / w.sum()
    return x[np.searchsorted(c, q)]
def wmean(x, w):
    m = x.notna(); return np.average(x[m], weights=w[m]) if m.any() else np.nan
def wshare(b, w):
    m = b.notna(); return 100*np.average(b[m].astype(float), weights=w[m]) if m.any() else np.nan
r = d[d.WOmieig_a == 1].copy()  # tenants
print(f"Respondents {len(d)}, tenants {len(r)}, with m2+rent {r.eur_m2.notna().sum()}, rent top-coded (>=1400) {(r.WOkami_a==12).sum()}")
print("\n== 1) EUR/m2 net rent by landlord (all tenants) ==")
for k, v in LANDLORD.items():
    g = r[r.WOverm_a == k]
    print(f"{v:26s} n={g.eur_m2.notna().sum():5d}  share={wshare(r.WOverm_a.dropna()==k, r.weight[r.WOverm_a.notna()]):4.1f}%  median {wq(g.eur_m2,g.weight):5.2f}  mean {wmean(g.eur_m2,g.weight):5.2f}  Q1 {wq(g.eur_m2,g.weight,.25):5.2f} Q3 {wq(g.eur_m2,g.weight,.75):5.2f}  rent>=1400: {wshare(g.WOkami_a==12,g.weight):4.1f}%")
print("\n== 2) EUR/m2 by landlord and length of residence in the dwelling ==")
for k, v in LANDLORD.items():
    line = f"{v:26s}"
    for dk, dv in TENURE.items():
        g = r[(r.WOverm_a == k) & (r.FFdauliw_a == dk)]
        line += f" | {dv}: med {wq(g.eur_m2,g.weight):5.2f} mean {wmean(g.eur_m2,g.weight):5.2f} (n={g.eur_m2.notna().sum()})"
    print(line)
line = f"{'all tenants':26s}"
for dk, dv in TENURE.items():
    g = r[r.FFdauliw_a == dk]; line += f" | {dv}: med {wq(g.eur_m2,g.weight):5.2f} mean {wmean(g.eur_m2,g.weight):5.2f} (n={g.eur_m2.notna().sum()})"
print(line)
print("\n== 3) Rent increase since 5/2019 (share yes), only length of residence >=5 y ==")
for k, v in LANDLORD.items():
    g = r[(r.WOverm_a == k) & (r.FFdauliw_a >= 2) & r.WOmierh.notna()]
    print(f"{v:26s} yes {wshare(g.WOmierh==1, g.weight):4.1f}%  (n={len(g)})")
print("\n== 4) Occupancy of tenant households by age (under-occupied: rooms-persons>=2; over-occupied: rooms<persons) ==")
for k, v in AGE.items():
    g = r[(r.XDgebjahr_a == k) & r.rooms.notna() & r.persons.notna()]
    print(f"{v}: under-occupied {wshare(g.under,g.weight):4.1f}%  over-occupied {wshare(g.over,g.weight):4.1f}%  persons/household median {wq(g.persons,g.weight)}  (n={len(g)})")
g = r[r.rooms.notna() & r.persons.notna()]
print(f"all: under-occupied {wshare(g.under,g.weight):4.1f}%  over-occupied {wshare(g.over,g.weight):4.1f}%  (n={len(g)})")
print("\n   by length of residence:")
for dk, dv in TENURE.items():
    g = r[(r.FFdauliw_a == dk) & r.rooms.notna() & r.persons.notna()]
    print(f"   {dv}: under-occupied {wshare(g.under,g.weight):4.1f}%  over-occupied {wshare(g.over,g.weight):4.1f}% (n={len(g)})")
print("\n   by income (net equivalised):")
for ek in range(1, 7):
    g = r[(r.XDhhnek_a == ek) & r.rooms.notna() & r.persons.notna()]
    print(f"   level {ek}: under-occupied {wshare(g.under,g.weight):4.1f}%  over-occupied {wshare(g.over,g.weight):4.1f}% (n={len(g)})")
print("\n== 5) Swap calculation ==")
a = r[(r.XDgebjahr_a >= 5) & (r.persons <= 2) & (r.under) & (r.FFdauliw_a == 3)]
print(f"60+, 1-2 persons, under-occupied, >=15 y in dwelling: n={len(a)}, share of all tenant households {100*a.weight.sum()/r.weight.sum():.1f}%  rooms med {wq(a.rooms,a.weight)}  m2 med {wq(a.m2,a.weight)}  rent med {wq(a.rent,a.weight)}  EUR/m2 med {wq(a.eur_m2,a.weight):.2f}")
for rooms in (1, 2, 3):
    b = r[(r.FFdauliw_a == 1) & (r.rooms == rooms)]
    print(f"New leases (<5 y) {rooms} room(s): n={len(b)} m2 med {wq(b.m2,b.weight)}  rent med {wq(b.rent,b.weight)}  EUR/m2 med {wq(b.eur_m2,b.weight):.2f}")
print("\n== 6) Who rents to the under-occupying older people (group from 5)? ==")
for k, v in LANDLORD.items():
    print(f"{v:26s} {100*a.weight[a.WOverm_a==k].sum()/a.weight[a.WOverm_a.notna()].sum():4.1f}%")
print("\n== 7) Share of new leases (<5 y) with EUR/m2 >= 1.2 x median of long-term tenants, by landlord ==")
for k, v in LANDLORD.items():
    g = r[(r.WOverm_a == k) & (r.FFdauliw_a == 1)]
    print(f"{v:26s} >=16 EUR/m2: {wshare(g.eur_m2>=16, g.weight):4.1f}%   >=20 EUR/m2: {wshare(g.eur_m2>=20, g.weight):4.1f}%  (n={g.eur_m2.notna().sum()})")
