---
title: "New construction (Neubau) per year: which data exist, and can it be split into community and private?"
---

As of 15 Oct 2026. Data check before a new tab "Neubau". No design yet.

# 1. Result in short

- **Totals per year exist.** Pure new construction (dwellings in new residential buildings) is published for
  2000–2025 by the city. Older years exist only as net additions including conversions, with gaps. [belegt]
- **No source splits Frankfurt's new construction per year into community and private.** [belegt]
  - The official builder statistic (Bauherr) exists per city only for Germany and the Länder. Frankfurt published
    builder shares for 2003–2012 only.
  - Its categories cannot express "community". ABG, Nassauische Heimstätte and cooperatives all count as
    "Wohnungsunternehmen", next to commercial landlords and developers. "Öffentliche Bauherren" means only the
    administration itself (0.5–5 % of new dwellings).
  - Cooperatives were never a category of their own, also not before 1990. The non-profit category
    (gemeinnützige Wohnungsunternehmen) existed until 1989, but only in federal and Land tables.
- **The Zensus gives the current owner by decade of construction, not the builder.** It counts buildings, not
  dwellings. Owners change: the Nassauische Heimstätte moved from "Bund oder Land" (2011) to "Kommune" (2022);
  former non-profit stock now sits with private companies. [belegt]
- **Recommendation:** show new construction per year without ownership. The split would rest on an own estimate,
  not on a published number.
- **Decision (15.10.2026, `docs/decisions/2026-10-15-new-construction-data.md`):** whole city, 2011–2025, dwellings in
  new residential buildings of the HSL, with the subsidised dwellings (FW 1 and FW 2) as a part.

Fetched but not stored in `sources/` (links only): Statistisches Jahrbuch Frankfurt 2012 (Wayback copy of
frankfurt.de, `.../pdf/jahrbuch/statistisches-jahrbuch-2012.ashx`), Frankfurter Statistische Berichte 1/2003
(`frankfurt.de/sixcms/media.php/678/2003_1_Kurzinfo_Wohnungsbau2002.pdf`), statistik.aktuell 25/2011, 31/2013
(`frankfurt.de/sixcms/media.php/678/31_Baufertigstellungen2012.pdf`), 12/2018 and 16/2021, Baustein 2/12
(https://digital.zlb.de/viewer/api/v1/records/16322245/files/media/DOWNLOAD-BAUSTEIN_02_12.pdf), the annex of
B 483/2025 (https://www.stvv.frankfurt.de/download/B_483_2025_AN1.pdf), Fachserie 5 Reihe 1 1988–1991
(statistischebibliothek.de) and the Statistische Jahrbücher für die Bundesrepublik (scans of UB Mannheim,
https://digi.bib.uni-mannheim.de/fileadmin/statjahrb/).

# 2. Totals per year

| Years | What | Source | Status |
|---|---|---|---|
| 2020–2025 | Dwellings in new residential buildings, per Stadtteil; also new buildings by type | Statistikportal exports (Gebäudedatei), `sources/frankfurt/statistics/Fertiggestellte neue Wohngebäude und Wohnungen.xlsx` and `Fertiggestellte neue Gebäude und Wohnungen.xlsx` | in the repo |
| 2000, 2005, 2010, 2015–2020 | Same, city only (table 3.8) | Statistisches Jahrbuch 2021, `sources/frankfurt/statistics/` | in the repo |
| 2000–2011 | Same, city only (table 7.9) | Statistisches Jahrbuch 2012 (Wayback copy of frankfurt.de) | fetched, not in the repo |
| 2012–2014 | Same | Statistische Jahrbücher 2013–2016 (Wayback) | not fetched |
| 1990–2002 | New-build, conversion, demolition, net | Frankfurter Statistische Berichte 1/2003 (Wayback) | fetched, not in the repo |
| 1953–1978, with gaps | Net additions incl. conversions, per city | Statistisches Jahrbuch für die Bundesrepublik, table of large cities (UB Mannheim scans) | fetched in part |
| 1951–1990 | Unknown, maybe with builder | Statistische Jahrbücher Frankfurt (print only, UB Frankfurt or ISG) | not seen |

Check: 2020 in the Statistikportal export (320 buildings, 3,488 dwellings) equals table 3.8 of the Jahrbuch 2021.

Breaks:

- Since 2019 dwellings in Wohnheime (student and similar residences) count as completions.
- Net completions from 2021 differ between two city publications. Gebäudedatei (`BT_Reinzugang.csv`, row
  "insgesamt"): 2,865 (2021), 3,313 (2022), 3,942 (2024). Magistrat (B 483/2025): 3,914, 2,951, 4,203. Both give
  4,349 for 2020. `BT_Reinzugang.csv` has a city row "insgesamt"; summing all rows doubles each year.
- "Neu- und Umbau" totals include conversions. Only "Wohnungen in neuen Wohngebäuden" is pure new construction.
- Before 2003 the numbers come from the Hessisches Statistisches Landesamt, since 2003 from the city's own statistics.

## 2.1 The break of 2019 and the official series of the Land

The city series counts Wohnheime only since 2019. The official building statistic of the Hessisches Statistisches
Landesamt (HSL) counts them as residential buildings since 1983 ("Wohnheime werden erst ab 1983 den Wohngebäuden
zugeordnet", report F II 2, editions 2010 and 2024). Its Hessen series of permits notes "Ab 2002 inklusive
Wohnheime".

- Regionaldatenbank, table 31121-01-02-4 "Fertigstellungen neuer Wohngebäude und Wohnungen in Wohngebäuden",
  Gebäudeart "Wohngebäude (inkl. Wohnheime)", Frankfurt (06412), 1995–2024, fetched on 15.10.2026 through the open API
  of the web client (`https://www.regionalstatistik.de/gngServer/api/rest/tables/31121-01-02-4/data/...`).
- 2025: report "Baufertigstellungen in Hessen 2025" (F II 2 j/25), table 17, Frankfurt: 238 new residential buildings,
  3,463 dwellings. 2024 gives also 3,463 dwellings (Regionaldatenbank and report 2024), with other floor area and
  costs. Both values read from the scans.
- B 483/2025 gives 4,203 completed dwellings for 2024. This equals "Wohnungen insgesamt" of all building measures for
  Frankfurt in the HSL report 2024. B 12/2024 names Amt 12 (Bürgeramt, Statistik und Wahlen) as the source of its
  "Nettozugang" 2010–2022, yet its 2021 and 2022 values (3,914, 2,951) differ from `BT_Reinzugang.csv` (2,865,
  3,313). The conflict is not resolved. It does not touch the series of new residential buildings.

Dwellings in new residential buildings, city (Gebäudedatei) against HSL, sums:

| Years | HSL | City | City against HSL |
|---|---|---|---|
| 2000–2011 | 24,438 | 23,184 | −5.1 % |
| 2015–2018 | 14,839 | 12,932 | −12.9 % |
| 2019–2024 | 19,127 | 18,403 | −3.8 % |

The gap is largest in 2015–2018 (many student residences) and shrinks once the city counts Wohnheime. This fits the
break. Single years differ much more, e.g. 2015: HSL 4,076, city 3,051; 2022: HSL 2,498, city 3,025. The HSL gives
the city only, no Stadtteile.

# 3. Builder statistic (Bauherr)

- GENESIS has builder tables for Germany (31121-0002, from 2001) and the Länder (31121-0101 from 2008, 31121-0110
  from 2015). The Regionaldatenbank has none for districts or municipalities (all 15 tables of 31121 checked).
- The report "Baufertigstellungen in Hessen" (F II 2) has builder tables only for the Land (editions 2010, 2024, 2025
  read).
- Categories (`BAUBH1`): Öffentliche Bauherren; Unternehmen (Wohnungsunternehmen, Immobilienfonds, sonstige);
  Private Haushalte; Organisationen ohne Erwerbszweck. No cooperatives.
- Definitions (Hessen report): the builder is recorded at the time of the permit. Companies owned by a public body are
  not public builders, whatever their legal form.
- Frankfurt published builder shares in statistik.aktuell 25/2011 and 31/2013 (2003–2012). Example: 2012 public
  3.0 %, housing companies 79.0 %, funds 0.3 %, private households 9.5 %, other 8.2 %. Nothing found after 2012.
- Fachserie 5 Reihe 1: "Gemeinnützige Wohnungs- und ländliche Siedlungsunternehmen" until 1989 (Germany 1989:
  15,046 completed dwellings), from 1991 only "Wohnungsunternehmen".

# 4. Zensus: current owner by decade of construction

Table 3000G-2001 (already in `sources/zensus/`), buildings with residential space, 15.5.2022. Share of buildings
owned today by Kommune (ABG, NH), cooperatives or Bund/Land:

| Built | Buildings | Kommune | Cooperative | Bund/Land | Share |
|---|---|---|---|---|---|
| before 1919 | 15,250 | 420 | 310 | 11 | 4.9 % |
| 1919–1949 | 14,656 | 3,019 | 537 | 64 | 24.7 % |
| 1950–1959 | 13,898 | 2,008 | 389 | 243 | 19.0 % |
| 1960–1969 | 10,891 | 1,411 | 278 | 48 | 15.9 % |
| 1970–1979 | 5,660 | 370 | 102 | 20 | 8.7 % |
| 1980–1989 | 4,475 | 387 | 67 | 119 | 12.8 % |
| 1990–1999 | 3,948 | 247 | 34 | 21 | 7.6 % |
| 2000–2009 | 6,279 | 207 | 40 | 30 | 4.4 % |
| 2010–2015 | 3,554 | 177 | 23 | 20 | 6.2 % |
| 2016 and later | 2,071 | 253 | 19 | 0 | 13.1 % |

Limits:

- Buildings, not dwellings. A building of ABG holds many more dwellings than a single-family house, so the share of
  dwellings is higher. No Zensus table crosses dwellings, year of construction and owner at municipal level (the
  tables 4000W-4010/4013 exist only for Germany and the Länder; 4000W-3033 counts only vacant dwellings).
- Decades, not years. Only buildings that still stand.
- Current owner, not builder. Between 2011 and 2022 the class "Bund oder Land" of the 1950s fell from 892 to 243
  buildings, "Kommune" rose from 1,505 to 2,008 (Nassauische Heimstätte reclassified). Former non-profit stock
  (e.g. Neue Heimat, GWH) now counts as private companies.

# 5. Subsidised housing and single builders

- B 12/2024 (answer of the Magistrat, 8.1.2024, fetched): subsidised new dwellings completed or ready for occupancy
  per year 2010–2023, Förderweg 1 and Förderweg 2 (with the predecessor programmes). Sum 3,626 (FW 1 1,984, FW 2
  1,642). ABG built 1,839 of them, only as a sum.

| Year | FW 1 | FW 2 | Total |
|---|---|---|---|
| 2010 | 126 | – | 126 |
| 2011 | 83 | 82 | 165 |
| 2012 | 90 | 109 | 199 |
| 2013 | 56 | 52 | 108 |
| 2014 | 307 | 96 | 403 |
| 2015 | 431 | 67 | 498 |
| 2016 | 226 | 64 | 290 |
| 2017 | 68 | 52 | 120 |
| 2018 | 52 | 318 | 370 |
| 2019 | 111 | 298 | 409 |
| 2020 | 53 | 120 | 173 |
| 2021 | 131 | 210 | 341 |
| 2022 | 160 | 88 | 248 |
| 2023 | 90 | 86 | 177 |

- 2024 is not clear. The annex of B 483/2025 (page 14) gives 102 FW 1 and 126 FW 2 dwellings "zur erstmaligen
  Belegung / Vermietung". B 483/2025 gives 716 FW 1 completions 2019–2024; minus 2019–2023 of B 12/2024 (545) this
  leaves 171.
- Later answers revise single years. 2023 FW 1: 90 (B 12/2024), 170 (F 3150/2025), 182 (F 158/2026). 2024 FW 1:
  131 completed, 102 ready for occupancy in the same year (F 79/2026); FW 2: 100 (F 3150/2025) or 117 (F 79/2026).
  2025: FW 1 343 completed, 269 ready; FW 2 346 completed (F 9/2026). F 158/2026 splits FW 1 2023–2025 into
  "Wohnungsbaugesellschaften/-genossenschaften" (166, 116, 151) and "Private/Institutionelle Akteure" (16, 15, 192).
- F 120/2026: subsidised dwellings completed since 2020 in projects with a 30 % quota, by public, private and
  "GuG" (community and cooperative) projects. Only sums since 2020.
- 2000–2009: Stadtplanungsamt, Baustein 2/12 "Geförderter Wohnungsbau in Frankfurt am Main" (2012), pp. 82–83
  (digital.zlb.de, record 16322245), lists subsidised rental new construction 1999–2013 per project with builder.
  Two large projects carry only a range of years: McNair (2000–2004, 585 dwellings) and Atterberry & Betts
  (2004–2010, 647). 2012 and 2013 were plans when printed. The column adds up to 3,637 by our parse, the printed sum
  is 3,577. Overlap with B 12/2024 does not match (2011: 248 against 165; 2012: 142 against 199).
- Decision of the user (15.10.2026): "davon gefördert" only if the whole series 2000–2025 holds. It does not hold:
  2000–2009 has no clean value per year, and later years were revised several times.
- Span with subsidised dwellings (checked 15.10.2026):
  - 2011–2022 rests on one source, B 12/2024. 2019 and 2020 agree with the Wohnungsmarktbericht 2019/20 (B 430/2022,
    tables 3 and 4). 2010 has no FW 2 value in B 12/2024 (empty cell, although the predecessor programme ran
    since 2009), so 2010 is left out.
  - 2023–2025 exist only in later answers, latest values: 2023 FW 1 182 (F 158/2026), FW 2 108 (F 3150/2025);
    2024 FW 1 131, FW 2 117 (F 79/2026); 2025 FW 1 343, FW 2 346 (F 9/2026). Early counts were always revised
    upwards (2020: 149 in F 147/2021, later 173; 2023 FW 1: 90, 170, 182).
  - Share of subsidised dwellings in dwellings of new residential buildings (HSL): 3.0 % (2017) to 12.2 % (2015),
    19.9 % in 2025. Student residences are in the HSL total but not in FW 1 or FW 2.
- These are subsidised dwellings, not an owner type. They include completions by private builders.
- Trap: B 483 divides FW 1 completions by all completions including conversions. Our series counts only new
  residential buildings; the two must not be mixed.

- B 483/2025: Förderweg 1 completions 2019–2024 total 716 (ABG 422, Nassauische Heimstätte 185, GWH 55,
  cooperatives 9, private 45). Approvals of the last five years 1,001 (ABG 334, NH 363, cooperatives 2, private 302).
  Only as a sum over the years.
- Wohnungsmarktbericht 2019/20 (B 430/2022): subsidised completions per year by programme, not by builder.
- ABG Geschäftsberichte: completions of the group, partly outside Frankfurt. NH reports cover Hessen. Cooperatives
  publish separately. Adding these up would be an own count, not a published number.

# 6. Open routes to a split

- Ask Bürgeramt, Statistik und Wahlen whether the Gebäudedatei holds the owner type and can give completions by owner
  type per year.
- Special evaluation of the Hessisches Statistisches Landesamt: only builder categories, cooperatives not separable.
  Does not answer the question.
- Statistische Jahrbücher Frankfurt 1951–1990 by hand (UB Frankfurt, ISG): may hold non-profit builders for the city.
