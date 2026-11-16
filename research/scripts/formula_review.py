# Formula review: the numbers behind the formulas of the ownership use cases. The sections D1 to D7 follow the old
# protocol of the review (tag docs-history-2026-10-20 of the local archive of the old history).
# Reads the interim data of a build and the Zensus tables named in pipeline/config.py.
# Call: .venv/bin/python -I research/scripts/formula_review.py interim > research/results/formula_review.txt
import sys
from pathlib import Path

import pandas as pd

from pipeline import config as cf
from pipeline.use_cases.public_housing.model import estimate_by_size, size_tables
from pipeline.shared.zensus.tables import read_buildings_by_size, read_dwellings_by_size, read_dwellings_history
from pipeline.shared.zensus.model import CLASSES, SIZES

interim = Path(sys.argv[1])
read = lambda name: pd.read_csv(interim / name)
c22 = read("cells_2022.csv")
c22 = c22[c22.edge == 0]
m = (c22.merge(read("cells_2011_dwellings.csv"), on="cell_id", how="left")
     .merge(read("cells_2011_buildings.csv"), on="cell_id", how="left")
     .merge(read("ownership_cells.csv"), on="cell_id", how="left").fillna(0).set_index("cell_id"))
ph = read("public_housing_quarters.csv").set_index("quarter")
city = read("city_values.csv").set_index("indicator")["value"]
history = read_dwellings_history(cf.ZENSUS_4000W_1011.read_text(encoding="utf-8"))
known22 = m[[f"bld_{k}" for k in CLASSES]].sum(axis=1) > 0
known11 = m[[f"bld_{k}_2011" for k in CLASSES]].sum(axis=1) > 0
no_owner = (m.dw_total_2011 - m[[f"dw_{k}_2011" for k in CLASSES]].sum(axis=1)).clip(lower=0)
GROUPS = {"Genossenschaften": ["coop"], "Private Unternehmen": ["housing_company", "other_company"],
          "Privatpersonen + WEG": ["condo", "person"]}

print("# D1: table 2011 and 2022, gap of the 2011 grid, map 2022 against the table")
for name, ks in GROUPS.items():
    g11 = sum(m[f"dw_{k}_2011"].sum() for k in ks)
    t11, t22 = (sum(history[y][k] for k in ks) for y in (2011, 2022))
    mp = sum(m[f"dw_{k}"].sum() for k in ks)
    print(f"{name:22} table 2011 {t11:7,.0f}  table 2022 {t22:7,.0f} ({t22 / t11 - 1:+.1%})  "
          f"missing in grid 2011 {(t11 - g11) / t11:.1%}  map 2022 {mp / t22 - 1:+.1%}")
old_coop = m.dw_coop_2011 > 0
lost_coop = old_coop & known22 & (m.bld_coop == 0)
print(f"coop dwellings 2011 in cells without coop building 2022: {m.dw_coop_2011[lost_coop].sum():,.0f} "
      f"({m.dw_coop_2011[lost_coop].sum() / m.dw_coop_2011.sum():.0%}), median per cell "
      f"{m.dw_coop_2011[lost_coop].median():.0f}")

print("\n# D2: Genossenschaften = (a) count 2011 + (b) secrecy gap 2011 + (c) estimate 2022 in new cells")
share = (m.dw_coop / m.dwellings.where(m.dwellings > 0)).fillna(0)
a = m.dw_coop_2011.where(old_coop, 0)
b = (no_owner * share).where(old_coop & known22, 0)
c = m.dw_coop.where(~old_coop, 0)
t22 = history[2022]["coop"]
print(f"a {a.sum():,.0f}  b {b.sum():,.0f}  c {c.sum():,.0f}  a+b {(a + b).sum():,.0f} ({(a + b).sum() / t22 - 1:+.1%})  "
      f"a+b+c {(a + b + c).sum():,.0f} ({(a + b + c).sum() / t22 - 1:+.1%})  map {m.dw_coop.sum():,.0f}  table 2022 {t22:,}")
gap11 = history[2011]["coop"] - m.dw_coop_2011.sum()
print(f"secrecy gap 2011 {gap11:,.0f}; located by (b) on all cells known in 2022: "
      f"{(no_owner * share).where(known22, 0).sum() / gap11:.0%}")
other11 = (~old_coop) & (c > 0) & (m.dw_total_2011 > 0) & (m.bld_coop_2011 == 0)
growth = (m.dwellings - m.dw_total_2011) >= 0.8 * c
hidden = no_owner >= 0.5 * c
kind5 = other11 & ~growth & ~hidden
print(f"(c) in cells with 2011 dwellings but no coop: {c[kind5].sum():,.0f} in {int(kind5.sum())} cells; coop buildings "
      f"2022 there {int(m.bld_coop[kind5].sum())}; persons + WEG 2011 there "
      f"{(m.dw_person_2011 + m.dw_condo_2011)[kind5].sum():,.0f} of "
      f"{m.loc[kind5, [f'dw_{k}_2011' for k in CLASSES]].sum().sum():,.0f} with an owner")
print(f"(c) where the growth of the cell covers it: {c[(~old_coop) & (c > 0) & growth].sum():,.0f}")

cells = m.copy()
B = read_buildings_by_size(cf.ZENSUS_3000G_2007.read_text(encoding="utf-8"))
D = read_dwellings_by_size(cf.ZENSUS_4000W_2013.read_text(encoding="utf-8"))
est = {}
for year, suf, tot in ((2011, "_2011", cells.dw_total_2011), (2022, "", cells.dwellings)):
    seed, mean = size_tables(B[year], D[year])
    est[year] = estimate_by_size(cells[[f"bld_{k}{suf}" for k in CLASSES]].set_axis(list(CLASSES), axis=1),
                                 cells[[f"bld_size_{x}{suf}" for x in SIZES]].set_axis(SIZES, axis=1), tot, seed, mean)
fc = old_coop & known22 & known11
f22 = est[2022].coop.where(fc, 0).groupby(m.quarter).sum()
f11 = est[2011].coop.where(fc, 0).groupby(m.quarter).sum()
factor = (f22 / f11.where(f11 > 0)).fillna(1)
print("change factor coop (rejected):", ", ".join(f"{q} {factor[q]:.2f}" for q in ("Nieder-Eschbach", "Bornheim",
      "Niederrad")), f"; city {f22.sum() / f11.sum():.2f}")

print("\n# D3: ABG and NH, method D (map) against S = a + b + c + research")
nh = m.dw_state_2011.where((m.bld_municipal > 0) | ~known22, 0)
pub11 = m.dw_municipal_2011 + nh
old = pub11 > 0
share_m = (m.dw_municipal / m.dwellings.where(m.dwellings > 0)).fillna(0)
s = (pub11.where(old, 0) + (no_owner * share_m).where(old & known22, 0) + m.dw_municipal.where(~old, 0))
q = pd.DataFrame({"S": s.groupby(m.quarter).sum() + ph.research_new, "D": ph.public_value, "half": ph.public_half})
big = q[q.D >= 200]
dev = big.S / big.D - 1
print(f"Frankfurt S {q.S.sum():,.0f}  D {q.D.sum():,.0f}  table 4000W-2002 {history[2022]['municipal']:,}; "
      f"within ±15 % of each other {int((dev.abs() <= .15).sum())} of {len(big)}, median {dev.abs().median():.1%}")
for name in ("Ginnheim", "Innenstadt", "Rödelheim", "Bonames"):
    sel = (m.quarter == name) & old
    print(f"{name:11} D {q.D[name]:6,.0f} ± {q.half[name]:4,.0f}  S {q.S[name]:6,.0f}  factor {ph.factor[name]:.2f}  "
          f"dwellings of the cells 2011 {m.dw_total_2011[sel].sum():,.0f} -> 2022 {m.dwellings[sel].sum():,.0f}")
lost = old & known22 & (m.bld_municipal == 0)
print(f"public dwellings 2011 in cells without municipal building 2022: {pub11[lost].sum() / pub11[old].sum():.0%} "
      f"(coops {m.dw_coop_2011[lost_coop].sum() / m.dw_coop_2011.sum():.0%})")

print("\n# D4: denominator of the ownership shares")
G = {"company": ["housing_company", "other_company"], "person": ["condo", "person"], "state": ["state"],
     "nonprofit": ["nonprofit"]}
d4 = pd.DataFrame({k: sum(m[f"dw_{x}"] for x in v).groupby(m.quarter).sum() for k, v in G.items()})
d4["known"] = d4.sum(axis=1) + m.dw_municipal.groupby(m.quarter).sum() + m.dw_coop.groupby(m.quarter).sum()
d4["sum_a"] = d4[list(G)].sum(axis=1) + ph.public_value + (a + b + c).groupby(m.quarter).sum()
drift = d4.sum_a / d4.known - 1
rest = d4.known - ph.public_value - (a + b + c).groupby(m.quarter).sum() - d4[["company", "state", "nonprofit"]].sum(axis=1)
print(f"known {d4.known.sum():,.0f}, sum of groups {d4.sum_a.sum():,.0f} ({d4.sum_a.sum() / d4.known.sum() - 1:+.1%}); "
      f"drift per Stadtteil {drift.min():+.1%} to {drift.max():+.1%}; Bonames {ph.public_value['Bonames']:,.0f} ÷ "
      f"{d4.known['Bonames']:,.0f} = {ph.public_value['Bonames'] / d4.known['Bonames']:.1%}")
print(f"option C (persons + WEG = rest): negative {int((rest < 0).sum())}, largest change "
      f"{(rest / d4.person - 1).abs().max():.0%}")

# backtest on 2011: estimate from the buildings of 2011 against the counted dwellings, error in 9 of 10 areas with at
# least 200 dwellings of the group; E0 = buildings × dwellings per building of the type in Frankfurt, E1 = with sizes
bo = m[[f"bld_{k}_2011" for k in CLASSES]].set_axis(list(CLASSES), axis=1)
dw = m[[f"dw_{k}_2011" for k in CLASSES]].set_axis(list(CLASSES), axis=1)
test = (bo.sum(axis=1) > 0) & (dw.sum(axis=1) > 0)
seed, mean = size_tables(B[2011], D[2011])
e1 = estimate_by_size(bo, m[[f"bld_size_{x}_2011" for x in SIZES]].set_axis(SIZES, axis=1), dw.sum(axis=1), seed, mean)
f0 = {k: sum(D[2011][k][x] for x in SIZES) / sum(B[2011][k][x] for x in SIZES) for k in CLASSES}
raw = pd.DataFrame({k: bo[k] * f0[k] for k in CLASSES})
e0 = raw.mul((dw.sum(axis=1) / raw.sum(axis=1).where(raw.sum(axis=1) > 0)).fillna(0), axis=0)
for level in ("quarter", "district"):
    for name, ks in (("Private Unternehmen", G["company"]), ("Privatpersonen + WEG", G["person"]),
                     ("Genossenschaften", ["coop"])):
        count = dw.loc[test, ks].sum(axis=1).groupby(m.loc[test, level]).sum()
        err = {n: (e.loc[test, ks].sum(axis=1).groupby(m.loc[test, level]).sum()[count >= 200] / count[count >= 200] - 1)
               .abs().quantile(.9) for n, e in (("E0", e0), ("E1", e1))}
        print(f"backtest {level:8} {name:22} areas {int((count >= 200).sum()):3}  E0 {err['E0']:.0%}  E1 {err['E1']:.0%}")

print("\n# D5: Benachteiligungsindex")
s5 = read("monitoring_by_district.csv").SOC_INDEX
city_index = f"city value {city['SOC_INDEX']}" if "SOC_INDEX" in city else "no city value (D5)"
print(f"{len(s5)} districts, min {s5.min():.0f}, max {s5.max():.0f}, mean {s5.mean():.1f}, {city_index}")

print("\n# D6: Wohnfläche je Kopf: see research/scripts/space_check.py (the layer went on 12 Oct 2026)")

print("\n# D7: template Lücke bei öffentlichen Wohnungsbaugesellschaften")
qi = read("indicators_quarters.csv")
hit = (qi.SOC_MIN_INCOME >= city["SOC_MIN_INCOME"]) & (qi.OWN_PUBLIC < city["OWN_PUBLIC"])
upper = hit & (qi.OWN_PUBLIC_HIGH < city["OWN_PUBLIC"])
print(f"city {city['OWN_PUBLIC']:.1f} %; hits {int(hit.sum())}, upper end below city {int(upper.sum())}; dropped: "
      + ", ".join(qi.loc[hit & ~upper, "name"]))
print(f"Genossenschafts-Lücke: upper end of coop < city met by {int((qi.OWN_COOP_HIGH < city['OWN_COOP']).sum())} of "
      f"{len(qi)} Stadtteile, {int((qi.OWN_COOP == 0).sum())} without coop")

print("\n# Round 2: backtest of the new design on 2011 (public and coop counted, the others share the rest by E0)")
R = {"company": ["housing_company", "other_company"], "person": ["condo", "person"], "state": ["state"],
     "nonprofit": ["nonprofit"]}
HALF_PP = {"company": 3.5, "person": 5.4, "state": 1.4, "nonprofit": None}  # nonprofit: measured below
REL = {}
for level in ("quarter", "district"):
    area = m.loc[test, level]
    tot = dw.loc[test].sum(axis=1).groupby(area).sum()
    fixed = dw.loc[test, ["municipal", "coop"]].sum(axis=1).groupby(area).sum()
    est_r = {k: e0.loc[test, v].sum(axis=1).groupby(area).sum() for k, v in R.items()}
    s_r = sum(est_r.values())
    for name in HALF_PP:
        cnt = dw.loc[test, R[name]].sum(axis=1).groupby(area).sum()
        est = est_r[name] / s_r.where(s_r > 0) * (tot - fixed)
        ok = cnt >= 200
        rel = (est[ok] / cnt[ok] - 1).abs()
        pp = (100 * (est - cnt) / tot).abs()
        REL[level, name] = rel.quantile(.9)
        print(f"{level:8} {name:8} areas {int(ok.sum()):3}  9 of 10: ±{rel.quantile(.9):.0%} / {pp.quantile(.9):.1f} pp  "
              f"largest {pp.max():.1f} pp ({pp.idxmax()})")
        if level == "quarter":
            share_c, share_e = 100 * cnt / tot, 100 * est / tot
            err = (share_e - share_c).abs()
            rule_rel = REL[level, name] * share_e
            half = HALF_PP[name] if HALF_PP[name] is not None else round(pp.quantile(.9), 1)
            print(f"         range rules, Stadtteile covered of {len(err)}: relative {int((err <= rule_rel).sum())}, "
                  f"fixed {half} pp {int((err <= half).sum())}, larger of both "
                  f"{int((err <= rule_rel.clip(lower=half)).sum())}")
hausen = test & (m.quarter == "Hausen")
print(f"Hausen nonprofit: counted {dw.loc[hausen, 'nonprofit'].sum():,.0f} dwellings in {bo.loc[hausen, 'nonprofit'].sum():.0f} "
      f"buildings, E0 {e0.loc[hausen, 'nonprofit'].sum():,.0f}")
bins = [0, 5, 15, 30, 101]
area = m.loc[test, "quarter"]
tot = dw.loc[test].sum(axis=1).groupby(area).sum()
share_c = 100 * dw.loc[test, R["company"]].sum(axis=1).groupby(area).sum() / tot
share_e = 100 * e0.loc[test, R["company"]].sum(axis=1).groupby(area).sum() / tot
print(f"classes (under 5, 5-15, 15-30, 30 and more), Private Unternehmen per Stadtteil: right class "
      f"{(pd.cut(share_e, bins, right=False) == pd.cut(share_c, bins, right=False)).mean():.0%}")

print("\n# Round 2: range of the coop formula: estimated part (b + c) ± 34 %")
known = m[[f"dw_{k}" for k in CLASSES]].sum(axis=1)
cq = pd.DataFrame({"a": a, "b": b, "c": c, "known": known}).groupby(m.quarter).sum()
cq["value"] = cq.a + cq.b + cq.c
cq["half"] = 0.34 * (cq.b + cq.c)
bigc = cq[cq.value >= 200]
print(f"Stadtteile with at least 200: {len(bigc)}; half at most 15 %: {int((bigc.half <= .15 * bigc.value).sum())}; median "
      f"±{(bigc.half / bigc.value).median():.0%}; Bornheim {100 * cq.value['Bornheim'] / cq.known['Bornheim']:.1f} % "
      f"({100 * (cq.value - cq.half)['Bornheim'] / cq.known['Bornheim']:.1f}–"
      f"{100 * (cq.value + cq.half)['Bornheim'] / cq.known['Bornheim']:.1f} %)")

print("\n# Round 2: overlay per 100-m cell, backtest 2011 (cells with at least 10 dwellings, all with an owner)")
GG = {"public": ["municipal", "state"], "coop": ["coop"], "company": ["housing_company", "other_company"],
      "person": ["person", "condo"], "nonprofit": ["nonprofit"]}
full = test & (dw.sum(axis=1) >= 10) & ((m.dw_total_2011 - dw.sum(axis=1)) <= 0)
group = lambda x: pd.DataFrame({g: x[ks].sum(axis=1) for g, ks in GG.items()})[full]
cnt, est, bld = group(dw), group(e0), group(bo)
main = cnt.idxmax(axis=1)
print(f"cells {int(full.sum())}; main group right: by estimated dwellings {(est.idxmax(axis=1) == main).mean():.0%}, "
      f"by buildings {(bld.idxmax(axis=1) == main).mean():.0%}")
for g in ("public", "company"):
    sel = main == g
    print(f"  main group {g:8} ({int(sel.sum())} cells): estimate {(est.idxmax(axis=1)[sel] == g).mean():.0%}, "
          f"buildings {(bld.idxmax(axis=1)[sel] == g).mean():.0%}")
wrong = (est - cnt).abs().sum(axis=1) / 2 / cnt.sum(axis=1)
print(f"dwellings per cell assigned to a wrong group, 9 of 10 cells: up to {wrong.quantile(.9):.0%}")
