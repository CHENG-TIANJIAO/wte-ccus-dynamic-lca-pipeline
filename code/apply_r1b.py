# -*- coding: utf-8 -*-
"""
Phase 2b-C, revision R1 of the manuscript: write the phase-2b (R1b) anchors and parameters
into model_parameters.json of THIS LOCAL COPY and install the tonnage-weighted regional
table.  Runs on top of apply_r1_anchors.py (phase 2C); idempotent.

Source of every number written here: R1_revision/02_analyses/P2B2_anchors.json (phase 2b
anchors, itemised cell by cell in P2B2_anchors.md; decisions D6-D13 of the authors).
Nothing is computed or fitted here; the script copies the P2B2 values into the parameter
file and asserts the closures that P2B2 itself asserts, with its own arithmetic.

What changes in model_parameters.json
  STATIC_R1 (new, documentation)  the phase-2 (R1) anchors and terms this file carried
                                   before, kept for the R0 -> R1 -> R1b comparison.
  STATIC_SRC_BASIS        <- P2B2 STATIC_SRC_BASIS_R1b: documentary itemised sum with
                             every electricity line at the factor the source ledger
                             used (STATIC_SRC_BASIS_FACTOR: 0.438 for M1-M4 and G1/G2,
                             0.433 for U1/U2a/U2b, S0 and R1-R3).  Not read by the model.
  STATIC_V4               <- P2B2 STATIC_V4_R1b: the same items with every electricity
                             line at the official 0.423 t-CO2/MWh from source MWh (D7).
  E_PROC_MWH              <- all 13 pathways from source kWh (D7): M1 46,787.54,
                             M2 21,341.65, M3 17,762.33, M4 38,365.90, G1 6,044.32 (90 kWh
                             per t-CO2 x 67,159.14 t), G2 7,253.19 (dep 1.2, declared
                             unsourced), U1 8,649.63 and U2a/U2b 16,387.34 (synthesis
                             block + the 15 kWh/t capture line moved out of the residual,
                             D10a); S0 0, R1/R2 357, R3 6,048 as shipped.
  REAGENT_T               <- 1,057.228 for the nine capture pathways = 1,008 declared
                             solvent + 40.295 activated-carbon increment (D13) + 8.932
                             NaOH increment; REAGENT_T_SPLIT documents the three parts.
  TRANSPORT_T             <- U1/U2a/U2b 449.966 (0.134 kg/t-km x 50 km x 67,159.14 t,
                             D9); G, M unchanged from phase 2.
  CAPITAL_U (new)          U1 2,014.892 / U2a, U2b 1,079.399 t-CO2/y (资本财计算.xlsx!
                             Sheet1!V10 / V9, D10b); constant, inside the residual.
  PLANT_FUEL_T, SOURCE_ELECTRICITY_MWH, FIXED_BALANCE_REMAINDER (new, documentation)
                             the light-oil fuel 239.115 t/y and the two plant electricity
                             lines at source MWh whose 11.017 MWh difference from the
                             Eq. 2 constants is the only electricity content of C_p.
  RESIDUAL_EXPECTED_R1B (new)  C_p per pathway, asserted by carbon_model.py Check 5.
  SENSITIVITIES_DECLARED (new) the D11 variants (multipliers and absolute values) that
                             compare_P2C2.py evaluates deterministically.

Regional layer (D12): region_waste_carbon.csv <- the tonnage-weighted W2a table
(P2B2_region_waste_carbon_W2a.csv); the shipped unweighted table is kept as
region_waste_carbon_unweighted.csv (asserted byte-identical to the frozen R0 file) and is
selected with REGION_WEIGHTING=unweighted (regional_model.py / regional_2050.py).

Run from this directory:  python apply_r1b.py   (a second run verifies and changes nothing)
"""
import csv
import hashlib
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P2B2 = os.path.normpath(os.path.join(HERE, '..', '..', 'P2B2_anchors.json'))
W2A_CSV = os.path.normpath(os.path.join(HERE, '..', '..', 'P2B2_region_waste_carbon_W2a.csv'))
LED_PATH = os.path.join(HERE, 'model_parameters.json')
REG_CSV = os.path.join(HERE, 'region_waste_carbon.csv')
REG_UNW = os.path.join(HERE, 'region_waste_carbon_unweighted.csv')
# SHA-256 of regions/region_waste_carbon.csv as submitted (frozen manifest,
# _R0_SUBMITTED_2026-08-07/MANIFEST_SHA256.txt line "04_root_scripts_and_data/regions/...")
SHIPPED_REGION_SHA = 'a7821261bf6773e824f89a552a96b3feef0231206d9bdab9427dae27d47d7a0f'

ORDER = ['S0', 'M1', 'M2', 'M3', 'M4', 'G1', 'G2', 'U1', 'U2a', 'U2b', 'R1', 'R2', 'R3']
CAPTURE = ['M1', 'M2', 'M3', 'M4', 'G1', 'G2', 'U1', 'U2a', 'U2b']
CLASS = {'S0': 'ref', 'M1': 'min', 'M2': 'min', 'M3': 'min', 'M4': 'min',
         'G1': 'geo', 'G2': 'geo', 'U1': 'ccu', 'U2a': 'ccu', 'U2b': 'ccu',
         'R1': 'cr', 'R2': 'cr', 'R3': 'cr'}
D_P = {'R1': 17678.0, 'R2': 17678.0, 'R3': 17650.0}          # as in carbon_model.py
AUX, EXP_NOCC, EXP_CC, CR = 24360.0, 43207.0, 30120.0, 0.90   # as in carbon_model.py
# phase-2 (R1) E_PROC values that carbon_model.py hard-coded for M, G and R (L64-68)
E_PROC_R1_HARDCODED = {'S0': 0.0, 'M1': 46453.0, 'M2': 21123.0, 'M3': 17560.0,
                       'M4': 38070.0, 'G1': 6716.0, 'G2': 8059.0,
                       'R1': 357.0, 'R2': 357.0, 'R3': 6048.0}
TOL = 1e-6


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def groups_national(led, p, e_proc, reag, trans):
    """Seven Eq. 2 groups at national conditions, same formulas as carbon_model.terms()."""
    F, T, EF = led['F_NAT'], led['T_NAT'], led['EF_OFFICIAL']
    c = CLASS[p]
    sc, sF, f = 1.0, 1.0, F / T
    b_fix = (AUX - EXP_NOCC) * EF
    cap = p in CAPTURE
    b_steam = (EXP_NOCC - EXP_CC) * sc * EF if cap else 0.0
    b_el = e_proc * (sc if cap else (sF if c == 'cr' else 1.0)) * EF
    if c == 'ref':
        phi = F
    elif c == 'geo':
        phi = (1 - CR) * F
    elif c == 'min':
        phi = (1 - CR) * F + led['L_REACTOR'][p] * sc * f
    elif c == 'ccu':
        phi = (1 - CR) * F + led['VENT'][p] * sc * f - (led['QA'][p] - f * led['QB'][p]) * sc
    else:
        phi = F - D_P[p] * sF
    b_h2 = led['H2_T'].get(p, 0.0) * sc
    return dict(b_fix=b_fix, b_steam=b_steam, b_el=b_el, phi=phi, b_h2=b_h2,
                b_reag=reag * sc, b_trans=trans * sc)


p2b2 = json.load(open(P2B2, encoding='utf-8'))
led = json.load(open(LED_PATH, encoding='utf-8'))
chain = p2b2['parameters_for_chain_stage']
basis = p2b2['basis']
cells = p2b2['source_cells_re_read']
already = 'STATIC_R1' in led

# ---------------------------------------------------------------- values to write
V4 = {p: chain['STATIC_V4'][p] for p in ORDER}
SRC = {p: chain['STATIC_SRC_BASIS'][p] for p in ORDER}
SRC_F = {p: chain['STATIC_SRC_BASIS_factor'][p] for p in ORDER}
EPROC = {p: chain['E_PROC_MWH_all13'][p] for p in ORDER}
REAG = {p: chain['REAGENT_T'][p] for p in ORDER}
TRANS = {p: chain['TRANSPORT_T'][p] for p in ORDER}
RES = {p: chain['residual_expected'][p] for p in ORDER}
split = p2b2['REAGENT_T_split']
cap_u = p2b2['CAPITAL_U']
fuel = cells['[T2024] LCCO2計算（CO2固定化）.xlsx!廃棄物処理施設ーLCA計算!H7']['value']
aux_src = basis['source_MWh']['plant_auxiliary']
exp_src = basis['source_MWh']['export_with_capture']
rem_mwh = basis['fixed_balance_MWh_remainder']['MWh']
rem_t = basis['fixed_balance_MWh_remainder']['tCO2_at_0.423']
captured = basis['captured_stream_0.9T']
EF = led['EF_OFFICIAL']
assert EF == 0.423 == basis['EF_OFFICIAL']
assert abs(captured - CR * led['T_NAT']) < 1e-9

# ---------------------------------------------------------------- closure assertions
# (1) S0 and R1-R3: unchanged from R0 and R1; the shipped rebase identity still holds
R0 = led['STATIC_R0']
for p in ('S0', 'R1', 'R2', 'R3'):
    assert abs(V4[p] - R0['STATIC_V4'][p]) < TOL and abs(SRC[p] - R0['STATIC_SRC_BASIS'][p]) < TOL, p
    assert abs(SRC[p] + (EF - led['EF_SRC']) * led['MWH_EF'][p] - V4[p]) < TOL, p
    assert SRC_F[p] == led['EF_SRC'] == 0.433
    assert REAG[p] == 0.0 and TRANS[p] == 0.0
    assert EPROC[p] == E_PROC_R1_HARDCODED[p]
# (2) nine capture pathways: SRC - V4 = (EF_src - 0.423) x (aux - export + E_PROC) MWh
for p in CAPTURE:
    ident = (SRC_F[p] - EF) * (aux_src - exp_src + EPROC[p])
    assert abs((SRC[p] - V4[p]) - ident) < TOL, (p, SRC[p] - V4[p], ident)
    assert SRC_F[p] == (0.433 if CLASS[p] == 'ccu' else 0.438), p
# (3) bottom-up: the summed items of the P2B2 tables reproduce STATIC_V4_R1b
for p in CAPTURE:
    items = p2b2['pathways'][p]['items']
    s = sum(i['value'] for i in items if i['in_sum'])
    assert abs(s - V4[p]) < TOL, (p, s, V4[p])
    # the one item not summed is the fixed-balance remainder, identical in every capture pathway
    not_summed = [i for i in items if not i['in_sum']]
    assert len(not_summed) == 1 and abs(not_summed[0]['value'] - rem_t) < 1e-9, p
# (4) seven-group closure at national conditions: V4 - sum(groups) = residual_expected
for p in ORDER:
    g = groups_national(led, p, EPROC[p], REAG[p], TRANS[p])
    res = V4[p] - sum(g.values())
    assert abs(res - RES[p]) < TOL, (p, res, RES[p])
    gj = p2b2['pathways'][p]['R1b']['groups_national']
    for k in g:
        assert abs(g[k] - gj[k]) < TOL, (p, k, g[k], gj[k])
# (5) residual composition: residual-class items + fixed-balance remainder = C_p
for p in CAPTURE:
    items = p2b2['pathways'][p]['items']
    r_items = sum(i['value'] for i in items if i['in_sum'] and i['group'] == 'residual')
    assert abs(r_items + rem_t - RES[p]) < TOL, (p, r_items + rem_t, RES[p])
    if CLASS[p] == 'geo':
        assert abs(RES[p] - rem_t) < TOL, p
    if CLASS[p] == 'ccu':
        assert abs(RES[p] - (fuel + cap_u[p] + rem_t)) < TOL, p
# (6) the fixed-balance remainder is the two plant electricity lines at source MWh
#     minus the Eq. 2 constants, at 0.423
assert abs((aux_src - AUX + EXP_CC - exp_src) - rem_mwh) < 1e-9
assert abs(rem_mwh * EF - rem_t) < 1e-9
# (7) REAGENT_T = declared solvent + two Bisinella Fig. 2 capture-unit increments
ac = 0.1e-3 * captured * cells['[T2024] LCCO2計算（CO2固定化）.xlsx!cc-LCA計算!F28']['value']
naoh = 0.1e-3 * captured * cells['[T2024] LCCO2計算（CO2固定化）.xlsx!cc-LCA計算!F32']['value']
assert split['solvent_declared'] == 1008.0
assert abs(ac - split['activated_carbon_increment']) < 1e-9
assert abs(naoh - split['NaOH_increment']) < 1e-9
for p in CAPTURE:
    assert abs(REAG[p] - (1008.0 + ac + naoh)) < 1e-9, p
# (8) TRANSPORT_T: U on the t-km basis; G 20 kg per t-CO2; M unchanged from phase 2
t_u = (cells['[T2023] LCCO2.xlsx!co2運搬!C6']['value'] * cells['[T2023] LCCO2.xlsx!co2運搬!C4']['value']
       * captured / 1000.0)
for p in ('U1', 'U2a', 'U2b'):
    assert abs(TRANS[p] - t_u) < 1e-9, p
for p in ('G1', 'G2'):
    assert abs(TRANS[p] - 20.0 * captured / 1000.0) < 1e-9, p
for p in ('M1', 'M2', 'M3', 'M4'):                  # unchanged from phase 2 (D3, D9 recorded)
    assert abs(TRANS[p] - led['TRANSPORT_T'][p]) < 1e-9, p
# (9) E_PROC from source kWh
src = basis['source_MWh']
assert abs(src['capture_unit_90kWh_per_t'] - 90.0 * captured / 1000.0) < 1e-9
assert abs(src['capture_unit_15kWh_per_t'] - 15.0 * captured / 1000.0) < 1e-9
assert abs(EPROC['G1'] - src['capture_unit_90kWh_per_t']) < 1e-9
assert abs(EPROC['G2'] - 1.2 * src['capture_unit_90kWh_per_t']) < 1e-9
for p in ('M1', 'M2', 'M3', 'M4'):
    assert abs(EPROC[p] - (src['capture_unit_90kWh_per_t'] + src['mineralization'][p])) < 1e-9, p
assert abs(EPROC['U1'] - (src['ccu_synthesis']['U1'] + src['capture_unit_15kWh_per_t'])) < 1e-9
for p in ('U2a', 'U2b'):
    assert abs(EPROC[p] - (src['ccu_synthesis']['U2'] + src['capture_unit_15kWh_per_t'])) < 1e-9, p
# the synthesis blocks are the values derive_parameters.py had written (unchanged)
u_prev = led['STATIC_R1']['E_PROC_MWH'] if already else led['E_PROC_MWH']
assert abs(u_prev['U1'] - src['ccu_synthesis']['U1']) < 1e-9
assert abs(u_prev['U2a'] - src['ccu_synthesis']['U2']) < 1e-9
# (10) capital from the capital workbook
assert abs(cap_u['U1'] - cells['[T2023] 资本财计算.xlsx!Sheet1!V10']['value']) < 1e-9
assert abs(cap_u['U2a'] - cells['[T2023] 资本财计算.xlsx!Sheet1!V9']['value']) < 1e-9
assert cap_u['U2b'] == cap_u['U2a']
# (11) delta R1b - R1 per pathway equals the P2B2 decomposition total
R1_V4 = led['STATIC_R1']['STATIC_V4'] if already else led['STATIC_V4']
for p in ORDER:
    d = p2b2['pathways'][p]['delta']
    assert abs(R1_V4[p] - d['R1_v4']) < TOL, p
    assert abs((V4[p] - R1_V4[p]) - d['total_R1b_minus_R1']) < TOL, p
    assert abs((V4[p] - R0['STATIC_V4'][p]) - d['total_R1b_minus_R0']) < TOL, p
print('closure assertions (1)-(11) passed')

# ---------------------------------------------------------------- regional table (D12)
w2a_rows = list(csv.DictReader(open(W2A_CSV, encoding='utf-8-sig')))
assert [r['region'] for r in w2a_rows] == [r['region'] for r in p2b2['regional_W2a']['rows']]
for r, j in zip(w2a_rows, p2b2['regional_W2a']['rows']):
    for k in ('plastic_pct', 'moisture_pct', 'fossil_share_of_C_pct', 'CO2_total_t_per_t_dry',
              'CO2_fossil_t_per_t_dry', 'grid_EF_2025_tCO2_per_kWh', 'grid_EF_2050_proportional',
              'grid_EF_2050_convergence'):
        assert abs(float(r[k]) - float(j[k])) < 1e-12, (r['region'], k)
if not os.path.exists(REG_UNW):
    assert sha256(REG_CSV) == SHIPPED_REGION_SHA, 'region_waste_carbon.csv is not the shipped file'
    shutil.copyfile(REG_CSV, REG_UNW)
    print('kept the shipped (unweighted) table as region_waste_carbon_unweighted.csv')
assert sha256(REG_UNW) == SHIPPED_REGION_SHA, 'unweighted table differs from the frozen R0 file'
unw_rows = list(csv.DictReader(open(REG_UNW, encoding='utf-8-sig')))
for r, u in zip(w2a_rows, unw_rows):                # same regions, same grid columns
    assert r['region'] == u['region'] and r['n_prefectures'] == u['n_prefectures']
    for k in ('grid_EF_2025_tCO2_per_kWh', 'grid_EF_2050_proportional', 'grid_EF_2050_convergence'):
        assert r[k] == u[k], (r['region'], k)
if sha256(REG_CSV) != sha256(W2A_CSV):
    # R1e guard: the R1e transparent rebuild replaced this table; never copy the R1b W2a table back
    if os.path.exists(os.path.join(HERE, 'region_waste_carbon_W1.csv')) or 'R1D_NOTE' in led:
        sys.exit('apply_r1b.py refused: region_waste_carbon.csv carries the R1e rebuild '
                 '(R1_revision/02_analyses/R1e_regional/build_R1e.py); re-running R1b would overwrite it')
    shutil.copyfile(W2A_CSV, REG_CSV)
    print('installed the tonnage-weighted W2a table as region_waste_carbon.csv')
assert sha256(REG_CSV) == sha256(W2A_CSV)

# ---------------------------------------------------------------- write the ledger
new = dict(led)
if not already:
    new['STATIC_R1'] = {
        'STATIC_SRC_BASIS': dict(led['STATIC_SRC_BASIS']), 'STATIC_V4': dict(led['STATIC_V4']),
        'E_PROC_MWH': {**E_PROC_R1_HARDCODED, **led['E_PROC_MWH']},
        'REAGENT_T': dict(led['REAGENT_T']), 'TRANSPORT_T': dict(led['TRANSPORT_T']),
        'note': 'phase-2 (R1) anchors and terms written by apply_r1_anchors.py from '
                'P2B_corrected_anchors.json, kept for the R0 -> R1 -> R1b comparison only; '
                'E_PROC_MWH lists the values carbon_model.py hard-coded for M, G and R in '
                'that state; not read by the model'}
new['STATIC_SRC_BASIS'] = SRC
new['STATIC_SRC_BASIS_FACTOR'] = SRC_F
new['STATIC_V4'] = V4
new['E_PROC_MWH'] = EPROC
new['REAGENT_T'] = REAG
new['REAGENT_T_SPLIT'] = {'solvent_declared': 1008.0, 'activated_carbon_increment': ac,
                          'NaOH_increment': naoh, 'total': 1008.0 + ac + naoh,
                          'note': 'solvent: Bisinella et al. 2021, Waste Manag. 128, 99-113, '
                                  'Table 4, 12 kg CO2-eq per t ww x 84,000 t; increments: same '
                                  'paper Fig. 2, 0.1 kg per t-CO2 captured x 67,159.14 t at the '
                                  'workbook factors 6 (activated carbon, cc-LCA計算!F28) and 1.33 '
                                  '(NaOH, F32); one CAP-class term (D13)'}
new['TRANSPORT_T'] = TRANS
new['CAPITAL_U'] = {'U1': cap_u['U1'], 'U2a': cap_u['U2a'], 'U2b': cap_u['U2b'],
                    'placement': 'residual (constant)', 'source': cap_u['source'],
                    'replaces': 'LCCO2.xlsx!まとめ!J12 = 1770 / K12 = 803 (hard-coded), D10b'}
new['PLANT_FUEL_T'] = {'value': fuel, 'applies_to': 'S0 and the nine capture pathways (inside C_p)',
                       'source': 'LCCO2計算（CO2固定化）.xlsx!廃棄物処理施設ーLCA計算!H7 = LCCO2.xlsx!'
                                 'まとめ!D6 (light oil / kerosene, 1.09 L/t x 2.61 kg-CO2/L)'}
new['SOURCE_ELECTRICITY_MWH'] = {
    'plant_auxiliary': aux_src, 'export_with_capture': exp_src,
    'source': '廃棄物処理施設ーLCA計算!E6 = 廃棄物焼却施設設定!D31 x 300 x 280; E34 = D15 x 300 x 280',
    'note': 'Eq. 2 evaluates b_fix and b_steam with the rounded constants 24,360 / 43,207 / '
            '30,120 MWh; the difference to the source MWh is FIXED_BALANCE_REMAINDER'}
new['FIXED_BALANCE_REMAINDER'] = {'MWh': rem_mwh, 'tCO2_at_0.423': rem_t,
                                  'formula': basis['fixed_balance_MWh_remainder']['formula']}
new['RESIDUAL_EXPECTED_R1B'] = RES
new['RESIDUAL_COMPOSITION_R1B'] = dict(p2b2['residual_composition_R1b'])
new['SENSITIVITIES_DECLARED'] = {
    'note': 'D11 declared deterministic variants evaluated by chain_r1/compare_P2C2.py '
            '(static 2025, 2050 national, regional counts); the Monte Carlo multipliers of '
            'the same terms (lognormal GSD 1.15) are narrower than these ranges',
    'solvent_multipliers_on_declared_1008': [0.5, 2.0],
    'G_transport_multipliers': [0.0, 2.0, 4.0],
    'G_transport_workbook_chain_tCO2_per_y': 1509.9104511857463,
    'M12_ore_transport_multipliers': [0.5, 2.0],
    'losses_G_fraction_of_captured': 0.03,
    'losses_note': 'Bisinella et al. 2021: 1 % transport + 2 % storage; convention A charges '
                   'f x 3 % x cr T, convention B the full 3 % x cr T (D8)',
    'U_transport_shipped_tCO2_per_y': 719.0,
    'U_full_capture_electricity_kWh_per_t': 90.0,
    'U_extra_capture_electricity_MWh': 75.0 * captured / 1000.0}
new['EXPLICIT_TERMS_NOTE'] = (
    'REAGENT_T and TRANSPORT_T are national-scale t-CO2/y, class CAP (multiplied by s_cap in '
    'every region, year and draw). Sources (P2B2_anchors.json): solvent 1,008 (Bisinella et '
    'al. 2021, Waste Manag. 128, 99-113, Table 4, 12 kg CO2-eq per t ww x 84,000 t) + '
    'activated-carbon 40.30 and NaOH 8.93 capture-unit increments (same paper Fig. 2, 0.1 kg '
    'per t-CO2 at the workbook factors); G transport 20 kg-CO2 per t-CO2 x 67,159.14 t '
    '(Section 2.4); M1/M2 ore transport LCCO2計算（CO2固定化）.xlsx!運搬 on the t-km basis; '
    'M3/M4 slag transport 運搬!C67 / C78 (explicit CAP term, decision recorded, D9); U CO2 '
    'transport 0.134 kg/t-km x 50 km x 67,159.14 t (LCCO2.xlsx!co2運搬!C6, C4; D9). '
    'Declared sensitivities: SENSITIVITIES_DECLARED.')
new['R1B_NOTE'] = (
    'Phase 2b (2026-09-19, apply_r1b.py): D6 plant APC/boiler chemicals 1,010.87 t/y removed '
    'from M1-M4 (outside the boundary for every pathway); D7 every electricity line of the '
    'nine capture pathways at 0.423 from source MWh, E_PROC_MWH for all 13 pathways, no '
    'rebase remainder in C_p; D9 U transport on the t-km basis; D10a U capture-unit '
    'electricity (1,007.387 MWh) inside E_PROC / b_el; D10b U capital from the capital '
    'workbook; D12 tonnage-weighted regional table; D13 activated-carbon increment. The '
    'rebase identity STATIC_V4 = STATIC_SRC_BASIS + (0.423 - 0.433) x MWH_EF now holds for '
    'S0 and R1-R3 only; for the nine capture pathways STATIC_SRC_BASIS - STATIC_V4 = '
    '(STATIC_SRC_BASIS_FACTOR - 0.423) x (24,348.90 - 30,119.91 + E_PROC_MWH) MWh.')

if already:
    changed = [k for k in new if json.dumps(new[k], sort_keys=True) != json.dumps(led.get(k), sort_keys=True)]
    assert not changed, f'ledger already carries R1b but differs in {changed}'
    print('model_parameters.json already carries the R1b parameters; verified, nothing written')
else:
    with open(LED_PATH, 'w', encoding='utf-8') as fh:
        json.dump(new, fh, ensure_ascii=False, indent=1)
    print('model_parameters.json updated with the P2B2 (R1b) parameters')

print(f'{"path":<5}{"R0 V4":>13}{"R1 V4":>13}{"R1b V4":>13}{"d R1b-R1":>11}{"SRC (factor)":>20}'
      f'{"E_PROC MWh":>12}{"REAG":>9}{"TRANS":>10}{"C_p":>12}')
for p in ORDER:
    print(f'{p:<5}{R0["STATIC_V4"][p]:>13,.2f}{R1_V4[p]:>13,.2f}{V4[p]:>13,.2f}'
          f'{V4[p] - R1_V4[p]:>+11,.2f}{SRC[p]:>13,.2f} ({SRC_F[p]:.3f})'
          f'{EPROC[p]:>12,.1f}{REAG[p]:>9,.1f}{TRANS[p]:>10,.1f}{RES[p]:>12,.2f}')
print(f'regional table: region_waste_carbon.csv = W2a (sha256 {sha256(REG_CSV)[:12]}...), '
      f'region_waste_carbon_unweighted.csv = shipped ({SHIPPED_REGION_SHA[:12]}...)')
