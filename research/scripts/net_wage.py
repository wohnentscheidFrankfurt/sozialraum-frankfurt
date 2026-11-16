"""Net monthly wage of a single full-time employee (research of warm rent and income, S1).

Steuerklasse I, no children (childless surcharge of the care insurance), no church tax, statutory health insurance
with the average Zusatzbeitrag. The wage tax follows the Programmablaufplan (PAP) of the Bundesministerium der
Finanzen for the year: annual wage = 12 × monthly wage, minus Werbungskosten-Pauschbetrag, Sonderausgaben-Pauschbetrag
(36 €) and Vorsorgepauschale (§ 39b EStG), tariff of § 32a EStG, Soli with Freigrenze and Milderungszone (§ 4
SolZG). The rules hold on the survey day of the Mietspiegel: June 2017, 1.7.2021, 1.7.2023, 1.7.2025.

Sources of the values (checked against the PAP XML of 2025, https://www.bmf-steuerrechner.de/javax.faces.resource/
daten/xmls/Lohnsteuer2025.xml.xhtml, lines 577–612, 1001–1049, 1121–1125, 1367–1391; older years against the
calculator of the BMF, see BMF_CHECK):
- tariff: § 32a EStG in the version of the year (2017: Gesetz vom 20.12.2016; 2021: Zweites
  Familienentlastungsgesetz; 2023: Inflationsausgleichsgesetz; 2025: Steuerfortentwicklungsgesetz);
- Soli: § 3 and § 4 SolZG 1995 (Freigrenze 972 € and 20 % until 2020; from 2021 the raised Freigrenze and 11.9 %);
- ceilings: Sozialversicherungs-Rechengrößenverordnung 2017, 2021, 2023, 2025 (pension insurance West until 2024);
- average Zusatzbeitrag: Bekanntmachung des BMG for the year; paid by the employee alone until 2018, half from 2019;
- care insurance: § 55 SGB XI (rates from 1.7.2023 by the Pflegeunterstützungs- und -entlastungsgesetz);
- Mindestlohn: Mindestlohnanpassungsverordnung of 2016 (8.84 € from 1.1.2017), Dritte (9.60 € from 1.7.2021),
  Mindestlohnerhöhungsgesetz (12.00 € from 1.10.2022), Vierte (12.82 € from 1.1.2025).

Call from the repo root:
    .venv/bin/python -I research/scripts/net_wage.py
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Tariff:
    gfb: float  # Grundfreibetrag
    z1: float  # upper end of the first progression zone
    a1: float  # (a1 · y + 1400) · y
    z2: float  # upper end of the second progression zone
    a2: float  # (a2 · z + 2397) · z + c2
    c2: float
    c3: float  # 0.42 · x − c3 up to 277,826 € (2025; the 45 % zone is out of reach here)


@dataclass(frozen=True)
class Rules:
    tariff: Tariff
    werbungskosten: float  # Arbeitnehmer-Pauschbetrag
    rv_share_vsp: float  # part of the pension contribution in the Vorsorgepauschale
    soli_free: float  # Freigrenze of the annual wage tax
    soli_slope: float  # Milderungszone
    rv: float  # employee rate, pension insurance
    av: float  # employee rate, unemployment insurance
    kv_zusatz: float  # average Zusatzbeitrag (whole rate)
    kv_zusatz_employee_alone: bool
    pv: float  # employee rate of the care insurance incl. the childless surcharge
    ceiling_rv: float  # €/month, also unemployment insurance
    ceiling_kv: float  # €/month, also care insurance


RULES = {
    2017: Rules(Tariff(8820, 13769, 1007.27, 54057, 223.76, 939.57, 8475.44), 1000, 0.68, 972, 0.20,
                0.0935, 0.015, 0.011, True, 0.01525, 6350, 4350),
    2021: Rules(Tariff(9744, 14753, 995.21, 57918, 208.85, 950.96, 9136.63), 1000, 0.84, 16956, 0.119,
                0.093, 0.012, 0.013, False, 0.01775, 7100, 4837.50),
    2023: Rules(Tariff(10908, 15999, 979.18, 62809, 192.59, 966.53, 9972.98), 1230, 1.00, 17543, 0.119,
                0.093, 0.013, 0.016, False, 0.023, 7300, 4987.50),
    2025: Rules(Tariff(12096, 17443, 932.30, 68480, 176.64, 1015.13, 10911.92), 1230, 1.00, 19950, 0.119,
                0.093, 0.013, 0.025, False, 0.024, 8050, 5512.50),
}
MINDESTLOHN = {2017: 8.84, 2021: 9.60, 2023: 12.00, 2025: 12.82}  # €/hour on the survey day
CEILING_RV = {year: rules.ceiling_rv for year, rules in RULES.items()}  # €/month on the survey day

# Wage tax and Soli per month from the Lohnsteuerrechner of the BMF (https://www.bmf-steuerrechner.de/bl/bl<year>/
# eingabeformbl<year>.xhtml; 2023: bl2023_01, „ab Juli“), read on 1.11.2026 by browser automation: monthly wage,
# Steuerklasse 1, no Kinderfreibetrag, no church tax, gesetzliche RV and KV, Zusatzbeitrag of RULES, care insurance
# „mit Zuschlag“. (year, person) -> (gross €/month, Lohnsteuer €/month, Soli €/month).
BMF_CHECK: dict[tuple[int, str], tuple[float, float, float]] = {
    (2021, "mindestlohn"): (1664.00, 93.66, 0.00), (2021, "median"): (4273.15, 735.08, 0.00),
    (2021, "ceiling"): (7100.00, 1759.83, 41.27),
    (2023, "mindestlohn"): (2080.00, 138.75, 0.00), (2023, "median"): (4594.05, 741.66, 0.00),
    (2023, "ceiling"): (7300.00, 1693.83, 27.59),
    (2025, "mindestlohn"): (2222.13, 138.25, 0.00), (2025, "median"): (5074.10, 817.16, 0.00),
    (2025, "ceiling"): (8050.00, 1866.33, 24.25),
}
# The Lohnsteuerrechner starts with 2021. For 2017 the Einkommensteuerrechner of the BMF (https://www.bmf-steuerrechner.de/
# ekst/eingabeformekst.xhtml, Berechnungsjahr 2017, alleinstehend) checks the tariff and the Soli on the taxable income
# of the three persons, read on 1.11.2026: taxable income € per year -> (Einkommensteuer, Soli) € per year. The
# Vorsorgepauschale of 2017 (68 % of the pension contribution) has no check of its own; its code is the one checked
# for 2021 (84 %).
EKST_CHECK_2017 = {14281: (1062.00, 18.00), 37894: (8024.00, 441.32), 65294: (18948.00, 1042.14)}
TOLERANCE = 0.01  # € per month: the own calculation matches the BMF to the cent


def full_time(hourly: float) -> float:
    """Monthly wage of 40 hours a week: hourly × 40 × 52 ÷ 12."""
    return hourly * 40 * 52 / 12


def kv_employee_rate(rules: Rules) -> float:
    """General rate 14.6 % half, plus the Zusatzbeitrag (whole until 2018, half from 2019)."""
    return 0.073 + (rules.kv_zusatz if rules.kv_zusatz_employee_alone else rules.kv_zusatz / 2)


def contributions(gross: float, year: int) -> float:
    """Employee contributions per month: pension, unemployment, health, care."""
    r = RULES[year]
    up_rv, up_kv = min(gross, r.ceiling_rv), min(gross, r.ceiling_kv)
    return up_rv * (r.rv + r.av) + up_kv * (kv_employee_rate(r) + r.pv)


def _tariff(x: float, t: Tariff) -> float:
    """Annual income tax of § 32a EStG for a taxable income x (whole euros), rounded down."""
    if x <= t.gfb:
        return 0.0
    if x <= t.z1:
        y = math.floor((x - t.gfb) / 10000 * 1e6) / 1e6
        return math.floor((t.a1 * y + 1400) * y)
    if x <= t.z2:
        z = math.floor((x - t.z1) / 10000 * 1e6) / 1e6
        return math.floor((t.a2 * z + 2397) * z + t.c2)
    return math.floor(0.42 * x - t.c3)


def _vorsorgepauschale(annual: float, r: Rules) -> float:
    """§ 39b EStG as the PAP computes it: pension part plus the larger of 12 % (at most 1,900 €) and health and care."""
    vsp1 = min(annual, 12 * r.ceiling_rv) * r.rv * r.rv_share_vsp
    vsp2 = min(0.12 * annual, 1900)
    # the PAP takes the reduced general rate (14.0 %, half 7.0 %) for the Vorsorgepauschale
    kv = 0.07 + (r.kv_zusatz if r.kv_zusatz_employee_alone else r.kv_zusatz / 2)
    vsp3 = min(annual, 12 * r.ceiling_kv) * (kv + r.pv)
    return math.ceil(vsp1 + max(vsp2, vsp3))


def income_tax(gross: float, year: int) -> tuple[float, float]:
    """Lohnsteuer and Soli per month, rounded down to cents like the PAP."""
    r = RULES[year]
    annual = 12 * gross
    zve = math.floor(annual - r.werbungskosten - 36 - _vorsorgepauschale(annual, r))
    tax = _tariff(max(zve, 0), r.tariff)
    soli = 0.0 if tax <= r.soli_free else min(0.055 * tax, (tax - r.soli_free) * r.soli_slope)
    return math.floor(tax / 12 * 100) / 100, math.floor(soli / 12 * 100) / 100


def net(gross: float, year: int) -> float:
    lohnsteuer, soli = income_tax(gross, year)
    return gross - contributions(gross, year) - lohnsteuer - soli


def gross_wages(median: dict[int, float]) -> dict[tuple[int, str], float]:
    """The twelve gross wages: three persons × four survey years."""
    out = {}
    for year in RULES:
        out[(year, "mindestlohn")] = full_time(MINDESTLOHN[year])
        out[(year, "median")] = median[year]
        out[(year, "ceiling")] = CEILING_RV[year]
    return out


def check_bmf() -> list[str]:
    """One line per BMF value; raises if a value is off by more than TOLERANCE."""
    lines = []
    for (year, person), (gross, lst, soli) in sorted(BMF_CHECK.items()):
        own_lst, own_soli = income_tax(gross, year)
        ok = abs(own_lst - lst) <= TOLERANCE and abs(own_soli - soli) <= TOLERANCE
        lines.append(f"{'OK ' if ok else 'BAD'} {year} {person:11s} gross {gross:9.2f}  Lohnsteuer own {own_lst:8.2f}"
                     f" BMF {lst:8.2f}  Soli own {own_soli:6.2f} BMF {soli:6.2f}")
        assert ok, lines[-1]
    return lines


def check_ekst_2017() -> list[str]:
    r = RULES[2017]
    lines = []
    for zve, (est, soli) in EKST_CHECK_2017.items():
        own = _tariff(zve, r.tariff)
        own_soli = 0.0 if own <= r.soli_free else min(0.055 * own, (own - r.soli_free) * r.soli_slope)
        ok = abs(own - est) < 0.005 and abs(round(own_soli, 2) - soli) < 0.005
        lines.append(f"{'OK ' if ok else 'BAD'} 2017 taxable {zve:6d}  ESt own {own:9.2f} BMF {est:9.2f}  "
                     f"Soli own {own_soli:8.2f} BMF {soli:8.2f}")
        assert ok, lines[-1]
    return lines


def main() -> None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from warm_rent_wage import wage  # noqa: E402
    median = {year: wage(year) for year in RULES}
    print("Inputs for https://www.bmf-steuerrechner.de (Lohnsteuer, monthly wage, Steuerklasse I, no church tax,")
    print("no children / kinderlos, gesetzlich versichert, Zusatzbeitrag as given)")
    print("year person       gross €/month  Zusatzbeitrag  own Lohnsteuer  own Soli  contributions  net")
    for (year, person), gross in gross_wages(median).items():
        lst, soli = income_tax(gross, year)
        print(f"{year} {person:11s} {gross:14.2f}  {100 * RULES[year].kv_zusatz:11.1f} %  {lst:14.2f}  {soli:8.2f}"
              f"  {contributions(gross, year):13.2f}  {net(gross, year):7.2f}")
    print(*check_bmf(), sep="\n")
    print(*check_ekst_2017(), sep="\n")


if __name__ == "__main__":
    main()
