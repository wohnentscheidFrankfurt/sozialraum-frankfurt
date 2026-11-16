"""Checks of the city values against the Zensus tables: vacancy (4000W-2002, WHG009 and the 1-km grid), Mieteranteil
(4000W-0001) and rent (4000W-0004). Pure module."""
from __future__ import annotations

from pipeline.shared.core.checks import OK, WARN, Check, check_tolerance, number, thousands


def check_vacancy_4000w(city_value: float, table: dict[str, int], limit: float = 1.0) -> Check:
    expected = 100 * table["vacant"] / table["occupied_and_vacant"]
    status = OK if abs(city_value - expected) <= limit else WARN
    return Check("Vacancy: city value against 4000W", status,
                 f"grid {number(city_value)} %, table 4000W {number(expected)} % ({thousands(table['vacant'])} of "
                 f"{thousands(table['occupied_and_vacant'])} dwellings), allowed ± {limit:g} "
                 f"{'point' if limit == 1 else 'points'}. The grid counts only residential buildings without "
                 "dormitories, and \"–\" is filled from the 1-km grid")


def check_vacancy_count(city_count: float, table: dict[str, int], rel: float = 0.10) -> Check:
    """The summed vacant dwellings of the grid against the table count. The grid holds fewer dwellings than the table
    (residential buildings without dormitories), so the build lies about 7 % below (README)."""
    return check_tolerance("Vacancy: city count against 4000W", city_count, table["vacant"], rel=rel, on_failure=WARN)


def check_vacancy_city(city_value: float, official: float, limit: float = 0.15) -> Check:
    """The filled city vacancy against the official 3.1 % (4000W-0001, WHG009$QMU, one decimal). The limit is the
    rounding of the table (0.05) plus the weights (all dwellings against residential buildings without dormitories)."""
    status = OK if abs(city_value - official) <= limit else WARN
    return Check("Vacancy: city value against WHG009", status,
                 f"grid {number(city_value)} %, table WHG009 {number(official)} %, allowed ± {limit:g} points")


def check_vacancy_km(city: dict, reference: dict[str, float], limit: float = 0.2) -> Check:
    """Both vacancy rates against the 1-km grid of the same Zensus (185 cells with dwellings wholly inside Frankfurt
    and BBOX_3035). The filled rates (`fill_rate`) lie within 0.05 points of it; the limit 0.2 leaves room for
    the edge cells and the rest that was negative in a few 1 km cells.
    This compares with the grid the fill itself uses, so it guards the formula, not the data. The independent check is
    WHG009 (`check_vacancy_city`)."""
    pairs = {"HOU_VACANT_MARKET": reference["vacancy_market_km_2022"],
             "HOU_VACANT_ALL": reference["vacancy_all_km_2022"]}
    off = [k for k, v in pairs.items() if abs(city[k] - v) > limit]
    return Check("Vacancy: city values against the 1-km grid", WARN if off else OK,
                 "; ".join(f"{k} {number(city[k])} % against {number(v)} %" for k, v in pairs.items())
                 + f", allowed ± {limit:g} points")


def check_city_tables(city: dict, owner_rate: float, rent: float, rel: float = 0.02) -> list[Check]:
    """The city values of the map against the Zensus tables for Frankfurt (2 % relative; README, Checks)."""
    return [check_tolerance("Housing: Mieteranteil against 4000W-0001", city["HOU_RENTERS"], 100 - owner_rate, rel=rel),
            check_tolerance("Housing: Miete im Bestand against 4000W-0004", city["HOU_RENT"], rent, rel=rel)]
