"""
Reconciliation of the regional equation against the values plotted in Fig. 3.

The manuscript previously wrote the regional model with a single coefficient acting on
the fossil carbon of the waste. That form cannot represent the model actually used,
because the carbon term of several pathway classes depends on the total combustion
carbon as well as on its fossil share: the substitution credit of the utilization
pathways follows the captured stream, and the process CO2 loss of the mineralization
pathways is apportioned by the fossil share of that stream. The exact form is

  net_p(r) = net_p(nat) + E_net,p (EF_r - EF_nat) + [ Phi_p(F_r,T_r) - Phi_p(F_nat,T_nat) ]

with the carbon term Phi_p taken directly from the partition of Eq. 1a (v4 forms,
R1: the captured-stream-scaled group E_net,p now also holds the explicit solvent and
transport terms, which follow s_cap, so the second bracket of the expression is
[E_p(r) - E_p(nat)] over the whole captured-stream-scaled block, not the electricity
part alone; carbon_model.terms4 documents the fold),
f = F / T the fossil share of the captured stream, s_cap the captured-stream scale):

  reference          Phi = F
  geological storage Phi = (1 - cr) F
  mineralization     Phi = (1 - cr) F + f L_R,p s_cap
  utilization        Phi = (1 - cr) F + f V_p s_cap - (QA_p - f QB_p) s_cap
  chemical recycling Phi = F - D_p (F / F_nat)

This script recomputes every pathway in every region from that expression and compares
it with the value plotted in Fig. 3, which is the difference from the region's own
reference plant.
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'regions'))
import carbon_model as CB
import regional_model as RV

CR = CB.CR


def eq2(p, F, T, EF):
    """Eq. 2 written out from the four additive groups of the throughput-scaled model."""
    e0, ep0, c0, h0 = CB.terms4(p, CB.F_NAT, CB.T_NAT, CB.EF_NAT)
    e, ep, c, h = CB.terms4(p, F, T, EF)
    return CB.NET_NAT[p] + (e - e0) + (ep - ep0) + (c - c0) + (h - h0)


def main():
    regs = RV.load()
    names = sorted(regs)
    rows, worst, nfail = [], 0.0, 0
    for p in CB.ORDER:
        for n in names:
            r = regs[n]
            code = CB.net(p, r['F'], r['T'], r['EF'])
            mine = eq2(p, r['F'], r['T'], r['EF'])
            ref_code = CB.net('S0', r['F'], r['T'], r['EF'])
            ref_mine = eq2('S0', r['F'], r['T'], r['EF'])
            d_code = (code - ref_code) / 1000.0        # value plotted in Fig. 3, kt
            d_mine = (mine - ref_mine) / 1000.0
            diff = abs(d_mine - d_code)
            worst = max(worst, diff)
            ok = diff <= 0.01
            nfail += (not ok)
            rows.append([p, n, round(r['F'], 0), round(r['T'], 0), round(r['EF'], 4),
                         round(CB.E_PROC[p], 0), round(mine, 1), round(d_mine, 3),
                         round(d_code, 3), round(diff, 4), 'pass' if ok else 'FAIL'])

    print('Reconciliation of Eq. 2 against the values plotted in Fig. 3')
    print(f'  cells checked      : {len(rows)}')
    print(f'  tolerance          : 0.01 kt-CO2/y')
    print(f'  largest difference : {worst:.6f} kt-CO2/y')
    print(f'  failures           : {nfail}')
    print()
    print('  worked example, U2a in Hokkaido:')
    r = regs['Hokkaido']
    print(f"    F_r = {r['F']:,.0f}   T_r = {r['T']:,.0f}   EF_r = {r['EF']:.3f}")
    e0, ep0, c0, h0 = CB.terms4('U2a', CB.F_NAT, CB.T_NAT, CB.EF_NAT)
    e, ep, c, h = CB.terms4('U2a', r['F'], r['T'], r['EF'])
    _t = CB.terms('U2a', r['F'], r['T'], r['EF'])
    _t0 = CB.terms('U2a', CB.F_NAT, CB.T_NAT, CB.EF_NAT)
    print(f"    fixed electricity {e-e0:+,.0f}, captured-stream-scaled block {ep-ep0:+,.0f} "
          f"(of which solvent {_t[5]-_t0[5]:+,.1f}, transport {_t[6]-_t0[6]:+,.1f}), "
          f"carbon incl. credit {c-c0:+,.0f}, hydrogen {h-h0:+,.0f} t-CO2/y")
    print(f"    net = {eq2('U2a', r['F'], r['T'], r['EF']):,.0f}  "
          f"vs reference {eq2('S0', r['F'], r['T'], r['EF']):,.0f}  "
          f"-> {(eq2('U2a', r['F'], r['T'], r['EF']) - eq2('S0', r['F'], r['T'], r['EF']))/1000:+.2f} kt")

    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs',
                      'reconciliation_regional.csv')
    with open(fp, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['pathway', 'region', 'F_r', 'T_r', 'EF_r', 'E_proc',
                    'regional absolute (Eq. 2)', 'difference from local reference (Eq. 2, kt)',
                    'value plotted in Fig. 3 (kt)', 'abs difference (kt)', 'check'])
        w.writerows(rows)
    print(f'\n  wrote {fp}')


if __name__ == '__main__':
    main()
