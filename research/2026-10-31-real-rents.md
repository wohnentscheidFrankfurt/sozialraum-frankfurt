# Rents in Frankfurt adjusted for inflation, 2009–2025

31 Oct 2026. Question: can we give an average rent for all of Frankfurt between 2011 and 2025, or a part of it,
adjusted for inflation?

Answer: yes, at six points in time from December 2009 to July 2025. The source is the sample mean of the Frankfurter
Mietspiegel. The deflator is the consumer price index of Hessen. In prices of July 2025 the mean rose from 10.59 to
12.28 €/m² (+16 %). Most of the rise fell in 2009–2017. The mean is not the rent of all flats. It covers only rents
agreed or changed in the last four or six years.

## Sources

- Frankfurter Mietspiegel 2008–2026 with their reports, in `sources/frankfurt/offices/` (file names in
  `sources/README.md`).
- `sources/hessen/statistics/mi2_j25.pdf`: HSL, Verbraucherpreisindex in Hessen 2022 bis 2025 (M I 2 j/25), table 3
  (PDF page 20): overall index, 2020 = 100, per month.
- For a check: `sources/frankfurt/statistics/statistikportal/Wie hoch ist Ihre gegenwärtige monatliche Kaltmiete bzw.
  Belastung für Wohneigentum – ohne Heizungs- und sonstige Betriebskosten?.xlsx` (survey „Leben in Frankfurt“
  2021–2025) and table 1 of `mi2_j25.pdf` (index of the Nettokaltmiete in Hessen).

## Which editions count

Only editions with a survey or a sample of their own give a rent. [belegt]

| Edition | Basis | Reference date | Mean €/m² net | Where |
|---|---|---|---:|---|
| 2010 | survey | December 2009 | 7.78 | brochure 2010 p. 5 (date); report 2014 p. 21, footnote 4 (mean) |
| 2012 | VPI carried forward (Dec 2009 → Dec 2011) | – | – | brochure 2012 p. 4 |
| 2014 | survey | April 2013 | 8.66 | report 2014 p. 5 (date), p. 21 (mean) |
| 2016 | VPI carried forward (Apr 2013 → Apr 2015) | – | – | brochure 2016 p. 4 |
| 2018 | survey | June 2017 | 9.36 | report 2018 p. 23 |
| 2020 | VPI carried forward (Jun 2017 → Jun 2019) | – | – | brochure 2020 p. 4 |
| 2022 | survey | 01.07.2021 | 10.29 | brochure 2022 p. 6 (date); report 2022 p. 89 (mean) |
| 2024 | sample carried forward | 01.07.2023 | 11.50 | brochure 2024 p. 6 (date); report 2024 p. 29 (mean) |
| 2026 | survey | 01.07.2025 | 12.28 | brochure 2026 p. 5 (date); documentation 2026 p. 102 (mean) |

Page numbers are PDF pages. The mean is the weighted arithmetic mean of the net rent per m² in the sample.

## Inflation-adjusted series

Real value = nominal mean × VPI July 2025 ÷ VPI of the month of the reference date. VPI Hessen, 2020 = 100: December
2009 89.3, April 2013 93.7, June 2017 97.2, July 2021 103.1, July 2023 116.6, July 2025 121.5. For „01.07.“ I use
July. [belegt for the index values, eigene Auswertung for the result]

| Reference date | Nominal | VPI | Real, prices of July 2025 | Real change to the previous point |
|---|---:|---:|---:|---:|
| December 2009 | 7.78 | 89.3 | 10.59 | |
| April 2013 | 8.66 | 93.7 | 11.23 | +6.1 % |
| June 2017 | 9.36 | 97.2 | 11.70 | +4.2 % |
| July 2021 | 10.29 | 103.1 | 12.13 | +3.6 % |
| July 2023 | 11.50 | 116.6 | 11.98 | −1.2 % |
| July 2025 | 12.28 | 121.5 | 12.28 | +2.5 % |

[eigene Auswertung]

- December 2009 to July 2025: nominal +57.8 %, prices +36.1 %, real +16.0 %.
- December 2009 to June 2017: real +10.5 %. June 2017 to July 2025: real +5.0 %.
- In 2021–2023 the rents did not keep up with the high inflation. In real terms they fell a little.

## New contracts and older contracts

The reports split the sample into new contracts (start in the observation period) and older contracts with a rent
increase. [belegt: report 2022 p. 89, figure 21 and text; documentation 2026 p. 102]

| Reference date | Older contracts | Real | New contracts | Real |
|---|---:|---:|---:|---:|
| April 2013 | 8.06 | 10.45 | 9.48 | 12.29 |
| June 2017 | 8.69 | 10.86 | 10.21 | 12.76 |
| July 2021 | 9.14 | 10.77 | 11.56 | 13.62 |
| July 2025 | 10.11 | 10.11 | 13.95 | 13.95 |

Real in prices of July 2025. [eigene Auswertung]

- April 2013 to July 2025: older contracts real −3.3 %, new contracts real +13.5 %.
- The gap between new and older contracts grew from 1.42 to 3.84 €/m² (nominal).
- The split for July 2023 is not in the reports I read. [offen]

## Traps

1. **The Mietspiegel mean is not the average rent of all flats.** It covers only free-financed flats whose rent was
   agreed or changed in the observation period (§ 558 BGB). Social housing and rents unchanged for longer are
   missing. The report of 2022 says the sample is no representative picture of all flats: small flats change
   tenants more often, so they weigh more (report 2022 p. 33). [belegt] Small flats and new contracts cost more per
   m², so the mean should lie above the average of all rents. [unsicher, see the Zensus check below]
2. **Break in 2021.** Since 2020 the observation period is six years, before it was four (brochure 2020 p. 4). The
   survey of 2021 is the first with six years. A longer period takes in more older rents. This pulls the mean
   down. The step from 2017 to 2021 is therefore rather too small. The size of the effect is not known. [unsicher]
3. **The editions 2012, 2016 and 2020 must not be used.** They are the previous table times the price index. In
   real terms they would only repeat the previous value. [belegt]
4. **No price index for Frankfurt.** I use the index of Hessen. [belegt]
5. **New contracts are not the same group over time.** Until 2017 they span four years, from 2021 six years.
   [belegt]

## Checks against other sources

- **Survey „Leben in Frankfurt“:** median cold rent per month of tenants 700 € (2021), 700 € (2022), 750 € (2023),
  799 € (2024), 800 € (2025). Real, with the annual VPI (2021 102.8, 2025 121.1): 681 € and 661 € in prices of 2020,
  −3.0 %. This is the rent per month, not per m², and covers all tenants. The answers cluster on round sums. The
  direction fits the older contracts of the Mietspiegel (2021–2025 real −6.1 %). [eigene Auswertung]
- **Index of the Nettokaltmiete, Hessen (VPI, table 1 of `mi2_j25.pdf`):** 102.7 (2022) to 109.7 (2025), against the
  overall index 109.8 to 121.1. Real −3.2 %. It covers existing rents in Hessen. [eigene Auswertung]
- **Mikrozensus:** Frankfurt 9.80 €/m² net in 2018 (HSL, press release of October 2019, quoted by frankfurt-live), 11.60
  €/m² gross cold in 2022 (HSL, press release 2.5.2023). Net and gross differ, and the survey changed in 2020. Not a
  series. The files are not in `sources/`. [belegt, not used]
- **Zensus 2022:** 10.58 €/m² net, all rented flats (Zensus database 4000W-0004,
  `sources/zensus/Zensus2022_4000W-0004_Frankfurt.csv`). The Zensus 2011 has no rents. [belegt, one point only]

The Mietspiegel mean of July 2021 (10.29 €/m²) lies below the Zensus value of May 2022 (10.58 €/m²). Trap 1 would put
the Mietspiegel above the Zensus. The two differ in flats (the Zensus includes social housing), date and method
(sample with interviews against a full count with owner answers). The cause is not known. [offen]
