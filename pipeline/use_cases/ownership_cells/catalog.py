"""Texts of the ownership estimate and of the overlay „Eigentum je 100-m-Feld“. Pure module."""
from __future__ import annotations

from pipeline.shared.core.indicator import TEST_2011, Z11_AS_OF, Z22_AS_OF, ZENSUS_LICENSE, Source, year_of
from pipeline.use_cases.ownership_cells.model import BACKTEST_CELLS_RIGHT, BACKTEST_PUBLIC_RIGHT, MIN_DWELLINGS_PER_CELL

OWN_AS_OF = f"{Z22_AS_OF} · {Z11_AS_OF}, wo 2022 die Eigentumsform fehlt"
OWN_LEGEND_BASE = "Anteil der Wohnungen"
OWN_LEGEND_NOTE = f"{OWN_LEGEND_BASE}, {year_of(Z22_AS_OF)}, geschätzt"
OWN_LEGEND_NOTE_COOP = f"{OWN_LEGEND_BASE}, {year_of(Z22_AS_OF)}, aus {year_of(Z11_AS_OF)} geschätzt"
ZENSUS_2022 = Source("Zensus 2022 (100-m- und 1-km-Gitter: Gebäude, Wohnungen, Eigentümerquote, Nettokaltmiete, "
                     "Leerstandsquote; Tabellen 4000W)", Z22_AS_OF, ZENSUS_LICENSE)
ZENSUS_2011 = Source("Zensus 2011 (Gitter 100 m, Wohnungen nach Eigentumsform und Baujahr, Gebäude nach "
                     "Eigentumsform und Zahl der Wohnungen)", Z11_AS_OF, ZENSUS_LICENSE)
SOURCES = [ZENSUS_2022, ZENSUS_2011]
# The group in the dative, for „Die meisten Wohnungen gehören <dative> (geschätzt).“ in the grid tooltip
GROUP_DATIVE = {"OWN_PUBLIC": "der ABG und der Nassauischen Heimstätte", "OWN_STATE": "dem Bund oder dem Land",
                "OWN_COOP": "Genossenschaften", "OWN_COMPANY": "privaten Unternehmen",
                "OWN_PERSON": "Privatpersonen und WEG", "OWN_NONPROFIT": "Organisationen ohne Erwerbszweck"}


def grid_overlay() -> dict:
    """ⓘ of the overlay „Eigentum je 100-m-Feld“ (docs/data-rules.md, Level; docs/texts.md, ⓘ protocol)."""
    return {"title": "Eigentum je 100-m-Feld (nah gezoomt)",  # the tooltip is built in the browser (web/js/04_overlays.js)
            "source": "Zensus 2022, 100-m-Gitter (Gebäude nach Eigentumsform, Wohnungen) · Zensus 2011, 100-m-Gitter "
                      "(Wohnungen nach Eigentumsform)",
            "as_of": f"{Z22_AS_OF} · {Z11_AS_OF}",
            "calc": "Die Farbe zeigt die Gruppe mit den meisten Wohnungen. Diese Wohnungen sind geschätzt. Die Zahlen "
                    "sind gezählte Gebäude 2022. Wo 2022 die Eigentumsform fehlt, zeigt das Feld die gezählten "
                    "Wohnungen von 2011.",
            "rule": f"Die Karte zeigt nur Felder ab {MIN_DWELLINGS_PER_CELL} Wohnungen mit geschätzter Eigentumsform. "
                    "Die Felder erscheinen erst, wenn man nah heranzoomt.",
            "uncertainty": f"{TEST_2011} Die Farbe stimmte in {BACKTEST_CELLS_RIGHT} % der Felder. Wo ABG oder "
                           f"Nassauische Heimstätte vorn lagen, stimmte sie in {BACKTEST_PUBLIC_RIGHT} %."}
