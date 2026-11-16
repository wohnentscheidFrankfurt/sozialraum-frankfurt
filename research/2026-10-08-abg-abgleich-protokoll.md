---
title: "ABG-Bestand: Abgleich der Recherche mit der Karte – Ergebnisprotokoll"
---

Stand: 2026-10-08. Grundlagen:

- die eigene Recherche „ABG-Holding-Karte“ (GeoJSON mit 209 Orten des ABG-Konzerns aus 122 öffentlichen Quellen)
- das Zensus-Gitter 2022 und das Zensus-Gitter 2011 (100 m)
- die ABG-Chronik „Wohnen für alle“ (2015) und der ABG-Geschäftsbericht 2024

Kennzeichnung wie in den Protokollen vom 6.10. und 8.10.:

- **[belegt]**: Primärquelle eingesehen.
- **[eigene Auswertung]**: selbst gerechnet.
- **[unsicher]**: Deutung mit Vorbehalt.
- **[offen]**: nicht gefunden.

Die Rechnungen liegen im Repo der Karte unter `docs/recherche/2026-10-08-abg-holding-abgleich/`, zusammen mit der Recherche selbst.

------------------------------------------------------------------------

# 1. Ergebnis in Kürze

- **Die Schätzung der Karte passt.** ABG und Nassauische Heimstätte (NH) zusammen ergeben etwa die Zensus-Klasse „Kommune“. Die Karte schätzt die ABG jetzt auf 53.739 Wohnungen. Der Konzern meldet für Ende 2022 54.122. [belegt: Geschäftsbericht 2024; eigene Auswertung]
- **Gallus als Gegenprobe.** Laut ABG-Chronik gehören der ABG im Gallus „rund 5.700 Wohnungen“. Die Karte schätzt 5.974 für 2022. Dazwischen liegt Neubau. [belegt: Chronik, PDF-Seite 19; eigene Auswertung]
- **Hochhäuser fehlten.** Der Zensus 2022 hält die Gebäudezahl geheim, wenn in einer 100-m-Zelle nur ein oder zwei Häuser stehen. Dann fehlt auch die Eigentumsform. Das betraf 28.778 Wohnungen (7,4 %), darunter das Mainfeld in Niederrad. [eigene Auswertung]
- **Die Karte füllt diese Lücke jetzt aus dem Zensus 2011.** Ohne Eigentumsform bleiben nur noch 11.533 Wohnungen (3,0 %). Das sind vor allem Neubauten nach 2011. [eigene Auswertung]
- **Die Kandidaten bleiben gleich.** Lücke bei ABG und NH: 8 Bezirke. Lücke bei der ABG: 9. Genossenschafts-Lücke: 19. [eigene Auswertung]
- **Die Recherche ist eine Untergrenze.** Sie belegt 18.799 Wohnungen in Frankfurt bis 2022, das sind 35 % des ABG-Bestands. Einen Stadtteil-Bestand der ABG veröffentlicht niemand. [eigene Auswertung; offen]

# 2. Die Recherche

- 194 Orte mit Lage und 15 ohne Lage:
  - 91 Bestand, 46 Neubau fertig, 12 im Bau oder geplant
  - 26 SAALBAU-Häuser, 12 Parkhäuser, 4 Bauten für die Stadt, 3 Sonstiges
- Die Koordinaten sind von Hand gesetzt, nicht geokodiert.
- Im Bau oder geplant sind rund 4.000 Wohnungen, zum Beispiel Hilgenfeld (860), Lurgiallee (1.000) und Rebstock (373). [Recherche]
- Bewusst nicht aufgenommen sind fünf Siedlungen der NH: Heimatsiedlung, Riedhof-Ost, Fritz-Kissel-Siedlung, Adolf-Miersch-Siedlung und Ben-Gurion-Ring.

# 3. Abgleich mit der Karte

- **Stadt.** Der Zensus 2022 zählt 69.558 Wohnungen der Klasse „Kommune“ (Tabelle 4000W). ABG (54.122) und NH (rund 16.000) ergeben zusammen rund 70.100. Die Annahme „Kommune = ABG + NH“ hält. [belegt; eigene Auswertung]
- **Stadtteile.** In keinem Stadtteil liegen die belegten Wohnungen deutlich über der Schätzung:
  - Berkersheim: belegt 234 (Edwards-Siedlung), geschätzt 250. Die Quelle (Mieterzeitung der ABG, 2005) war nicht abrufbar. [unsicher]
  - Preungesheim: belegt 1.653, geschätzt 1.499. Vermutlich ist ein Projekt doppelt gezählt: „Frankfurter Bogen“ (160) und „Preungesheimer Karree“ (160 plus 33), beide 2004. [unsicher]
- **NH.** Die fünf ausgelassenen NH-Siedlungen liegen dort, wo die Karte viel NH sieht, zum Beispiel 77 % im Bezirk der Fritz-Kissel-Siedlung. [eigene Auswertung]
- **Frühere US-Siedlungen.** Die ABG kaufte Mitte der 1990er 1.569 Wohnungen vom Bund, vor allem in Ginnheim. Der Zensus 2011 führt sie schon als „Kommune“. Die Karte zählt sie richtig zur ABG. [belegt: Chronik; eigene Auswertung]

# 4. Die Lücke und ihre Schließung

- Das Gitter 2022 kennt keine Werte 1 und 2. Stehen in einer Zelle nur ein oder zwei große Häuser, fehlen alle Gebäudezahlen.
- **Mainfeld:** vier Zellen mit 608 Wohnungen. 2011 waren 610 davon kommunal. 2022 hatten sie keine Eigentumsform. Jetzt zählen sie zur ABG. [eigene Auswertung]
- **Windthorststraße 35 (Höchst):** Eine Zelle hat genau 171 Wohnungen, wie das Hochhaus laut Recherche. 2011 waren 160 davon kommunal. [eigene Auswertung]
- **Regel:** Zellen ohne Eigentumsform 2022 bekommen die Wohnungen 2011 je Eigentumsform, höchstens bis zur Zahl der Wohnungen 2022. „Bund oder Land“ 2011 zählt dort als NH.
- **Probe:** In 3.254 Zellen mit beiden Jahren stimmen öffentliche Eigentümer 2011 und 2022 gut überein (Korrelation 0,93). Genossenschaften ebenso (0,83). Die Trennung zwischen privaten Unternehmen und Privatpersonen stimmt nicht. Sie ist in den ergänzten Zellen unsicher. [eigene Auswertung]

| Stadt | vorher | nachher |
|---|---|---|
| ABG, Wohnungen | 50.733 | 53.739 |
| NH, Wohnungen | 12.637 | 13.603 |
| Wohnungen mit Eigentumsform | 92,6 % | 97,0 % |
| ABG + NH (Anteil) | 17,5 % | 17,8 % |

# 5. Wirkung je Bezirk

| Bezirk | ABG-Anteil vorher | nachher | ABG-Wohnungen mehr | NH-Wohnungen mehr |
|---|---|---|---|---|
| Niederrad-Nord | 25,1 % | 32,3 % | 698 | 1 |
| Eckenheim | 18,0 % | 19,2 % | 229 | 134 |
| Höchst-West | 15,1 % | 19,6 % | 163 | 44 |
| Niederursel-West | 18,3 % | 16,4 % | 0 | 196 |
| Rödelheim-Ost | 3,3 % | 6,4 % | 182 | 0 |
| Fechenheim-Nord | 13,1 % | 15,4 % | 154 | 0 |
| Heddernheim-West | 81,4 % | 77,9 % | 151 | 0 |

[eigene Auswertung]

# 6. Schwächen der Recherche

- 25 Punkte liegen in einem anderen Stadtteil als angegeben. Oft ist es nur ein anderer Name (Gutleutviertel, Goldstein, Nordweststadt, Riedberg). Manchmal liegt der Punkt daneben, zum Beispiel Höhenstraße 15–17, Hilgenfeld und In der Römerstadt 126–134. [eigene Auswertung]
- Viele Zahlen sind Bauzahlen, nicht der heutige Bestand. Beispiele: Römerstadt 1.182, Westhausen 1.116, Bornheimer Hang 1.234.
- Die Angaben aus der Mieterzeitung stammen aus 2003 bis 2006. Spätere Verkäufe sind möglich.

# 7. Offen

- **Fischstein-Siedlung und Hansapark.** Beide liegen auf früherem US-Gelände. Daneben liegen Zellen, die 2011 „Bund oder Land“ und 2022 kommunal waren. Die Karte zählt sie als NH. Hat die ABG dort nach 2011 vom Bund gekauft, gehören sie zur ABG. Das Kaufdatum ist offen. [offen]
- **ABG-Orte in der Karte.** Eine Überlagerung mit den Orten der Recherche ist möglich. Vorher müssten die Adressen geokodiert werden. [offen]

# 8. Quellen

- ABG-Chronik „Wohnen für alle“ (2015): https://www.abg.de/wp-content/uploads/ABG-Chronik.pdf (abgerufen 8.10.2026)
- ABG-Geschäftsbericht 2024: https://epflicht-hessen.hebis.de/ubffm/download/pdf/8631395
- Zensus 2022, Gitter 100 m, und Tabelle 4000W; Zensus 2011, Gitter 100 m, Wohnungen nach Eigentumsform (Statistische Ämter des Bundes und der Länder, dl-de/by-2-0)
- Recherche „ABG-Holding-Karte“, Stand 8.10.2026
