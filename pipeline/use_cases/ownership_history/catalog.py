"""German texts of the view "Trend" (README).
pipeline/use_cases/ownership_history/checks.py (check_history_headings) reads these texts and checks every statement in them."""
from __future__ import annotations

from pipeline.shared.core import palette
from pipeline.shared.core.indicator import Z11_AS_OF, Z22_AS_OF, ZENSUS_LICENSE, Source

# Groups of the charts „houses“ and „arrows“ (README). Colours: pipeline/shared/core/palette.py.
# "about" stands in every tooltip of the group, "example" only in the tooltips of 2022 and of the chart „arrows“:
# Vonovia was called Deutsche Annington in 2011. "lines" breaks a long title in the chart „arrows“. The two company
# classes keep the names of the Zensus.
CONDO_RENTED = "meist vermietet"  # check_condo_rented guards it
GROUP_TEXTS = {
    "person": {"title": "Privatpersonen", "color": palette.PERSON,
               "about": "Das sind einzelne Personen, Paare oder Erbengemeinschaften.", "example": ""},
    "condo": {"title": "Wohnungseigentümer*innen (WEG)", "color": palette.CONDO,
              "about": f"Die Häuser sind in Eigentumswohnungen aufgeteilt, die {CONDO_RENTED} werden. "
                       "Die Wohnungen gehören Personen oder Firmen.",
              "example": ""},
    "public": {"title": "Öffentlich (Kommune, Bund, Land)", "color": palette.PUBLIC,
               "about": "Dazu gehören Stadt, Land und Bund mit ihren Unternehmen. Der Zensus zählte die Nassauische Heimstätte 2011 "
                        "zum Land und 2022 zur Kommune. Deshalb fasst diese Ansicht Kommune, Bund und Land zusammen.",
               "example": "Z. B. ABG, Nassauische Heimstätte und Bundesanstalt für Immobilienaufgaben."},
    "housing_company": {"title": "Privatwirtschaftliche Wohnungsunternehmen", "color": palette.HOUSING_COMPANY,
                        "lines": ["Privatwirtschaftliche", "Wohnungsunternehmen"],
                        "about": "Ihr Geschäft ist die Vermietung.",
                        "example": "Z. B. Vonovia, die GWH und das Familienunternehmen Sahle Wohnen."},
    "other_company": {"title": "Andere privatwirtschaftliche Unternehmen", "color": palette.OTHER_COMPANY,
                      "lines": ["Andere privatwirtschaftliche", "Unternehmen"],
                      "about": "Dazu gehören Banken, Fonds & Co. Ihr Hauptgeschäft ist nicht die Vermietung.",
                      "example": "Z. B. Industria Wohnen und Hamburg Trust."},
    "coop": {"title": "Genossenschaften", "color": palette.COOP, "about": "",
             "example": "Z. B. Volks- Bau- und Sparverein, Beamten-Wohnungs-Verein und Bauverein für Höchst."},
    "nonprofit": {"title": "Organisationen ohne Erwerbszweck", "color": palette.NONPROFIT, "about": "",
                  "example": "Z. B. Kirchen wie der Evangelische Regionalverband Frankfurt und Offenbach."},
}
# The sum of both company classes: lead lines and the charts „sizes“ and „decades“
COMPANY_TITLE = "Private Unternehmen"
# Sectors as in the city profile of the Rosa-Luxemburg-Stiftung (sources/other/RLS_Stadtprofil_Frankfurt.pdf, p. 1):
# plain sums of Zensus classes. The bars show each sector as one block; companies start at the left edge. "color" is the
# main colour of the sector: the colour of its first group, for its label in chart 1.
SECTORS = {"private": {"title": "Privat", "color": palette.HOUSING_COMPANY,
                       "groups": ["housing_company", "other_company", "condo", "person"]},
           "community": {"title": "Gemeinschaft", "color": palette.PUBLIC, "groups": ["public", "coop", "nonprofit"]}}
BAR_ORDER = [g for s in SECTORS.values() for g in s["groups"]]
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
ZENSUS_DATABASE = Source("Zensusdatenbank, Tabellen 4000W-0001, 4000W-0004, 4000W-1008, 4000W-1011, 4000W-2013, "
                         "3000G-2001 und 3000G-2007 (Zensus 2011 und 2022, Gebietsstand 2022)",
                         f"{Z11_AS_OF} und {Z22_AS_OF}", ZENSUS_LICENSE)
OTHER_EXAMPLES_SOURCE = Source(
    "Beispiele weiterer Eigentümergruppen: Wohnungsmarktbericht 2019/2020 (B 430/2022), Antwort der Bundesregierung "
    "(BT-Drs. 19/7092), Kooperation Frankfurt, efo-magazin, Antwort des Magistrats F 677/2017, Website Sahle Wohnen",
    "2018–2026",
    "Veröffentlichungen der Stadt, der Bundesregierung, der Genossenschaften, der evangelischen Kirche und des "
    "Unternehmens Sahle Wohnen")
SOURCES = [ZENSUS_DATABASE, OTHER_EXAMPLES_SOURCE]
# the one source line below the charts; the licence as dl-de/by-2-0 asks; the tables are named in the data flow (docs/architecture.md, Data flow)
HISTORY_SOURCE = "Zensus 2011 und 2022, Gebäude mit Wohnraum · Statistische Ämter des Bundes und der Länder, dl-de/by-2-0"
# Phrases of the headings, lead lines and tooltips that check_history_headings guards. Each stands once, here; the
# texts of CHARTS are built from them and the checks read them.
HOUSES_TITLE = "Häuser privater Unternehmen sind im Schnitt am größten"
HOUSES_LEAD_BUILDINGS = "8 % der Häuser"
HOUSES_LEAD_DWELLINGS = "19 % der Wohnungen"
DECADES_TITLE = "Private Unternehmen wachsen vor allem im Bestand"
DECADES_LEAD = "Drei von vier"
ARROWS_TITLE = "Wohnungen privater Unternehmen haben sich verdoppelt"
ARROWS_LEAD = "nur halb so stark"
SIZES_TITLE = "Jede dritte Wohnung großer Häuser gehört privaten Unternehmen"
SIZES_LEAD = "jede sechste"
SIZES_TIP = "Zwei Drittel des Zuwachses"
# Texts of the four charts in the order of the view (README). The checks read them. „link“ names the question of a
# chart in the fragment of a direct link (docs/design.md, Direct links); once published it never changes.
CHARTS = {
    "houses": {"title": HOUSES_TITLE, "link": "wem-gehoeren-die-wohnungen",
               "lead": f"2022 gehören ihnen {HOUSES_LEAD_BUILDINGS} und {HOUSES_LEAD_DWELLINGS}.",
               "caveat": "Zur Gemeinschaft zählen die öffentliche Hand, Genossenschaften und "
                         "Organisationen ohne Erwerbszweck."},
    "decades": {"title": DECADES_TITLE, "link": "wachstum-im-bestand",
                "lead": f"{DECADES_LEAD} zusätzlichen Häusern seit 2011 sind vor 2010 gebaut.",
                "caveat": ""},
    "arrows": {"title": ARROWS_TITLE, "link": "wer-waechst",
               "lead": f"Die Zahl ihrer Häuser stieg {ARROWS_LEAD}.",
               "key": "Der dünne Pfeil zeigt Häuser, der dicke Wohnungen. Er läuft vom Kreis (2011) zur Spitze (2022).",
               "caveat": "Ein Wechsel der Gruppe kann auch eine neue Einordnung sein."},
    "sizes": {"title": SIZES_TITLE, "link": "grosse-haeuser",
              "lead": f"Das gilt 2022 für Häuser ab 13 Wohnungen. 2011 war es {SIZES_LEAD}.",
              "tip_large": SIZES_TIP + " seit 2011 liegen hier (+{large} von +{total}).",
              "caveat": ""},
}
# Row labels and the long form for tooltips ("in Häusern mit 13 und mehr Wohnungen")
SIZE_LABELS = {"1": {"label": "1 Wohnung", "long": "1 Wohnung"},
               "2": {"label": "2 Wohnungen", "long": "2 Wohnungen"},
               "3_6": {"label": "3–6 Wohnungen", "long": "3–6 Wohnungen"},
               "7_12": {"label": "7–12 Wohnungen", "long": "7–12 Wohnungen"},
               "13_plus": {"label": "13 und mehr", "long": "13 und mehr Wohnungen"}}
