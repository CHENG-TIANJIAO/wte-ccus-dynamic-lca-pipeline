# -*- coding: utf-8 -*-
"""Time-dimension sensitivity (revision R2; Supplementary Information Section S23, Tables S32 to S34).

Nothing in the model is changed. Every number comes from the functions of the model in ../code (carbon_model,
scenario_decomposition, build_climate), with the 2025 and 2050 background values that the Shapley decomposition
already uses. What is new is only where the functions are evaluated.

  A  Background trajectory. The three background drivers (grid factor, waste fossil and total carbon, hydrogen
     factor) are moved together from their 2025 to their 2050 values in annual steps. The path between the two
     published states is not known, so a linear path is used as an illustration, not a forecast; B makes the
     conclusions independent of that path.
  B  Path-free sweep. Grid factor and waste carbon are varied independently over the whole box spanned by their
     2025 and 2050 values (hydrogen at either value), so any trajectory between the two states lies inside it.
  C  Every assessment endpoint. Cumulative radiative forcing and competition ranks at every annual endpoint from
     2026 to 2125 (horizons 1 to 100 years), under both chemical-recycling treatments, instead of four endpoints.

Guards: the eight corner combinations of A/B reproduce code/outputs/Shapley_decomposition_audit.csv for all
thirteen pathways; the 2025 and 2050 ends of A reproduce value_2025 and value_2050; the break-even of storage on
the 2050 background reproduces 4,417 t-CO2 per year; the four published endpoints of C reproduce
code/outputs/Fig5_source_data.csv.
Writes, beside itself: R2_background_trajectory.csv, R2_grid_waste_sweep.csv, R2_endpoint_annual.csv,
R2_time_sensitivity_summary.md.
Run:  python analysis/R2_time_sensitivity.py
"""
import csv
import importlib
import os
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
AN = os.path.dirname(os.path.abspath(__file__))        # <root>/analysis
CODE = os.environ.get('R1_CODE') or os.path.normpath(os.path.join(AN, '..', 'code'))
OUT = AN
sys.path.insert(0, CODE)
os.chdir(CODE)                                   # the model modules resolve their inputs relative to themselves

import numpy as np                               # noqa: E402
import carbon_model as CB                        # noqa: E402
import scenario_decomposition as SD              # noqa: E402

ORDER = CB.ORDER
STORAGE = ('G1', 'G2')


def read_csv(name):
    with open(os.path.join(CODE, 'outputs', name), encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def net_at(p, g, w, h):
    """Net life-cycle CO2 (t-CO2/y) with each driver at fraction g, w, h of its way from 2025 to 2050.
    At g, w, h in {0, 1} this is exactly SD.net, which produced the published Shapley audit."""
    EF = SD.G25 + g * (SD.G50 - SD.G25)
    F = SD.F25 + w * (SD.F50 - SD.F25)
    T = SD.T25 + w * (SD.T50 - SD.T25)
    v = CB.net(p, F, T, EF)
    if p in CB.H2:
        H = SD.H25 + h * (SD.H50 - SD.H25)
        v += CB.H2[p] * CB.s_cap(T, CB.CR) * (H / SD.H25 - 1.0)
    return v


def ranks(values):
    """Standard competition ranking on unrounded values (1 = lowest net emission)."""
    srt = sorted(values.values())
    return {p: 1 + srt.index(v) for p, v in values.items()}


def guards():
    audit = {r['pathway']: r for r in read_csv('Shapley_decomposition_audit.csv')}
    worst = 0.0
    for p in ORDER:
        for g in (0, 1):
            for w in (0, 1):
                for h in (0, 1):
                    ref = float(audit[p][f'combo_g{g}_w{w}_h{h}'])
                    worst = max(worst, abs(net_at(p, g, w, h) - ref))
        worst = max(worst, abs(net_at(p, 0, 0, 0) - float(audit[p]['value_2025'])),
                    abs(net_at(p, 1, 1, 1) - float(audit[p]['value_2050'])))
    assert worst < 5e-4, f'Shapley audit not reproduced: {worst}'
    # published break-even of storage (about 4,417 t-CO2/y): 2050 background, total waste carbon at its 2050
    # value, only the fossil carbon varied, as published
    f = lambda F: CB.net('G1', F, SD.T50, SD.G50) - CB.net('S0', F, SD.T50, SD.G50)
    lo, hi = 1000.0, 40000.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if f(mid) < 0 else (mid, hi)
    F_be = 0.5 * (lo + hi)
    assert abs(F_be - 4417) < 1.0, F_be
    return worst, F_be


def break_even_on_grid(EF):
    """Fossil combustion CO2 at which G1 equals the reference, total waste carbon at its 2050 value, for a
    given grid factor (the published value is this at 0.07)."""
    f = lambda F: CB.net('G1', F, SD.T50, EF) - CB.net('S0', F, SD.T50, EF)
    lo, hi = 100.0, 60000.0
    if f(lo) * f(hi) > 0:
        return float('nan')
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if f(mid) < 0 else (mid, hi)
    return 0.5 * (lo + hi)


def part_a():
    rows = []
    for yr in range(2025, 2051):
        lam = (yr - 2025) / 25
        v = {p: net_at(p, lam, lam, lam) for p in ORDER}
        r = ranks(v)
        rows.append(dict(year=yr, lam=lam, values=v, ranks=r,
                         adv=(v['G1'] - v['S0'], v['G2'] - v['S0']),
                         grid=SD.G25 + lam * (SD.G50 - SD.G25),
                         fossil=SD.F25 + lam * (SD.F50 - SD.F25)))
    return rows


def part_b(n=36):
    gs = np.linspace(0, 1, n)
    ws = np.linspace(0, 1, n)
    grid, adv, lead = [], {}, {}
    for h in (0, 1):
        for g in gs:
            for w in ws:
                v = {p: net_at(p, g, w, h) for p in ORDER}
                adv[(h, g, w)] = (v['G1'] - v['S0'], v['G2'] - v['S0'])
                best = min(v, key=v.get)
                second = sorted(v, key=v.get)[1]
                lead[(h, g, w)] = (best, v[second] - v[best], sorted(v, key=v.get))
    return gs, ws, adv, lead


def part_c():
    out = {}
    for case in ('A', 'B'):
        os.environ['R_CASE'] = case
        BC = importlib.reload(importlib.import_module('build_climate'))
        crf = {p: np.asarray(BC.CRF[p]) for p in ORDER}
        per_h = []
        for H in range(1, BC.T + 1):
            v = {p: crf[p][H] for p in ORDER}
            per_h.append(dict(H=H, year=BC.START + H, crf=v, ranks=ranks(v),
                              share=crf['U2b'][H] / crf['U2a'][H]))
        static = dict(BC.static)
        out[case] = dict(per_h=per_h, static=static, static_ranks=ranks(static), T=BC.T, START=BC.START)
    # guard against the published four endpoints (treatment B is what Fig5_source_data.csv holds)
    fig5 = {r['pathway']: r for r in read_csv('Fig5_source_data.csv')}
    worst = 0.0
    for row in out['B']['per_h']:
        if str(row['year']) in ('2030', '2050', '2100', '2125'):
            for p in ORDER:
                ref = float(fig5[p][f"CRF_{row['year']}_W_m2_y"])
                worst = max(worst, abs(row['crf'][p] - ref) / max(abs(ref), 1e-30))
                assert row['ranks'][p] == int(fig5[p][f"rank_{row['year']}"]), (p, row['year'])
            if fig5['U2b'][f"benefit_share_vs_U2a_{row['year']}_pct"]:
                assert abs(100 * row['share'] - float(fig5['U2b'][f"benefit_share_vs_U2a_{row['year']}_pct"])) < 0.006
    assert worst < 1e-6, worst
    return out, worst


def main():
    worst_a, F_be = guards()
    A = part_a()
    gs, ws, adv, lead = part_b()
    C, worst_c = part_c()

    with open(os.path.join(OUT, 'R2_background_trajectory.csv'), 'w', encoding='utf-8', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['year', 'lambda', 'grid_tCO2_per_MWh', 'waste_fossil_tCO2_per_y']
                    + [f'net_{p}' for p in ORDER] + [f'rank_{p}' for p in ORDER]
                    + ['G1_minus_S0', 'G2_minus_S0'])
        for r in A:
            wr.writerow([r['year'], f"{r['lam']:.2f}", f"{r['grid']:.4f}", f"{r['fossil']:.1f}"]
                        + [f"{r['values'][p]:.4f}" for p in ORDER] + [r['ranks'][p] for p in ORDER]
                        + [f"{r['adv'][0]:.4f}", f"{r['adv'][1]:.4f}"])
    with open(os.path.join(OUT, 'R2_grid_waste_sweep.csv'), 'w', encoding='utf-8', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['hydrogen_2050', 'g', 'w', 'grid_tCO2_per_MWh', 'waste_fossil_tCO2_per_y',
                     'G1_minus_S0', 'G2_minus_S0', 'leader', 'leader_margin', 'order'])
        for (h, g, w), (a1, a2) in sorted(adv.items()):
            best, margin, order = lead[(h, g, w)]
            wr.writerow([h, f'{g:.4f}', f'{w:.4f}', f'{SD.G25 + g * (SD.G50 - SD.G25):.4f}',
                         f'{SD.F25 + w * (SD.F50 - SD.F25):.1f}', f'{a1:.4f}', f'{a2:.4f}', best,
                         f'{margin:.4f}', ' '.join(order)])
    with open(os.path.join(OUT, 'R2_endpoint_annual.csv'), 'w', encoding='utf-8', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['treatment', 'endpoint_year', 'horizon_y'] + [f'CRF_{p}_W_m2_y' for p in ORDER]
                    + [f'rank_{p}' for p in ORDER] + ['U2b_share_of_U2a_pct'])
        for case in ('A', 'B'):
            for r in C[case]['per_h']:
                wr.writerow([case, r['year'], r['H']] + [f"{r['crf'][p]:.6e}" for p in ORDER]
                            + [r['ranks'][p] for p in ORDER] + [f"{100 * r['share']:.2f}"])

    # ---- summary
    L = []
    w = L.append
    w('# Time-dimension sensitivity (revision R2) — summary\n')
    w(f'Checks: Shapley audit (8 corners x 13 pathways, and both ends) reproduced, worst deviation '
      f'{worst_a:.2e} t-CO2/y; waste-only storage break-even {F_be:,.1f} t-CO2/y fossil (published 4,417); '
      f'four published endpoints reproduced, worst relative CRF deviation {worst_c:.1e}, all ranks equal.\n')
    w('## A. Linear background trajectory 2025 -> 2050 (all three drivers together)\n')
    w('| year | grid | fossil CO2 | S0 | G1 | G1-S0 | G2-S0 | U2a | rank order (best first) |')
    w('|---|---|---|---|---|---|---|---|---|')
    for r in A:
        if r['year'] % 5 == 0:
            order = sorted(ORDER, key=lambda p: r['values'][p])
            w(f"| {r['year']} | {r['grid']:.3f} | {r['fossil']:,.0f} | {r['values']['S0']:,.0f} | "
              f"{r['values']['G1']:,.0f} | {r['adv'][0]:,.0f} | {r['adv'][1]:,.0f} | {r['values']['U2a']:,.0f} | "
              f"{' '.join(order)} |")
    leaders = {sorted(ORDER, key=lambda p: r['values'][p])[0] for r in A}
    adv_all = [r['adv'] for r in A]
    w(f"\nLeader in every year: {', '.join(sorted(leaders))}. Storage minus reference ranges from "
      f"{min(a[0] for a in adv_all):,.0f} to {max(a[0] for a in adv_all):,.0f} (G1) and from "
      f"{min(a[1] for a in adv_all):,.0f} to {max(a[1] for a in adv_all):,.0f} (G2); "
      f"{'negative in every year' if all(a[0] < 0 and a[1] < 0 for a in adv_all) else 'not negative in every year'}.")
    rank_changes = sorted({p for p in ORDER for r in A if r['ranks'][p] != A[0]['ranks'][p]})
    w(f"Pathways whose rank changes somewhere along the path: {', '.join(rank_changes) or 'none'}.")
    for p in rank_changes:
        seq = []
        for r in A:
            if not seq or seq[-1][1] != r['ranks'][p]:
                seq.append((r['year'], r['ranks'][p]))
        w(f"  {p}: " + ', '.join(f'{y}: {k}' for y, k in seq))
    w('\n## B. Path-free sweep: grid 0.423 -> 0.07 t-CO2/MWh x waste fossil carbon 26,475 -> 10,416 t-CO2/y\n')
    for h in (0, 1):
        a1 = [v[0] for k, v in adv.items() if k[0] == h]
        a2 = [v[1] for k, v in adv.items() if k[0] == h]
        leads = {lead[k][0] for k in lead if k[0] == h}
        margin = min(lead[k][1] for k in lead if k[0] == h)
        n_up = sum(1 for k, v in adv.items() if k[0] == h and (v[0] >= 0 or v[1] >= 0))
        n_all = sum(1 for k in adv if k[0] == h)
        below = ('storage below the reference at every point' if n_up == 0 else
                 f'storage below the reference at {n_all - n_up:,} of {n_all:,} points')
        w(f"- hydrogen at its {'2050' if h else '2025'} value: G1-S0 from {min(a1):,.0f} to {max(a1):,.0f}, "
          f"G2-S0 from {min(a2):,.0f} to {max(a2):,.0f}; {below}; leader at every point: "
          f"{', '.join(sorted(leads))} (smallest margin over the second {margin:,.0f} t-CO2/y)")
    w('\nBreak-even fossil combustion CO2 of storage (G1 = S0; total waste carbon at its 2050 value) against '
      'the grid factor:')
    for EF in (0.07, 0.15, 0.25, 0.35, 0.423):
        be = break_even_on_grid(EF)
        w(f"  grid {EF:.3f}: {be:,.0f} t-CO2/y fossil (plastic ~{be / SD.F50 * 5:.1f} % wet, linear rule "
          f"5 % at {SD.F50:,.0f})")
    w('\n## C. Every annual endpoint 2026 -> 2125\n')
    for case in ('A', 'B'):
        ph = C[case]['per_h']
        leaders = {min(r['crf'], key=r['crf'].get) for r in ph}
        second = {sorted(ORDER, key=lambda p: r['crf'][p])[1] for r in ph}
        changing = sorted({p for p in ORDER for r in ph if r['ranks'][p] != ph[0]['ranks'][p]})
        w(f"- treatment {case}: leader at every endpoint {', '.join(sorted(leaders))}, second "
          f"{', '.join(sorted(second))}; U2b share of the U2a benefit {100 * ph[0]['share']:.1f}% at "
          f"{ph[0]['year']}, {100 * ph[4]['share']:.1f}% at 2030, {100 * ph[24]['share']:.1f}% at 2050, "
          f"{100 * ph[74]['share']:.1f}% at 2100, {100 * ph[-1]['share']:.1f}% at 2125; pathways whose rank "
          f"changes across endpoints: {', '.join(changing) or 'none'}")
        for p in changing:
            seq = []
            for r in ph:
                if not seq or seq[-1][1] != r['ranks'][p]:
                    seq.append((r['year'], r['ranks'][p]))
            w(f"    {p}: " + ', '.join(f'{y}: {k}' for y, k in seq))
    open(os.path.join(OUT, 'R2_time_sensitivity_summary.md'), 'w', encoding='utf-8', newline='\n').write(
        '\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
