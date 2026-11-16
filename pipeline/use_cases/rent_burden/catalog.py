"""German texts of the view „Miete“ (README) and the constants behind their statements. Figure S1: the warm rent of
one flat against the net wage of three model persons, new and older contracts, in the latest survey year of the
Mietspiegel (wage bars).
Figure S2: the warm rent against the household income of adult tenants per income group, split into burden classes.
checks.py checks every statement of title, lead and ⓘ."""
from __future__ import annotations

from pipeline.shared.core import palette
from pipeline.shared.core.indicator import Source, format_de
from pipeline.use_cases.new_construction.catalog import RENT_FROM, RENT_TO, SURVEY_DATES, month_name
from pipeline.use_cases.survey.model import BREAKDOWN_IDS, INCOME_LIMITS

# the model persons: full time at the Mindestlohn, at the median wage of the residents, at the pension ceiling
PERSONS = ("mindestlohn", "median", "high")
CONTRACTS = ("new", "old")  # the two groups of the Mietspiegel: new contracts and older (raised) contracts
FLAT_M2 = 55  # the median class 50–60 m² of one-person tenant households, Leben in Frankfurt 2024 and 2025
CALC_PERSON, CALC_CONTRACT = "mindestlohn", "new"  # the written sums of the ⓘ of S1 (wage_view)
NEBENKOSTEN_MONTH = 6  # the Kosten der Unterkunft of the BA are those of June of each survey year (BA_KDU_XLSX)
# The statements of title and ⓘ; checks.py tests each against the data (docs/data-rules.md, Checks). The lead
# takes its euros from the table.
FACTOR_RANGE = (2.5, 3.5)  # title „etwa dreimal“: share Mindestlohn ÷ share high wage, both contracts of RENT_TO
SENSITIVITY_POINTS = (1, 4)  # Unsicherheit: with the Nebenkosten of the Mietspiegel the share lies this much lower
MEASURED = 29  # Unsicherheit: the published median burden of all tenants (Leben in Frankfurt 2024 and 2025), percent
CEILING_ABOVE = 11  # Regel „gut 11 %“: percent of full-time employees in Hessen above the pension ceiling (P88–P89)

# S2 title „etwa der Hälfte“: every median of the lowest group, whatever the income inside its class, lies this many
# points around 50 (checks.py)
ABOUT_HALF = 7.5
# S2 lead „knapp ein Viertel“: the median of the highest group, from this to under that, in percent (checks.py)
ALMOST_QUARTER = (20, 25)
# S2 lead „~17 %“: the share of the lowest group, rounded half up to whole percent, lies at most this many percent
# from the main case under every sensitivity of the income (checks.py)
ABOUT_SHARE = 1

_LAST_SURVEY = SURVEY_DATES[RENT_TO]
_HSL_MONTH = "April 2025"  # the month of the wage distribution of Hessen (HSL N I 9 j/25), the Regel „gut 11 %“

# „link“ names the question of the figure in the fragment of a direct link (docs/design.md, Direct links); once
# published it never changes
WAGE_TEXTS = {
    "link": "warmmiete-und-lohn",
    "title": "Mit Mindestlohn kostet dieselbe Wohnung einen etwa dreimal so großen Teil des Lohns wie mit hohem Lohn",
    # {left_low}, {left_high}: what is left at the Mindestlohn and at the high wage, new contract (wage_view)
    "lead": "Nach der Warmmiete bleiben mit Mindestlohn {left_low} im Monat, mit hohem Lohn {left_high}.",
    "info": {
        "source": "Mietspiegel · Bundesagentur für Arbeit (Kosten der Unterkunft, Entgeltstatistik) · Lohnsteuer "
                  "nach Bundesfinanzministerium · Hessisches Statistisches Landesamt (Verdienstverteilung in Hessen)",
        "as_of": f"Mieten {_LAST_SURVEY} · Nebenkosten {month_name(NEBENKOSTEN_MONTH)} {RENT_TO} · Löhne "
                 f"31.12.{RENT_TO} · Steuern und Beiträge {_LAST_SURVEY} · Verdienstverteilung {_HSL_MONTH}",
        # the formulas stand in the written sums (calc_net, calc_share); the prose keeps what no sum shows
        "calc": "Steuerklasse I, ohne Kinder, ohne Kirchensteuer.",
        "rule": f"Der mittlere Lohn ist der Median der Vollzeitbeschäftigten mit Wohnort Frankfurt. Der hohe Lohn "
                f"liegt an der Beitragsbemessungsgrenze der Rentenversicherung; in Hessen verdienen gut "
                f"{CEILING_ABOVE} % der Vollzeitbeschäftigten mehr.",
        "uncertainty": f"Die Nebenkosten stammen von Haushalten mit Grundsicherung. Mit den Werten des Mietspiegels "
                       f"läge der Anteil {SENSITIVITY_POINTS[0]} bis {SENSITIVITY_POINTS[1]} Punkte niedriger, beim "
                       f"Mindestlohn am meisten. Gemessen gibt die Hälfte der Mieter*innen "
                       f"mindestens {MEASURED} % ihres Einkommens für die Warmmiete aus.",
    },
    # the browser prints the line as it is: it names its sources itself („Quellen:“). The Mietspiegel of a year
    # rests on the survey of the year before.
    "source": f"Rechenbeispiel. Quellen: Frankfurter Mietspiegel {RENT_TO + 1}, Bundesagentur für Arbeit, "
              f"Bundesministerium der Finanzen, Hessisches Statistisches Landesamt",
    # the line that explains the drawing
    "explain": f"Jeder Balken ist der Nettolohn eines Monats, der rote Teil die Warmmiete. Eine Person lebt allein in "
               f"{FLAT_M2} m² und arbeitet Vollzeit.",
    # the labels of the drawing: once over the red block, per row under the name and in or right of the frame
    "rent_label": "Warmmiete {rent}",
    "net_label": "Nettolohn {net}",
    "left_label": "bleiben {left}",
    # the names of the rows (persons) and of the switch (contracts)
    "names": {"mindestlohn": "Mindestlohn", "median": "mittlerer Lohn", "high": "hoher Lohn"},
    "contracts": {"new": "Neuer Vertrag", "old": "Älterer Vertrag"},
    "tip": "{contract}, {name}: Warmmiete {warm_rent}, Nettolohn {net}. Das sind {share} des Nettolohns. Es bleiben "
           "{left}.",
    # the written sums of the ⓘ at CALC_PERSON and CALC_CONTRACT (docs/texts.md, Written sums): label and row texts;
    # {hourly}: the Mindestlohn per hour
    "calc_net": {"label": "Nettolohn am Beispiel Mindestlohn",
                 "gross": "Bruttolohn ({hourly} × 40 Stunden × 52 Wochen ÷ 12)", "contributions": "Sozialbeiträge",
                 "wage_tax": "Lohnsteuer", "soli": "Solidaritätszuschlag", "net": "Nettolohn"},
    "calc_share": {"label": "Rechnung am Beispiel Mindestlohn, neuer Vertrag", "cold": "Nettokaltmiete je m²",
                   "costs": "Betriebs- und Heizkosten je m²", "m2": "m²", "warm": "Warmmiete", "net": "Nettolohn",
                   "share": "Anteil am Nettolohn"},
}

# --- S2, tenants by income group ---

SURVEY_YEARS = (2024, 2025)  # the surveys of the microdata (config.SURVEY_MICRODATA), pooled
# the burden classes: percent of the household income, from the lower bound to under the upper (None: open)
CLASSES = ((0, 30), (30, 40), (40, 50), (50, None))
# the red family of the rents, darker = heavier burden (call 2 of the plan); the key and the tooltips name the classes
CLASS_COLOURS = (palette.STATE, palette.NONPROFIT, palette.PUBLIC, palette.COOP)


def _class_name(low: float, high: float | None, unit: str) -> str:
    """„unter 30 %“, „30 bis unter 40 %“, „50 % und mehr“: a class from its bounds (0: open at the bottom)."""
    low_text, high_text = format_de(low, 0), None if high is None else format_de(high, 0)
    if low == 0:
        return f"unter {high_text} {unit}"
    return f"{low_text} {unit} und mehr" if high is None else f"{low_text} bis unter {high_text} {unit}"


_GROUP_BOUNDS = tuple(zip((0, *INCOME_LIMITS), (*INCOME_LIMITS, None)))
_SURVEYS = f"{SURVEY_YEARS[0]} und {SURVEY_YEARS[1]}"
_LOWER, _UPPER = (format_de(limit, 0) for limit in INCOME_LIMITS)

# „link“ as in WAGE_TEXTS; once published it never changes. The lead takes the share of the lowest group („~17 %“,
# checks.py keeps it between the bounds and within ABOUT_SHARE under every sensitivity); „knapp ein Viertel“ is the
# median of the highest group (ALMOST_QUARTER).
LOW_INCOME_TEXTS = {
    "link": "warmmiete-und-einkommen",
    "title": f"Bei Mieter*innen mit weniger als {_LOWER} € netto entspricht die Warmmiete etwa der Hälfte des "
             f"Einkommens",
    "lead": f"Das betrifft {{share}} der erwachsenen Mieter*innen. Ab {_UPPER} € ist es knapp ein Viertel.",
    "info": {
        "source": f"Leben in Frankfurt {_SURVEYS}, eigene Auswertung der Einzeldaten",
        "as_of": f"Befragungen {_SURVEYS}",
        # the formula stands in the written sum of LIF_RENT_BURDEN_RATIO (bars_view); the prose keeps the rest
        "calc": "Die Warmmiete schließt Heizung und Nebenkosten ein. Die Umfrage fragt Miete, Nebenkosten und "
                "Einkommen in Klassen ab; gerechnet wird mit der Mitte jeder Klasse.",
        "rule": "Die Anteile zählen erwachsene Mieter*innen, nicht Haushalte.",
        # {low} and {high}: the lowest median of the sensitivities rounded down, the highest rounded half up;
        # {mikrozensus}: the classes of „mikrozensus“ with their values, rounded
        "uncertainty": "Einkommen gibt es nur in Klassen; je nach Lage in der Klasse liegt der Median zwischen {low} "
                       "und {high} %. Haushalte, deren Miete das Jobcenter zahlt, lassen sich nicht erkennen. Zum "
                       "Vergleich der Mikrozensus 2018, ohne Heizung: {mikrozensus}.",
    },
    # the browser prints the line as it is, like the line of S1
    "source": f"Quelle: Leben in Frankfurt {_SURVEYS}, eigene Auswertung",
    "groups": dict(zip(BREAKDOWN_IDS, (_class_name(low, high, "€") for low, high in _GROUP_BOUNDS))),
    "classes": [_class_name(low, high, "%") for low, high in CLASSES],
    # the classes of MIKROZENSUS_2018 (sources.py) as the Unsicherheit names them
    "mikrozensus": {"under 900": "unter 900 €", "1,500-2,000": "1.500 bis 2.000 €"},
    "median_label": "Median {median}",
    "tip_bar": "{group}: {share} der erwachsenen Mieter*innen. Im Median entspricht die Warmmiete {median} des "
               "Einkommens.",
    "tip_segment": "{group}: Bei {value} dieser Mieter*innen liegt die Warmmiete bei {name} des Einkommens.",
}

_YEARS = sorted(SURVEY_DATES)
_LISTED = f"{', '.join(map(str, _YEARS[:-1]))} und {_YEARS[-1]}"
BA_LICENSE = "Statistik der Bundesagentur für Arbeit"  # free use with this source notice (sources/README.md)
SOURCES = [
    Source(f"Statistik der Bundesagentur für Arbeit, Kosten der Unterkunft (SGB II), Kreis Frankfurt am Main: "
           f"Tabelle 1b, {month_name(NEBENKOSTEN_MONTH)} {_LISTED}", f"{month_name(NEBENKOSTEN_MONTH)} {RENT_TO}",
           BA_LICENSE),
    Source(f"Statistik der Bundesagentur für Arbeit, Entgeltstatistik: Median der Vollzeitbeschäftigten nach Wohnort, "
           f"Tabelle 16.2 ({RENT_FROM}) und Tabelle 9.2 (2021 bis {RENT_TO})", f"31.12.{RENT_TO}", BA_LICENSE),
    Source("Hessisches Statistisches Landesamt, Verdienstverteilung in Hessen im Jahr 2025: Bericht N I 9 j/25, "
           "Tabelle 2.2.4", _HSL_MONTH, "dl-de/by-2-0, Hessisches Statistisches Landesamt"),
    Source("Amt für Wohnungswesen, Wohnungsmarktbericht 2019/2020, Abbildung 41 (Mikrozensus 2018)", "2018",
           "Stadt Frankfurt am Main"),
]
