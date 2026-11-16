"""Titles and ⓘ of the survey indicators and the worked example of the rent burden. Pure module."""
from __future__ import annotations

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import Indicator, Source, format_de, year_of
from pipeline.use_cases.survey.model import BREAKDOWN_IDS, INCOME_LIMITS, MIN_CASES, STEP, round_half_up

SURVEY_LEVELS = ("district",)  # every district lies in one survey area (README)
SURVEY_AS_OF = "Mai–August 2025"
SURVEY_2024_AS_OF = "April–August 2024"
SURVEY_REPORT = "Leben in Frankfurt 2025 (Frankfurter Umfragen 5)"
MICRODATA = "Einzeldaten Leben in Frankfurt 2024 und 2025"
SOURCES = [Source("Leben in Frankfurt 2025 (Bericht Frankfurter Umfragen 5)", "2025",
                  "dl-de/by-2-0, Stadt Frankfurt am Main"),
           Source("Leben in Frankfurt 2024 und 2025 (Einzeldaten)", "2024, 2025",
                  "dl-de/by-2-0, Stadt Frankfurt am Main")]
SURVEY_YEAR = year_of(SURVEY_AS_OF)
SURVEY_RULE = "Jeder Bezirk zeigt die Klasse seines Umfragebezirks. {} heißt über {} bis {}."
SURVEY_UNCERTAINTY = ("Befragt wurde nur ein Teil der Einwohner*innen. Daraus ergibt sich je Umfragebezirk eine Unsicherheit "
                      "von ±4 bis 4,5 Prozentpunkten.")
# Abbildung 4.5 prints no margin. The ±4 to 4.5 points (own value from Tab. 9.5 of the report with the design effect;
# README, Limits) hold for shares of respondents only
RENT_BURDEN_UNCERTAINTY = "Der Wert beruht auf einer Stichprobe. Der Bericht nennt für die Quote keine Fehlerspanne."
SURVEY_CLASSES = "Der Bericht zeigt Klassen je Umfragebezirk."

# The income groups of the tooltip (model.INCOME_LIMITS), as lines under „Nach Haushaltsnettoeinkommen“
_LOWER, _UPPER = (format_de(limit, 0) for limit in INCOME_LIMITS)
INCOME_TITLES = dict(zip(BREAKDOWN_IDS, (f"unter {_LOWER} €", f"{_LOWER} bis {_UPPER} €", f"ab {_UPPER} €")))
INCOME_LEAD = "Nach Haushaltsnettoeinkommen"
_LOW_ID, _MID_ID, _HIGH_ID = BREAKDOWN_IDS
INCOME_CALC = ("Die Werte nach Einkommen im Tooltip rechnet die Karte selbst aus den Einzeldaten der Umfragen 2024 und "
               "2025. Sie zeigen den Median der Mieter*innen in jeder Einkommensgruppe. Für Frankfurt ergeben sich "
               f"{{city_{_LOW_ID}}} {INCOME_TITLES[_LOW_ID]}, {{city_{_MID_ID}}} bei {INCOME_TITLES[_MID_ID]} und "
               f"{{city_{_HIGH_ID}}} {INCOME_TITLES[_HIGH_ID]}.")
INCOME_RULE = (f"Im Tooltip rundet die Karte die Werte nach Einkommen auf {STEP} Prozentpunkte. Mit weniger als "
               f"{MIN_CASES} Befragten in einer Gruppe steht dort „k. A.“.")
# Placeholders of the half widths (model.breakdown_half_widths), apart from the range_/high_ names of catalog_numbers:
# typical and largest of the lowest group, largest of the two upper groups
HALF_WIDTH_NAMES = {"typical": f"typical_{_LOW_ID}", "max_low": f"max_{_LOW_ID}",
                    "max_upper": "max_LIF_RENT_BURDEN_INCOME_UPPER"}
_TYPICAL, _MAX_LOW, _MAX_UPPER = ("{" + name + "}" for name in HALF_WIDTH_NAMES.values())
INCOME_UNCERTAINTY = (f"Unter {_LOWER} € können die Werte nach Einkommen je Umfragebezirk typisch um ±{_TYPICAL} "
                      f"Prozentpunkte abweichen, höchstens aber um ±{_MAX_LOW}. Darüber sind es höchstens ±{_MAX_UPPER}. "
                      "Haushalte nahe einer Einkommensgrenze können in der Nachbargruppe liegen.")


def half_width_numbers(widths: dict[str, float]) -> dict[str, str]:
    """The half widths of the build as whole points, rounded half up, for the Unsicherheit of the rent burden."""
    return {name: format_de(round_half_up(widths[key], 1), 0) for key, name in HALF_WIDTH_NAMES.items()}

INDICATORS: list[Indicator] = [
    Indicator("LIF_RENT_BURDEN_RATIO", "Mietbelastungsquote", "Miete", "%", SURVEY_LEVELS,
              f"{SURVEY_REPORT}, Abbildung 4.5 · {MICRODATA}", f"{SURVEY_AS_OF} · {SURVEY_2024_AS_OF}",
              "Warmmiete ÷ Haushaltsnettoeinkommen. Die Befragten nennen ihr Einkommen in Stufen. Der Bericht rechnet "
              "mit der Mitte jeder Stufe. Für Frankfurt insgesamt nennt der Bericht den Median. "
              "Die Hälfte der Menschen gibt mindestens 29 Prozent ihres Einkommens für Wohnkosten aus. "
              "Die Klassen zeigen, wie sich die Quote je Umfragebezirk unterscheidet. " + INCOME_CALC, "orange", 0,
              type="classes", rule=SURVEY_RULE.format("„26–28“", 25, 28) + " " + INCOME_RULE,
              uncertainty=f"{RENT_BURDEN_UNCERTAINTY} {INCOME_UNCERTAINTY}",
              legend_note=f"Warmmiete im Verhältnis zum Einkommen, je Umfragebezirk, {SURVEY_YEAR}",
              breakdown_lead=INCOME_LEAD, section="rent", survey_area=True),
    # tooltip lines of the rent burden, no layer; the ⓘ of the rent burden explains them
    *(Indicator(kid, title, "Miete", "%", SURVEY_LEVELS, MICRODATA, f"{SURVEY_AS_OF} · {SURVEY_2024_AS_OF}",
                "Median von Warmmiete ÷ Haushaltsnettoeinkommen der Mieter*innen in der Einkommensgruppe.", "orange",
                0, layer=False, criterion=False, estimate=True, breakdown_of="LIF_RENT_BURDEN_RATIO", section="rent",
                survey_area=True)
      for kid, title in INCOME_TITLES.items()),
    Indicator("LIF_ATTACHMENT", "Würden ihr Wohnviertel vermissen", "Soziale Lage", "%", SURVEY_LEVELS,
              SURVEY_REPORT + ", Abbildung 4.11", SURVEY_AS_OF,
              "Anteil der Befragten, die ihr Viertel bei einem Wegzug vermissen würden. " + SURVEY_CLASSES,
              "teal", 0, type="classes", rule=SURVEY_RULE.format("„64–70“", 63, 70), uncertainty=SURVEY_UNCERTAINTY,
              legend_note=f"Anteil der Befragten im Umfragebezirk, {SURVEY_YEAR}", section="situation",
              survey_area=True),
]


# The household of the worked example (model.example_household); the browser writes „Rechnung am Beispiel <area>“
CALC_EXAMPLE_HOUSEHOLD = "einer alleinlebenden Person"


def _class_text(e: dict, kind: str) -> str:
    return f"Stufe {format_de(e[f'{kind}_low'], 0)} bis {format_de(e[f'{kind}_high'], 0)} €"


def survey_calc_example(e: dict) -> CalcExample:
    """Written sum of one household (docs/texts.md, Written sums): rent and costs, warm rent, income, its ratio. The
    ratio is one household, not the map value: whole percent, rounded half up, without „~“. e: example_household."""
    return CalcExample(CALC_EXAMPLE_HOUSEHOLD, (
        Row("", round(e["rent"]), 0, f"Kaltmiete ({_class_text(e, 'rent')})", unit="€"),
        Row("+", round(e["costs"]), 0, f"Nebenkosten ({_class_text(e, 'costs')})", unit="€"),
        Row("", round(e["rent"] + e["costs"]), 0, "Warmmiete", total=True, unit="€"),
        Row("÷", round(e["income"]), 0, f"Einkommen ({_class_text(e, 'income')})", unit="€"),
        Row("", int(round_half_up(e["ratio"], 1)), 0, "Mietbelastung dieser Person", total=True, unit="%")))
