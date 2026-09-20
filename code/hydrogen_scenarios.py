# -*- coding: utf-8 -*-
"""
Hydrogen-supply scenarios for the three utilization pathways.

The base case charges hydrogen at 5.4459 kg-CO2 per kg-H2, which is a
bottom-up build-up for DEDICATED photovoltaic electricity:

    (13.8 g/MJ compression, storage and transport + 10 g/MJ equipment) x 120 MJ/kg
    + 48.5 kWh/kg x 0.0534 kg-CO2/kWh  =  5.4459

The electricity term is therefore 53.4 g-CO2/kWh, while the capture, compression
and conversion electricity of the SAME system is charged at the Japanese grid
average of 423 g-CO2/kWh.  That is an eight-fold difference between two electricity
flows inside one system boundary, and it is the single assumption on which the
utilization results turn.  This module makes the dependence explicit.

Every net result is exactly linear in the hydrogen factor, because the hydrogen
burden enters Eq. 2 as H_p x s_cap x (h2 / h2_base) and nothing else depends on it:

    net_p(h2) = net_p(base) + M_H2,p x (h2 - h2_base)

so the scenarios below are exact, not interpolated.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import carbon_model as CB

LED = CB.LED
H2_BASE = LED['H2_FACTOR']['now']            # 5.4459 kg-CO2 per kg-H2
H2_2050 = LED['H2_FACTOR']['y2050']          # 3.535
MASS_H2 = LED['H2_MASS']                     # t-H2 per year, per pathway
KWH_PER_KG = 48.5                            # electrolysis energy, SI Section S2
NON_ELEC = H2_BASE - KWH_PER_KG * 0.0534     # compression, storage, transport, plant
UTIL = ['U1', 'U2a', 'U2b']


def net_at(p, h2):
    """Static national result of pathway p if hydrogen cost h2 kg-CO2 per kg-H2."""
    return CB.NET_NAT[p] + MASS_H2.get(p, 0.0) * (h2 - H2_BASE)


def from_electricity(ef_kg_per_kwh):
    """Hydrogen factor implied by electrolysis on electricity of this intensity,
    keeping the non-electric part (compression, storage, transport, plant) fixed."""
    return NON_ELEC + KWH_PER_KG * ef_kg_per_kwh


def break_even(p, target=0.0, lo=0.1, hi=60.0):
    """Hydrogen factor at which pathway p reaches `target` t-CO2 per year."""
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if net_at(p, mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# Each entry is (name, hydrogen factor, electrolytic?, note).  The implied
# electricity factor is reported ONLY for electrolytic scenarios: for a supply that
# is not electrolysis the inversion h2 -> EF has no physical meaning, because the
# non-electric part of the build-up (compression, storage, transport, plant) is not
# the same and the burden is not an electricity burden at all.
SCENARIOS = [
    ('Dedicated photovoltaic electricity (base case)', H2_BASE, True,
     'bottom-up build-up of SI Section S2; electricity at 0.0534 kg-CO2 per kWh'),
    ('Photovoltaic electricity, 2050 background', H2_2050, True,
     'same build-up with the 2050 photovoltaic factor 0.014 kg-CO2 per kWh'),
    ('Illustrative low hydrogen factor', 3.0, False,
     'round value, not a sourced inventory: a deliberately generous supply, below '
     'anything the present study can substantiate, used to show how far the result '
     'can move in the favourable direction'),
    ('Illustrative high hydrogen factor', 9.0, False,
     'round value, not a sourced inventory: an unfavourable supply used as the '
     'mirror image of the previous line'),
    ('Electrolysis on the Japanese grid average', from_electricity(CB.EF_NAT), True,
     'same electrolysis energy charged at the grid factor used for every other '
     'electricity flow in this study'),
]


def main():
    out = os.path.join(HERE, 'outputs', 'Hydrogen_supply_scenarios.csv')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rows = []
    for name, h2, electrolytic, note in SCENARIOS:
        rows.append([name, f'{h2:.4f}',
                     f'{(h2 - NON_ELEC) / KWH_PER_KG:.4f}' if electrolytic
                     else 'n/a (not electrolytic)']
                    + [f'{net_at(p, h2):.4f}' for p in UTIL]
                    + [f'{net_at(p, h2) - CB.NET_NAT["S0"]:.4f}' for p in UTIL]
                    + [note])
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['scenario', 'hydrogen_factor_kgCO2_per_kgH2',
                    'implied_electricity_kgCO2_per_kWh']
                   + [f'{p}_net_tCO2_per_y' for p in UTIL]
                   + [f'{p}_minus_reference_tCO2_per_y' for p in UTIL]
                   + ['note'])
        w.writerows(rows)
    print(f'  wrote {out} ({len(rows)} rows)')

    print('\nHydrogen demand implied by the base case')
    for p in UTIL:
        gwh = MASS_H2[p] * 1000 * KWH_PER_KG / 1e6
        print(f'  {p:<4}{MASS_H2[p]:>10,.0f} t-H2/y   {gwh:>7,.0f} GWh/y'
              f'   ({gwh / (CB.EXP_NOCC / 1000):>5,.1f} x the plant baseline export)')

    print('\nStatic national result, t-CO2 per year (reference plant '
          f'{CB.NET_NAT["S0"]:,.0f})')
    print(f'{"scenario":<48}{"h2":>7}' + ''.join(f'{p:>12}' for p in UTIL))
    for name, h2, _e, _n in SCENARIOS:
        print(f'{name:<48}{h2:>7.2f}'
              + ''.join(f'{net_at(p, h2):>12,.0f}' for p in UTIL))

    # The Monte Carlo multiplies the base factor by a lognormal with GSD 1.20, so the
    # sampled 95 % range of the factor itself is H2_BASE x 1.20 ** (-1.96, +1.96).
    lo, hi = H2_BASE * 1.20 ** -1.96, H2_BASE * 1.20 ** 1.96
    print(f'\nThresholds on the hydrogen factor (kg-CO2 per kg-H2); the Monte Carlo '
          f'samples the factor over a 95 % range of {lo:.2f} to {hi:.2f}')
    inside = []
    for p in UTIL:
        for label, th in (('net-negative', break_even(p)),
                          ('better than the reference',
                           break_even(p, CB.NET_NAT['S0']))):
            within = lo < th < hi
            inside.append((p, label, th)) if within else None
            print(f'  {p:<4}{label:<26}below {th:>6.2f}   '
                  f'{"INSIDE the sampled range" if within else "outside"}')
    print(f'  -> {len(inside)} of {2 * len(UTIL)} thresholds lie inside the sampled '
          f'range:', ', '.join(f'{p} {lab} ({th:.2f})' for p, lab, th in inside)
          or 'none')
    print('     so those two switches actually occur in the ensemble; the draw-level '
          'frequencies are reported in MonteCarlo_summary_AB.csv')


if __name__ == '__main__':
    main()
