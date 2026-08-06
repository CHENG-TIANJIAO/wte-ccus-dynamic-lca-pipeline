"""
Generate every machine-readable file named in the Data availability statement, plus the
Eq. 2 / Eq. 6 reconciliation and the A/B pairing audit.
"""
import numpy as np, csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'regions'))
import carbon_model as CB
import monte_carlo as M
import regional_model as RV
OUT = os.path.join(HERE, 'outputs')

A, B = M.evaluate(M.MASTER, 'A'), M.evaluate(M.MASTER, 'B')
KEYS = list(M.MASTER)


def w(name, header, rows):
    fp = os.path.join(OUT, name)
    with open(fp, 'w', newline='', encoding='utf-8') as f:
        c = csv.writer(f); c.writerow(header); c.writerows(rows)
    print(f'  wrote {name} ({len(rows)} rows)')


# ---- 1. full master draw matrix (all N draws) ----
w('MonteCarlo_master_draws.csv', ['draw_id'] + KEYS,
  [[k] + [f'{M.MASTER[key][k]:.8f}' for key in KEYS] for k in range(M.N)])

# ---- 2. pathway-level outputs, both treatments ----
for t, net in (('A', A), ('B', B)):
    w(f'MonteCarlo_pathway_outputs_{t}.csv', ['draw_id'] + M.ORDER,
      [[k] + [f'{net[p][k]:.6f}' for p in M.ORDER] for k in range(M.N)])

# ---- 3. pairing audit ----
rkA = np.vstack([A[p] for p in M.ORDER]).argsort(0).argsort(0)
rkB = np.vstack([B[p] for p in M.ORDER]).argsort(0).argsort(0)
rows = []
for i, p in enumerate(M.ORDER):
    aff = CB.CLASS[p] == 'cr'
    d = A[p] - B[p]
    r1a, r1b = np.mean(rkA[i] == 0), np.mean(rkB[i] == 0)
    rows.append([p, 'yes' if aff else 'no',
                 f'{np.abs(d).max():.10f}',
                 f'{np.median(d):.10f}',
                 f'{np.median(A[p]) - np.median(B[p]):.10f}',
                 f'{np.percentile(d, 2.5):.10f}',
                 f'{np.percentile(d, 97.5):.10f}',
                 f'{np.percentile(A[p], 2.5) - np.percentile(B[p], 2.5):.10f}',
                 f'{np.percentile(A[p], 97.5) - np.percentile(B[p], 97.5):.10f}',
                 f'{np.mean(A[p] < A["S0"]) - np.mean(B[p] < B["S0"]):.10f}',
                 f'{np.mean(A[p] < 0) - np.mean(B[p] < 0):.10f}',
                 f'{r1a:.6f}', f'{r1b:.6f}', f'{r1a - r1b:.6f}',
                 'boundary changes the diverted-carbon credit' if aff
                 else 'unaffected by the recycling boundary; draws identical, so every '
                      'draw-level and summary difference is exactly zero except the rank '
                      'probability, which changes because the competing set has changed'])
w('MonteCarlo_pairing_audit.csv',
  ['pathway', 'affected_by_recycling_boundary',
   'max_abs_draw_level_difference',
   'median_of_draw_level_difference',
   'difference_between_treatment_medians',
   'p2.5_of_draw_level_difference',
   'p97.5_of_draw_level_difference',
   'difference_between_treatment_p2.5',
   'difference_between_treatment_p97.5',
   'P(<reference)_difference', 'P(net_negative)_difference',
   'P_rank_1_A', 'P_rank_1_B', 'P_rank_1_difference', 'explanation'], rows)

# ---- 4. rank correlations: EVERY sampled input, both treatments, all pathways ----
def sp(a, b):
    return np.corrcoef(a.argsort().argsort(), b.argsort().argsort())[0, 1]
SHARED = ['fossil_C', 'throughput', 'grid_EF', 'capture_rate', 'H2_EF',
          'fossil_share']
rows = []
for t, net in (('A', A), ('B', B)):
    for p in M.ORDER:
        applies = {'fossil_C': 'all', 'throughput': 'all', 'grid_EF': 'all',
                   'capture_rate': 'capture pathways only',
                   'H2_EF': 'utilization pathways only',
                   'fossil_share': 'capture pathways (credits, vents, losses)'}
        for key in SHARED:
            rows.append([t, p, key, 'shared background', applies[key],
                         f'{sp(M.MASTER[key], net[p]):.4f}', M.N, M.SEED])
        for f_ in M.FAMILIES:
            rows.append([t, p, 'elec_mult_' + f_, 'process-electricity multiplier',
                         'technology family ' + f_,
                         f'{sp(M.MASTER["elec_mult_" + f_], net[p]):.4f}', M.N, M.SEED])
        for q in M.ORDER:
            rows.append([t, p, 'rem_mult_' + q, 'residual multiplier',
                         'pathway ' + q,
                         f'{sp(M.MASTER["rem_mult_" + q], net[p]):.4f}', M.N, M.SEED])
w('MonteCarlo_rank_correlations.csv',
  ['treatment', 'pathway', 'input_variable', 'variable_class', 'applies_to',
   'spearman_coefficient', 'sample_size', 'seed'], rows)

# ---- 4b. paired A/B summary, referenced by the SI ----
rows = []
for t, net in (('A', A), ('B', B)):
    rk = np.vstack([net[p] for p in M.ORDER]).argsort(0).argsort(0)
    for i, p in enumerate(M.ORDER):
        v = net[p]
        rows.append([t, p, f'{np.median(v):.4f}', f'{np.percentile(v,2.5):.4f}',
                     f'{np.percentile(v,97.5):.4f}', f'{np.mean(v<net["S0"]):.6f}',
                     f'{np.mean(rk[i]==0):.6f}', f'{np.mean(v<0):.6f}'])
w('MonteCarlo_summary_AB.csv',
  ['treatment', 'pathway', 'median', 'p2.5', 'p97.5', 'P(<reference)', 'P(rank_1)',
   'P(net_negative)'], rows)

# ---- 5. Eq.2 / Eq.6 deterministic reconciliation ----
det = {'fossil_C': np.array([CB.F_NAT]), 'throughput': np.array([CB.T_NAT]),
       'grid_EF': np.array([CB.EF_NAT]), 'capture_rate': np.array([CB.CR]),
       'H2_EF': np.array([1.0]),
       'fossil_share': np.array([CB.F_NAT / CB.T_NAT])}
for f_ in M.FAMILIES: det['elec_mult_' + f_] = np.array([1.0])
for p in M.ORDER: det['rem_mult_' + p] = np.array([1.0])
detA = M.evaluate(det, 'A')
rows = []
mx = 0.0
for p in M.ORDER:
    e2 = CB.net(p, CB.F_NAT, CB.T_NAT, CB.EF_NAT); e6 = float(detA[p][0])
    mx = max(mx, abs(e2 - e6))
    rows.append([p, f'{e2:.6f}', f'{e6:.6f}', f'{e2-e6:.10f}'])
w('Eq2_Eq6_reconciliation.csv',
  ['pathway', 'Eq2_deterministic', 'Eq6_deterministic_all_multipliers_one',
   'difference'], rows)
print(f'  max |Eq.2 - Eq.6| = {mx:.10f}')

# ---- 6. Fig 2 source data (computed from the model, not from the plotting script) ----
import scenario_decomposition as SD
_A25 = {p: CB.net(p, CB.F_NAT, CB.T_NAT, CB.EF_NAT) for p in CB.ORDER}
_A50 = {p: SD.net(p, True, True, True) for p in CB.ORDER}
_rows = []
for p in sorted(CB.ORDER, key=lambda q: _A50[q]):
    bio = CB.CLASS[p] in ('min', 'geo')
    _b25 = CB.bio_stored(p, CB.F_NAT, CB.T_NAT)     # net-permanent only (v4)
    _b50 = CB.bio_stored(p, SD.F50, SD.T50)
    _rows.append([p, f'{_A25[p]:.4f}', f'{_A50[p]:.4f}',
                  f'{_A25[p]-_b25:.4f}' if bio else '',
                  f'{_A50[p]-_b50:.4f}' if bio else ''])
w('Fig2_source_data.csv', ['pathway', 'A_2025', 'A_2050', 'B_2025', 'B_2050'], _rows)

# ---- 7. Fig 3 source data: 130 absolute + 120 relative ----
regs = RV.load()
rows = []
mx_disc, mx_cell = 0.0, ''
for p in CB.ORDER:
    for n in sorted(regs):
        r = regs[n]
        sc = CB.s_cap(r['T'], CB.CR)
        b_fix, b_steam, b_el, phi, b_h2 = CB.terms(p, r['F'], r['T'], r['EF'])
        if CB.CLASS[p] == 'ccu':
            _fr = r['F'] / r['T']
            qsub = -(CB.QA[p] - _fr * CB.QB[p]) * sc     # signed, <= 0
        else:
            qsub = 0.0
        absv = CB.net(p, r['F'], r['T'], r['EF'])
        ref = CB.net('S0', r['F'], r['T'], r['EF'])
        rel = absv - ref
        # value as displayed in Fig. 3, kt to three decimals
        disp = round(rel / 1000.0, 3)
        disc = abs(rel / 1000.0 - disp)
        if p != 'S0' and disc > mx_disc:
            mx_disc, mx_cell = disc, f'{p}-{n}'
        rows.append([p, n, f"{r['EF']:.4f}", f"{r['F']:.4f}", f"{r['T']:.4f}",
                     f'{sc:.8f}', f'{b_fix:.4f}', f'{b_steam + b_el:.4f}',
                     f'{phi:.4f}', f'{qsub:.4f}', f'{b_h2:.4f}',
                     f'{CB.residual(p):.4f}', f'{absv:.4f}', f'{ref:.4f}',
                     '' if p == 'S0' else f'{rel/1000:.6f}',
                     '' if p == 'S0' else f'{disp:.3f}',
                     '' if p == 'S0' else f'{disc:.9f}',
                     't-CO2/y except EF (t-CO2/MWh), scaling factor (dimensionless) '
                     'and the last three columns (kt-CO2/y)'])
w('Fig3_source_data.csv',
  ['pathway', 'region', 'regional_electricity_factor_EF_r',
   'fossil_carbon_parameter_F_r', 'regional_throughput_T_r',
   'captured_stream_scaling_factor_s_cap',
   'fixed_contribution', 'captured_stream_scaled_contribution',
   'carbon_flow_contribution', 'substitution_credit_within_carbon_flow',
   'hydrogen_contribution', 'calibrated_residual',
   'absolute_result', 'reference_result',
   'relative_result_exact_kt', 'Fig3_displayed_value_kt',
   'reconciliation_discrepancy_kt', 'unit'], rows)
print(f'  -> {len(rows)} absolute results, {len(rows)-10} relative heatmap cells')
print(f'  -> max display reconciliation discrepancy {mx_disc:.9f} kt at {mx_cell}')

# ---- 8. Fig 6 source data ----
rows = []
for t, net in (('A', A), ('B', B)):
    arr = np.vstack([net[p] for p in M.ORDER]); rk = arr.argsort(0).argsort(0)
    for i, p in enumerate(M.ORDER):
        v = net[p]
        rows.append([t, p, f'{np.median(v):.4f}', f'{np.percentile(v,2.5):.4f}',
                     f'{np.percentile(v,97.5):.4f}', f'{np.mean(v<net["S0"]):.6f}',
                     f'{np.mean(rk[i]==0):.6f}', f'{np.mean(v<0):.6f}'])
w('Fig6_source_data.csv',
  ['treatment', 'pathway', 'median', 'p2.5', 'p97.5', 'P(<reference)',
   'P(rank1)', 'P(net_negative)'], rows)

# ---- 9. Shapley audit: all 8 combinations ----
import itertools, scenario_decomposition as SD
D = ['grid50', 'waste50', 'h2_50']
rows = []
for p in CB.ORDER:
    vals = {}
    for combo in itertools.product([False, True], repeat=3):
        kw = dict(zip(D, combo)); vals[combo] = SD.net(p, **kw)
    sh = {d: 0.0 for d in D}
    for order in itertools.permutations(D):
        S = set()
        for d in order:
            before = tuple(x in S for x in D); S.add(d)
            after = tuple(x in S for x in D)
            sh[d] += vals[after] - vals[before]
    for d in D: sh[d] /= 6.0
    base = vals[(False, False, False)]; full = vals[(True, True, True)]
    rows.append([p, f'{base:.4f}', f'{full:.4f}', f'{full-base:.4f}',
                 f'{sh["grid50"]:.4f}', f'{sh["waste50"]:.4f}', f'{sh["h2_50"]:.4f}',
                 f'{sum(sh.values()):.4f}', f'{(full-base)-sum(sh.values()):.8f}']
                + [f'{vals[c]:.4f}' for c in itertools.product([False, True], repeat=3)])
w('Shapley_decomposition_audit.csv',
  ['pathway', 'value_2025', 'value_2050', 'total_change', 'shapley_grid',
   'shapley_waste', 'shapley_hydrogen', 'sum_shapley', 'closure_discrepancy']
  + [f'combo_g{int(c[0])}_w{int(c[1])}_h{int(c[2])}'
     for c in itertools.product([False, True], repeat=3)], rows)

print('\nall machine-readable files written to outputs/')
