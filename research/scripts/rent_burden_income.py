# Rent burden by household income from the public files "Leben in Frankfurt" 2025 and 2024 (tenants, weighted with `weight`).
# Call: python rent_burden_income.py <leben-in-frankfurt_2025.csv> <leben-in-frankfurt_2024.csv>
# Rent, costs and income exist only in classes of the codebook; the maps below use class midpoints. The raw household income is
# not public: the income is rebuilt from the equivalised income class (XDhhnek_a) times the equivalence scale.
# Sections: 1 validation against the report, 2 equivalised-income view, 3 groups by household income per year,
# 4 pooled values per survey area, 5 bootstrap, 6 sensitivity of the open classes, 7 worked example.
import sys, numpy as np, pandas as pd

AREAS = {1: 'Innenstadt I', 2: 'Innenstadt II', 3: 'Innenstadt III', 4: 'Bornheim/Ostend', 5: 'Süd', 6: 'West',
         7: 'Mitte-West', 8: 'Nord-West', 9: 'Mitte-Nord', 10: 'Nord-Ost', 11: 'Ost', 12: 'Kalbach/Riedberg', 13: 'Nord'}
# Class bounds (lo, hi); None = open. Rent: 12 classes of 100 EUR, costs: 8 classes of 50 EUR, equivalised income: 6 classes of 1,000 EUR.
KALT = {1: (0, 400), 12: (1400, None)}; KALT.update({i: (400 + 100 * (i - 2), 500 + 100 * (i - 2)) for i in range(2, 12)})
BK = {1: (0, 100), 8: (400, None)}; BK.update({i: (100 + 50 * (i - 2), 150 + 50 * (i - 2)) for i in range(2, 8)})
NEK = {1: (0, 1000), 2: (1000, 2000), 3: (2000, 3000), 4: (3000, 4000), 5: (4000, 5000), 6: (5000, None)}
# Printed classes of Abb. 4.5 (p. 27 of FU 5), copied from FIGURES["LIF_RENT_BURDEN_RATIO"] in pipeline/use_cases/survey/sources.py:
# class (lo, hi) -> areas. Research scripts do not import the pipeline.
CLASSES = {(26, 28): ('Innenstadt III', 'Innenstadt II', 'Mitte-Nord'), (29, 29): ('Innenstadt I', 'Bornheim/Ostend', 'Süd'),
           (30, 30): ('Mitte-West', 'Nord', 'Ost'), (31, 33): ('West', 'Nord-West', 'Kalbach/Riedberg', 'Nord-Ost')}
CLASS_OF = {n: c for c, ns in CLASSES.items() for n in ns}
GROUPS = ['<2000', '2000-3200', '>=3200']


def wq(x, w, q=.5):
    x, w = np.asarray(x, float), np.asarray(w, float)
    m = ~np.isnan(x) & ~np.isnan(w); x, w = x[m], w[m]
    if len(x) == 0: return np.nan
    o = np.argsort(x); x, w = x[o], w[o]; c = np.cumsum(w) / w.sum()
    return x[np.searchsorted(c, q)]


def wshare(b, w, m):
    b, w, m = np.asarray(b, float), np.asarray(w, float), np.asarray(m, bool)
    return 100 * np.average(b[m], weights=w[m]) if m.any() else np.nan


def load(csv, top_kalt=1700, top_nek=6000, low_nek=750):
    """All respondents with warm rent, household income and burden q (percent). Open classes: rent >= 1,400 = top_kalt, income >= 5,000 = top_nek, income < 1,000 = low_nek."""
    df = pd.read_csv(csv, sep=';', encoding='utf-8-sig', low_memory=False)
    cols = ['Umfragebezirk', 'WOmieig_a', 'WOkami_a', 'WObtrko_a', 'XDhhnek_a', 'XDhhgrabs_a', 'XDhhgr017_a', 'XDhhform_a', 'WObelko']
    d = df[cols].apply(pd.to_numeric, errors='coerce')
    d[d < 0] = np.nan  # -42 = no answer
    d['w'] = pd.to_numeric(df['weight'].astype(str).str.replace(',', '.'))
    kalt_mid = {k: (lo + hi) / 2 if hi else top_kalt for k, (lo, hi) in KALT.items()}; kalt_mid[1] = 325
    bk_mid = {k: (lo + hi) / 2 if hi else 450 for k, (lo, hi) in BK.items()}; bk_mid[1] = 75
    nek_mid = {k: (lo + hi) / 2 if hi else top_nek for k, (lo, hi) in NEK.items()}; nek_mid[1] = low_nek
    # household size and children (0-17; the scale wants under 14, so 14-17 get 0.3 instead of 0.5)
    d['n'] = d.XDhhgrabs_a.where(d.XDhhgrabs_a.notna(), d.XDhhform_a.map({1: 1, 2: 2}))
    d['kids'] = d.XDhhgr017_a.map({1: 0, 2: 1, 3: 2, 4: 3})
    d.loc[d.XDhhform_a.isin([1, 2]), 'kids'] = 0
    d.loc[d.kids.isna() & d.n.isin([1, 2]) & d.XDhhform_a.isna(), 'kids'] = 0  # shared flat and other: adults only
    d['scale'] = 1 + 0.5 * (d.n - 1 - d.kids).clip(lower=0) + 0.3 * d.kids
    d['warm'] = d.WOkami_a.map(kalt_mid) + d.WObtrko_a.map(bk_mid)
    d['hhinc'] = d.XDhhnek_a.map(nek_mid) * d.scale
    d['q'] = 100 * d.warm / d.hhinc
    # lowest rent against highest income of the classes (lower bound of the burden)
    d['warm_lo'] = d.WOkami_a.map({k: v[0] for k, v in KALT.items()}) + d.WObtrko_a.map({k: v[0] for k, v in BK.items()})
    d['inc_hi'] = d.XDhhnek_a.map({k: v[1] if v[1] else np.inf for k, v in NEK.items()}) * d.scale
    d['q_lo'] = 100 * d.warm_lo / d.inc_hi
    d['kalt_mid'] = d.WOkami_a.map(kalt_mid)
    d['bk_mid'] = d.WObtrko_a.map(bk_mid)
    d['inc_class_mid'] = d.XDhhnek_a.map(nek_mid)
    return d


def tenants(d):
    r = d[(d.WOmieig_a == 1) & d.q.notna()].copy()
    r['grp'] = pd.cut(r.hhinc, [0, 2000, 3200, np.inf], right=False, labels=GROUPS)
    return r


def r5(x): return 5 * np.floor(x / 5 + .5)  # rounded half up to 5 points


f25, f24 = sys.argv[1], sys.argv[2]
D = {2025: load(f25), 2024: load(f24)}
R = {y: tenants(D[y]) for y in D}
T = {y: D[y][D[y].WOmieig_a == 1] for y in D}  # all tenants, also without income

print('== 1 Validation: median burden of all tenants (report FU 5: 29 %, FU 4: 29 %)')
for y in (2025, 2024):
    t = T[y]; ok = t.q.notna()
    print(f'{y}: tenants {len(t)}, with burden {ok.sum()}; median {wq(t.q, t.w):.1f}; '
          f'kalt median {wq(t.kalt_mid, t.w):.0f}, warm median {wq(t.warm, t.w):.0f}, Q1 {wq(t.warm, t.w, .25):.0f}, Q3 {wq(t.warm, t.w, .75):.0f}')
print('2025 report: kalt 800, warm 1030, Q1 792, Q3 1400.')
print('Per survey area 2025: own median, shown value (rounded half up), printed class, gap outside the class (unrounded | rounded):')
gaps = []
for a, name in AREAS.items():
    s = T[2025][T[2025].Umfragebezirk == a]; m = wq(s.q, s.w); lo, hi = CLASS_OF[name]; shown = np.floor(m + .5)
    gap = lambda v: max(lo - v, v - hi, 0)
    gaps.append((gap(m), gap(shown), name))
    print(f'  {name:17s} {m:5.1f} -> {shown:3.0f}  class {lo}-{hi}  gap {gap(m):.1f} | {gap(shown):.0f}')
print(f'largest gap unrounded {max(gaps)[0]:.1f} ({max(gaps)[2]}), rounded {max(g[1] for g in gaps):.0f} ({", ".join(g[2] for g in gaps if g[1] == max(x[1] for x in gaps))})')

print('\n== 2 Equivalised-income view, tenants 2025: n, share, median, Q1, Q3, >30 %, >40 %, lower bound >30 %, self-rated high burden')
t = T[2025]; ok = t.q.notna()  # all tenants; the burden columns use only those with a burden
for g, ks in {'NEK <1000': [1], '1000-2000': [2], '2000-3000': [3], '>=3000': [4, 5, 6]}.items():
    s = t[t.XDhhnek_a.isin(ks)]; m = s.q.notna().values
    print(f'{g:10s} n={m.sum():4d} share={100 * s.w[m].sum() / t.w[ok].sum():4.1f}% med {wq(s.q, s.w):5.1f} Q1 {wq(s.q, s.w, .25):5.1f} '
          f'Q3 {wq(s.q, s.w, .75):5.1f} >30 {wshare(s.q > 30, s.w, m):4.1f}% >40 {wshare(s.q > 40, s.w, m):4.1f}% '
          f'lo>30 {wshare(s.q_lo > 30, s.w, m):4.1f}% high {wshare(s.WObelko <= 2, s.w, s.WObelko.notna()):4.1f}%')

print('\n== 3 Groups by household net income per year: median (n, share above 40 %)')
for y in (2025, 2024):
    r = R[y]
    lo = r.XDhhnek_a.map({k: v[0] for k, v in NEK.items()}) * r.scale
    hi = r.XDhhnek_a.map({k: v[1] or np.inf for k, v in NEK.items()}) * r.scale
    sure = (hi <= 2000) | ((lo >= 2000) & (hi <= 3200)) | (lo >= 3200)
    print(f'-- {y}: tenant households with burden {len(r)}; group certain from the classes {100 * np.average(sure, weights=r.w):.0f} %; '
          f'shares {dict((c, round(100 * r.w[r.grp == c].sum() / r.w.sum(), 1)) for c in GROUPS)}')
    for name, s in [('Frankfurt', r)] + [(n, r[r.Umfragebezirk == a]) for a, n in AREAS.items()]:
        cells = ' | '.join(f'{wq(s[s.grp == c].q, s[s.grp == c].w):3.0f} % ({(s.grp == c).sum():3d}, >40: {wshare(s[s.grp == c].q > 40, s[s.grp == c].w, s[s.grp == c].q.notna()):3.0f} %)' for c in GROUPS)
        print(f'{name:17s} {wq(s.q, s.w):3.0f} %   {cells}')

P = pd.concat([R[2025], R[2024]])
print('\n== 4 Pooled 2025 + 2024: median -> rounded to 5 points, n (unweighted)')
print('Frankfurt', {c: (round(wq(P[P.grp == c].q, P[P.grp == c].w), 1), int((P.grp == c).sum())) for c in GROUPS})
for a, name in AREAS.items():
    s = P[P.Umfragebezirk == a]
    print(f'{name:17s}', ' | '.join(f'{wq(s[s.grp == c].q, s[s.grp == c].w):5.1f}->{r5(wq(s[s.grp == c].q, s[s.grp == c].w)):3.0f} n={(s.grp == c).sum():3d}' for c in GROUPS))

print('\n== 5 Bootstrap (400 draws, seed 1), 90 % interval of the weighted median')
print('-- 2025 alone: median [interval] (2024 median) | share above 40 % [interval] (2024)')
rng = np.random.default_rng(1)
res = []
for a, name in AREAS.items():
    for c in GROUPS + ['all']:
        pick = lambda r: r[(r.Umfragebezirk == a) & ((r.grp == c) if c != 'all' else True)]
        s, s4 = pick(R[2025]), pick(R[2024])
        q, w = s.q.values, s.w.values
        idx = [rng.integers(0, len(q), len(q)) for _ in range(400)]
        bm = [wq(q[i], w[i]) for i in idx]
        bs = [100 * np.average(q[i] > 40, weights=w[i]) for i in idx]
        res.append(dict(area=name, grp=c, n=len(s), med=wq(s.q, s.w), lo=np.percentile(bm, 5), hi=np.percentile(bm, 95), med24=wq(s4.q, s4.w),
                        s40=100 * np.average(s.q > 40, weights=s.w), s40lo=np.percentile(bs, 5), s40hi=np.percentile(bs, 95),
                        s40_24=100 * np.average(s4.q > 40, weights=s4.w)))
t5 = pd.DataFrame(res)
for c in GROUPS + ['all']:
    x = t5[t5.grp == c]
    print(f'\n== {c}')
    for _, r in x.iterrows():
        print(f'{r.area:17s} n={r.n:3d}  {r.med:4.0f} [{r.lo:3.0f}-{r.hi:3.0f}] ({r.med24:3.0f}) | {r.s40:3.0f} [{r.s40lo:3.0f}-{r.s40hi:3.0f}] ({r.s40_24:3.0f})')
    print(f'range of areas: median {x.med.min():.0f}-{x.med.max():.0f}, mean half-width {((x.hi - x.lo) / 2).mean():.1f}; '
          f'>40 {x.s40.min():.0f}-{x.s40.max():.0f}, half-width {((x.s40hi - x.s40lo) / 2).mean():.1f}; '
          f'corr 2025/2024 median {x.med.corr(x.med24):.2f}, >40 {x.s40.corr(x.s40_24):.2f}')
print('\n-- pooled 2025 + 2024: median [interval], half width')
rng = np.random.default_rng(1)
hw = {c: [] for c in GROUPS}
for a, name in AREAS.items():
    cells = []
    for c in GROUPS:
        s = P[(P.Umfragebezirk == a) & (P.grp == c)]
        q, w = s.q.values, s.w.values
        bm = [wq(q[i], w[i]) for i in (rng.integers(0, len(q), len(q)) for _ in range(400))]
        lo, hi = np.percentile(bm, 5), np.percentile(bm, 95); hw[c].append((hi - lo) / 2)
        cells.append(f'{wq(q, w):4.0f} [{lo:3.0f}-{hi:3.0f}] n={len(q):3d}')
    print(f'{name:17s} ' + ' | '.join(cells))
print('half width of the interval per group (smallest, mean, largest): ' + '; '.join(f'{c}: {min(v):.1f}, {np.mean(v):.1f}, {max(v):.1f}' for c, v in hw.items()))

print('\n== 6 Sensitivity of the open classes (rent >= 1,400 / income >= 5,000), pooled city median')
sens = {}
for tk, tn in [(1550, 5500), (1700, 6000), (1900, 7000)]:
    p = pd.concat([tenants(load(f25, tk, tn)), tenants(load(f24, tk, tn))])
    sens[f'{tk}/{tn}'] = {g: round(wq(p[p.grp == g].q, p[p.grp == g].w), 1) for g in GROUPS} | {'all': round(wq(p.q, p.w), 1)}
print(pd.DataFrame(sens))

print('\n== 6b Sensitivity of the lowest equivalised class (under 1,000 EUR, central 750): group under 2,000 EUR, pooled')
print('value | city median (unrounded, rounded to 5) | 13 area values rounded (min-max) | all tenants')
for ln in (600, 650, 700, 750, 800, 850):
    p = pd.concat([tenants(load(f25, low_nek=ln)), tenants(load(f24, low_nek=ln))]); lowg = p[p.grp == GROUPS[0]]
    areas = [r5(wq(lowg[lowg.Umfragebezirk == a].q, lowg[lowg.Umfragebezirk == a].w)) for a in AREAS]
    t25 = load(f25, low_nek=ln); t25 = t25[t25.WOmieig_a == 1]  # check against the report: median of all tenants 2025
    print(f'{ln} | {wq(lowg.q, lowg.w):.1f}, {r5(wq(lowg.q, lowg.w)):.0f} | {min(areas):.0f}-{max(areas):.0f} | all tenants 2025 {wq(t25.q, t25.w):.1f}')

print('\n== 7 Worked example: singles (1 person) with equivalised income 1,000-2,000 EUR, pooled, weighted medians')
s = pd.concat([T[2025], T[2024]]); s = s[s.q.notna() & (s.n == 1) & (s.XDhhnek_a == 2)]
low = P[P.hhinc < 2000]
print(f'n {len(s)}, share of the group under 2,000 EUR {100 * s.w.sum() / low.w.sum():.1f} %')
print(f'median kalt class {wq(s.WOkami_a, s.w):.0f}, median cost class {wq(s.WObtrko_a, s.w):.0f}')
print(f'kalt (class midpoint) {wq(s.kalt_mid, s.w):.0f}, costs (class midpoint) {wq(s.bk_mid, s.w):.0f}, warm {wq(s.kalt_mid, s.w) + wq(s.bk_mid, s.w):.0f}, '
      f'income {wq(s.hhinc, s.w):.0f}, ratio {100 * (wq(s.kalt_mid, s.w) + wq(s.bk_mid, s.w)) / wq(s.hhinc, s.w):.1f} %; median of the ratios {wq(s.q, s.w):.1f} %; median of the warm rents {wq(s.warm, s.w):.0f}')
