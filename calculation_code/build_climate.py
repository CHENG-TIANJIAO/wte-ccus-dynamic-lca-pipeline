# -*- coding: utf-8 -*-
"""
Apply the physical climate layer to the thirteen pathways and compare rankings:
  (i)   static net LCCO2 (v4 model)
  (ii)  physical cumulative radiative forcing at fixed endpoints (2030/2050/2100/2125)
  (iii) normative discounted emissions (policy time preference, reported separately)
National reference plant, convention A, 2025 grid.

v4 dynamic-layer rules (uniform across pathways):
  - within-year releases are charged in the STATIC (so U1 and U2a fuel combustion
    and U2b's non-retained 20 % are day-0 quantities);
  - only genuinely delayed releases enter the dynamic layer;
  - the deferred quantity of the feedstock route is the NET of the two worlds at
    the product lifetime: the intervention releases f x 0.80 x M x stoich while
    the counterfactual would have released the full 0.80 x M x stoich, so the
    deferred quantity is a net CREDIT.  Durability cancels between intervention
    and counterfactual because the displaced fossil methanol has the same
    downstream fate; what is postponed is the benefit of the carbon-origin switch;
  - substitution credits are static day-0 quantities for every pathway; the timing
    of displaced processes is not modelled (declared limitation).

Bookkeeping: for a pathway with a deferred pool S the series is built with
n0_series = static + S and dE(0) = n0_series - S, so that dE(0) equals the static
and the pool is released on top of it; sum(dE) = static + S by construction.
"""
import numpy as np
from climate_response import emission_series, crf, A_CO2, KG_PER_T
import carbon_model as CB

T = 100
START = 2025
HORIZONS = {'2030': 5, '2050': 25, '2100': 75, '2125': 100}

NET = {p: CB.net(p, CB.F_NAT, CB.T_NAT, CB.EF_NAT) for p in CB.ORDER}
_U2B = CB.LED['POOLS']['U2b']
# NET deferred quantity of the feedstock route: the intervention releases
# f x 0.80 x M x stoich at the product lifetime while the counterfactual would
# have released the full 0.80 x M x stoich, so the deferred quantity is a net
# CREDIT (negative). Durability itself cancels between the two worlds; what is
# postponed is the benefit of the carbon-origin switch.
S_U2B = _U2B['deferred_net']             # = -(1 - f) x 0.80 x M x stoich
# Retention: eta_MTO = 0.80 (Tian et al. 2015); eta_CR = 0.45 (pyrolysis naphtha/BTX)
ETA_CR = 0.45

P = {
 'S0':  dict(n0=NET['S0'], S=0, mode='none'),
 'M1':  dict(n0=NET['M1'], S=0, mode='none'),
 'M2':  dict(n0=NET['M2'], S=0, mode='none'),
 'M3':  dict(n0=NET['M3'], S=0, mode='none'),
 'M4':  dict(n0=NET['M4'], S=0, mode='none'),
 'G1':  dict(n0=NET['G1'], S=0, mode='none'),
 'G2':  dict(n0=NET['G2'], S=0, mode='none'),
 'U1':  dict(n0=NET['U1'], S=0, mode='pulse'),
 'U2a': dict(n0=NET['U2a'], S=0, mode='pulse'),
 'U2b': dict(n0=NET['U2b'] + S_U2B, S=S_U2B, mode='weibull',
             tau50=_U2B['tau50'], k=_U2B['k']),
}

# ---- Chemical recycling: two bounding treatments of the diverted plastic carbon ----
# The source inventory reports a credit of -17,678 t-CO2/y labelled "CO2 sequestered"
# for the plastic diverted from incineration. Its validity depends on the fate of the
# pyrolysis product, which the source does not resolve, so both bounds are carried:
#   A "substitution credited"  the diverted carbon is credited as displacing virgin
#      fossil feedstock/fuel; the credit stays in the static balance and no delayed
#      release is modelled (this is the conventional treatment).
#   B "carbon tracked"         the credit is removed and the carbon is followed
#      explicitly: released on use for fuels, retained (eta_CR = 0.45) for polymers.
# The diverted plastic carbon is entirely fossil, so no share factor applies here.
R_TREATMENT = {
 'A': {'R1': dict(n0=NET['R1'], S=0, mode='pulse'),
       'R2': dict(n0=NET['R2'], S=0, mode='pulse'),
       'R3': dict(n0=NET['R3'], S=0, mode='pulse')},
 'B': {'R1': dict(n0=NET['R1'] + CB.D_P['R1'], S=0, mode='pulse'),
       'R2': dict(n0=NET['R2'] + CB.D_P['R2'], S=ETA_CR * CB.D_P['R2'],
                  mode='weibull', tau50=10, k=2.0),
       'R3': dict(n0=NET['R3'] + CB.D_P['R3'], S=ETA_CR * CB.D_P['R3'],
                  mode='weibull', tau50=15, k=2.0)},
}
import os as _os
_t = _os.environ.get('R_CASE', 'B')
P.update(R_TREATMENT[_t])
ORDER = CB.ORDER
NAME = {'S0': 'Reference WtE', 'M1': 'Mineral. olivine', 'M2': 'Mineral. serpentine',
 'M3': 'Mineral. carbide slag', 'M4': 'Mineral. steel slag', 'G1': 'Geol. CCS 1200 m',
 'G2': 'Geol. CCS 3000 m', 'U1': 'CCU methane', 'U2a': 'CCU MeOH-fuel',
 'U2b': 'CCU MeOH-chemicals', 'R1': 'CR oil-fuel', 'R2': 'CR naphtha',
 'R3': 'CR HVC'}

series, CRF = {}, {}
for p in ORDER:
    d = P[p]
    dE = emission_series(d['n0'], d['S'], T, d['mode'],
                         d.get('tau50'), d.get('k', 2.0))
    series[p] = dE
    CRF[p] = crf(dE)

static = {p: NET[p] + (CB.D_P[p] if _t == 'B' and p in CB.D_P else 0.0)
          for p in ORDER}

if __name__ == '__main__':
    print('Physical climate metric: cumulative radiative forcing (1e-12 W m-2 y)')
    print('for one year of plant operation, convention A, 2025 grid, v4 model\n')
    hdr = ''.join(f'{h:>12}' for h in HORIZONS)
    print(f"{'path':<5}{'static':>10}" + hdr + '   name')
    for p in ORDER:
        row = ''.join(f'{CRF[p][H]*1e12:>12.2f}' for H in HORIZONS.values())
        print(f'{p:<5}{static[p]:>10,.0f}' + row + f'   {NAME[p]}')

    print('\nRanking comparison (1 = lowest / best):')
    print(f"{'path':<5}{'static':>8}" + ''.join(f'{h:>8}' for h in HORIZONS))
    rank_static = {p: i + 1 for i, p in enumerate(sorted(ORDER, key=lambda q: static[q]))}
    rank_h = {}
    for h, H in HORIZONS.items():
        rank_h[h] = {p: i + 1 for i, p in
                     enumerate(sorted(ORDER, key=lambda q: CRF[q][H]))}
    for p in ORDER:
        marks = ''.join(f"{rank_h[h][p]:>8}" for h in HORIZONS)
        flag = ('  <- reorders' if len({rank_static[p]} |
                {rank_h[h][p] for h in HORIZONS}) > 1 else '')
        print(f'{p:<5}{rank_static[p]:>8}' + marks + flag)

    print('\nU2a vs U2b (same plant, different product market and carbon fate):')
    print(f"  static: U2a {static['U2a']:>10,.0f}   U2b {static['U2b']:>10,.0f} t-CO2/y")
    for h, H in HORIZONS.items():
        a, b = CRF['U2a'][H] * 1e12, CRF['U2b'][H] * 1e12
        print(f'  {h}: U2a {a:>9.2f}   U2b {b:>9.2f}   difference {b - a:+9.2f}')
    print(f"  U2b defers a NET CREDIT of {abs(S_U2B):,.0f} t-CO2 to the product "
          f"lifetime (it is not stored fossil carbon: the displaced fossil methanol "
          f"would have been burnt in the counterfactual too, so only the timing "
          f"differs): series total {series['U2b'].sum():,.0f} = operating-year "
          f"static {static['U2b']:,.0f} + deferred credit {S_U2B:,.0f}")
    assert abs(series['U2b'].sum() - (static['U2b'] + S_U2B)) < 1e-6
    assert abs(series['U2b'][0] - static['U2b']) < 1e-6

    print('\nNormative layer, reported separately (discounted emissions, t-CO2):')
    print(f"{'path':<5}" + ''.join(f'{f"r={r:.1%}":>12}'
                                   for r in (0.0, 0.02, 0.03, 0.035)))
    for p in ('U2a', 'U2b', 'R2', 'R3'):
        vals = []
        for r in (0.0, 0.02, 0.03, 0.035):
            w = np.exp(-r * np.arange(T + 1))
            vals.append(float((series[p] * w).sum()))
        print(f'{p:<5}' + ''.join(f'{v:>12,.0f}' for v in vals))
