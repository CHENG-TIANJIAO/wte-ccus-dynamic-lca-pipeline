# -*- coding: utf-8 -*-
"""
Regional evaluation on the 2050 background.

The 2025 regional layer (regions/regional_model.py) varies two measured drivers: the
region's waste carbon and its official grid emission factor.  This module repeats
that evaluation on the 2050 background, where each driver has its own scenario:

  grid    two published regionalizations of the national 2050 factor, both already
          tabulated per region in regions/region_waste_carbon.csv --
            'proportional' keeps each region's present ratio to the national mean;
            'convergence'  moves every region to the national 2050 value.
  waste   ONE common trajectory, applied to every region: the national 2050 anchor
          (F50, T50 of scenario_decomposition.py) scaled onto each region's own
          measured 2025 carbon, i.e. F_r,2050 = F_r x F50/F_nat and likewise for T.
          This is an assumption, and it is the only way to regionalize the waste
          scenario with the data in hand: the 2050 composition is a national
          scenario and there is no regional projection of it.  It means the fossil
          share of the waste is the same in every region in 2050, so the regional
          spread below comes from the grid alone.

Output: outputs/regional_2050.csv, one row per pathway and region, plus the count
of regions in which each intervention beats its own regional reference.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'regions'))
import carbon_model as CB
import scenario_decomposition as SD

SCEN = {'proportional': 'grid_EF_2050_proportional',
        'convergence': 'grid_EF_2050_convergence'}
# R1b (D12) / R1e: same regional-table switch as regional_model.py (default W2a, R1e rebuild,
# tonnage-weighted; REGION_WEIGHTING=W1 or =unweighted select the sensitivities)
REGION_FILES = {'W2a': 'region_waste_carbon.csv',
                'unweighted': 'region_waste_carbon_unweighted.csv',
                'W1': 'region_waste_carbon_W1.csv'}      # R1e sensitivity: facility tonnage-weighted
WEIGHTING = os.environ.get('REGION_WEIGHTING', 'W2a')


def load(weighting=None):
    w = weighting or WEIGHTING
    assert w in REGION_FILES, f'REGION_WEIGHTING must be one of {list(REGION_FILES)}'
    # in the development tree the regional data sits in regions/; in the shipped
    # archive it sits beside the code
    for p in (os.path.join(HERE, REGION_FILES[w]),
              os.path.join(HERE, 'regions', REGION_FILES[w])):
        if os.path.exists(p):
            break
    rows = list(csv.DictReader(open(p, encoding='utf-8-sig')))
    fos = [float(r['CO2_fossil_t_per_t_dry']) for r in rows]
    tot = [float(r['CO2_total_t_per_t_dry']) for r in rows]
    fm, tm = sum(fos) / len(fos), sum(tot) / len(tot)
    out = {}
    for r in rows:
        out[r['region']] = dict(
            F25=CB.F_NAT * float(r['CO2_fossil_t_per_t_dry']) / fm,
            T25=CB.T_NAT * float(r['CO2_total_t_per_t_dry']) / tm,
            **{k: float(r[v]) * 1000.0 for k, v in SCEN.items()})
    return out


def main():
    regs = load()
    names = sorted(regs)
    kF, kT = SD.F50 / CB.F_NAT, SD.T50 / CB.T_NAT
    rows = []
    counts = {}
    for scen in SCEN:
        M = {}
        for p in CB.ORDER:
            M[p] = {n: CB.net(p, regs[n]['F25'] * kF, regs[n]['T25'] * kT,
                              regs[n][scen]) for n in names}
        for p in CB.ORDER:
            for n in names:
                rows.append([scen, p, n, f'{regs[n][scen]:.6f}',
                             f'{regs[n]["F25"] * kF:.4f}',
                             f'{regs[n]["T25"] * kT:.4f}',
                             f'{M[p][n]:.4f}', f'{M[p][n] - M["S0"][n]:.4f}'])
        counts[scen] = {p: sum(1 for n in names if M[p][n] < M['S0'][n])
                        for p in CB.ORDER if p != 'S0'}

    out = os.path.join(HERE, 'outputs', 'regional_2050.csv')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['grid_scenario', 'pathway', 'region', 'EF_r_2050_tCO2_per_MWh',
                    'F_r_2050_tCO2_per_y', 'T_r_2050_tCO2_per_y',
                    'net_tCO2_per_y', 'difference_from_regional_reference_tCO2_per_y'])
        w.writerows(rows)
    print(f'  wrote {out} ({len(rows)} rows)')
    print(f'  regional table: {REGION_FILES[WEIGHTING]} (REGION_WEIGHTING={WEIGHTING})')
    print(f'  2050 waste anchor: F50 {SD.F50:,.0f}  T50 {SD.T50:,.0f} '
          f'(x{kF:.4f} and x{kT:.4f} on every region)')
    print('\n  regions (of 10) in which the pathway beats its own 2050 reference')
    print(f'  {"path":<5}' + ''.join(f'{s:>16}' for s in SCEN))
    for p in CB.ORDER:
        if p == 'S0':
            continue
        print(f'  {p:<5}' + ''.join(f'{counts[s][p]:>16}' for s in SCEN))


if __name__ == '__main__':
    main()
