"""Titles and ⓘ of the monitoring indicators. Pure module."""
from __future__ import annotations

from pipeline.shared.core.indicator import BOTH, Indicator, Source

MON = "Monitoring 2024 zur sozialen Segregation (Stadt Frankfurt)"
MON_AS_OF = "Ende 2022"
SOURCES = [Source("Monitoring 2024 zur sozialen Segregation", "2022", "Stadt Frankfurt am Main")]
MON_RULE = ("Manche Bezirke fasst das Monitoring zusammen. Die Karte zeigt sie als ein Gebiet. Fasst eine Tabelle "
            "andere Bezirke zusammen, nennt die Karte den gemeinsamen Wert. Fehlt ein Wert im Monitoring, steht "
            "„k. A.“. Für Stadtteile gilt das, wenn Bezirke mit mehr als 5 % der Einwohner*innen keinen Wert haben.")

INDICATORS: list[Indicator] = [
    # benefits as defined by the Monitoring for 2022 (p. 79): Bürgergeld only started on 1.1.2023
    Indicator("SOC_MIN_INCOME", "Mindestsicherung", "Soziale Lage", "%", BOTH, MON + ", Tabelle 14", MON_AS_OF,
              "Personen mit Arbeitslosengeld II, Sozialgeld, Hilfe zum Lebensunterhalt, Grundsicherung im Alter und bei "
              "Erwerbsminderung außerhalb von Einrichtungen oder Asylbewerberleistungen ÷ Einwohner*innen. Für Stadtteile "
              "mittelt die Karte die Bezirke, gewichtet nach Einwohner*innen.", "purple", rule=MON_RULE,
              uncertainty="Bewohner*innen von Unterkünften für Geflüchtete zählen mit. In Bezirken mit großen Unterkünften ist "
                          "der Wert deshalb hoch.",
              legend_note=f"Anteil der Einwohner*innen, {MON_AS_OF}", section="situation"),
    Indicator("SOC_UNEMPLOYED", "Arbeitslosendichte", "Soziale Lage", "%", BOTH, MON + ", Tabelle 12", MON_AS_OF,
              "Arbeitslose ÷ Einwohner*innen von 15 bis unter 65 Jahren. Für Stadtteile mittelt die Karte die Bezirke, "
              "gewichtet nach diesen Einwohner*innen.", "purple", rule=MON_RULE,
              legend_note=f"Arbeitslose je Einwohner*in von 15 bis 64 Jahren, {MON_AS_OF}", section="situation"),
    Indicator("SOC_INDEX", "Benachteiligungsindex", "Soziale Lage", "", ("district",), MON + ", Tabelle 28", MON_AS_OF,
              "Das Monitoring bildet einen Rang von 1 bis 114 aus Arbeitslosendichte, Mindestsicherung und Wohnfläche "
              "je Person. Je höher der Rang, desto stärker ist das Gebiet benachteiligt.", "purple", rule=MON_RULE,
              legend_note="Rang von 1 bis 114. Je höher der Rang, desto stärker ist das Gebiet benachteiligt.",
              decimals=0, rank=114, section="situation"),
]
