"""The figures of the survey Leben in Frankfurt 2025."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SURVEY_AREAS = {1: "Innenstadt I", 2: "Innenstadt II", 3: "Innenstadt III", 4: "Bornheim/Ostend", 5: "Süd",
                6: "West", 7: "Mitte-West", 8: "Nord-West", 9: "Mitte-Nord", 10: "Nord-Ost", 11: "Ost",
                12: "Kalbach/Riedberg", 13: "Nord"}
# Classes of the maps in the report "Leben in Frankfurt 2025" (Frankfurter Umfragen 5, April 2026), as the legend
# prints them, and the printed city value. The map shows them as they are (README).
FIGURES: dict[str, dict] = {
    "LIF_RENT_BURDEN_RATIO": {  # Abb. 4.5, p. 27; city: "Die Hälfte … mindestens 29 Prozent" (p. 27)
        "city": 29,
        "classes": {(26, 28): ("Innenstadt III", "Innenstadt II", "Mitte-Nord"),
                    (29, 29): ("Innenstadt I", "Bornheim/Ostend", "Süd"),
                    (30, 30): ("Mitte-West", "Nord", "Ost"),
                    (31, 33): ("West", "Nord-West", "Kalbach/Riedberg", "Nord-Ost")}},
    "LIF_ATTACHMENT": {  # Abb. 4.11, p. 31; city: "62 Prozent würden das eigene Wohnviertel … vermissen" (p. 30)
        "city": 62,
        "classes": {(51, 61): ("Innenstadt I", "West", "Nord-Ost"),
                    (62, 63): ("Nord", "Nord-West", "Mitte-Nord"),
                    (64, 70): ("Kalbach/Riedberg", "Mitte-West", "Ost", "Süd"),
                    (71, 82): ("Innenstadt II", "Innenstadt III", "Bornheim/Ostend")}},
}
# Page in the PDF (printed page + 3, counted from 0) and the areas the legend names as minimum and maximum
PRINTED_EXTREMES = {"LIF_RENT_BURDEN_RATIO": (27 + 3, "Innenstadt III", "Nord-Ost"),
                    "LIF_ATTACHMENT": (31 + 3, "Innenstadt I", "Innenstadt III")}
# Printed city median of the rent burden per report: page in the PDF (printed page + 3, counted from 0), median
PRINTED_CITY_BURDEN = {2025: (27 + 3, 29), 2024: (22 + 3, 29)}

MISSING = -42  # "keine Angabe" in every column of the microdata


def _steps(first_high: int, last_low: int, step: int, count: int) -> dict[int, tuple[float, float | None]]:
    """Classes of equal width: code 1 is "unter first_high", then `count` steps, the last class is open."""
    classes: dict[int, tuple[float, float | None]] = {1: (0, first_high)}
    for code in range(2, count + 2):
        low = first_high + (code - 2) * step
        classes[code] = (low, low + step)
    classes[count + 2] = (last_low, None)
    return classes


# Class bounds in euros per code, codebook 2025 pp. 103-104 and 277 (low, high; high None for an open class)
RENT_CLASSES = _steps(400, 1400, 100, 10)  # WOkami_a: unter 400, 400-500 ... 1300-1400, 1400 und mehr
COSTS_CLASSES = _steps(100, 400, 50, 6)  # WObtrko_a: unter 100, 100-150 ... 350-400, 400 und mehr
INCOME_CLASSES = _steps(1000, 5000, 1000, 4)  # XDhhnek_a: unter 1.000, 1.000-2.000 ... 4.000-5.000, 5.000 und mehr
PERSONS = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}  # XDhhgrabs_a: 5 = "5 und mehr"
CHILDREN = {1: 0, 2: 1, 3: 2, 4: 3}  # XDhhgr017_a: 4 = "3 und mehr"
HOUSEHOLD_FORMS = {1: "single", 2: "couple", 3: "couple_children", 4: "single_parent"}  # XDhhform_a
TENANCY = {1: True, 2: False}  # WOmieig_a: 1 zur Miete, 2 Eigentum


def _decode(raw: pd.Series, table: dict, column: str) -> pd.Series:
    """Map the codes of one column; -42 gives NaN or None, any other unknown code stops the read."""
    unknown = sorted(set(raw.unique()) - set(table) - {MISSING})
    if unknown:
        raise ValueError(f"Unknown code {unknown} in column {column}")
    return raw.map(table)


def _bounds(raw: pd.Series, classes: dict, column: str) -> tuple[pd.Series, pd.Series]:
    low = _decode(raw, {code: bounds[0] for code, bounds in classes.items()}, column).astype(float)
    high = _decode(raw, {code: np.nan if bounds[1] is None else bounds[1] for code, bounds in classes.items()},
                   column).astype(float)
    return low, high


def read_microdata(path: Path, year: int) -> pd.DataFrame:
    """One row per respondent of Leben in Frankfurt with the household and rent classes as euro bounds."""
    columns = ["Umfragebezirk", "weight", "WOmieig_a", "WOkami_a", "WObtrko_a", "XDhhnek_a", "XDhhgrabs_a",
               "XDhhgr017_a", "XDhhform_a"]
    raw = pd.read_csv(path, sep=";", encoding="utf-8-sig", decimal=",", usecols=columns)
    area = raw["Umfragebezirk"]
    if not area.isin(SURVEY_AREAS).all():
        raise ValueError(f"Unknown code {sorted(set(area) - set(SURVEY_AREAS))} in column Umfragebezirk")
    rent_low, rent_high = _bounds(raw["WOkami_a"], RENT_CLASSES, "WOkami_a")
    costs_low, costs_high = _bounds(raw["WObtrko_a"], COSTS_CLASSES, "WObtrko_a")
    income_low, income_high = _bounds(raw["XDhhnek_a"], INCOME_CLASSES, "XDhhnek_a")
    tenancy = _decode(raw["WOmieig_a"], TENANCY, "WOmieig_a")
    household_form = _decode(raw["XDhhform_a"], HOUSEHOLD_FORMS, "XDhhform_a")
    return pd.DataFrame({
        "year": year, "survey_area": area.map(SURVEY_AREAS), "weight": raw["weight"].astype(float),
        "tenant": tenancy.eq(True),
        "rent_low": rent_low, "rent_high": rent_high, "costs_low": costs_low, "costs_high": costs_high,
        "income_low": income_low, "income_high": income_high,
        "persons": _decode(raw["XDhhgrabs_a"], PERSONS, "XDhhgrabs_a").astype(float),
        "children": _decode(raw["XDhhgr017_a"], CHILDREN, "XDhhgr017_a").astype(float),
        "household_form": household_form.astype(object).where(household_form.notna(), None)})
