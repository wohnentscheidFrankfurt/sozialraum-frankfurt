# Warm rent and income: three wages and the tenants under 2,000 €

1 Nov 2026. Two questions of the user:

- S1: how much of a net wage does the warm rent take, 2017 to 2025, for a new and an older contract?
- S2: how much of their income do tenants with less than 2,000 € net household income spend on the warm rent, and how
  many are they?

Labels: [belegt] = printed in the source; [eigene Auswertung] = counted by us; [unsicher]; [offen].

## Answer

- S1: for one person living alone in 55 m², the warm rent of a new contract took 31.3 % of the median net wage in 2017
  and 31.4 % in 2025. At the pension ceiling it took 20.7 % and 21.1 %. At the full-time Mindestlohn it took 65.6 % and
  61.9 %. The share of a wage stayed about the same, because net wages grew about as fast as warm rents (+34.4 %
  against +34.7 %). The level differs by a factor of about three. For older contracts the share fell for all three.
  The longer observation window of the Mietspiegel from 2021 lowers every trend a little (Limits). [eigene Auswertung]
- S2: tenants with less than 2,000 € spend a median of 53 % of their income on the warm rent (2024+2025 pooled, 90 %
  interval 52 to 55), at the midpoint of each income class. With the income placed lower or higher in its class the
  median lies between 48.5 and 55.4 %: about half the income holds, more than half holds only at the midpoint. They
  are 16.7 % of the adult tenants by the class midpoints, surely 14.2 % and at most 28.1 %; per household about 22 %.
  [eigene Auswertung]

## Sources

- Rents: Mietspiegel means of new and older contracts, as the build reads them (`interim/new_construction_rents.csv`;
  provenance in `pipeline/use_cases/new_construction/README.md`). [belegt]
- Betriebskosten and Heizkosten: Arbeitsagentur, „Wohn- und Kostensituation“ SGB II, Frankfurt, table 1b (renting
  households), actual running costs per m², June 2017, 2021, 2023, 2025 (`sources/arbeitsagentur/kdu-06412-0-*`).
  Sensitivity: Betriebskostenspiegel of the Mietspiegel (Gutachten 2018 table 9, Gutachten 2022 table 15, Gutachten
  2024 table 6, Dokumentation 2026 table 10). [belegt]
- Wages: Arbeitsagentur, Entgeltstatistik, median gross monthly wage of full-time employees (Kerngruppe), Frankfurt,
  Wohnort and Arbeitsort, 31.12. (`sources/arbeitsagentur/entgelt-*`). Hessen distribution 2025:
  `sources/hessen/statistics/ni9_j25_2aa.pdf`, table 2.2.4. [belegt]
- Net wage: own calculation of the Programmablaufplan of the BMF (`research/scripts/net_wage.py`). [eigene Auswertung]
- Prices: VPI Hessen of the survey month, as the build reads it. [belegt]
- Survey: Leben in Frankfurt 2024 and 2025, microdata (`sources/frankfurt/statistics/leben-in-frankfurt_*.csv`), the
  formula of the use case `survey`. [belegt, eigene Auswertung]
- Mikrozensus for Frankfurt: Wohnungsmarktbericht 2019/2020, figures 40 and 41
  (`sources/frankfurt/offices/Wohnungsmarktbericht 2019_2020.pdf`, PDF pages 62 and 63). [belegt]
- Cross-check only: IWU for the Deutscher Mieterbund, June 2026 (`sources/other/Kurzstudie-WohnkostenbelastungIWU_DMB.pdf`,
  table 2). [belegt]
- Scripts: `research/scripts/warm_rent_wage.py`, `research/scripts/net_wage.py`, `research/scripts/low_income_burden.py`;
  results `research/results/warm_rent_wage.txt`, `research/results/low_income_burden.txt`.

## S1: inputs

| Survey year | Net cold rent new / older €/m² | Betriebskosten + Heizkosten (BA) €/m² | Median gross wage, Wohnort, 31.12. |
|---|---|---|---|
| 2017 | 10.21 / 8.69 | 2.33 + 0.86 | 3,861 € |
| 2021 | 11.56 / 9.14 | 2.45 + 0.86 | 4,273 € |
| 2023 | 13.05 / 9.43 | 2.63 + 1.41 | 4,594 € |
| 2025 | 13.95 / 10.11 | 2.72 + 1.39 | 5,074 € |

[belegt]

- The three persons live alone and work full time: Mindestlohn × 40 hours × 52 ÷ 12 (8.84, 9.60, 12.00, 12.82 € per
  hour on the survey day); the median above; a wage at the Beitragsbemessungsgrenze of the pension insurance (6,350,
  7,100, 7,300, 8,050 €). Steuerklasse I, no children, no church tax, statutory insurance with the average
  Zusatzbeitrag (1.1, 1.3, 1.6, 2.5 %).
- The wage of a survey year is the median on 31.12. of that year. Trap: the Arbeitsagentur publishes no Wohnort median
  for 31.12.2018 to 2020 in this series, so a mean around mid-year exists only for 2017, 2023 and 2025 (sensitivity
  below). [belegt]
- The flat: 55 m², the midpoint of the median class 50–60 m² of one-person tenant households in the survey 2024+2025
  (computed in the scratch check of 1.11.2026, not by a committed script). Of those that moved in less than 5 years ago,
  49.1 % live below 50 m², so their median lies at about 50 m²; the 50 m² sensitivity is the closer one for new
  contracts. [eigene Auswertung]
- The ceiling in the distribution: 37.6 % of the full-time residents of Frankfurt earn more than 6,000 € gross
  (31.12.2025), the top class is open. In Hessen (April 2025) the ceiling of 8,050 € lies between the 88th percentile
  (7,859 €) and the 89th (8,074 €); the 9th decile is 8,318 €. No such table exists for Frankfurt or before 2022.
  [belegt]

## S1: net wage and its check

- The calculation follows the PAP: annual wage minus Arbeitnehmer-Pauschbetrag, 36 €, Vorsorgepauschale; tariff of
  § 32a EStG; Soli with Freigrenze and Milderungszone. Contributions: pension, unemployment, health (general rate plus
  Zusatzbeitrag, whole until 2018), care (with the childless surcharge), each up to its ceiling.
- Check, read on 1.11.2026 by browser automation from the calculators of the BMF:
  - Lohnsteuerrechner 2021, 2023 (ab Juli) and 2025: Lohnsteuer and Soli of all nine cases equal to the cent.
  - 2017 has no Lohnsteuerrechner. The Einkommensteuerrechner 2017 gives the tariff and the Soli of the three taxable
    incomes equal to the cent. The Vorsorgepauschale of 2017 (68 % of the pension contribution) has no check of its
    own; it uses the code checked for 2021. [unsicher, small]
  - The contributions are not part of either calculator. Their rates and ceilings are the legal values named in the
    script. [belegt, not checked by a calculator]
- Net median wage: 2,354 € (2017), 3,163 € (2025), +34.4 %; gross +31.4 %. The net grew faster because the Soli fell
  away from 2021 for these wages and the tax brackets moved. [eigene Auswertung]

## S1: shares

Share of the net wage, warm rent of 55 m² (main case: BA costs, wage on 31.12.):

| Person | Contract | 2017 | 2021 | 2023 | 2025 | Change |
|---|---|---|---|---|---|---|
| Mindestlohn | new | 65.6 % | 66.3 % | 62.5 % | 61.9 % | −3.7 |
| Mindestlohn | older | 58.1 % | 55.5 % | 49.3 % | 48.7 % | −9.4 |
| median | new | 31.3 % | 30.6 % | 32.6 % | 31.4 % | +0.1 |
| median | older | 27.8 % | 25.6 % | 25.7 % | 24.7 % | −3.0 |
| ceiling | new | 20.7 % | 20.0 % | 21.9 % | 21.1 % | +0.4 |
| ceiling | older | 18.3 % | 16.8 % | 17.3 % | 16.6 % | −1.7 |

[eigene Auswertung]

- What is left after the warm rent of a new contract, in euros of 2017 (VPI Hessen): Mindestlohn 387 → 490, median
  1,617 → 1,736, ceiling 2,826 → 2,968. [eigene Auswertung]
- Sensitivities (change 2017 to 2025 of the median, new contract, in points): Mietspiegel Nebenkosten −0.1 (level
  about 2 points lower: 29.4 → 29.3 %); median at Arbeitsort +0.1 (level about 2 points lower); mean around mid-year
  +0.4; flat 50 m² +0.1 (28.5 %), 60 m² +0.1 (34.2 %). The change stays within ±0.5 points in every case; the Mindestlohn
  falls by 3.4 to 4.0 points; older contracts fall for all three. [eigene Auswertung]
- The Mietspiegel Nebenkosten of 2023 and 2025 are an estimate: the printed sum of 2021 (2.61 €/m²) times the own sum
  of ten items of the year (2.19 and 2.40 €/m²) divided by that of 2021 (2.15 €/m²), giving 2.66 and 2.91 €/m². The
  reports of 2024 and 2026 print no sum. [eigene Auswertung, unsicher]

## S1: why the share stays flat while the block of rents in Neubau shows rents outgrowing wages

Growth 2017 to 2025: net cold rent of new contracts +36.6 %, Betriebskosten + Heizkosten (BA) +28.7 %, warm rent of a
new contract of 55 m² +34.7 %; Nominallohnindex Hessen (gross, the wage line in Neubau) +30.1 %, median gross wage of
Frankfurt residents +31.4 %, median net wage +34.4 %; prices +25.0 %. The two views compare different things: Neubau
the net cold rent against the gross wage index of Hessen, S1 the warm rent against the net wage of Frankfurt. Both hold.
[eigene Auswertung]

## S1: measured values

- Published median burden of all tenants 29 % (reports 2024 and 2025); own count 29.4 %. [belegt, eigene Auswertung]
- One-person tenant households in the flat for less than 5 years (1,007 cases, 2024+2025): median burden 33.9 %,
  median warm rent 875 €. Above the model median (31.4 %), below the Mindestlohn. [eigene Auswertung]
- IWU, Mikrozensus 2022 projected to 2024: Frankfurt 34 % of the household income, moved in 2020 or later 37 %
  (cross-check only). [belegt]

## S2: tenants under 2,000 €

Burden = warm rent ÷ household net income, adult tenants (the survey weights count adults), 2024+2025 pooled, 90 %
bootstrap intervals (400 draws):

| Income group | Share of tenants | Median | under 30 % | 30–40 % | 40–50 % | 50 % and more |
|---|---|---|---|---|---|---|
| under 2,000 € | 16.7 (16–18) | 53.3 (52–55) | 3.6 | 16.4 | 22.4 | 57.6 (55–61) |
| 2,000 to 3,200 € | 23.6 (23–25) | 36.1 (35–37) | 27.7 | 38.3 | 18.8 | 15.2 |
| 3,200 € and more | 59.7 (59–61) | 23.9 (24–24) | 73.0 | 20.7 | 4.5 | 1.8 |

[eigene Auswertung]

- 2025 alone: under 2,000 € median 55.0, share 17.3 %; 2024: 51.7 and 16.1 %. Median warm rent of the group 725 €,
  median household income 1,500 €. [eigene Auswertung]
- Group membership: 14.2 % of the adult tenants are surely under 2,000 € by the class bounds, 13.9 % are in doubt. So
  the group holds 14.2 to 28.1 %. [eigene Auswertung]
- Open lowest class (equivalised income under 1,000 €) at 600, 750, 800 €: median 55.0, 53.3, 51.7; 50 % and more 61.8,
  57.6, 56.4. [eigene Auswertung]
- Position of the income inside its closed class (0.5 = midpoint, the main case; the groups are formed again): at 0.4,
  0.5, 0.6, 0.7 the median is 55.4, 53.3, 51.6, 48.5 and the share with 50 % and more 64.1, 57.6, 52.7, 47.8. 56 % of the
  group are singles of the equivalised class 1,000 to 2,000 €, all set to 1,500 €. Where in the class their incomes lie
  is unknown; the class lies below the median income of all tenants, so a position above the midpoint is plausible.
  [eigene Auswertung, unsicher]
- Per household instead of per adult (weight ÷ adults, an approximation): the group holds 22.2 % of the tenant
  households. [eigene Auswertung, unsicher]
- By employment: berufstätig 566 cases (45.1 % of the group), median 51.7; nicht berufstätig 609 cases (53.0 %),
  median 55.0. Working does not take the group out of the burden. [eigene Auswertung]
- Mikrozensus for Frankfurt (Bruttokaltmiete without heating, mean): 2018 under 900 € 60.1 %, 900 to 1,500 € 42.1 %,
  1,500 to 2,000 € 33.7 %, all 29.1 %; 2006, 2010, 2014 in finer classes (all 23.6, 23.3, 28.6 %). Another
  definition: never on one line with the survey. The classes are nominal; 2,000 € of 2006 are not 2,000 € of 2025.
  [belegt]
- Bürgergeld: 27,547 renting households in the SGB II with recognised housing costs (BA, June 2025), against 312,915
  rented dwellings (Zensus 15.5.2022): 8.8 % of the households. The group under 2,000 € holds about 22 % of the tenant
  households. Part of it does not pay the rent itself; the microdata cannot mark them. [unsicher]

## Statements

| Statement | Verdict |
|---|---|
| For one person in 55 m² with a new contract, the share of the median net wage stayed about the same since 2017 (31 %) | holds under every calculated sensitivity (change −0.1 to +0.4 points); the change of the observation window of the Mietspiegel (below, Limits) pulls the later rents down, size unknown, so the true change may be a little higher |
| The same at the pension ceiling (21 %) | holds (+0.3 to +0.5), with the same caveat |
| At the full-time Mindestlohn the share fell a little, from about two thirds to about three fifths | holds (−3.4 to −4.0); levels 56–72 % by flat size; same caveat |
| The share at the Mindestlohn is about three times the share at the ceiling | holds: the ratio is the net wage at the ceiling ÷ the net Mindestlohn, 3.17 (2017), 3.31 (2021), 2.85 (2023), 2.93 (2025); rent and flat size do not change it |
| For older contracts the share fell for all three | holds in the calculation; the window caveat works in the same direction, so the fall may be smaller |
| Tenants under 2,000 € spend a median of more than half their income on the warm rent | holds only at the class midpoint (53.3 %); 48.5 to 55.4 % with the income placed elsewhere in its class |
| Tenants under 2,000 € spend about half their income on the warm rent | holds (48.5 to 55.4 % in every sensitivity) |
| For most of them the warm rent is half the income or more | holds only at the class midpoint or below (57.6 %, 47.8 to 64.1 %) |
| About one adult tenant in six has under 2,000 € | holds for the midpoints (16.7 %); safe only as „almost one in seven“ (14.2 %); per household about one in five (22 %) |
| „Ein großer Teil der Bevölkerung“ has under 2,000 € | not carried by the numbers: 14 to 28 % of adult tenants |
| What is left after the warm rent grew without inflation | holds in the main case for all three (new contract) |

## Limits

- S1 is a model person. Households average 1.85 persons, many have two incomes. The model says nothing about real
  households; the measured values do.
- Full-time employees only. Part time, Minijobs, civil servants and the self-employed are not in the median.
- The Nebenkosten of the BA are those of households in the Grundsicherung; the Mietspiegel gives lower levels. Heating
  rose by 62 % in the BA series from 2017 to 2025 and stayed flat as an item of the Mietspiegel (advance payments
  against the last annual statement).
- Selection: who moves in earns more; who cannot pay does not move or leaves the city. The measured burden hides this.
- The survey weights count adults, not households.
- The Mietspiegel counts contracts of the last 4 years in 2017 and of the last 6 years from 2021
  (`docs/data-rules.md`, Index of several series). The longer window lowers the means of 2021 to 2025. The size is
  unknown. Every trend of S1 is therefore a little too low. The levels from 2021 are those of a six-year window.
- Income classes: the survey gives household income only in classes. The burden of S2 rests on the class midpoint; its
  sensitivity is printed above.
