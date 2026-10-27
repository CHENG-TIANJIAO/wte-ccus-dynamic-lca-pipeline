# -*- coding: utf-8 -*-
"""
Phase 2b-E: factorial interaction terms and Shapley split of the 2025 -> 2050 drivers,
recomputed on the corrected chain (chain_r1, R1f state).

Reads (read-only):
  chain_r1/calculation_code/{carbon_model.py, scenario_decomposition.py, model_parameters.json}
  chain_r1/calculation_code/outputs/Shapley_decomposition_audit.csv
  R1_revision/02_analyses/E_shapley_interactions.csv            (R0-based, for the comparison)
Writes:
  R1_revision/02_analyses/E5_shapley_interactions.md
  R1_revision/02_analyses/E5_shapley_interactions.csv
  R1_revision/02_analyses/E5_shapley_interactions_terms.csv
Nothing in chain_r1 is modified (bytecode writing disabled).
This archive copy differs from the working-repository version only in (1) portable path resolution, so that the script finds the model and its own directory inside this archive. This does not affect any output: the matrices it writes here are byte-identical to the shipped ones (ZIP_VERIFICATION.md).
"""
import sys, os, csv, json, itertools
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode = True

AN = os.path.dirname(os.path.abspath(__file__))        # archive: <root>/analysis
CODE = os.environ.get('R1_CODE') or os.path.normpath(os.path.join(AN, '..', 'code'))
sys.path.insert(0, CODE)
import carbon_model as CB
import scenario_decomposition as SD
assert os.path.dirname(os.path.abspath(CB.__file__)) == CODE, CB.__file__
assert os.path.dirname(os.path.abspath(SD.__file__)) == CODE, SD.__file__

ORDER = CB.ORDER
D = ['grid50', 'waste50', 'h2_50']
COMBOS = list(itertools.product([False, True], repeat=3))

# ---- drivers ---------------------------------------------------------------------
G25, G50 = SD.G25, SD.G50
F25, T25, F50, T50 = SD.F25, SD.T25, SD.F50, SD.T50
H25, H50, H2S = SD.H25, SD.H50, SD.H2_SCALE
dEF = G50 - G25
s25, s50 = CB.s_cap(T25, CB.CR), CB.s_cap(T50, CB.CR)
ds_cap = s50 - s25
sF25, sF50 = CB.s_plastic(F25), CB.s_plastic(F50)
ds_F = sF50 - sF25
f25, f50 = F25 / T25, F50 / T50
dH = H2S - 1.0
STEAM_PEN = CB.STEAM_PEN
FIX_MWH = CB.AUX - CB.EXP_NOCC
assert G25 == 0.423 and G50 == 0.07
assert abs(STEAM_PEN - 13087.0) < 1e-9 and abs(FIX_MWH + 18847.0) < 1e-9

# ---- 8 combinations, main effects, interactions, Shapley -------------------------
def v8(p):
    return {c: SD.net(p, **dict(zip(D, c))) for c in COMBOS}

def factorial(vals):
    v = lambda g, w, h: vals[(bool(g), bool(w), bool(h))]
    r = {}
    r['base'], r['full'] = v(0, 0, 0), v(1, 1, 1)
    r['total'] = r['full'] - r['base']
    r['dG'] = v(1, 0, 0) - v(0, 0, 0)
    r['dW'] = v(0, 1, 0) - v(0, 0, 0)
    r['dH'] = v(0, 0, 1) - v(0, 0, 0)
    r['lG'] = v(1, 1, 1) - v(0, 1, 1)
    r['lW'] = v(1, 1, 1) - v(1, 0, 1)
    r['lH'] = v(1, 1, 1) - v(1, 1, 0)
    r['I_GW'] = v(1, 1, 0) - v(1, 0, 0) - v(0, 1, 0) + v(0, 0, 0)
    r['I_GH'] = v(1, 0, 1) - v(1, 0, 0) - v(0, 0, 1) + v(0, 0, 0)
    r['I_WH'] = v(0, 1, 1) - v(0, 1, 0) - v(0, 0, 1) + v(0, 0, 0)
    r['I_GWH'] = (v(1, 1, 1) - v(1, 1, 0) - v(1, 0, 1) - v(0, 1, 1)
                  + v(1, 0, 0) + v(0, 1, 0) + v(0, 0, 1) - v(0, 0, 0))
    r['sumI'] = r['I_GW'] + r['I_GH'] + r['I_WH'] + r['I_GWH']
    # Shapley, interaction (Harsanyi-dividend) form
    r['phiG_i'] = r['dG'] + r['I_GW'] / 2 + r['I_GH'] / 2 + r['I_GWH'] / 3
    r['phiW_i'] = r['dW'] + r['I_GW'] / 2 + r['I_WH'] / 2 + r['I_GWH'] / 3
    r['phiH_i'] = r['dH'] + r['I_GH'] / 2 + r['I_WH'] / 2 + r['I_GWH'] / 3
    # Shapley, permutation form (export_files.py section 9)
    sh = {d: 0.0 for d in D}
    for order in itertools.permutations(D):
        S = set()
        for d in order:
            before = tuple(x in S for x in D); S.add(d)
            after = tuple(x in S for x in D)
            sh[d] += vals[after] - vals[before]
    for d in D:
        sh[d] /= 6.0
    r['phiG_p'], r['phiW_p'], r['phiH_p'] = sh['grid50'], sh['waste50'], sh['h2_50']
    r['closure_i'] = r['total'] - (r['phiG_i'] + r['phiW_i'] + r['phiH_i'])
    r['closure_p'] = r['total'] - (r['phiG_p'] + r['phiW_p'] + r['phiH_p'])
    return r

# ---- term-level (seven groups + residual) -----------------------------------------
TERMS = ['b_fix', 'b_steam', 'b_el', 'phi', 'b_h2', 'b_reag', 'b_trans', 'residual']

def groups(p, g, w, h):
    EF = G50 if g else G25
    F, T = (F50, T50) if w else (F25, T25)
    b_fix, b_steam, b_el, phi, b_h2, b_reag, b_trans = CB.terms(p, F, T, EF)
    if h and p in CB.H2:
        b_h2 += CB.H2[p] * CB.s_cap(T, CB.CR) * (H2S - 1.0)
    d = dict(b_fix=b_fix, b_steam=b_steam, b_el=b_el, phi=phi, b_h2=b_h2,
             b_reag=b_reag, b_trans=b_trans, residual=CB.residual(p))
    assert abs(sum(d.values()) - SD.net(p, g, w, h)) < 1e-9, (p, g, w, h)
    return d

def term_factorial(p):
    out = {}
    for t in TERMS:
        vals = {c: groups(p, *c)[t] for c in COMBOS}
        out[t] = factorial(vals)
    return out

# ---- audit CSV of the copy ----------------------------------------------------------
audit = {}
with open(os.path.join(CODE, 'outputs', 'Shapley_decomposition_audit.csv'), encoding='utf-8') as fh:
    for row in csv.DictReader(fh):
        audit[row['pathway']] = row

# ---- R0-based E file (for the comparison) -------------------------------------------
e_r0 = {}
with open(os.path.join(AN, 'E_shapley_interactions.csv'), encoding='utf-8') as fh:
    for row in csv.DictReader(fh):
        e_r0[row['pathway']] = row
LED = CB.LED
E_PROC_R0 = LED['STATIC_R1']['E_PROC_MWH']     # the values carbon_model.py had hard-coded (R0 = R1)
V4_R0 = LED['STATIC_R0']['STATIC_V4']
for p in ORDER:   # sanity: the R0 E file starts from the shipped anchors
    assert abs(float(e_r0[p]['v_g0_w0_h0']) - V4_R0[p]) < 1e-5, p

# ---- compute ------------------------------------------------------------------------
R, T8, VALS = {}, {}, {}
for p in ORDER:
    VALS[p] = v8(p)
    R[p] = factorial(VALS[p])
    T8[p] = term_factorial(p)

# analytic closed forms
AN_I = {}
for p in ORDER:
    c = CB.CLASS[p]
    if p in CB.CAPTURES:
        igw = (STEAM_PEN + CB.E_PROC[p]) * ds_cap * dEF
    elif c == 'cr':
        igw = CB.E_PROC[p] * ds_F * dEF
    else:
        igw = 0.0
    iwh = CB.H2[p] * ds_cap * dH if p in CB.H2 else 0.0
    dW_ct = (CB.REAG[p] + CB.TRANS[p]) * ds_cap      # W-dependence added by the two CAP terms
    AN_I[p] = dict(I_GW=igw, I_WH=iwh, dW_capterms=dW_ct)

# ---- checks -------------------------------------------------------------------------
chk = {}
chk['combo_vs_audit'] = max(abs(VALS[p][c] - float(audit[p][f'combo_g{int(c[0])}_w{int(c[1])}_h{int(c[2])}']))
                            for p in ORDER for c in COMBOS)
chk['perm_vs_interaction'] = max(abs(R[p][f'phi{d}_p'] - R[p][f'phi{d}_i']) for p in ORDER for d in 'GWH')
chk['phi_vs_audit'] = max(abs(R[p]['phiG_p'] - float(audit[p]['shapley_grid'])) for p in ORDER)
chk['phi_vs_audit'] = max(chk['phi_vs_audit'],
                          max(abs(R[p]['phiW_p'] - float(audit[p]['shapley_waste'])) for p in ORDER),
                          max(abs(R[p]['phiH_p'] - float(audit[p]['shapley_hydrogen'])) for p in ORDER))
chk['closure'] = max(max(abs(R[p]['closure_i']), abs(R[p]['closure_p'])) for p in ORDER)
chk['audit_closure_col'] = max(abs(float(audit[p]['closure_discrepancy'])) for p in ORDER)
chk['identity'] = max(abs(R[p]['total'] - (R[p]['dG'] + R[p]['dW'] + R[p]['dH'] + R[p]['sumI'])) for p in ORDER)
chk['analytic'] = max(max(abs(R[p]['I_GW'] - AN_I[p]['I_GW']), abs(R[p]['I_WH'] - AN_I[p]['I_WH']),
                          abs(R[p]['I_GH']), abs(R[p]['I_GWH'])) for p in ORDER)
chk['term_sum'] = max(abs(sum(T8[p][t][k] for t in TERMS) - R[p][k])
                      for p in ORDER for k in ('dG', 'dW', 'dH', 'I_GW', 'I_GH', 'I_WH', 'I_GWH'))
# b_reag / b_trans: W-dependence only
chk['captems_no_G'] = max(max(abs(T8[p][t]['dG']), abs(T8[p][t]['I_GW']), abs(T8[p][t]['I_GH']),
                              abs(T8[p][t]['I_WH']), abs(T8[p][t]['I_GWH']), abs(T8[p][t]['dH']))
                          for p in ORDER for t in ('b_reag', 'b_trans'))
chk['captems_dW'] = max(abs(T8[p]['b_reag']['dW'] + T8[p]['b_trans']['dW'] - AN_I[p]['dW_capterms']) for p in ORDER)
chk['residual_const'] = max(max(abs(T8[p]['residual'][k]) for k in ('dG', 'dW', 'dH', 'I_GW', 'I_GH', 'I_WH', 'I_GWH'))
                            for p in ORDER)
# last-step = first-step + interactions
chk['bracket'] = max(max(abs(R[p]['lG'] - (R[p]['dG'] + R[p]['I_GW'] + R[p]['I_GH'] + R[p]['I_GWH'])),
                         abs(R[p]['lW'] - (R[p]['dW'] + R[p]['I_GW'] + R[p]['I_WH'] + R[p]['I_GWH'])),
                         abs(R[p]['lH'] - (R[p]['dH'] + R[p]['I_GH'] + R[p]['I_WH'] + R[p]['I_GWH'])))
                     for p in ORDER)

# R0 -> R1f change of the effects, predicted from the closed forms
CMP = {}
for p in ORDER:
    e = e_r0[p]
    dE = CB.E_PROC[p] - E_PROC_R0[p]
    if p in CB.CAPTURES:
        pred_dG = dE * dEF
        pred_dW = dE * ds_cap * G25 + AN_I[p]['dW_capterms']
        pred_I = dE * ds_cap * dEF
    elif CB.CLASS[p] == 'cr':
        pred_dG = dE * dEF
        pred_dW = dE * ds_F * G25
        pred_I = dE * ds_F * dEF
    else:
        pred_dG = pred_dW = pred_I = 0.0
    act_dG = R[p]['dG'] - float(e['main_G_first_step'])
    act_dW = R[p]['dW'] - float(e['main_W_first_step'])
    act_I = R[p]['I_GW'] - float(e['I_GW'])
    act_IWH = R[p]['I_WH'] - float(e['I_WH'])
    act_dH = R[p]['dH'] - float(e['main_H_first_step'])
    CMP[p] = dict(dE=dE, pred_dG=pred_dG, pred_dW=pred_dW, pred_I=pred_I, act_dG=act_dG,
                  act_dW=act_dW, act_I=act_I, act_IWH=act_IWH, act_dH=act_dH,
                  dG_R0=float(e['main_G_first_step']), dW_R0=float(e['main_W_first_step']),
                  dH_R0=float(e['main_H_first_step']), I_GW_R0=float(e['I_GW']), I_WH_R0=float(e['I_WH']),
                  phiG_R0=float(e['shapley_G']), phiW_R0=float(e['shapley_W']), phiH_R0=float(e['shapley_H']),
                  base_R0=float(e['v_g0_w0_h0']), full_R0=float(e['v_g1_w1_h1']),
                  part_dE_dW=(dE * ds_cap * G25 if p in CB.CAPTURES else (dE * ds_F * G25 if CB.CLASS[p] == 'cr' else 0.0)))
chk['r0_delta_pred'] = max(max(abs(CMP[p]['pred_dG'] - CMP[p]['act_dG']), abs(CMP[p]['pred_dW'] - CMP[p]['act_dW']),
                               abs(CMP[p]['pred_I'] - CMP[p]['act_I']), abs(CMP[p]['act_IWH']), abs(CMP[p]['act_dH']))
                           for p in ORDER)

print('CHECKS')
for k, v in chk.items():
    print(f'  {k:<22}{v:.3e}')
assert chk['combo_vs_audit'] < 6e-5 and chk['phi_vs_audit'] < 6e-5
assert chk['perm_vs_interaction'] < 1e-9 and chk['closure'] < 1e-8 and chk['analytic'] < 1e-8
assert chk['term_sum'] < 1e-8 and chk['captems_no_G'] < 1e-12 and chk['captems_dW'] < 1e-8
assert chk['residual_const'] < 1e-12 and chk['bracket'] < 1e-9 and chk['r0_delta_pred'] < 2e-5

# R1c: the declared high-compression scenario SC (+46 kWh/t on the nine capture pathways) moves I_GW
import r1c_modules as RM
EXTRA_SC = (RM.val('compressor_high') - RM.val('compressor')) * RM.Q_CAPTURED / 1000.0
I_GW_SC = {p: (STEAM_PEN + CB.E_PROC[p] + EXTRA_SC) * ds_cap * dEF for p in CB.CAPTURES}
# D8 losses convention A: f x 3 % x cr T -> W-only (no interaction); value 2025 / 2050
LOSS = LED['SENSITIVITIES_DECLARED']['losses_G_fraction_of_captured']
loss25, loss50 = f25 * LOSS * CB.CR * T25, f50 * LOSS * CB.CR * T50

# largest interaction
imax_p = max(ORDER, key=lambda p: R[p]['sumI'])

# G1 - S0 Shapley (Table 2 quantity)
def rel(p, k):
    return R[p][k] - R['S0'][k]

# G1 arithmetic for the narrative
pen_G1 = STEAM_PEN + CB.E_PROC['G1']
G1_pen25 = pen_G1 * G25
G1_grid_alone = pen_G1 * dEF
G1_stream_alone = pen_G1 * ds_cap * G25
G1_together = pen_G1 * s50 * G50 - G1_pen25
# U2a phi sub-parts (dW of the carbon-flow group)
def phi_parts(p, F, T):
    sc, f = CB.s_cap(T, CB.CR), F / T
    return dict(slip=(1 - CB.CR) * F, vent=CB.V_P[p] * sc * f, credit=-(CB.QA[p] - f * CB.QB[p]) * sc)
u2a_25, u2a_50 = phi_parts('U2a', F25, T25), phi_parts('U2a', F50, T50)
u2a_dphi = {k: u2a_50[k] - u2a_25[k] for k in u2a_25}
assert abs(sum(u2a_dphi.values()) - T8['U2a']['phi']['dW']) < 1e-9
u2a_dW_energy = T8['U2a']['b_steam']['dW'] + T8['U2a']['b_el']['dW']
u2a_dW_h2 = T8['U2a']['b_h2']['dW']
u2a_dW_ct = T8['U2a']['b_reag']['dW'] + T8['U2a']['b_trans']['dW']

# ---- formatting helpers -------------------------------------------------------------
def n0(x):  return f'{x:,.0f}'
def n1(x):  return f'{x:,.1f}'
def n2(x):  return f'{x:,.2f}'
def s1(x):  return f'{x:+,.1f}'
def s0(x):  return f'{x:+,.0f}'
def s2(x):  return f'{x:+,.2f}'
def z(x, f=n1):
    return '0.0' if abs(x) < 5e-7 else f(x)

# ---- CSV 1 ----------------------------------------------------------------------------
cols = (['pathway'] + [f'v_g{int(c[0])}_w{int(c[1])}_h{int(c[2])}' for c in COMBOS]
        + ['total_change', 'main_G_first_step', 'main_W_first_step', 'main_H_first_step',
           'last_step_G', 'last_step_W', 'last_step_H', 'I_GW', 'I_GH', 'I_WH', 'I_GWH', 'sum_interactions',
           'I_GW_analytic', 'I_WH_analytic', 'dW_from_b_reag_plus_b_trans',
           'shapley_G', 'shapley_W', 'shapley_H',
           'shapley_G_from_interactions', 'shapley_W_from_interactions', 'shapley_H_from_interactions',
           'shapley_G_audit_csv', 'shapley_W_audit_csv', 'shapley_H_audit_csv',
           'closure_total_minus_sum_shapley', 'closure_permutation_form',
           'E_PROC_R1c_MWh', 'E_PROC_R0_MWh', 'REAGENT_T', 'TRANSPORT_T',
           'main_G_R0', 'main_W_R0', 'main_H_R0', 'I_GW_R0', 'I_WH_R0', 'shapley_G_R0', 'shapley_W_R0', 'shapley_H_R0',
           'delta_main_G_R1c_minus_R0', 'delta_main_W_R1c_minus_R0', 'delta_I_GW_R1c_minus_R0',
           'delta_shapley_G_R1c_minus_R0', 'delta_shapley_W_R1c_minus_R0',
           'delta_main_G_predicted', 'delta_main_W_predicted', 'delta_I_GW_predicted'])
with open(os.path.join(AN, 'E5_shapley_interactions.csv'), 'w', newline='', encoding='utf-8') as fh:
    wr = csv.writer(fh); wr.writerow(cols)
    for p in ORDER:
        r, a, c = R[p], AN_I[p], CMP[p]
        row = ([p] + [f'{VALS[p][cc]:.6f}' for cc in COMBOS]
               + [f'{x:.6f}' for x in (r['total'], r['dG'], r['dW'], r['dH'], r['lG'], r['lW'], r['lH'],
                                       r['I_GW'], r['I_GH'], r['I_WH'], r['I_GWH'], r['sumI'],
                                       a['I_GW'], a['I_WH'], a['dW_capterms'],
                                       r['phiG_p'], r['phiW_p'], r['phiH_p'], r['phiG_i'], r['phiW_i'], r['phiH_i'])]
               + [audit[p]['shapley_grid'], audit[p]['shapley_waste'], audit[p]['shapley_hydrogen']]
               + [f'{r["closure_i"]:.10f}', f'{r["closure_p"]:.10f}']
               + [f'{CB.E_PROC[p]:.6f}', f'{E_PROC_R0[p]:.6f}', f'{CB.REAG[p]:.6f}', f'{CB.TRANS[p]:.6f}']
               + [f'{x:.6f}' for x in (c['dG_R0'], c['dW_R0'], c['dH_R0'], c['I_GW_R0'], c['I_WH_R0'],
                                       c['phiG_R0'], c['phiW_R0'], c['phiH_R0'],
                                       c['act_dG'], c['act_dW'], c['act_I'],
                                       r['phiG_p'] - c['phiG_R0'], r['phiW_p'] - c['phiW_R0'],
                                       c['pred_dG'], c['pred_dW'], c['pred_I'])])
        wr.writerow(row)

# ---- CSV 2 (term level, all 13) --------------------------------------------------------
with open(os.path.join(AN, 'E5_shapley_interactions_terms.csv'), 'w', newline='', encoding='utf-8') as fh:
    wr = csv.writer(fh); wr.writerow(['pathway', 'effect'] + TERMS + ['total_pathway'])
    for p in ORDER:
        for k in ('dG', 'dW', 'dH', 'I_GW', 'I_GH', 'I_WH', 'I_GWH'):
            wr.writerow([p, k] + [f'{T8[p][t][k]:.6f}' for t in TERMS] + [f'{R[p][k]:.6f}'])

# ---- Markdown ------------------------------------------------------------------------
L = []
w = L.append
w('# Task E3 - Factorial interaction terms of the 2025 -> 2050 drivers and their Shapley split, recomputed on the corrected chain (R1c)')
w('')
w('Question addressed: *"Did the Shapley decomposition correctly isolate the interaction terms among grid decarbonization, waste carbon decline, and hydrogen supply when the drivers were not additive, and was the sign of the interaction term physically interpreted?"*')
w('')
w('R1c (2026-09-19). This note supersedes `E5_shapley_interactions.md` (R1c chain) and `E_shapley_interactions.md` (submitted R0 chain); the comparison columns below are against R0, as in E2, and the R1c -> R1c movement is summarised in `P2C3_results_comparison.md` section 2. Everything below is recomputed at full floating-point precision on the corrected local chain `R1_revision/02_analyses/chain_r1/calculation_code` (R1f state: decisions D6-D13 applied by `apply_r1b.py`, then the unified modular boundary of `BOUNDARY_DESIGN_R1c.md` applied by `apply_r1c.py`; `chain_r1/CHANGES_R1.md`) by importing its `carbon_model.py` and `scenario_decomposition.py` and calling `scenario_decomposition.net()`, the function `export_files.py` section 9 uses to write `outputs/Shapley_decomposition_audit.csv`. The copy\'s own audit CSV is reproduced (Section 2). Nothing in `chain_r1`, the root chain, `outputs/`, the frozen R0 folder or the submission package was modified; the only files written are the three listed in Section 10. Unit throughout: t-CO2 per year, national scale (300 t/d, 84,000 t/y, captured CO2 67,159 t/y for every capture pathway), sign convention emissions positive.')
w('')
w('What is different from the R0 analysis (E) and why the numbers move (full comparison in Section 6):')
w('')
CAPS = [p for p in ORDER if p in CB.CAPTURES]
RS = LED['REAGENT_T_SPLIT']
w('1. **E_PROC from source kWh (D7, D10a) and the R1c modular items.** The process electricity of the nine capture pathways is now read from the ledger key `E_PROC_MWH` ('
  + ', '.join(f'{p} {CB.E_PROC[p]:,.2f}' for p in CAPS) + ' MWh; R0 had '
  + ', '.join(f'{p} {E_PROC_R0[p]:,.2f}' for p in CAPS) + ', ledger key `STATIC_R1.E_PROC_MWH`). E_PROC multiplies both the grid factor and the captured-stream scale, so every G x W interaction of a capture pathway moves with it.')
w('2. **Two new explicit groups, class CAP (R1-b in `carbon_model.py`).** `terms()` now returns seven groups: b_fix, b_steam, b_el, phi, b_h2, **b_reag** = REAGENT_T x s_cap ('
  + f'{CB.REAG["G1"]:,.2f} t/y for the nine capture pathways: solvent {RS["solvent_declared"]:,.0f} + activated carbon {RS["activated_carbon_increment"]:,.2f} + NaOH {RS["NaOH_increment"]:,.2f}, D2/D13) and **b_trans** = TRANSPORT_T x s_cap ('
  + '; '.join(f'{p} {CB.TRANS[p]:,.2f}' for p in CAPS) + ' t/y, D3/D9). In R0 these items sat inside the constant residual C_p. They scale with s_cap and contain no grid factor, so they add **W-dependence but no G-dependence**: they enter dW (and phi_W) and no interaction term (verified term by term, Section 5).')
w('3. **Anchors.** The corrected 2025 anchors (STATIC_V4, P2B2) enter only through the calibrated residual C_p, which is constant across the eight factorial cells; they change the 2025 and 2050 levels but no main effect and no interaction.')
w('')
w('Companion files with full precision: `E5_shapley_interactions.csv` (pathway level, incl. the R0 -> R1f change and its closed-form prediction) and `E5_shapley_interactions_terms.csv` (every effect of every pathway split over the seven groups and the residual).')
w('')
w('## 1. Drivers and definitions')
w('')
w('| Driver | 2025 | 2050 | Source |')
w('|---|---|---|---|')
w(f'| G, grid emission factor | {G25} t-CO2/MWh | {G50} t-CO2/MWh | `model_parameters.json` key `EF_OFFICIAL`; 2050 value `scenario_decomposition.py` line `G25, G50 = CB.EF_NAT, 0.07` (RITE 2050 CN) |')
w(f'| W, waste carbon: fossil F / total T | F = {F25:,.4f} / T = {T25:,.6f} t-CO2/y | F = {F50:,.1f} / T = {T50:,.1f} t-CO2/y | `model_parameters.json` keys `F_NAT`, `T_NAT`; 2050 values `scenario_decomposition.py` line `F50, T50 = 10416.0, 59388.0` |')
w(f'| H, hydrogen emission factor | {H25} t-CO2/t-H2 | {H50} t-CO2/t-H2 | `model_parameters.json` key `H2_FACTOR` (`now`, `y2050`) |')
w('')
w('Derived scaling quantities that the interaction terms are built from (unchanged from E; none of D6-D13 or R1c touches them):')
w('')
w(f'- dEF = {G50} - {G25} = {dEF:.4f} t-CO2/MWh')
w(f'- captured-stream scale s_cap = T cr / (T_nat cr): {s25:.6f} -> {s50:.6f}, ds_cap = {ds_cap:.6f} (the captured stream shrinks by {-ds_cap*100:.2f} % because T falls from {T25:,.0f} to {T50:,.0f})')
w(f'- plastic scale s_F = F / F_nat: {sF25:.6f} -> {sF50:.6f}, ds_F = {ds_F:.6f} (fossil carbon falls by {-ds_F*100:.2f} %)')
w(f'- fossil share f = F / T: {f25:.6f} -> {f50:.6f}')
w(f'- hydrogen scale H50 / H25 = {H2S:.6f}, i.e. dH2_scale = {dH:.6f}')
w(f'- steam-extraction export penalty STEAM_PEN = EXP_NOCC - EXP_CC = {CB.EXP_NOCC:,.0f} - {CB.EXP_CC:,.0f} = {STEAM_PEN:,.0f} MWh/y (`carbon_model.py`, `AUX, EXP_NOCC, EXP_CC = 24360.0, 43207.0, 30120.0`)')
w(f'- fixed plant balance AUX - EXP_NOCC = {CB.AUX:,.0f} - {CB.EXP_NOCC:,.0f} = {FIX_MWH:,.0f} MWh/y (net electricity export of the reference plant, identical for all 13 pathways)')
w(f'- ds_cap x dEF = {ds_cap*dEF:.6f} t-CO2 per MWh/y of captured-stream-scaled electricity: the G x W interaction per MWh of STEAM_PEN + E_PROC')
w('')
w('Let v(g,w,h) be the net result with each driver at 2025 (0) or 2050 (1). The 2^3 factorial decomposition and the Shapley split are as in E:')
w('')
w('```')
w('main effects (first step from 2025):  dG = v(1,0,0) - v(0,0,0);  dW = v(0,1,0) - v(0,0,0);  dH = v(0,0,1) - v(0,0,0)')
w('pairwise interactions:                I_GW = v(1,1,0) - v(1,0,0) - v(0,1,0) + v(0,0,0)   (and I_GH, I_WH alike)')
w('three-way interaction:                I_GWH = v(1,1,1) - v(1,1,0) - v(1,0,1) - v(0,1,1) + v(1,0,0) + v(0,1,0) + v(0,0,1) - v(0,0,0)')
w('identity:                             v(1,1,1) - v(0,0,0) = dG + dW + dH + I_GW + I_GH + I_WH + I_GWH')
w('Shapley (Harsanyi-dividend form):     phi_G = dG + I_GW/2 + I_GH/2 + I_GWH/3;  phi_W = dW + I_GW/2 + I_WH/2 + I_GWH/3;  phi_H = dH + I_GH/2 + I_WH/2 + I_GWH/3')
w('```')
w('')
w('`export_files.py` computes phi by averaging the marginal contributions over the six orderings (permutation form); both forms are computed below and agree to machine precision.')
w('')
w('## 2. Verification')
w('')
w(f'- The 8 recomputed combinations reproduce the copy\'s `outputs/Shapley_decomposition_audit.csv` (run `run_all_R1c.log`, columns `combo_g*_w*_h*`, 4 decimals): max |difference| = {chk["combo_vs_audit"]:.2e} t-CO2/y, within the 4-decimal rounding.')
w(f'- Shapley values, permutation form (as in `export_files.py`) vs interaction-split form: max |difference| = {chk["perm_vs_interaction"]:.2e} t-CO2/y.')
w(f'- Shapley values in the audit CSV (`shapley_grid`, `shapley_waste`, `shapley_hydrogen`, 4 decimals) vs recomputed: max |difference| = {chk["phi_vs_audit"]:.2e} t-CO2/y.')
w(f'- **Closure** (total change minus sum of the three Shapley values), both forms, all 13 pathways: max |discrepancy| = {chk["closure"]:.2e} t-CO2/y, i.e. 0.00000000 at 8 decimals for every pathway (CSV columns `closure_total_minus_sum_shapley`, `closure_permutation_form`, 10 decimals). The audit CSV column `closure_discrepancy` reports {chk["audit_closure_col"]:.8f} for all 13 pathways. The factorial identity total = dG + dW + dH + sum I closes to {chk["identity"]:.2e}.')
w(f'- Bracketing identities (last-step effect = first-step effect + every interaction the driver takes part in): max |difference| = {chk["bracket"]:.2e}.')
w(f'- **Analytic cross-check (closed forms re-verified on the seven-group model).** Every model term is at most bilinear in the drivers, so I_GW = (STEAM_PEN + E_PROC_p) x ds_cap x dEF for the nine capture pathways, I_GW = E_PROC_p x ds_F x dEF for the three chemical-recycling pathways, I_GW = 0 for S0; I_WH = H2_p x ds_cap x dH2_scale for the three utilization pathways and 0 otherwise; I_GH = 0 and I_GWH = 0 for every pathway. Max |factorial - analytic| over all pathways and terms = {chk["analytic"]:.2e} t-CO2/y. The two new groups do not appear in any closed form: b_reag and b_trans are class CAP (proportional to s_cap, no EF, no hydrogen factor), so their factorial effects are dW = (REAGENT_T + TRANSPORT_T) x ds_cap and nothing else (max |dG|, |dH|, |I_*| of the two groups over all pathways = {chk["captems_no_G"]:.1e}; their dW vs the closed form {chk["captems_dW"]:.1e}). The residual is constant in every cell (max effect {chk["residual_const"]:.1e}).')
w(f'- Term-level decomposition (Section 5): the effects summed over the seven groups and the residual reproduce the pathway effects to {chk["term_sum"]:.2e}.')
w(f'- R0 -> R1f change of dG, dW and I_GW (Section 6) is reproduced by the closed forms from the E_PROC change and the two new CAP terms to {chk["r0_delta_pred"]:.1e} t-CO2/y (the limit set by the 6-decimal rounding of the R0 CSV); dH and I_WH are unchanged to the same precision.')
w('')
w('## 3. Full table: main effects, interactions, Shapley split (t-CO2/y)')
w('')
w('Main effects are the first-step changes from the 2025 baseline. "Sum I" = I_GW + I_GH + I_WH + I_GWH. I_GH and I_GWH are identically zero (Section 5) and are shown to make the point.')
w('')
w('| ID | 2025 | 2050 | Total | dG | dW | dH | I_GW | I_GH | I_WH | I_GWH | Sum I | phi_G | phi_W | phi_H | Closure |')
w('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
for p in ORDER:
    r = R[p]
    w(f'| {p} | {n0(r["base"])} | {n0(r["full"])} | {s0(r["total"])} | {s0(r["dG"])} | {s0(r["dW"])} | {z(r["dH"], s0)} | {z(r["I_GW"], s1)} | {z(r["I_GH"])} | {z(r["I_WH"], s1)} | {z(r["I_GWH"])} | {z(r["sumI"], s1)} | {s1(r["phiG_p"])} | {s1(r["phiW_p"])} | {z(r["phiH_p"], s1)} | {abs(r["closure_p"]):.8f} |')
w('')
w('Bracketing check (what `scenario_decomposition.py` prints as first-step and last-step effects): the last-step effect of a driver equals its first step plus every interaction it takes part in, e.g. last-step W = dW + I_GW + I_WH + I_GWH. Full precision in the CSV columns `last_step_*`.')
w('')
w('| ID | first-step G | last-step G | width = I_GW+I_GH+I_GWH | first-step W | last-step W | width = I_GW+I_WH+I_GWH | first-step H | last-step H | width = I_GH+I_WH+I_GWH |')
w('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
for p in ORDER:
    r = R[p]
    w(f'| {p} | {s0(r["dG"])} | {s0(r["lG"])} | {z(r["lG"]-r["dG"], s1)} | {s0(r["dW"])} | {s0(r["lW"])} | {z(r["lW"]-r["dW"], s1)} | {z(r["dH"], s0)} | {z(r["lH"], s0)} | {z(r["lH"]-r["dH"], s1)} |')
w('')
w('## 4. How the Shapley values split each interaction')
w('')
w('With I_GH = I_GWH = 0 everywhere, the split reduces to: phi_G = dG + I_GW/2; phi_W = dW + I_GW/2 + I_WH/2; phi_H = dH + I_WH/2. The half-and-half share is the symmetry axiom of the Shapley value (two drivers that jointly create an interaction receive equal parts of it), and it is what makes the three attributions sum to the total. The first-step and last-step effects in the bracketing table are the two extreme one-at-a-time attributions; the Shapley value lies midway. The audit-CSV Shapley values (4 decimals) are reproduced by the arithmetic.')
w('')
w('| ID | dG | + I_GW/2 | = phi_G | audit CSV | dW | + I_GW/2 | + I_WH/2 | = phi_W | audit CSV | dH | + I_WH/2 | = phi_H | audit CSV |')
w('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
for p in ORDER:
    r = R[p]
    w(f'| {p} | {s1(r["dG"])} | {z(r["I_GW"]/2, s1)} | {s1(r["phiG_i"])} | {s1(float(audit[p]["shapley_grid"]))} | {s1(r["dW"])} | {z(r["I_GW"]/2, s1)} | {z(r["I_WH"]/2, s1)} | {s1(r["phiW_i"])} | {s1(float(audit[p]["shapley_waste"]))} | {z(r["dH"], s1)} | {z(r["I_WH"]/2, s1)} | {z(r["phiH_i"], s1)} | {z(float(audit[p]["shapley_hydrogen"]), s1)} |')
w('')
w('Consequences that matter for the manuscript text (Table 2 signs), with the R0 values from E in brackets:')
w('')
g1, g2, u1, u2a, u2b = R['G1'], R['G2'], R['U1'], R['U2a'], R['U2b']
w(f'- **G1**: the direct grid effect is a small reduction, dG = {s1(g1["dG"])} t-CO2/y (R0 {s1(CMP["G1"]["dG_R0"])}), but the Shapley grid value is positive, phi_G = {s1(g1["phiG_p"])} (R0 {s1(CMP["G1"]["phiG_R0"])}), because half of the positive G x W interaction ({s1(g1["I_GW"]/2)}) is assigned to the grid. The interaction share is now {abs(g1["I_GW"]/2/g1["dG"]):.1f} times the direct effect: the sign of the G1 grid attribution in Table 2 is a property of the interaction, not of the grid change alone.')
w(f'- **G2**: the same mechanism now flips the sign of the Table 2 entry. dG = {s1(g2["dG"])}, phi_G = {s1(g2["phiG_p"])} (R0 {s1(CMP["G2"]["phiG_R0"])}, negative). The direct effect became smaller in magnitude because E_PROC_G2 fell from {E_PROC_R0["G2"]:,.0f} to {CB.E_PROC["G2"]:,.2f} MWh (D7), so the export-credit devaluation (+{n1(T8["G2"]["b_fix"]["dG"])}) and the cheaper penalty ({s1(T8["G2"]["b_steam"]["dG"] + T8["G2"]["b_el"]["dG"])}) now cancel more completely (net {s1(g2["dG"])} instead of {s1(CMP["G2"]["dG_R0"])}), and the half-interaction ({s1(g2["I_GW"]/2)}) outweighs the net direct effect. Both grid attributions of G1/G2 are within +/-{max(abs(g1["phiG_p"]), abs(g2["phiG_p"]))/1000:.1f} kt of zero against single-driver components of 6-7 kt: the manuscript should describe them as "near zero, sign set by the interaction" rather than as a grid benefit or penalty.')
w(f'- **U1**: the opposite flip. dG = {s1(u1["dG"])} (R0 {s1(CMP["U1"]["dG_R0"])}), phi_G = {s1(u1["phiG_p"])} (R0 {s1(CMP["U1"]["phiG_R0"])}). E_PROC_U1 rose by {CMP["U1"]["dE"]:,.2f} MWh: the 15 kWh/t capture-unit line moved from the constant residual into b_el (D10a, 1,007.39 MWh), plus the R1c condenser + compressor (5,036.94 MWh) and tanker liquefaction (1,074.55 MWh), which makes the grid saving larger by {s1(CMP["U1"]["pred_dG"])} and raises the half-interaction by only {s1(CMP["U1"]["pred_I"]/2)}.')
w(f'- **U2a / U2b**: the direct waste-carbon effect is a reduction (dW = {s1(u2a["dW"])} / {s1(u2b["dW"])}; R0 {s1(CMP["U2a"]["dW_R0"])} / {s1(CMP["U2b"]["dW_R0"])}, now larger in magnitude by {s1(CMP["U2a"]["act_dW"])} because the solvent and CO2-transport terms scale with the captured stream, {s1(AN_I["U2a"]["dW_capterms"])}, and the larger E_PROC, {s1(CMP["U2a"]["part_dE_dW"])}) but the Shapley waste value stays positive ({s1(u2a["phiW_p"])} / {s1(u2b["phiW_p"])}; R0 {s1(CMP["U2a"]["phiW_R0"])} / {s1(CMP["U2b"]["phiW_R0"])}) because the waste-carbon decline shares two positive interactions, with the grid ({s1(u2a["I_GW"]/2)}) and with hydrogen ({s1(u2a["I_WH"]/2)}). The positive entry in Table 2 does not mean that less waste carbon raises the methanol result; it means that the smaller captured stream takes away part of the grid and hydrogen savings.')
w('')
w('## 5. Physical interpretation of the sign of each interaction')
w('')
w('Structure of the corrected model (`carbon_model.terms`, seven groups): v = b_fix + b_steam + b_el + phi + b_h2 + b_reag + b_trans + residual, with')
w('')
w('- b_fix = (AUX - EXP_NOCC) x EF: fixed plant electricity balance; depends on G only.')
w('- b_steam = STEAM_PEN x s_cap x EF and b_el = E_PROC_p x s_cap x EF for capture pathways (E_PROC_p x s_F x EF for chemical recycling, E_PROC_p x EF for S0, where E_PROC_S0 = 0): energy penalty of the capture and process; depends on G and W (bilinear). E_PROC is now the source-kWh value for all 13 pathways (D7, D10a) plus the R1c conditioning, liquefaction, unloading and wellhead items (r1c_modules.py).')
w('- phi: fossil-carbon flow; depends on W only (F, T, f = F/T, s_cap).')
w('- b_h2 = H2_p x s_cap x (H-scale): hydrogen burden, proportional to the captured stream; depends on W and H (bilinear), never on G because the hydrogen factor is a bottom-up PV-electrolysis chain with its own 2050 electricity factor (`scenario_decomposition.py` docstring), not the grid factor.')
w('- **b_reag = REAGENT_T x s_cap and b_trans = TRANSPORT_T x s_cap (new, class CAP)**: capture solvent burden with the two capture-unit increments, and transport of CO2, ore or slag. They depend on W only, through s_cap, and on nothing else: no grid factor (the solvent and transport burdens are declared t-CO2 figures per tonne captured or per t-km, Bisinella et al. 2021 and the source workbooks, not electricity), no hydrogen factor. They therefore contribute to dW, and through dW to phi_W, and to no interaction. Their whole W-effect is (REAGENT_T + TRANSPORT_T) x ds_cap: ' + '; '.join(f'{p} {s1(AN_I[p]["dW_capterms"])}' for p in ORDER if p in CB.CAPTURES) + ' t-CO2/y (0 for S0 and R1-R3).')
w('- residual: constant (the corrected anchors change it, not the effects).')
w('')
w('Hence a term contributes to an interaction only if it is a product of two driver-dependent factors. The bilinear terms are (s_cap or s_F) x EF and s_cap x H-scale, as in R0; the two new groups are linear in one driver. Every driver moves downward between 2025 and 2050 (EF, T, F and the hydrogen factor all fall), and the product of two negative changes is positive whenever the coefficient in front of it is positive (an energy penalty or a hydrogen burden). A positive interaction with two negative main effects means the joint saving is smaller than the sum of the two separate savings: the two drivers compete for the same tonnes.')
w('')
w('Term-by-term interaction for the four requested pathways (t-CO2/y; each column is the factorial interaction of that model term alone; they sum to the pathway interaction; all 13 pathways in `E5_shapley_interactions_terms.csv`):')
w('')
w('| ID | Interaction | b_fix | b_steam | b_el | phi | b_h2 | b_reag | b_trans | residual | Total |')
w('|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
for p in ('S0', 'G1', 'U2a', 'R1'):
    for k in ('I_GW', 'I_GH', 'I_WH', 'I_GWH'):
        w(f'| {p} | {k} | ' + ' | '.join(z(T8[p][t][k], s1) for t in TERMS) + f' | {z(R[p][k], s1)} |')
w('')
w('Main effects of the same four pathways, term by term (t-CO2/y), to show what each driver acts on:')
w('')
w('| ID | Effect | b_fix | b_steam | b_el | phi | b_h2 | b_reag | b_trans | residual | Total |')
w('|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
for p in ('S0', 'G1', 'U2a', 'R1'):
    for k in ('dG', 'dW', 'dH'):
        w(f'| {p} | {k} | ' + ' | '.join(z(T8[p][t][k], s1) for t in TERMS) + f' | {z(R[p][k], s1)} |')
w('')
s0r = R['S0']
w('### S0, reference incinerator (all interactions zero; unchanged from R0)')
w('')
w(f'- G acts only through the fixed plant balance b_fix = ({CB.AUX:,.0f} - {CB.EXP_NOCC:,.0f}) MWh/y x EF: a net electricity export that is a credit, so grid decarbonization devalues it, dG = {FIX_MWH:,.0f} x ({dEF:.3f}) = {s1(s0r["dG"])} t-CO2/y.')
w(f'- W acts only through phi = F, the fossil CO2 at the stack: dW = {F50:,.0f} - {F25:,.1f} = {s1(s0r["dW"])} t-CO2/y.')
w('- There is no term in which EF and F appear together, so I_GW = 0 exactly; S0 has no hydrogen, so I_GH = I_WH = I_GWH = 0; S0 has no capture unit, so REAGENT_T = TRANSPORT_T = 0 and the new groups do not exist for it. The reference plant is the additive case: its 2050 change is the plain sum of two independent effects. (Model assumption behind this: the plant electricity export is fixed by the plant workbook and is not tied to the waste heating value; if the export were scaled with the fossil (plastic) fraction, a G x W term would appear in S0 too. That coupling is outside the model and is stated here as a caveat, not modelled. The auxiliary-electricity regression cell 廃棄物焼却施設設定!D31, listed under "not decided", is common-mode on b_fix and would move dG of every pathway by the same amount without creating an interaction.)')
w('')
w('### G1, geological storage 1,200 m (I_GW > 0)')
w('')
tg = T8['G1']
w(f'- Grid alone: two opposite effects. The export credit is devalued exactly as in S0 ({s1(tg["b_fix"]["dG"])}), while the capture energy penalty, STEAM_PEN + E_PROC_G1 = {STEAM_PEN:,.0f} + {CB.E_PROC["G1"]:,.2f} = {pen_G1:,.2f} MWh/y, becomes cheaper ({s1(tg["b_steam"]["dG"] + tg["b_el"]["dG"])}). Net dG = {s1(g1["dG"])}: at 2025 waste the two nearly cancel. (R0: E_PROC_G1 = {E_PROC_R0["G1"]:,.0f} MWh, an arithmetic 90 kWh/t on the gross carbon T; D7 replaces it by the source value 90 kWh/t x 67,159.14 t captured = {CB.E_PROC["G1"]:,.2f} MWh, which is why dG moves from {s1(CMP["G1"]["dG_R0"])} to {s1(g1["dG"])}.)')
w(f'- Waste carbon alone: the capture slip (1 - cr) F falls ({s1(tg["phi"]["dW"])}); because the captured stream is {-ds_cap*100:.1f} % smaller, the energy penalty at the 2025 grid factor falls ({s1(tg["b_steam"]["dW"] + tg["b_el"]["dW"])}), and, new since R1 (explicit CAP terms), so do the solvent burden ({s1(tg["b_reag"]["dW"])}) and the CO2 transport ({s1(tg["b_trans"]["dW"])}), which scale with the captured stream instead of sitting in the constant residual. dW = {s1(g1["dW"])} (R0 {s1(CMP["G1"]["dW_R0"])}).')
w(f'- Interaction: I_GW = {pen_G1:,.2f} MWh/y x ds_cap ({ds_cap:.5f}) x dEF ({dEF:.3f}) = {s1(g1["I_GW"])} t-CO2/y, entirely in b_steam ({s1(tg["b_steam"]["I_GW"])}) + b_el ({s1(tg["b_el"]["I_GW"])}); the solvent and transport groups contribute exactly zero because they carry no grid factor. **Sign: positive.** Physically, the grid saving of a capture plant is proportional to its energy penalty, and the energy penalty is proportional to the CO2 it has to capture. In 2050 the waste carries less carbon (T falls from {T25:,.0f} to {T50:,.0f} t-CO2/y), so there is less CO2 to capture, a smaller steam-extraction and compression penalty, and therefore fewer grid-tonnes left for decarbonization to remove. Equivalently: once the grid is clean, shrinking the energy penalty saves less. In numbers: the penalty-related emission in 2025 is {pen_G1:,.2f} MWh/y x {G25} = {G1_pen25:,.1f} t-CO2/y; grid decarbonization alone removes {-G1_grid_alone:,.1f} t of it, the smaller captured stream alone removes {-G1_stream_alone:,.1f} t, together they remove {-G1_together:,.1f} t and not {-(G1_grid_alone + G1_stream_alone):,.1f} t. The {g1["I_GW"]:,.1f} t difference is the interaction: tonnes that both single-driver savings count, and that can only be removed once.')
w(f'- The relevant quantity is the total captured carbon T (fossil + biogenic), not the fossil fraction F: the capture unit treats the whole stream, so the energy penalty, the solvent and the transport track T (down {-ds_cap*100:.1f} %), whereas the direct stack term tracks F (down {-ds_F*100:.1f} %).')
w(f'- Relative to the reference plant (the quantity discussed in the manuscript for Table 2): since S0 has zero interaction, the interaction of the difference G1 - S0 is the same {s1(g1["I_GW"])} t-CO2/y, and the Shapley split of G1 - S0 is grid {s1(rel("G1", "phiG_p"))}, waste {s1(rel("G1", "phiW_p"))} (R0: {s1(CMP["G1"]["phiG_R0"] - CMP["S0"]["phiG_R0"])} / {s1(CMP["G1"]["phiW_R0"] - CMP["S0"]["phiW_R0"])}), against a total change of G1 - S0 of {s1(rel("G1", "total"))} (2025 {s1(rel("G1", "base"))}, 2050 {s1(rel("G1", "full"))}). For G2: grid {s1(rel("G2", "phiG_p"))}, waste {s1(rel("G2", "phiW_p"))}. These match `P2C3_results_comparison.md` section 2.')
w('')
w('### U2a, CCU methanol used as fuel (I_GW > 0, I_WH > 0, I_GH = I_GWH = 0)')
w('')
tu = T8['U2a']
w(f'- I_GW = (STEAM_PEN + E_PROC_U2a) x ds_cap x dEF = ({STEAM_PEN:,.0f} + {CB.E_PROC["U2a"]:,.2f}) x ({ds_cap:.5f}) x ({dEF:.3f}) = {s1(u2a["I_GW"])} t-CO2/y (R0 {s1(CMP["U2a"]["I_GW_R0"])} with E_PROC_U2a = {E_PROC_R0["U2a"]:,.2f} MWh; D10a moved the 15 kWh/t capture line out of the constant residual into b_el and R1c added the condenser, compressor and tanker liquefaction, together {CMP["U2a"]["dE"]:,.2f} MWh, which now take part in the interaction: {s1(CMP["U2a"]["pred_I"])}). **Positive**, same mechanism as G1 with a larger process electricity demand (`model_parameters.json` key `E_PROC_MWH`).')
w(f'- I_WH = H2_U2a x ds_cap x dH2_scale = {CB.H2["U2a"]:,.1f} x ({ds_cap:.5f}) x ({dH:.5f}) = {s1(u2a["I_WH"])} t-CO2/y (unchanged from R0; H2_U2a from `model_parameters.json` key `H2_T`: the hydrogen burden at 2025 factor and 2025 captured stream). **Positive.** The hydrogen demand of methanol synthesis is stoichiometric in the captured CO2, so a smaller captured stream in 2050 needs less hydrogen; cleaner hydrogen then has fewer tonnes to clean. Each driver alone reduces the burden (dH = {s1(u2a["dH"])}, hydrogen part of dW = {s1(u2a_dW_h2)}); jointly they reduce it by less than the sum, and the interaction is the {u2a["I_WH"]:,.0f} t counted twice.')
w(f'- I_GH = 0 exactly: the hydrogen factor is an exogenous bottom-up parameter ({H25} -> {H50} t-CO2/t-H2, dedicated PV electricity in 2050), so grid decarbonization does not touch the hydrogen term and the hydrogen change does not touch any grid term. This is a modelling choice to state explicitly in the response: with grid-powered electrolysis a negative I_GH would appear (grid decarbonization and a cleaner hydrogen factor would then be partly the same lever). The hydrogen-supply scenarios of the manuscript (`Hydrogen_supply_scenarios.csv`) treat that case separately.')
w('- I_GWH = 0 exactly: no model term contains all three drivers. The new solvent and transport groups contain one driver each and add nothing to any interaction of U2a (table above: zero in every interaction row).')
w(f'- Why the waste-carbon main effect of U2a is small (dW = {s1(u2a["dW"])}) although the interactions it enters are large: five burdens fall with the captured stream, the capture slip (1 - cr) dF = {s1(u2a_dphi["slip"])}, the energy penalty {s1(u2a_dW_energy)}, the hydrogen burden {s1(u2a_dW_h2)}, the solvent and CO2-transport terms {s1(u2a_dW_ct)} (new since R1 (explicit CAP terms)), and the process vent {s1(u2a_dphi["vent"])}; but the methanol substitution credit (QA - f QB) s_cap falls with the same stream, which raises the result by {s1(u2a_dphi["credit"])} (the lower fossil share f raises the credit per kg, which only partly compensates). Net carbon flow phi: {s1(tu["phi"]["dW"])}. Less CO2 captured means less methanol displacing fossil methanol.')
w('')
w('### R1, chemical recycling of plastics to fuel (I_GW > 0, small; unchanged from R0)')
w('')
tr = T8['R1']
w(f'- R1 captures nothing, so it has no STEAM_PEN, no hydrogen, no solvent and no CO2 transport: I_GH = I_WH = I_GWH = 0 and b_reag = b_trans = 0. Its only bilinear term is the process electricity, E_PROC_R1 = {CB.E_PROC["R1"]:,.0f} MWh/y, scaled with the plastic stream s_F = F / F_nat: I_GW = {CB.E_PROC["R1"]:,.0f} x ds_F ({ds_F:.5f}) x dEF ({dEF:.3f}) = {s1(R["R1"]["I_GW"])} t-CO2/y. **Positive**, for the same reason as the capture pathways: fewer plastics in the 2050 waste (F down {-ds_F*100:.1f} %) mean less pyrolysis electricity, so the grid saving on that electricity is smaller. The term is small because {CB.E_PROC["R1"]:,.0f} MWh/y is small.')
w(f'- Main effects: dG = {s1(tr["b_fix"]["dG"])} (export credit devalued, as S0) {s1(tr["b_el"]["dG"])} (process electricity) = {s1(R["R1"]["dG"])}; dW = {s1(tr["phi"]["dW"])} (phi = F - D_p s_F: the stack term and the diverted plastic carbon both shrink with F) {s1(tr["b_el"]["dW"])} (electricity) = {s1(R["R1"]["dW"])}.')
w('- R2 is numerically identical to R1 in this table because the two share one pyrolysis inventory and differ only in product-carbon fate, which the static balance does not see (manuscript Section 2, Table 1 note). R1-R3 are unchanged by D6-D13 and R1c (anchors, E_PROC and residuals as shipped), so every entry equals E.')
w('')
w('### General rule for the sign')
w('')
w(f'In this model every interaction is of the form (coefficient) x (change of one scale) x (change of one factor). The coefficients are burdens (energy penalty MWh/y; hydrogen burden t-CO2/y), so they are positive; both changes are negative (all drivers decarbonize); the product is positive. A negative interaction would require a credit that scales with the captured stream and is multiplied by a decarbonizing factor (for example, an avoided-electricity credit scaled with T), and no such term exists in Eq. 2; the two groups made explicit in R1 are burdens that scale with one driver only, so they cannot create an interaction of either sign. The interaction is therefore always a sub-additivity of savings: the drivers overlap, they never reinforce. Its magnitude is largest where the captured-stream-scaled burdens are largest: {imax_p} (sum I = {R[imax_p]["sumI"]:,.0f}), U2a/U2b ({R["U2a"]["sumI"]:,.0f}), then the mineralization routes with large process electricity (M1 {R["M1"]["sumI"]:,.0f}, M4 {R["M4"]["sumI"]:,.0f}).')
w('')
w('Declared sensitivities (D8-D11) and the interactions: the solvent multipliers (x0.5 / x2), every transport variant (G x0 / x2 / x4 / 1,509.91, ore x0.5 / x2, U 719) and the D8 loss term (convention A f x 3 % x cr T, ' + f'{loss25:,.1f} t/y in 2025 and {loss50:,.1f} in 2050, a function of F and T only) change dW and phi_W but no interaction term, because none of them carries a grid or hydrogen factor. In R1c the U 90 kWh/t module (the former D10c variant) is the base. The R1c scenarios that change an electricity item move I_GW by dE_PROC x ds_cap x dEF and nothing else; the largest is SC (compressor 111 instead of 65 kWh/t, +{EXTRA_SC:,.2f} MWh on each of the nine capture pathways): I_GW would become ' + ', '.join(f'{p} {I_GW_SC[p]:,.1f}' for p in ('G1', 'U1', 'U2a', 'M1')) + f' t-CO2/y (base {R["G1"]["I_GW"]:,.1f} / {R["U1"]["I_GW"]:,.1f} / {R["U2a"]["I_GW"]:,.1f} / {R["M1"]["I_GW"]:,.1f}), i.e. +{EXTRA_SC*ds_cap*dEF:,.1f} each, without changing any sign. The ship-fuel, pipeline and loss scenarios (transport and phi terms) act on dW only.')
w('')
w('## 6. What changed from the R0 analysis (E) to R1c, and why')
w('')
w('Every change is reproduced by the closed forms from two ingredients: dE = E_PROC(R1c) - E_PROC(R0) and the two new CAP-class terms, C = REAGENT_T + TRANSPORT_T. For a capture pathway: delta dG = dE x dEF; delta dW = dE x ds_cap x EF_2025 + C x ds_cap; delta I_GW = dE x ds_cap x dEF; delta dH = delta I_WH = 0. Predicted and actual agree to the 6-decimal rounding of the R0 CSV (Section 2). S0 and R1-R3: no change.')
w('')
w('| ID | E_PROC R0 -> R1f (MWh) | dE | C = R+Tr | dG R0 | dG R1c | delta dG | dW R0 | dW R1c | delta dW (of which C x ds_cap) | I_GW R0 | I_GW R1c | delta I_GW | phi_G R0 | phi_G R1c | phi_W R0 | phi_W R1c |')
w('|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
for p in ORDER:
    c, r = CMP[p], R[p]
    w(f'| {p} | {E_PROC_R0[p]:,.2f} -> {CB.E_PROC[p]:,.2f} | {z(c["dE"], s2)} | {n2(CB.REAG[p] + CB.TRANS[p])} | {s1(c["dG_R0"])} | {s1(r["dG"])} | {z(c["act_dG"], s1)} | {s1(c["dW_R0"])} | {s1(r["dW"])} | {z(c["act_dW"], s1)} ({z(AN_I[p]["dW_capterms"], s1)}) | {z(c["I_GW_R0"], s1)} | {z(r["I_GW"], s1)} | {z(c["act_I"], s1)} | {s1(c["phiG_R0"])} | {s1(r["phiG_p"])} | {s1(c["phiW_R0"])} | {s1(r["phiW_p"])} |')
w('')
w('Reading the table:')
w('')
w(f'- The largest movements of dW are the mineralization routes, where the ore transport made explicit (M1 {CB.TRANS["M1"]:,.2f}, M2 {CB.TRANS["M2"]:,.2f} t/y) and the solvent now shrink with the captured stream: M1 {s1(AN_I["M1"]["dW_capterms"])}, M2 {s1(AN_I["M2"]["dW_capterms"])} t-CO2/y of additional 2050 saving that R0 held constant. This is the same change that moves the Table 2 waste-carbon column of M1/M2 by about -1.4 / -1.9 kt.')
w(f'- G1/G2: dW moves by {s1(CMP["G1"]["act_dW"])} / {s1(CMP["G2"]["act_dW"])} (solvent + CO2 transport {s1(AN_I["G1"]["dW_capterms"])}, plus the E_PROC change R0 -> R1f {s1(CMP["G1"]["part_dE_dW"])} / {s1(CMP["G2"]["part_dE_dW"])}); dG by {s1(CMP["G1"]["act_dG"])} / {s1(CMP["G2"]["act_dG"])} (dE_PROC x dEF); I_GW by {s1(CMP["G1"]["act_I"])} / {s1(CMP["G2"]["act_I"])}. Net Shapley: phi_G {s1(CMP["G1"]["phiG_R0"])} -> {s1(g1["phiG_p"])} (G1), {s1(CMP["G2"]["phiG_R0"])} -> {s1(g2["phiG_p"])} (G2, sign flip); phi_W {s1(CMP["G1"]["phiW_R0"])} -> {s1(g1["phiW_p"])}, {s1(CMP["G2"]["phiW_R0"])} -> {s1(g2["phiW_p"])}.')
w(f'- U1/U2a/U2b: E_PROC rises by {CMP["U1"]["dE"]:,.2f} MWh (D10a capture line + R1c condenser/compressor 5,036.94 + tanker liquefaction 1,074.55), C = {CB.REAG["U1"] + CB.TRANS["U1"]:,.2f} (solvent 1,057.23 + t-km transport 449.97, D9); I_GW rises by {s1(CMP["U1"]["act_I"])}; phi_G {s1(CMP["U1"]["phiG_R0"])} -> {s1(u1["phiG_p"])} (U1, sign flip), {s1(CMP["U2a"]["phiG_R0"])} -> {s1(u2a["phiG_p"])} (U2a/U2b); phi_W {s1(CMP["U1"]["phiW_R0"])} -> {s1(u1["phiW_p"])}, {s1(CMP["U2a"]["phiW_R0"])} -> {s1(u2a["phiW_p"])}, {s1(CMP["U2b"]["phiW_R0"])} -> {s1(u2b["phiW_p"])}. phi_H is unchanged for all three (H2_T, the hydrogen factors and s_cap are untouched by D6-D13).')
w(f'- The largest interaction of any pathway is still U1 (I_GW + I_WH = {R["U1"]["I_GW"]:,.1f} + {R["U1"]["I_WH"]:,.1f} = {R["U1"]["sumI"]:,.1f} t-CO2/y; R0 {CMP["U1"]["I_GW_R0"] + CMP["U1"]["I_WH_R0"]:,.1f}); `P2C3_results_comparison.md` section 2 reports the same {R["U1"]["sumI"]:,.0f}.')
w('- The 2025 and 2050 levels (columns 2025/2050 of Section 3) carry the corrected anchors and are those of `P2C3_results_comparison.md` sections 1-2; the effects and interactions do not depend on the anchors.')
w('')
w('## 7. Reconciliation with the submitted text (to be revised with the R1c numbers)')
w('')
w(f'- Manuscript Section 3 (build_docx_v2.js line 152): *"the largest interaction term reaching 6.1 kt-CO2 per year"*. On the corrected chain the value is the U1 sum I_GW + I_WH = {R["U1"]["I_GW"]:,.1f} + {R["U1"]["I_WH"]:,.1f} = {R["U1"]["sumI"]:,.1f} t-CO2/y, i.e. **{R["U1"]["sumI"]/1000:.1f} kt** (the width of the U1 waste-carbon bracket, last-step minus first-step W). The sentence should name the two pairwise terms and their sign and cite the new SI table.')
w(f'- Table 2 grid column: G1 {s0(CMP["G1"]["phiG_R0"])} -> {s0(g1["phiG_p"])}; G2 {s0(CMP["G2"]["phiG_R0"])} -> {s0(g2["phiG_p"])} (sign flip); U1 {s0(CMP["U1"]["phiG_R0"])} -> {s0(u1["phiG_p"])} (sign flip); U2a/U2b {s0(CMP["U2a"]["phiG_R0"])} -> {s0(u2a["phiG_p"])}; M1 {s0(CMP["M1"]["phiG_R0"])} -> {s0(R["M1"]["phiG_p"])}; M2 {s0(CMP["M2"]["phiG_R0"])} -> {s0(R["M2"]["phiG_p"])}; M3 {s0(CMP["M3"]["phiG_R0"])} -> {s0(R["M3"]["phiG_p"])}; M4 {s0(CMP["M4"]["phiG_R0"])} -> {s0(R["M4"]["phiG_p"])}. Waste column: M1 {s0(CMP["M1"]["phiW_R0"])} -> {s0(R["M1"]["phiW_p"])}; M2 {s0(CMP["M2"]["phiW_R0"])} -> {s0(R["M2"]["phiW_p"])}; M3 {s0(CMP["M3"]["phiW_R0"])} -> {s0(R["M3"]["phiW_p"])}; M4 {s0(CMP["M4"]["phiW_R0"])} -> {s0(R["M4"]["phiW_p"])}; G1 {s0(CMP["G1"]["phiW_R0"])} -> {s0(g1["phiW_p"])}; G2 {s0(CMP["G2"]["phiW_R0"])} -> {s0(g2["phiW_p"])}; U1 {s0(CMP["U1"]["phiW_R0"])} -> {s0(u1["phiW_p"])}; U2a {s0(CMP["U2a"]["phiW_R0"])} -> {s0(u2a["phiW_p"])}; U2b {s0(CMP["U2b"]["phiW_R0"])} -> {s0(u2b["phiW_p"])}. S0, R1-R3 and every hydrogen entry unchanged. Sign flips against R0: G2 grid ({s0(g2["phiG_p"])}, within {abs(g2["phiG_p"])/1000:.2f} kt of zero, set by the half-interaction {s0(g2["I_GW"]/2)}; not to be read as a grid benefit or penalty) and U1 grid ({s0(u1["phiG_p"])}; in R1c this is no longer a near-zero entry: the larger E_PROC makes the grid driver a real saving of {abs(u1["phiG_p"])/1000:.1f} kt).')
w(f'- Section 3.3 / abstract quantity G1 - S0: Shapley grid {s0(rel("G1", "phiG_p"))}, waste {s0(rel("G1", "phiW_p"))} (R0 {s0(CMP["G1"]["phiG_R0"] - CMP["S0"]["phiG_R0"])} / {s0(CMP["G1"]["phiW_R0"] - CMP["S0"]["phiW_R0"])}); the interaction inside G1 - S0 is {s0(g1["I_GW"])} (R0 {s0(CMP["G1"]["I_GW_R0"])}).')
w('- `scenario_decomposition.py` (unchanged in chain_r1) still prints an `interact` column that is zero for every pathway. That is not an error: with three drivers, averaging the first-step and last-step effects assigns each pairwise interaction half to each participant, which is the Shapley split when I_GWH = 0, so the remainder is -I_GWH/2 = 0. The printed column is uninformative about the size of the interactions; the tables above replace it. (Observation only; the script was not changed.)')
w('- SI Section S9 / Table S11 state that the drivers interact and that closure is exact, but do not report the interaction terms themselves. The draft table of Section 8 answers the first half of the comment; Section 5 answers the second half (sign).')
w('')
w('## 8. Draft SI table (Table Sx, for `build_si_v2.js`)')
w('')
w('**Table Sx. Factorial main effects and interaction terms of the three 2025 -> 2050 background drivers and their Shapley split, national scale, convention A (t-CO2 per year, emissions positive).** G: grid emission factor 0.423 -> 0.07 t-CO2 MWh-1; W: waste fossil / total carbon 26,475 / 74,621 -> 10,416 / 59,388 t-CO2 y-1; H: hydrogen 5.4459 -> 3.535 t-CO2 t-1 (utilization pathways only). Main effects are first steps from 2025; I_GW and I_WH are the pairwise interactions; I_GH and I_GWH are identically zero because no term of Eq. 2 contains both the grid and the hydrogen factor or all three drivers. The Shapley values are phi_G = dG + I_GW/2, phi_W = dW + I_GW/2 + I_WH/2, phi_H = dH + I_WH/2 and sum to the total change to 8 decimals for every pathway (Shapley_decomposition_audit.csv). Closed forms: I_GW = (13,087 + E_proc) ds_cap dEF for the capture pathways, E_proc ds_F dEF for chemical recycling, 0 for the reference plant; I_WH = B_H2 ds_cap dH for the utilization pathways; with ds_cap = -0.2041, ds_F = -0.6066, dEF = -0.353 t-CO2 MWh-1, dH = -0.3509. The capture-solvent and transport terms (class CAP) enter dW only. Every interaction is positive: the drivers compete for the same tonnes, so their joint saving is smaller than the sum of the single-driver savings.')
w('')
w('| ID | 2025 | 2050 | Total change | dG | dW | dH | I_GW | I_WH | phi_G | phi_W | phi_H |')
w('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
for p in ORDER:
    r = R[p]
    w(f'| {p} | {n0(r["base"])} | {n0(r["full"])} | {s0(r["total"])} | {s0(r["dG"])} | {s0(r["dW"])} | {z(r["dH"], s0)} | {z(r["I_GW"], s0)} | {z(r["I_WH"], s0)} | {s0(r["phiG_p"])} | {s0(r["phiW_p"])} | {z(r["phiH_p"], s0)} |')
w('')
w('Footnotes for the table: (a) R2 equals R1 because both share one pyrolysis inventory (Table 1 note). (b) The hydrogen factor is a bottom-up PV-electrolysis chain independent of the grid, hence I_GH = 0; grid-powered electrolysis would create a negative G x H term (treated separately in the hydrogen-supply scenario table of the SI, `Hydrogen_supply_scenarios.csv`). (c) The reference-plant export is fixed by the plant inventory and not tied to the waste heating value, hence S0 is additive. (d) Values rounded to the tonne from the full-precision file `E5_shapley_interactions.csv`.')
w('')
w('## 9. Caveats')
w('')
w('- All interactions are conditional on the model structure (Eq. 2, seven groups): the hydrogen factor is independent of the grid (I_GH = 0), the reference-plant export is fixed (S0 interaction-free), the process electricity of chemical recycling scales with fossil carbon while the capture penalty scales with total carbon, and the solvent and transport burdens scale with the captured stream without a grid factor. These are the model assumptions of the revised version; none was changed here.')
w('- The 2050 waste values 10,416 / 59,388 t-CO2/y are the rounded per-tonne factors of the source (0.124 / 0.707 x 84,000 t); the exact per-fraction recomputation gives 10,472 for F (+0.53 %), as already disclosed in the SI (`scenario_decomposition.py` docstring). The interaction terms would move by a fraction of a percent under that alternative; not recomputed here.')
w('- Static, convention-A, national-scale result only; the dynamic layer, the regional grids (W2a table) and the Monte Carlo are outside this decomposition, as in Table 2. Under convention B the biogenic storage credit of G1/G2 and M1-M4 scales with (T - F) cr, a function of W only, so it would add to dW and phi_W but to no interaction.')
w('- Items left as shipped and listed for the authors (P2B2 section 9) that would touch the interactions if changed: the M3/M4 on-site compressor (65 kWh/t-CO2 inside E_PROC) and the G1/G2 storage-side energy (liquefaction 12,562 MWh, injection 3,331 / 9,994 MWh, not carried) would change I_GW of those pathways through E_PROC; the auxiliary-electricity regression (D31) is common-mode on b_fix and would change dG of every pathway equally without any interaction.')
w('')
w('## 10. Files and reproduction')
w('')
w('- `R1_revision/02_analyses/E5_shapley_interactions.csv`: 13 rows, the 8 combinations (6 decimals), main and last-step effects, the four interaction terms, the analytic forms, the W-effect of the two CAP groups, the Shapley values in permutation form, in interaction-split form and as read from the copy\'s audit CSV, the closure to 10 decimals, E_PROC / REAGENT_T / TRANSPORT_T, and the R0 values of E with the actual and predicted R1c - R0 change.')
w('- `R1_revision/02_analyses/E5_shapley_interactions_terms.csv`: 13 x 7 rows (dG, dW, dH, I_GW, I_GH, I_WH, I_GWH) split over b_fix, b_steam, b_el, phi, b_h2, b_reag, b_trans, residual, with the pathway total.')
w('- Generated by `R1_revision/02_analyses/E5_shapley_interactions.py` (run from any directory: it imports `carbon_model` and `scenario_decomposition` from `chain_r1/calculation_code` with bytecode writing disabled; reads the copy\'s `outputs/Shapley_decomposition_audit.csv` and the R0-based `E_shapley_interactions.csv`; asserts the thirteen checks of Section 2; writes only the three files of this section). `E_shapley_interactions.md/.csv` (R0) are left in place for the record. The SHA-256 of every file under `chain_r1` was taken before and after the run and found identical.')
w('')
with open(os.path.join(AN, 'E5_shapley_interactions.md'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(L))

print('\nKEY NUMBERS')
for p in ORDER:
    r = R[p]
    print(f'  {p:<4} base {r["base"]:>12,.4f} full {r["full"]:>12,.4f} dG {r["dG"]:>+11,.3f} dW {r["dW"]:>+11,.3f} dH {r["dH"]:>+11,.3f} '
          f'I_GW {r["I_GW"]:>+9,.3f} I_WH {r["I_WH"]:>+9,.3f} phiG {r["phiG_p"]:>+11,.3f} phiW {r["phiW_p"]:>+11,.3f} phiH {r["phiH_p"]:>+11,.3f} cl {r["closure_p"]:.2e}')
print(f'  G1-S0 phiG {rel("G1","phiG_p"):,.3f} phiW {rel("G1","phiW_p"):,.3f}; G2-S0 phiG {rel("G2","phiG_p"):,.3f} phiW {rel("G2","phiW_p"):,.3f}')
print(f'  largest sum I: {imax_p} {R[imax_p]["sumI"]:,.4f}')
print(f'  SC I_GW: {I_GW_SC}')
print(f'  loss A 2025 {loss25:,.3f} 2050 {loss50:,.3f}')
print('written: E5_shapley_interactions.md, .csv, _terms.csv')
