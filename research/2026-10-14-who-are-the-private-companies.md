# Who are the private companies? Audit of the 19 % and named owners

As of 14 Oct 2026. Three independent audits of the statement "Unternehmen: 8 % der Häuser, 19 % der Wohnungen" (view
„Trend“), then three research runs on the owners behind the two Zensus classes. Downloads of the runs lay in the
scratch folder of the session; the documents named below are public (PARLIS, company press releases).

Labels: [belegt] = printed in the source; [eigene Auswertung] = counted by us; [unsicher]; [offen].

## 1. The statement holds

| Zensus 2022, Frankfurt | Housing companies | Other companies | Together | All | Share |
|---|---|---|---|---|---|
| Dwellings (4000W-1011) | 57,076 | 19,264 | 76,340 | 402,826 | 18.95 % |
| Buildings (3000G-2007) | 5,173 | 1,623 | 6,796 | 80,679 | 8.42 % |

- Single values [belegt]; sums and shares [eigene Auswertung].
- A fresh download from the Zensus database on 14 Oct 2026 equals the files in `sources/zensus/` cell by cell.
- Dwellings per building 2022: companies 11.2, municipality 8.2, all owners 5.0. In 2011 the Organisationen ohne
  Erwerbszweck were ahead (8.6 against 8.4). The heading holds for 2022 only. [eigene Auswertung]
- Rented dwellings only (4000W-2002): companies 72,848 of 312,915, or 23.3 %. [eigene Auswertung]

Weak points a critic can use:

- "Unternehmen" is not "Konzerne". The class holds every private-law company, also family GmbHs.
- The heading says "Unternehmen" without "privat". ABG is a company too.
- The class is self-reported and partly imputed. The growth 2011–2022 is a comparison of two counts, not proof of
  sales.
- The owner of the building counts. Company dwellings in WEG buildings count as WEG; 19 % is rather a lower bound.

## 2. Two comparisons explained

- Rosa-Luxemburg-Stiftung, municipal 68,299: that is the class "Kommune" of rented dwellings (table 4000W-2002:
  68,305; the difference comes from the anonymisation). The view „Trend“ shows 75,209 for "Öffentlich": all dwellings
  of Kommune (69,558) plus Bund oder Land (5,651). [eigene Auswertung]
- Vonovia is a housing company. It belongs to the class "Privatwirtschaftliches Wohnungsunternehmen" (55,004 rented),
  not to "Anderes privatwirtschaftliches Unternehmen" (17,844 rented). [eigene Einschätzung, definition GEBEG1]

## 3. Named owners, city of Frankfurt

| Owner | Likely Zensus class | Dwellings | As of | Source |
|---|---|---|---|---|
| Vonovia without Deutsche Wohnen | housing company | about 11,500 [belegt] | 15 Mar 2022 | Vonovia press releases of 15 Mar, 26 Jul, 20 Sep and 22 Nov 2022 (e.g. vonovia.com/content/download/53221/3669001) |
| Deutsche Wohnen | housing company | about 5,000 [belegt] | 14 Jul 2021 | F 75/2021, p. 1 |
| Vonovia with Deutsche Wohnen | housing company | about 16,000 [belegt] | 24 Feb 2026 | Vonovia press release (vonovia.com/content/download/316454/16092725) |
| GWH (100 % Helaba) | housing company [unsicher] | 12,528 [belegt] | 2 Jul 2025 | F 3283/2025, p. 1 |
| BImA | Bund oder Land | 1,156 [belegt] | 1 Aug 2018 | BT-Drs. 19/7092, annex 1, p. 15 |

- Vonovia reported about 11,500 in 2022 and about 16,100 from 27 Jan 2023 on. The jump fits the stock of Deutsche
  Wohnen (about 5,000). Deutsche Wohnen remains a separate stock corporation, 86.87 % owned by Vonovia (F 1347/2023).
  [eigene Einschätzung]
- Party documents (motions of factions) are not used as sources here. Company reports and Magistrat answers only.
- Vonovia plus Deutsche Wohnen plus GWH: about 29,000 of 57,076, or 51 % of the class. About 28,000 are not named.
  The years differ. [eigene Auswertung]
- Heimstaden, LEG, TAG, Adler, Covivio, Vivion: no Frankfurt stock found. Grand City: only a region "Mannheim/KL/
  Frankfurt/Mainz". [offen]
- GWH: the Länder held 12.15 % of Helaba, the rest Sparkassen associations. Not Bund oder Land, not directly
  Kommune. The owner chose the class. [unsicher]

## 4. The class "Anderes privatwirtschaftliches Unternehmen"

- 1,623 buildings; 466 buildings with 13 and more dwellings carry 64 % of its dwellings. Vacancy 7.4 % (city 3.2 %).
  [eigene Auswertung, 3000G-2007, 4000W-2013, 4000W-2002]
- Funds found with Frankfurt stock before May 2022: Industria (about 250), Hamburg Trust Domicilium 6 (about 160) and
  11 (272 micro flats), KGAL (98). Together about 780, or 4 % of the class. [belegt per item; sum eigene Auswertung]
- Instone is a developer. It holds no rental stock. Its sales to funds (Kleyerquartier "franky" to a BVK fund,
  Schönhof to the Bayerische Ärzteversorgung) were finished 2024–2026, after the Zensus. [belegt]
- The rest is open: unreported small purchases, office buildings with single flats, student housing, family holding
  companies, companies that report as "other" instead of "housing company". [offen]
- The fall of Bund oder Land (−14,810 dwellings) is mostly the Nassauische Heimstätte, which moved to "Kommune"
  (`research/2026-10-07-nh-aus-gitter-2011/bericht.md`). No large sale found. [eigene Einschätzung]

## 5. What the data can put on the map

- The grid 2022 holds buildings of both classes apart (`bld_housing_company`, `bld_other_company`);
  `ownership_cells` already estimates dwellings of both apart. [belegt]
- Secrecy in the grid 2022: housing companies lose 3.2 % of the buildings, other companies 13.9 %. [eigene Auswertung]
- Backtest on 2011 per Stadtteil, 9 of 10 within: housing companies ±53 % or 3.3 points; other companies ±87 % or
  1.6 points, and about 35 % too low. Rank correlation 0.96 and 0.83. [eigene Auswertung]
- Stadtteile with at least 10 %: housing companies 29 of 45, other companies 5. [eigene Auswertung]
- Exact counts per Stadtteil exist only at the city: § 32 (2) ZensG 2022 lets the municipal statistics office use the
  single records of the count. [belegt; whether Frankfurt holds them: offen]
- Named owners per Siedlung: only a patchwork from PARLIS addresses and company websites. The Grundbuch needs a
  legitimate interest (§ 12 GBO). "Wem gehört die Stadt?" forbids machine use. [belegt]
