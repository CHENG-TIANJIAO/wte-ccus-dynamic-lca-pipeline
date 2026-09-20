# -*- coding: utf-8 -*-
"""
Decomposition of the 2025 -> 2050 change into its individual background drivers,
v4 model.

Drivers
  G  grid emission factor            0.423 -> 0.07 t-CO2/MWh (RITE 2050 CN scenario)
  W  waste fossil / total carbon     26,475 / 74,621 -> 10,416 / 59,388 t-CO2/y
     (2050 values are the source's own rounded per-tonne factors 0.124 / 0.707
      x 84,000 t; the exact per-fraction recomputation gives 10,472, +0.53 %,
      disclosed in the SI)
  H  hydrogen emission factor        5.4459 -> 3.535 t-CO2/t-H2 (same bottom-up
     formula, 2050 PV electricity 0.014 kg-CO2/kWh; utilization pathways only)

In v4 the hydrogen scale is consistent with the model base: the model's H2 terms
are built on 5.4459, and the 2050 branch of the source workbook itself uses 3.535.
(v3 scaled its 6.1179-based terms by 3.54/5.45, mixing the two bases.)

Because the drivers interact, this module prints each single-driver effect both as
a first step from the present baseline and as a last step onto the full 2050 case,
which bracket the interaction.  The values reported in the manuscript are the EXACT
Shapley values over all six orderings of the three drivers, computed in
export_files.py and written to Shapley_decomposition_audit.csv with the closure
discrepancy reported for every pathway.
"""
import carbon_model as CB

G25, G50 = CB.EF_NAT, 0.07     # 0.423 official national average / RITE 2050
F25, T25 = CB.F_NAT, CB.T_NAT
F50, T50 = 10416.0, 59388.0
H25 = CB.LED['H2_FACTOR']['now']          # 5.4459
H50 = CB.LED['H2_FACTOR']['y2050']        # 3.535
H2_SCALE = H50 / H25


def net(p, grid50=False, waste50=False, h2_50=False):
    """Throughput-scaled model; the hydrogen burden scales with the captured stream,
    so changing the waste carbon and the hydrogen factor together is not additive."""
    EF = G50 if grid50 else G25
    F, T = (F50, T50) if waste50 else (F25, T25)
    v = CB.net(p, F, T, EF)
    if h2_50 and p in CB.H2:
        v += CB.H2[p] * CB.s_cap(T, CB.CR) * (H2_SCALE - 1.0)
    return v


def main():
    print('Decomposition of the 2025 to 2050 change (t-CO2/y), v4 model\n')
    print(f"{'path':<5}{'2025':>9}{'2050':>9}{'total':>9}"
          f"{'grid':>9}{'waste':>9}{'H2':>8}{'interact':>10}")
    rows = {}
    for p in CB.ORDER:
        base = net(p)
        full = net(p, True, True, True)
        g1 = net(p, grid50=True) - base
        w1 = net(p, waste50=True) - base
        h1 = net(p, h2_50=True) - base
        g2 = full - net(p, waste50=True, h2_50=True)
        w2 = full - net(p, grid50=True, h2_50=True)
        h2_ = full - net(p, grid50=True, waste50=True)
        g, w, h = (g1 + g2) / 2, (w1 + w2) / 2, (h1 + h2_) / 2
        inter = (full - base) - (g + w + h)
        rows[p] = dict(base=base, full=full, g=g, w=w, h=h, i=inter)
        print(f'{p:<5}{base:>9,.0f}{full:>9,.0f}{full-base:>9,.0f}'
              f'{g:>9,.0f}{w:>9,.0f}{h:>8,.0f}{inter:>10,.0f}')

    print('\nCapture-based pathways: do the two drivers act in the same direction?')
    for p in ('G1', 'G2', 'M1', 'U1', 'U2a'):
        r = rows[p]
        same = 'same' if r['g'] * r['w'] > 0 else 'OPPOSITE'
        dom = 'grid' if abs(r['g']) > abs(r['w']) else 'waste carbon'
        print(f"  {p:<5} grid {r['g']:>+8,.0f}   waste {r['w']:>+8,.0f}   "
              f"{same}; larger effect: {dom}")

    print('\nMitigation relative to the reference plant, 2025 vs full 2050:')
    print(f"{'path':<5}{'2025':>10}{'2050':>10}{'change':>10}")
    for p in CB.ORDER:
        if p == 'S0':
            continue
        d25 = rows[p]['base'] - rows['S0']['base']
        d50 = rows[p]['full'] - rows['S0']['full']
        print(f'{p:<5}{d25:>10,.0f}{d50:>10,.0f}{d50-d25:>10,.0f}')


if __name__ == '__main__':
    main()
