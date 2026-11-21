"""Texts of the view "Trend" (texts.<lang>.yaml, README).
pipeline/use_cases/ownership_history/checks.py (check_history_headings, check_condo_rented) reads these texts and
checks every statement in them. Pure module."""
from __future__ import annotations

from pipeline.shared.core import palette
from pipeline.shared.core.indicator import Source
from pipeline.shared.core.texts import Texts, package_texts, per_language

T: dict[str, Texts] = package_texts(__file__)

# Colours of the groups of the charts „houses“ and „arrows“ (README; pipeline/shared/core/palette.py), in the order of
# the view. Their texts stand in the language files.
GROUP_COLORS = {"person": palette.PERSON, "condo": palette.CONDO, "public": palette.PUBLIC,
                "housing_company": palette.HOUSING_COMPANY, "other_company": palette.OTHER_COMPANY,
                "coop": palette.COOP, "nonprofit": palette.NONPROFIT}


def _group_texts(t: Texts) -> dict[str, dict]:
    """Per group: title, color, lines (only a long title), about, example (in this order, as the view reads them)."""
    out = {}
    for k, color in GROUP_COLORS.items():
        texts = t.tree(f"groups.{k}")
        lines = {"lines": list(texts.pop("lines").values())} if "lines" in texts else {}
        out[k] = {"title": texts.pop("title"), "color": color, **lines, **texts}
    return out


GROUP_TEXTS: dict[str, dict[str, dict]] = per_language(_group_texts, T)
# The sum of both company classes: lead lines and the charts „sizes“ and „decades“
COMPANY_TITLE: dict[str, str] = per_language(lambda t: t["company_title"], T)
# Sectors as in the city profile of the Rosa-Luxemburg-Stiftung (sources/other/RLS_Stadtprofil_Frankfurt.pdf, p. 1):
# plain sums of Zensus classes. The bars show each sector as one block; companies start at the left edge. "color" is the
# main colour of the sector: the colour of its first group, for its label in chart 1.
SECTOR_GROUPS = {"private": {"color": palette.HOUSING_COMPANY,
                             "groups": ["housing_company", "other_company", "condo", "person"]},
                 "community": {"color": palette.PUBLIC, "groups": ["public", "coop", "nonprofit"]}}
SECTORS: dict[str, dict[str, dict]] = per_language(
    lambda t: {k: {"title": t[f"sectors.{k}"], **v} for k, v in SECTOR_GROUPS.items()}, T)
BAR_ORDER = [g for s in SECTOR_GROUPS.values() for g in s["groups"]]
# Named examples outside the companies (the companies: EXAMPLES in ownership_shares/catalog.py). Each name stands in a
# tooltip; check_examples finds its phrases in the source (a path in pipeline/config.py). The tooltips print no numbers.
# Sahle Wohnen stands here, not in ownership_shares: only the tooltips of the view Trend name it (README).
# Two sources: the Magistrat names it as owner, its own page says family-run.
EXAMPLES = [
    # the passage names the owners of the subsidised stock; it backs „öffentlich“, not a size of the whole stock
    {"name": "ABG", "source": "HOUSING_MARKET_REPORT_PDF",
     "phrases": ["öffentlichen Wohnungsunternehmen festzustellen (siehe Abb. 48). Knapp über die Hälfte des Bestands "
                 "steht im Eigentum der ABG Frankfurt Holding"]},
    {"name": "Nassauische Heimstätte", "source": "HOUSING_MARKET_REPORT_PDF",
     "phrases": ["Mit deutlichem Abstand folgt die Nassauische Heimstätte Wohnstadt"]},
    {"name": "Bundesanstalt für Immobilienaufgaben", "source": "BIMA_ANSWER_PDF",
     "phrases": ["Antwort der Bundesregierung", "Bundesanstalt für Immobilienaufgaben (BImA)", "bundeseigene Wohnungen",
                 "Frankfurt am Main 1.015 1.156 2.171"]},
    {"name": "Volks- Bau- und Sparverein", "source": "COOP_VBS_HTML",
     "phrases": ["Volks- Bau- und Sparverein Frankfurt am Main eG", "Anzahl der Wohnungen 4.375"]},
    {"name": "Beamten-Wohnungs-Verein", "source": "COOP_BWV_HTML",
     "phrases": ["Beamten-Wohnungs-Verein Frankfurt am Main eG", "Anzahl der Wohnungen 1.491"]},
    {"name": "Bauverein für Höchst", "source": "COOP_BVH_HTML",
     "phrases": ["Bauverein für Höchst am Main und Umgebung eG", "Anzahl der Wohnungen 1.500"]},
    {"name": "Evangelische Regionalverband", "source": "CHURCH_INTERVIEW_HTML",
     "phrases": ["Wir haben gut 500 Mietwohnungen", "rund 170 Seniorenwohnungen im Westend",
                 "der Evangelische Regionalverband investiert", "17. September 2019"]},
    {"name": "Sahle Wohnen", "source": "SAHLE_SUBSIDISED_PDF",
     "phrases": ["Sahle Wohnen 915", "Stand: 31.12.2016"]},
    {"name": "Sahle Wohnen", "source": "SAHLE_PAGE_HTML",
     "phrases": ["Die familiengeführte Gruppe besitzt, vermietet und betreut etwa 23.000 Wohnungen",
                 "Hamburg und Frankfurt am Main aktiv"]},
]
ZENSUS_DATABASE: dict[str, Source] = per_language(lambda t: Source(**t.tree("sources.zensus_database")), T)
OTHER_EXAMPLES_SOURCE: dict[str, Source] = per_language(lambda t: Source(**t.tree("sources.other_examples")), T)
SOURCES: dict[str, list[Source]] = per_language(lambda t: [ZENSUS_DATABASE[t.lang], OTHER_EXAMPLES_SOURCE[t.lang]], T)
# the one source line below the charts (docs/architecture.md, Data flow)
HISTORY_SOURCE: dict[str, str] = per_language(lambda t: t["history_source"], T)
# Phrases of the headings, lead lines and tooltips that check_history_headings and check_condo_rented guard
PHRASES: dict[str, dict[str, str]] = per_language(lambda t: t.tree("phrases"), T)
# „link“ names the question of a chart in the fragment of a direct link (docs/design.md, Direct links); once
# published it never changes. The order is the order of the view (README).
CHART_FRAGMENTS = {"houses": "wem-gehoeren-die-wohnungen", "decades": "wachstum-im-bestand", "arrows": "wer-waechst",
               "sizes": "grosse-haeuser"}


def _charts(t: Texts) -> dict[str, dict]:
    """Texts of the four charts: title, link, then the texts of the language file in their order."""
    out = {}
    for k, link in CHART_FRAGMENTS.items():
        texts = t.tree(f"charts.{k}")
        out[k] = {"title": texts.pop("title"), "link": link, **texts}
    return out


CHARTS: dict[str, dict[str, dict]] = per_language(_charts, T)
# Row labels and the long form for tooltips, per size class (pipeline/shared/zensus/model.py, SIZES)
SIZE_LABELS: dict[str, dict[str, dict]] = per_language(lambda t: t.tree("sizes"), T)
