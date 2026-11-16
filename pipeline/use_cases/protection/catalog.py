"""Title and ⓘ of the coverage with Milieuschutz, and the ⓘ of the statute overlays. Pure module."""
from __future__ import annotations

from pipeline.shared.core.indicator import BOTH, Z22, Indicator, Z22_AS_OF, Source

# the planAS data of protection and land are fetched together; assembly puts in the fetch date
SOURCES = [Source("Erhaltungssatzungen und Bebauungspläne (planAS)", "abgerufen {fetch_date}",
                  "dl-de/by-2-0, Stadt Frankfurt am Main")]

INDICATORS: list[Indicator] = [
    Indicator("PROT_SOCIAL", "Abdeckung mit Milieuschutz", "Planung", "%", BOTH,
              "planAS, Erhaltungssatzungen · " + Z22 + " (Einwohner*innen)", "Abruf {fetch_date} · " + Z22_AS_OF,
              "Einwohner*innen in Milieuschutzgebieten ÷ Einwohner*innen im Gebiet. Ein 100-m-Feld zählt, wenn sein Mittelpunkt in "
              "einem gültigen Milieuschutzgebiet liegt.", "teal", 0, layer=False,
              rule="Als Milieuschutz zählt hier eine Satzung nach § 172 Abs. 1 Nr. 2 BauGB. Gebiete im Verfahren zählen nicht.",
              section="planning"),
]


# The four statute overlays: title in the list, tip before the name in the tooltip, and the result protocol of the ⓘ:
# Quelle, Stand, Regel (docs/texts.md, ⓘ protocol). `since` ends the tip of an Ortsbildsatzung.
_STATUTES, _FETCHED = "planAS, Erhaltungssatzungen", "Abruf {fetch_date}"
OVERLAYS: dict[str, dict] = {
    "social_preservation": {"title": "Milieuschutz (schraffiert)", "key": "Milieuschutz", "tip": "Milieuschutz:",
                            "source": _STATUTES, "as_of": _FETCHED,
                            "rule": "Die Karte zeigt gültige Satzungen nach § 172 Abs. 1 Nr. 2 BauGB."},
    "social_preservation_pending": {"title": "Milieuschutz im Verfahren (gestrichelt)",
                                    "key": "Milieuschutz im Verfahren",
                                    "tip": "Milieuschutz im Verfahren:", "source": _STATUTES, "as_of": _FETCHED,
                                    "rule": "Die Karte zeigt Satzungen nach § 172 Abs. 1 Nr. 2 BauGB im Verfahren. "
                                            "Die Aufstellung ist beschlossen. Die Satzung ist noch nicht in Kraft."},
    "townscape": {"title": "Ortsbildsatzung (gepunktet)", "key": "Ortsbildsatzung", "tip": "Ortsbildsatzung:", "since": "in Kraft seit",
                  "source": _STATUTES, "as_of": _FETCHED,
                  "rule": "Die Karte zeigt Satzungen nach § 172 Abs. 1 Nr. 1 BauGB. Ist eine Satzung zugleich "
                          "Milieuschutz, steht sie beim Milieuschutz."},
    "townscape_pending": {"title": "Ortsbildsatzung im Verfahren (blau gestrichelt)",
                          "key": "Ortsbildsatzung im Verfahren", "tip": "Ortsbildsatzung:",
                          "since": "im Verfahren seit", "source": _STATUTES, "as_of": _FETCHED,
                          "rule": "Die Karte zeigt Satzungen nach § 172 Abs. 1 Nr. 1 BauGB im Verfahren. Ist eine "
                                  "Satzung zugleich Milieuschutz, steht sie beim Milieuschutz."}}
