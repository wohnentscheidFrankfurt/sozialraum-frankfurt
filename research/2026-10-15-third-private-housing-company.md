# A third example for „Privatwirtschaftliche Wohnungsunternehmen“

As of 15 Oct 2026. One research run for a third named example next to Vonovia and GWH in the view „Trend“ (Zensus
2022: 57,076 dwellings in the class). Builds on `research/2026-10-14-who-are-the-private-companies.md` and
`docs/decisions/2026-10-14-trend-owner-examples.md`. The cited sources are stored in `sources/` (see
`sources/README.md`, sections `frankfurt/parlis` and `companies`; provenance and retrieval date 15 Oct 2026).

Labels: [belegt] = printed in the source; [eigene Auswertung] = counted by us; [unsicher]; [offen].

## 1. The key source: owners of the subsidised stock, F 677/2017

- Answer of the Magistrat to F 677 (question of 22 Jun 2017, as of 31 Dec 2016). It lists every owner with at least
  50 subsidised dwellings (1. Förderweg) in Frankfurt. [belegt]
- Passage: „Die Eigentümer - Gesellschaften, Vereine, Genossenschaften et cetera -, die über „nennenswerte“ öffentlich
  geförderte Wohnungsbestände verfügen, mindestens 50 Wohneinheiten, sind folgender Tabelle zu entnehmen“. [belegt]
- Private housing companies in the table, besides GWH (2.443) and Vonovia SE (289): „Gemeinn. Siedlungswerk GmbH
  1.160“, „Sahle Wohnen 915“, „Rhein-Main Wohnen GmbH 141“, „ZaaLim AG 149“, „Mavest Wohnungsbau GmbH 106“. [belegt]
- Funds in the table (class „Andere“): „PATRIZIA GewerbeInvest Kapitalanlagegesellschaft mbH 356“, „DG
  Immobilien-Anlagegesellschaft 55“. [belegt]
- The counts are subsidised dwellings only. The total stock in Frankfurt is higher. They are lower bounds as of 2016.
  [eigene Einschätzung]
- File: `sources/frankfurt/parlis/F_677_2017.pdf`, p. 1–2. URL: https://www.stvv.frankfurt.de/download/F_677_2017.pdf

## 2. Candidates, ranked

| # | Name | Owner | Frankfurt dwellings | Zensus class | Variety next to Vonovia and GWH |
|---|---|---|---|---|---|
| 1 | Sahle Wohnen | family Sahle (Greven) | 915 subsidised [belegt], 31 Dec 2016 | housing company, sure | family business, social housing |
| 2 | Gemeinnütziges Siedlungswerk GmbH | four Catholic dioceses and their Caritas associations | 1,160 subsidised [belegt], 31 Dec 2016; region 3,536 [belegt], 31 Dec 2025 | housing company, likely [unsicher] | church owner, seat in Frankfurt, low rents |
| 3 | Deutsche Wohnen | 86.87 % Vonovia | about 5,000 [belegt], 2021 | housing company, sure | none: part of the 16,000 of Vonovia |
| 4 | Mavest Wohnungsbau GmbH | today [offen]; the city sold its shares (titles M 46/1993, NR 765/1996) | 106 subsidised [belegt], 2016 | housing company [unsicher] | former city stake; too small and unclear |

### 2.1 Sahle Wohnen

- **Owner:** family business. „Die familiengeführte Gruppe besitzt, vermietet und betreut etwa 23.000 Wohnungen.“
  The managing directors include Uwe Sahle and Friederich Sahle. [belegt; sahle-wohnen.de/geschaeftsfuehrung,
  undated, retrieved 15 Oct 2026; `sources/companies/Sahle_Wohnen_Geschaeftsfuehrung.html`]
- **History:** „Mit dem Bau von Wohnungen für seine Mitarbeiter im Grevener Hansaviertel legt der Schuhfabrikant Paul
  Sahle im Jahr 1963 den Grundstein für das Unternehmen Sahle Wohnen.“ [belegt;
  `sources/companies/Sahle_Wohnen_Firmengeschichte.html`]
- **Frankfurt:** „Darüber hinaus ist das Unternehmen in Hamburg und Frankfurt am Main aktiv und wächst stetig.“
  [belegt; `sources/companies/Sahle_Wohnen_Geschaeftsfuehrung.html`, not the page
  „Firmengeschichte“]
- **Frankfurt count:** „Sahle Wohnen 915“ (subsidised, 31 Dec 2016). [belegt; F 677/2017, p. 2]
- **Frankfurt quarters:** customer centre Valentin-Senger-Straße 136b (Bornheim), office hours at Maastrichter Ring
  36 (Europaviertel) and Hans-Leistikow-Straße 6 (Riedberg). Quote of the Frankfurt team lead: „Die Mehrzahl unserer
  Wohnungen ist gefördert“ and „In unseren drei großen Wohnquartieren ist zudem Parea aktiv.“ [belegt;
  `sources/companies/Sahle_Wohnen_Wohnen_in_Frankfurt.html`]
- **Magistrat confirms the owner:** Helenenhöfe, Europaviertel: „den Bau von 111 Mietwohnungen gefördert“ and „Er
  wird dennoch mit der Sahle Wohnen GmbH in Kontakt treten“. [belegt; F 1527/2018,
  `sources/frankfurt/parlis/F_1527_2018.pdf`]
- **Total in Frankfurt:** above 915; most are subsidised, so probably not above about 2,000. [eigene Einschätzung,
  unsicher]
- **Zensus class:** a GmbH & Co. KG whose business is building and letting dwellings. „Privatwirtschaftliches
  Wohnungsunternehmen“ fits the definition GEBEG1 without doubt. [eigene Einschätzung, sure]
- **Risks:**
  - The Frankfurt count dates from 2016. No newer count found. [offen]
  - The 23,000 are mostly in North Rhine-Westphalia. A tooltip without numbers avoids that trap.
  - Several legal entities: „Sahle Wohnen GmbH & Co. KG“, „Sahle Baubetreuungsgesellschaft mbH“ (management). The
    brand „Sahle Wohnen“ covers both. [belegt]
  - A dispute with Mainova over power cables in the Europaviertel (ST 1041/2020, „die von Sahle Wohnen widerrechtlich
    verlegten Kabel“). Small, about the power supply, not about rents. [belegt;
    `sources/frankfurt/parlis/ST_1041_2020.pdf`]

### 2.2 Gemeinnütziges Siedlungswerk GmbH (GSW)

- **Owner:** „Unsere Gesellschafter sind Bistum Limburg Bischöflicher Stuhl zu Mainz Bischöflicher Stuhl zu Fulda
  Bistum Erfurt Caritasverband für die Diözese Limburg e.V. Caritasverband für die Diözese Mainz e.V.
  Caritasverband für die Diözese Fulda e.V. Caritasverband für das Bistum Erfurt e.V.“ [belegt;
  gsw-ffm.de/de/gsw/gesellschafter, `sources/companies/GSW_Gesellschafter.html`; also GB 2025, p. 55]
- **Seat:** Blumenstraße 14–16, Frankfurt. Founded 1949 by the bishops of Limburg, Mainz and Fulda. [belegt; GB 2024,
  p. 6, https://www.gsw-ffm.de/pdf/GSW_GB_2024.pdf]
- **Stock:** „7.654 eigene Wohnungen, 112 eigene gewerblich genutzte Einheiten, 700 Treuhandwohnungen und 410
  fremdverwaltete Wohnungen“, 31 Dec 2025. [belegt; GB 2025, p. 22, https://www.gsw-ffm.de/pdf/GSW%20GB2025.pdf]
- **Region:** chart „GSW Wohnungsbestand – Regionale Verteilung“: Großraum Frankfurt 3.536, Wiesbaden/Mainz 1.630,
  Erfurt 819, Nordhessen 1.498, Rhein-Neckar 171. [belegt; GB 2025, p. 11,
  https://www.gsw-ffm.de/pdf/GSW%20GB2025.pdf] The five
  bars add up to 7,654, the own stock. [eigene Auswertung] 2024: Großraum Frankfurt 3.523 [belegt; GB 2024, p. 9].
- **Großraum Frankfurt is not the city.** It includes Offenbach, Oberursel, Bad Homburg, Kelkheim and Königstein (all
  named in the reports). [belegt]
- **City of Frankfurt:** „Gemeinn. Siedlungswerk GmbH 1.160“ subsidised dwellings, 31 Dec 2016. [belegt; F 677/2017,
  p. 1] Named Frankfurt sites 2025: Trifelsstr./Donnersbergstr. (Niederrad), Oederweg/Mittelweg (Nordend),
  Lettigkautweg (86 dwellings), Schliemannweg 25–29, Alzeyer Straße, Wiener Straße. [belegt; GB 2025, p. 11, 13, 14,
  22]
- **Business:** „Bewirtschaftung von bezahlbarem Wohnraum mit ca. 9.000 Wohnungen, die Bautätigkeit für den eigenen
  Bestand, das Bauträgergeschäft und Bauen für Dritte“. Average rent 8.10 €/m². [belegt;
  `sources/companies/GSW_Das_Unternehmen.html`]
- **Zensus class:** a GmbH with a housing purpose. It keeps profits (Gewinnrücklagen 101.6 Mio. €, GB 2025, p. 23). Its
  housing non-profit status ended in 1990 („Nach Wegfall der Wohnungsgemeinnützigkeit“, GB 2025, p. 55). By the
  definition it is a „Privatwirtschaftliches Wohnungsunternehmen“. The company filled in the form itself. It may have
  chosen „Organisation ohne Erwerbszweck (z. B. Kirchen)“. [unsicher]
- **Variety:** a church owner, seated in Frankfurt, with low rents. It shows that the class follows the legal form,
  not the profit motive.
- **Risks:**
  - The class is less sure than for Sahle (see above).
  - Readers may see a contradiction. The tooltip of „Organisationen ohne Erwerbszweck“ names „Kirchen“.
  - „Gemeinnützig“ is part of the name. The tax status is not stated. Readers may read it as a non-profit.
  - Name traps: „GSW“ in Berlin is the former GSW Immobilien AG, now Deutsche Wohnen. „Siedlungswerk GmbH Wohnungs- und
    Städtebau“ (siedlungswerk.de) sits in Stuttgart and has no Frankfurt stock. Use the full name, not „GSW“.

### 2.3 Deutsche Wohnen (not recommended)

- About 5,000 dwellings in Frankfurt (F 75/2021). It is 86.87 % owned by Vonovia (F 1347/2023). [belegt, earlier run]
- It adds no variety. Its stock lies inside the „rund 16.000“ of Vonovia. Naming both counts the same flats twice in
  the reader's mind.

### 2.4 Mavest Wohnungsbau GmbH (not recommended)

- 106 subsidised dwellings, 2016 (F 677/2017). [belegt] Founded 1926 as the housing company of the Frankfurt crafts
  („Mavestblock“, Siedlung Raimundstraße; Ernst-May-Gesellschaft, hint only). The PARLIS titles M 46/1993 („MAVEST
  Wohnungsbaugesellschaft mbH; hier: Verkauf von Geschäftsanteilen“) and NR 765/1996 („Veräußerung von Beteiligungen
  hier: MAVEST“) show a sale of city shares. The documents are not downloadable (404). [belegt as titles; rest offen]
- Today's owner and stock: [offen]. Too small and too unclear for the map.

## 3. Checked and left out

- **VBL (Versorgungsanstalt des Bundes und der Länder):** sells its Frankfurt stock (ST 1419/2025,
  `sources/frankfurt/parlis/ST_1419_2025.pdf`). Public law,
  owners Bund and Länder. Class „Bund oder Land“, not this class. [eigene Einschätzung]
- **Akelius:** sold its German stock (Berlin, Hamburg) to Heimstaden in 2021. No Frankfurt stock found. PARLIS has no
  hit. [offen]
- **Grand City Properties, Dawonia:** no PARLIS hit, no Frankfurt count. [offen]
- **Rhein-Main Wohnen GmbH (141), ZaaLim AG (149), "Riedpark" Verwaltungs-GmbH (242):** in F 677/2017. Owners not
  found. [offen]
- **Patrizia, DG Immobilien-Anlagegesellschaft:** fund companies. They belong to „Andere privatwirtschaftliche
  Unternehmen“. They could back that tooltip, which already names Industria Wohnen and Hamburg Trust.
- **KEG (Konversions-Grundstücksentwicklungsgesellschaft):** a city company. Class „Kommune“.
- **WohnBau Rhein-Main AG:** the city sold its shares in 1999 (PARLIS title M 266/1999). Deutsche Wohnen grew from the
  housing stocks of the former Hoechst AG (Deutsche Wohnen annual report 2003, hint only). Whether WohnBau Rhein-Main
  went there: [offen]. Either way it would sit inside Vonovia today.

## 4. Recommendation

- **Sahle Wohnen.** A family business next to a listed giant (Vonovia) and a bank subsidiary (GWH). The class is sure.
  The Magistrat names it as owner in Frankfurt (F 677/2017, F 1527/2018). Its own website names Frankfurt. No
  confusion with another group.
- Tooltip (2022 and arrows): „Z. B. Vonovia, die GWH und Sahle Wohnen.“
- Longer variant, if the kind of owner should show: „Z. B. Vonovia, die GWH und das Familienunternehmen Sahle Wohnen.“
- **Alternative:** „Z. B. Vonovia, die GWH und das Gemeinnützige Siedlungswerk der katholischen Bistümer.“ Shows the
  widest variety. But the Zensus class is less sure, and it can collide with „Kirchen“ in the tooltip of
  „Organisationen ohne Erwerbszweck“.
- **For `EXAMPLES`** (`pipeline/use_cases/ownership_shares/catalog.py`): sources to store in `sources/companies/` and
  `sources/frankfurt/parlis/`:
  - `F_677_2017.pdf`, phrase „Sahle Wohnen 915“ (or „Gemeinn. Siedlungswerk GmbH 1.160“).
  - Sahle page „Geschäftsführung“, phrases „Die familiengeführte Gruppe besitzt, vermietet und betreut etwa 23.000
    Wohnungen“ and „in Hamburg und Frankfurt am Main aktiv“.
  - For the alternative: GSW page „Gesellschafter“ („Bistum Limburg“) and GB 2025 („Frankfurt am Main, Trifelsstr. /
    Donnersbergstr.“).
- The footer of sources then adds „Antwort des Magistrats F 677/2017, Website Sahle Wohnen“. The span „2014–2026“
  stays.
