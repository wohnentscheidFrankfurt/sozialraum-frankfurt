"""Titles and ⓘ of the election indicators; the list shares follow the lists of the build. Pure module."""
from __future__ import annotations

from pipeline.shared.core.indicator import QUARTERS_ONLY, Indicator, Source
from pipeline.use_cases.election.model import THRESHOLD

ELECTION_SOURCE = "votemanager, amtliches Endergebnis Stadtverordnetenwahl"
ELECTION_DAY = "15.3.2026"
SOURCES = [Source(f"Stadtverordnetenwahl {ELECTION_DAY[-4:]} (votemanager)", ELECTION_DAY, "Stadt Frankfurt am Main")]
ELECTION_LAYERS = ("ELEC_STRONGEST", "ELEC_TURNOUT")  # the layers besides the share of a list; the browser lists them first


def election_indicators(lists: list[dict]) -> list[Indicator]:
    ks = [Indicator(ELECTION_LAYERS[0], "Stärkste Liste", "Wahl", "", QUARTERS_ONLY, ELECTION_SOURCE, ELECTION_DAY,
                    "Liste mit den meisten Stimmen im Stadtteil", type="category",
                    legend_note=f"Liste mit den meisten Stimmen, {ELECTION_DAY}", section="election"),
          Indicator(ELECTION_LAYERS[1], "Wahlbeteiligung", "Wahl", "%", QUARTERS_ONLY, ELECTION_SOURCE, ELECTION_DAY,
                    "Wählende ÷ Wahlberechtigte. Briefwählende zählen mit.", "teal",
                    legend_note=f"Anteil der Wahlberechtigten, die gewählt haben, {ELECTION_DAY}", section="election"),
          Indicator("ELEC_VOTERS", "Wahlbeteiligung, Wählende", "Wahl", "Wählende", QUARTERS_ONLY, ELECTION_SOURCE,
                    ELECTION_DAY, "Wählende laut amtlichem Endergebnis", decimals=0, layer=False, criterion=False,
                    count_of=ELECTION_LAYERS[1], count_total="ELEC_ELIGIBLE", section="election")]
    other = f"Stimmen aller Listen unter {THRESHOLD:.0f} % in der Stadt ÷ gültige Stimmen im Stadtteil"
    return ks + [Indicator(l["key"], f"Anteil {l['name']}", "Wahl", "%", QUARTERS_ONLY, ELECTION_SOURCE, ELECTION_DAY,
                           other if l["key"] == "ELEC_OTHER" else "Stimmen der Liste ÷ gültige Stimmen im Stadtteil",
                           f"color:{l['color']}", legend_note=f"Bezogen auf die gültigen Stimmen, {ELECTION_DAY}",
                           section="election") for l in lists]


INDICATORS: list[Indicator] = election_indicators([])
