"""German texts of the view „Neubau“ (README). checks.py checks every statement of title, lead and ⓘ of both
charts."""
from __future__ import annotations

import re

from pipeline.shared.core import palette
from pipeline.shared.core.checks import de_thousands
from pipeline.shared.core.indicator import Source

FIRST_YEAR, LAST_YEAR = 2011, 2025
PROVISIONAL_FROM = 2023  # from here the subsidised numbers rest on the latest answer of the Magistrat
YEARS, AVERAGE = 10, 4100  # the lead: the mean of all dwellings of the last YEARS years, rounded to hundreds
FIFTH = "fast jede fünfte"  # 18 % ≤ share of the last year < 20 %
EIGHTH = "höchstens jede achte"  # every share before the last year ≤ 12.5 %
STOCK_BREAKS = (2022,)  # from here stock and population rest on the Zensus 2022; the lines do not connect the year before
BASE_EFFECTS = (25679, 4378)  # the ⓘ: the Zensus 2022 lowered the population and the dwellings by these numbers
OLD_BASE, NEW_BASE = 2011, 2022  # Zensus of the stock and the population before and from STOCK_BREAKS
RENT_FROM = 2017  # the base of the second block (rents, prices, wages): all lines start here at 100; heading starts "Seit"
# the rents of new contracts must outgrow the dwellings in Euro by more than this (4 index points): above the sampling
# error of the Mietspiegel in Euro, about ±3.2 points by an own estimate (docs/data-rules.md, Uncertainty)
RENT_MARGIN = 0.04
# from the survey of this year the Mietspiegel counts the contracts of six years before the survey, before of four
# (§ 558 BGB since 2020); the sentence stands in the Unsicherheit of the rents
SIX_YEARS_FROM = 2021
MIETSPIEGEL_WINDOW = f"Seit {SIX_YEARS_FROM} zählt der Mietspiegel sechs statt vier Jahre."
PRICE_MONTH = 7  # the VPI of this month stands for a year without Mietspiegel survey (survey months: July, 2017 June)
WAGE_QUARTERS = (2, 3)  # the wage of a year is the mean of these quarters (the survey days lie on their border)
# the value axes of the two charts of the second block (index, 2017 = 100): lowest and highest value and the ticks
# (docs/design.md, View Neubau); rents_view stops if a value lies outside
RENT_AXES = {"nominal": {"min": 95, "max": 140, "ticks": (100, 110, 120, 130, 140)},
             "real": {"min": 86, "max": 112, "ticks": (90, 95, 100, 105, 110)}}
OUTFLOW_THIRD = 1 / 3  # below this part of the mean outflow of the other years, the ⓘ names OUTFLOW_CAVEAT
# HSL, F I 1 j/25, Vorbemerkungen: since the HBO of 14.10.2025 (§ 63a) most demolitions need no permit
OUTFLOW_CAVEAT = ("Seit Oktober 2025 brauchen die meisten Abrisse keine Genehmigung mehr. Das Landesamt erfasst "
                  "Abgänge deshalb womöglich nicht mehr vollständig.")

# „link“ of TEXTS and RENTS_TEXTS names the question of the figure in the fragment of a direct link (docs/design.md,
# Direct links); once published it never changes
TEXTS = {
    "link": "gefoerderte-wohnungen",
    "title": f"{LAST_YEAR} wurde {FIFTH} neue Wohnung gefördert, bis {LAST_YEAR - 1} {EIGHTH}",
    "lead": f"Insgesamt wurden in den letzten {YEARS} Jahren jährlich durchschnittlich {de_thousands(AVERAGE)} "
            f"Wohnungen gebaut, auch durch Umbau.",
    "key": {"new": "Neubau", "subsidised": "davon gefördert (Miete gebunden)", "provisional": "vorläufig",
            "conversions": "Umbau bestehender Gebäude"},
    "info": {
        "source": "Hessisches Statistisches Landesamt, Baufertigstellungen · Magistrat der Stadt Frankfurt, Antworten "
                  "B 12/2024, F 3150/2025, F 79/2026, F 9/2026 und F 158/2026",
        "as_of": "Fertiggestellte Wohnungen bis 2025 (Bericht Mai 2026) · Geförderte Wohnungen: Antworten bis August 2026",
        # the column and the share stand in the written sums (calc_column, calc_share); the prose keeps the terms
        "calc": "Neubau sind Wohnungen in neu gebauten Gebäuden, Wohnheime eingeschlossen. Umbau sind Wohnungen aus "
                "Baumaßnahmen an bestehenden Gebäuden, also aus Umbau, Ausbau, Erweiterung oder Wiederherstellung. "
                "Gefördert sind Wohnungen aus den Frankfurter Programmen für den Neubau bezahlbarer Mietwohnungen, "
                "Förderweg 1 und Förderweg 2. Der Magistrat zählt die Programme mit, die es vorher gab. Weil diese "
                "Programme den Neubau fördern, teilt der Anteil durch den Neubau, nicht durch alle Wohnungen.",
        "rule": "Gefördert heißt, dass die Miete für eine Zeit gebunden ist. Das sagt nichts über das Eigentum. Auch "
                "private Unternehmen und Personen bauen geförderte Wohnungen. Für 2023 bis 2025 gilt die letzte Antwort des "
                "Magistrats.",
        "uncertainty": "Die Förderzahlen 2023 bis 2025 sind vorläufig. Bisher hat der Magistrat frühe Zahlen nur nach "
                       "oben korrigiert. Die geförderten Wohnungen zählt die Stadt nach ihren Förderprogrammen, den "
                       "Neubau zählt das Landesamt. Beide Zählungen passen nicht genau zusammen. Wohnheime für "
                       "Studierende zählen zum Beispiel nur beim Neubau mit. Vereinzelt entstehen geförderte Wohnungen "
                       "auch durch Umbau. Beim Umbau zählt das Landesamt, was unter dem Strich dazukommt. Wer zwei "
                       "Wohnungen zusammenlegt, verringert die Zahl. Für 2019 und 2020 nennt der Magistrat niedrigere "
                       "Gesamtzahlen als das Landesamt.",
    },
    "source": "Hessisches Statistisches Landesamt, Baufertigstellungen · Magistrat der Stadt Frankfurt",
    "color": palette.SUBSIDISED,
    "provisional_note": "Die Förderzahl ist vorläufig.",
    # the written sums of the ⓘ for the last year (docs/texts.md, Written sums): label and row texts
    "calc_column": {"label": "Säule am Beispiel {year}", "new_res": "Neubau in Wohngebäuden",
                    "new_nonres": "Neubau in Nichtwohngebäuden", "new": "Neubau", "conversions": "Umbau",
                    "all": "fertiggestellte Wohnungen"},
    "calc_share": {"label": "Anteil am Beispiel {year}", "fw1": "Förderweg 1", "fw2": "Förderweg 2",
                   "subsidised": "geförderte Wohnungen", "subsidised_provisional": "geförderte Wohnungen (vorläufig)",
                   "new": "Neubau", "share": "Anteil gefördert"},
}

# The survey days the tooltips show; the check compares year and month with the dates read from the brochures. The day
# is pinned in the date patterns of RENT_SOURCES.
SURVEY_DATES = {2017: "Juni 2017", 2021: "1.7.2021", 2023: "1.7.2023", 2025: "1.7.2025"}
RENT_TO = max(SURVEY_DATES)  # the rents block ends at the last survey year; the columns and the stock run to LAST_YEAR
# The German month names, to read the month of a date of SURVEY_DATES (shown_month) and to name a month in the texts.
# sources.py keeps the same list for the brochures: it may not import this module (tests/test_architecture.py), a test
# compares both.
GERMAN_MONTHS = {name: number for number, name in enumerate(
    ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November",
     "Dezember"], 1)}


def shown_month(shown: str) -> tuple[int, int] | None:
    """(year, month) of a survey date as the tooltips show it („1.7.2021“ or „Juni 2017“); None for any other form."""
    numeric, named = re.fullmatch(r"\d{1,2}\.(\d{1,2})\.(\d{4})", shown), re.fullmatch(r"(\w+) (\d{4})", shown)
    if numeric:
        month, year = int(numeric[1]), int(numeric[2])
    elif named:
        month, year = GERMAN_MONTHS.get(named[1]), int(named[2])
    else:
        return None
    return (year, month) if month is not None and 1 <= month <= 12 else None


def month_name(month: int) -> str:
    """The German name of a month number (1 to 12)."""
    return list(GERMAN_MONTHS)[month - 1]


RENT_MONTH = month_name(shown_month(SURVEY_DATES[RENT_TO])[1])  # the month of the last survey: the price of RENT_TO

RENTS_TEXTS = {
    "link": "wohnungen-und-mieten",
    "title": f"Seit {RENT_FROM} wuchs die Zahl der Wohnungen schneller als die Bevölkerung, die Mieten neuer Verträge "
             f"noch schneller",
    "lead": "Die Mieten älterer Verträge stiegen weniger als Preise und Löhne.",
    "info": {
        "source": "Hessisches Statistisches Landesamt: Fortschreibung des Wohnungsbestands (Berichte F I 1 j/25 und "
                  "j/22, Regionaldatenbank Tabelle 31231-02-01-4) · Fortschreibung des Bevölkerungsstands "
                  "(Regionaldatenbank Tabelle 12411-01-01-4, Bericht A I 2, 2. Halbjahr 2022) · "
                  "Verbraucherpreisindex Hessen (Bericht M I 2 j/25, Tabelle 3) · Nominallohnindex Hessen "
                  "(Pressetabelle 3. Quartal 2025) · Stadt Frankfurt: Mietspiegel 2018, 2022 und 2024 (Gutachten), "
                  "Mietspiegel 2026 (Dokumentation), Mietspiegel-Broschüren 2022 bis 2026 · Melderegister, offene "
                  "Daten „Bevölkerung in Haushalten“ nach Stadtbezirken",
        "as_of": f"Wohnungen und Einwohner*innen 31.12.{RENT_TO} · Mieten {SURVEY_DATES[RENT_TO]} · Preise "
                 f"{RENT_MONTH} {RENT_TO} · Löhne {WAGE_QUARTERS[-1]}. Quartal "
                 f"{RENT_TO}",
        # the index and „ohne Inflation“ stand in the written sum (calc_rent); the prose keeps the rest
        "calc": "Wohnungen und Einwohner*innen zählen am 31.12., Mieten, Preise und Löhne zur Jahresmitte. Die Miete "
                "ist der Mittelwert der Nettokaltmiete je Quadratmeter in der Stichprobe des Mietspiegels. Die anderen "
                "Linien rechnen genauso. Ohne Inflation wird auch der Lohn durch die Preise geteilt.",
        "rule": f"Neue Verträge haben in den sechs Jahren vor der Erhebung begonnen, {RENT_FROM} in den vier Jahren "
                f"davor. Ältere Verträge haben früher begonnen, ihre Miete wurde in dieser Zeit erhöht. Geförderte "
                f"Wohnungen mit gebundener Miete zählen im Mietspiegel nicht mit. Einwohner*innen sind Personen mit "
                f"Hauptwohnsitz in Frankfurt. Preise sind der Verbraucherpreisindex Hessen im Monat der Erhebung, in "
                f"den Jahren dazwischen im {month_name(PRICE_MONTH)}. Löhne sind die Bruttomonatsverdienste in Hessen "
                f"im 2. und 3. Quartal. Die Haushaltsgröße zählt Personen je Haushalt im Melderegister. Sie lag von "
                f"{RENT_FROM} bis {RENT_TO} zwischen 1,84 und 1,87.",  # the check „rents households“ guards the range
        # the four growths are literals; the check „rents uncertainty“ guards them (docs/data-rules.md, Uncertainty)
        "uncertainty": f"{MIETSPIEGEL_WINDOW} Das senkt seine Mittelwerte etwas. "
                       f"Der Mietspiegel rechnet nicht heraus, wie viel des Anstiegs auf neue und modernisierte "
                       f"Wohnungen entfällt. Verträge ohne Erhöhung fehlen im Mietspiegel. Die älteren Mieten sanken "
                       f"ohne Inflation vor allem 2022 und 2023, als die Preise stark stiegen. Die Löhne gelten für "
                       f"ganz Hessen. Der Zensus {NEW_BASE} hat die Bevölkerung um {de_thousands(BASE_EFFECTS[0])} "
                       f"und die Wohnungen um {de_thousands(BASE_EFFECTS[1])} nach unten korrigiert. Auf gleicher "
                       f"Grundlage gerechnet wuchsen die Wohnungen seit {RENT_FROM} um 7,8 % und die Bevölkerung um "
                       f"5,3 %. Die Linien zeigen die veröffentlichten Zahlen, 6,6 % und 1,8 %. {OUTFLOW_CAVEAT} Die "
                       f"Zahlen zeigen nicht, wie viele Menschen eine passende Wohnung suchen. Sie zeigen auch nicht, "
                       f"wie hoch die Mieten ohne die neuen Wohnungen wären.",
    },
    "source": f"Index: Ende {RENT_FROM} bzw. Mitte {RENT_FROM} = 100. Quellen: Hessisches Statistisches Landesamt "
              f"(Fortschreibung, Verbraucherpreisindex Hessen, Nominallohnindex Hessen), Frankfurter Mietspiegel 2018 "
              f"bis 2026, Melderegister der Stadt Frankfurt",
    "break_note": f"ab {STOCK_BREAKS[0]} Zensus {NEW_BASE}",
    "old_base": f"auf Grundlage des Zensus {OLD_BASE}",  # the tooltips of the hollow dots
    # the note below chart 1 in the wide drawing (the key holds the same entry on phones)
    "old_base_note": f"Die hohlen Punkte zeigen {STOCK_BREAKS[0]} auf der alten Grundlage (Zensus {OLD_BASE}).",
    "charts": {
        "nominal": {
            "title": "Mieten in Euro, wie im Vertrag",
            "explain": "Das graue Band reicht zum Vergleich von den Preisen bis zu den Löhnen. Punkte zeigen die "
                       "Stichtage des Mietspiegels.",
            "key": {"dwellings": "Wohnungen", "population": "Einwohner*innen", "new": "Miete neuer Verträge",
                    "old": "Miete älterer Verträge", "prices": "Preise", "wages": "Löhne in Hessen",
                    "old_base": f"{STOCK_BREAKS[0]} auf alter Grundlage (Zensus {OLD_BASE})"},
        },
        "real": {
            "title": "Mieten ohne Inflation",
            "explain": "Hier ist die Inflation herausgerechnet. Eine Linie unter 100 heißt, dass die Miete weniger "
                       "stieg als die Preise.",
            "key": {"new": "Miete neuer Verträge", "old": "Miete älterer Verträge", "prices": "Preise (= 100)",
                    "wages": "Löhne in Hessen, ohne Inflation"},
        },
    },
    # the end labels at the last year (wide drawing only): value, then the name
    "names": {"new": "neue Verträge", "old": "ältere Verträge", "prices": "Preise", "wages": "Löhne in Hessen",
              "dwellings": "Wohnungen", "population": "Einwohner*innen"},
    # the tooltip of a year slot: head and rows (value, then the label), a note, in 2022 the old base
    "tip_head": "{year}, Index {base} = 100",
    "tip_dwellings": "Wohnungen", "tip_population": "Einwohner*innen", "tip_new": "neue Verträge",
    "tip_old": "ältere Verträge", "tip_prices": "Preise", "tip_wages": "Löhne in Hessen",
    "tip_wages_real": "Löhne in Hessen, ohne Inflation",
    "tip_survey": "Miete zum Stichtag des Mietspiegels.",
    "tip_no_survey": "Keine Mietspiegel-Erhebung in diesem Jahr.",
    "tip_old_base": "Auf alter Grundlage: Wohnungen {dwellings}, Einwohner*innen {population}.",
    # the written sum of the ⓘ: the new contracts of the last year as index and without inflation
    "calc_rent": {"label": "Rechnung am Beispiel neuer Verträge {year}",
                  "rent": "Nettokaltmiete je m², neue Verträge {year}", "base": "dasselbe {first}",
                  "nominal": "in Euro, wie im Vertrag ({first} = 100)", "prices": "Preise {year} ({first} = 100)",
                  "real": "ohne Inflation"},
}

# Rents of the Mietspiegel: per survey year the mean net rent per m² of the new and of the older (raised) contracts
# and the survey day. `config` names the file in pipeline/config.py. `pattern` is the pinned phrase as
# re.sub(r"\s+", " ", " ".join(page_texts(path))) renders it (PDF hyphenation stays: "ei- nen", "veränder- ten").
# The date pattern has the named groups month (digits or a German month name) and year. A survey day is the literal 01
# in the pattern, not a group: a brochure with another day finds no hit and the reader stops (SURVEY_DATES shows 1.7.).
# 2017: the labels of figure 21 of the Gutachten 2022 (all, older and new contracts in 2013, 2017 and 2021, in this
# order); REPORT_GROWTHS guards the order.
RENT_SOURCES = [
    {"year": 2017,
     "values": {"config": "MIETSPIEGEL_2022_REPORT_PDF",
                "pattern": r"€8,66 €9,36 €10,29 €(\d+,\d+) €(\d+,\d+) (\d+,\d+) €(\d+,\d+) €(\d+,\d+) (\d+,\d+)",
                "new_group": 5, "old_group": 2},
     "date": {"config": "MIETSPIEGEL_2018_REPORT_PDF",
              "pattern": r"Stichmonat für die zu ermittelnde Vergleichsmiete war der (?P<month>[A-Za-zäöü]+) "
                         r"(?P<year>\d{4})"}},
    {"year": 2021,
     "values": {"config": "MIETSPIEGEL_2022_REPORT_PDF",
                "pattern": r"Teilmenge der erhöhten Altverträge weist ei- nen Mittelwert von (\d+,\d+) €/m² auf, was "
                           r"einer relativen Wachstumsrate von \d+,\d+ % entspricht\. Der Mittelwert der neu "
                           r"abgeschlossenen Verträge beträgt (\d+,\d+) €/m²",
                "new_group": 2, "old_group": 1},
     "date": {"config": "MIETSPIEGEL_2022_PDF",
              "pattern": r"Erhebungsstichtag des Mietspiegels 2022 war der 01\.(?P<month>\d{2})\."
                         r"(?P<year>\d{4})"}},
    {"year": 2023,
     "values": {"config": "MIETSPIEGEL_2024_REPORT_PDF",
                "pattern": r"Untergruppe der Neuverträge beträgt (\d+,\d+) €/m2, für die Untergruppe der veränder- "
                           r"ten Altverträge (\d+,\d+) €/m2",
                "new_group": 1, "old_group": 2},
     "date": {"config": "MIETSPIEGEL_2024_PDF",
              "pattern": r"Erhebungsstichtag für die Anpassungsstichprobe des Mietspiegels 2024 war der "
                         r"01\.(?P<month>\d{2})\.(?P<year>\d{4})"}},
    {"year": 2025,
     "values": {"config": "MIETSPIEGEL_2026_REPORT_PDF",
                "pattern": r"Teilmenge der erhöhten Altverträge weist einen Mittelwert von (\d+,\d+) €/m² auf, was "
                           r"einer Wachstumsrate von \d+,\d+ % entspricht\. Der Mittelwert der neu abgeschlossenen "
                           r"Verträge beträgt (\d+,\d+) €/m²",
                "new_group": 2, "old_group": 1},
     "date": {"config": "MIETSPIEGEL_2026_PDF",
              "pattern": r"Erhebungsstichtag für den Mietspiegel 2026 war der 01\.(?P<month>\d{2})\."
                         r"(?P<year>\d{4})"}},
]
# The growth rates (percent) the reports print for the two groups against the survey before. The check compares them
# with the growth of the values read; this guards the labels of 2017, which no sentence prints.
REPORT_GROWTHS = [
    {"year": 2021, "base": 2017, "config": "MIETSPIEGEL_2022_REPORT_PDF",
     "pattern": r"Altverträge weist ei- nen Mittelwert von \d+,\d+ €/m² auf, was einer relativen Wachstumsrate von "
                r"(\d+,\d+) % entspricht\. Der Mittelwert der neu abgeschlossenen Verträge beträgt \d+,\d+ €/m², "
                r"entsprechend einer relativen Wachstumsrate von (\d+,\d+) %",
     "new_group": 2, "old_group": 1},
    {"year": 2025, "base": 2023, "config": "MIETSPIEGEL_2026_REPORT_PDF",
     "pattern": r"Altverträge weist einen Mittelwert von \d+,\d+ €/m² auf, was einer Wachstumsrate von (\d+,\d+) % "
                r"entspricht\. Der Mittelwert der neu abgeschlossenen Verträge beträgt \d+,\d+ €/m², die "
                r"entsprechende Wachs- tumsrate liegt bei (\d+,\d+) %",
     "new_group": 2, "old_group": 1},
]

# Subsidised dwellings from 2023: per year and programme the latest answer of the Magistrat. `config` names
# the file in pipeline/config.py; `pattern` is the pinned phrase, `group` the number in it. 2011–2022: B 12/2024.
SUBSIDISED_SOURCES = [
    {"year": 2023, "programme": "fw1", "config": "ANSWER_F_158_2026_PDF",
     "pattern": r"2023 (\d+) (\d+) (\d+) 2024 (\d+) (\d+) (\d+) 2025 (\d+) (\d+) (\d+)", "group": 3},
    {"year": 2023, "programme": "fw2", "config": "ANSWER_F_3150_2025_PDF",
     "pattern": r"2023: Förderweg 1: (\d+) WE, Förderweg 2: (\d+) WE", "group": 2},
    {"year": 2024, "programme": "fw1", "config": "ANSWER_F_79_2026_PDF",
     "pattern": r"(\d+) Wohneinheiten fielen auf den Förderweg 1", "group": 1},
    {"year": 2024, "programme": "fw2", "config": "ANSWER_F_79_2026_PDF",
     "pattern": r"Im Förderweg 2, FW 2, wurden (\d+) Wohneinheiten fertiggestellt", "group": 1},
    {"year": 2025, "programme": "fw1", "config": "ANSWER_F_9_2026_PDF",
     "pattern": r"wurden 2025 (\d+) Wohneinheiten im Förderweg 1", "group": 1},
    {"year": 2025, "programme": "fw2", "config": "ANSWER_F_9_2026_PDF",
     "pattern": r"Im Förderweg 2 wurden (\d+) Wohneinheiten fertiggestellt", "group": 1},
]
# F 158/2026 confirms FW 1 2025 (checks.py)
CONFIRM_FW1_LAST = {"config": "ANSWER_F_158_2026_PDF", "pattern": SUBSIDISED_SOURCES[0]["pattern"], "group": 9}

SOURCES = [
    Source("Hessisches Statistisches Landesamt, Baufertigstellungen: Regionaldatenbank Tabellen 31121-01-02-4, "
           "31121-02-02-4 und 31121-03-02-4 und Bericht F II 2 2025, Tabellen 15, 17 und 19", "Mai 2026",
           "dl-de/by-2-0, Hessisches Statistisches Landesamt"),
    Source("Hessisches Statistisches Landesamt, Fortschreibung des Wohnungsbestands: Bericht F I 1 j/25, Tabelle 4, "
           "Bericht F I 1 j/22 (Juli 2023), Tabelle 4, und Regionaldatenbank Tabelle 31231-02-01-4", "Juni 2026",
           "dl-de/by-2-0, Hessisches Statistisches Landesamt"),
    Source("Hessisches Statistisches Landesamt, Fortschreibung des Bevölkerungsstands: Regionaldatenbank Tabelle "
           "12411-01-01-4 und Berichte A I 2 mit A II, A III, A V, 2. Halbjahr 2022 (Juni 2023) und 2. Halbjahr 2025 "
           "(Juli 2026)", "Juli 2026",
           "dl-de/by-2-0, Hessisches Statistisches Landesamt"),
    Source("Hessisches Statistisches Landesamt, Verbraucherpreisindex in Hessen 2022 bis 2025: Bericht M I 2 j/25, "
           "Tabelle 3", "Januar 2026", "dl-de/by-2-0, Hessisches Statistisches Landesamt"),
    Source("Hessisches Statistisches Landesamt, Nominallohnindex Hessen: Pressetabelle „Entwicklung des Reallohn-, "
           "Nominallohn- und Verbraucherpreisindex in Hessen 2007 bis 2025“", "3. Quartal 2025",
           "dl-de/by-2-0, Hessisches Statistisches Landesamt"),
    Source("Frankfurter Mietspiegel: Gutachten 2018, 2022 und 2024, Dokumentation 2026, Broschüren 2022 bis 2026 "
           "(Amt für Wohnungswesen)", "2018–2026", "Stadt Frankfurt am Main"),
    Source("Melderegister, Bevölkerung in Haushalten nach Stadtbezirken (offene Daten)", f"31.12.{RENT_TO}",
           "dl-de/by-2-0, Stadt Frankfurt am Main"),
    Source("Geförderte neue Wohnungen: Antworten des Magistrats B 12/2024, F 3150/2025, F 79/2026, F 9/2026 und "
           "F 158/2026", "2024–2026", "Stadt Frankfurt am Main"),
]
