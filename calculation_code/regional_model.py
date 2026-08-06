"""
Regional results rebuilt on the explicit carbon balance (carbon_balance.py).

Supersedes regional_engine.py, whose single coefficient phi = 1 - 2cr = -0.80 for all
storage pathways was not derivable from the carbon flows and double-counted the stored
fraction. Every regional value here follows from the region's measured fossil and total
combustion CO2 and its official grid emission factor.
"""
import csv, os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import carbon_model as CB

HERE = os.path.dirname(os.path.abspath(__file__))
EF_NAT_OFFICIAL = 0.423          # national average of the utility list, t-CO2/MWh


def load():
    rows = list(csv.DictReader(open(os.path.join(HERE, 'region_waste_carbon.csv'),
                                    encoding='utf-8-sig')))
    fos_mean = st.mean([float(r['CO2_fossil_t_per_t_dry']) for r in rows])
    tot_mean = st.mean([float(r['CO2_total_t_per_t_dry']) for r in rows])
    out = {}
    for r in rows:
        out[r['region']] = dict(
            EF=float(r['grid_EF_2025_tCO2_per_kWh']) * 1000.0,
            F=CB.F_NAT * float(r['CO2_fossil_t_per_t_dry']) / fos_mean,
            T=CB.T_NAT * float(r['CO2_total_t_per_t_dry']) / tot_mean,
            fossil_share=float(r['fossil_share_of_C_pct']),
            plastic=float(r['plastic_pct']))
    return out


def main():
    regs = load()
    names = sorted(regs)

    print('Net life-cycle CO2 (t-CO2/y), convention A, present grid, treatment A')
    print('rebuilt from the explicit carbon balance\n')
    print(f"{'path':<5}" + ''.join(f'{n[:6]:>8}' for n in names))
    M = {}
    for p in CB.ORDER:
        M[p] = {n: CB.net(p, regs[n]['F'], regs[n]['T'], regs[n]['EF']) for n in names}
        print(f'{p:<5}' + ''.join(f'{M[p][n]:>8.0f}' for n in names))

    print('\nMitigation relative to the region own reference plant (t-CO2/y):')
    print(f"{'path':<5}" + ''.join(f'{n[:6]:>8}' for n in names) + f"{'min':>9}{'max':>9}")
    D = {}
    for p in CB.ORDER:
        if p == 'S0':
            continue
        D[p] = {n: M[p][n] - M['S0'][n] for n in names}
        v = list(D[p].values())
        print(f'{p:<5}' + ''.join(f'{D[p][n]:>8.0f}' for n in names)
              + f'{min(v):>9,.0f}{max(v):>9,.0f}')

    print('\nHow many regions does each pathway beat its own reference in?')
    for p in CB.ORDER:
        if p == 'S0':
            continue
        k = sum(1 for n in names if D[p][n] < 0)
        tag = '' if k in (0, 10) else '   <- region-dependent'
        print(f'  {p:<5}{k:>3}/10{tag}')

    print('\nBest pathway per region:')
    for n in names:
        b = min([p for p in CB.ORDER if p != 'S0'], key=lambda p: M[p][n])
        print(f'  {n:<10} -> {b:<4} ({M[b][n]:,.0f}; mitigation {D[b][n]:,.0f})')

    print('\nRegional spread of each pathway (absolute net):')
    print(f"{'path':<5}{'min':>10}{'max':>10}{'spread':>10}")
    for p in CB.ORDER:
        v = [M[p][n] for n in names]
        print(f'{p:<5}{min(v):>10,.0f}{max(v):>10,.0f}{max(v)-min(v):>10,.0f}')

    print('\nRank reversals between regions:')
    found = 0
    for i, a in enumerate(CB.ORDER):
        for b in CB.ORDER[i+1:]:
            sign = {n: M[a][n] < M[b][n] for n in names}
            if len(set(sign.values())) > 1:
                wa = [n[:4] for n in names if sign[n]]
                wb = [n[:4] for n in names if not sign[n]]
                gap = max(abs(M[a][n] - M[b][n]) for n in names)
                print(f'  {a} vs {b}: {a} better in {",".join(wa)} | '
                      f'{b} better in {",".join(wb)}  (max gap {gap:,.0f})')
                found += 1
    if not found:
        print('  none')

    fp = os.path.join(HERE, 'regional_net_v2.csv')
    with open(fp, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['pathway'] + names)
        for p in CB.ORDER:
            w.writerow([p] + [round(M[p][n], 1) for n in names])
    print('\nwrote', fp)


if __name__ == '__main__':
    main()
