# -*- coding: utf-8 -*-
"""
Revision R1c of WM-26-3165: write the unified modular boundary (BOUNDARY_DESIGN_R1c.md,
sections 1, 2, 6, decisions E1-E8) into model_parameters.json of THIS LOCAL COPY.
Runs on top of apply_r1b.py (phase 2b, R1b); idempotent (a second run re-derives
everything from the R1b state kept under STATIC_R1B, asserts, and writes nothing).

Source of every new number: r1c_modules.py, whose constants cite
R1_revision/03_new_sources/CONDITIONING_ENERGY_CANDIDATES.md row by row; everything R1c
does not touch is carried from the R1b ledger, which is asserted equal to
R1_revision/02_analyses/P2B2_anchors.json first.  Nothing is fitted.

R1c base relative to R1b (captured stream Q = 67,159.1422656 t-CO2/y; MWh = kWh/t x Q/1000):
  U1, U2a, U2b  E_PROC += condenser 10 + compressor 65 kWh/t = 5,036.936 MWh (common 90 kWh/t
                module, design C1) and += tanker liquefaction 16 kWh/t = 1,074.546 MWh
                (analogy, IEAGHG 2020-10 Table 10-7, decision E7); TRANSPORT_T unchanged
                (road tanker 50 km, 449.966 t).
  G1, G2        E_PROC = capture + conditioning 90 kWh/t 6,044.323 MWh (the unsourced G2
                dep = 1.2 removed, design C5) + ship liquefaction 17.4 kWh/t 1,168.569 MWh
                (Roussanaly et al. 2021 Table 3) + unloading 2.5 kWh/t 167.898 MWh (IEAGHG
                Table 10-11) (+ G2 wellhead boost 10.7 -> 15 MPa 7 kWh/t 470.114 MWh,
                Koornneef et al. 2008 Table 4; G1 none, decision E4); TRANSPORT_T = ship fuel
                22 kg/t 1,477.501 t (author-DERIVED, Roussanaly Table 4 x IMO Table 21,
                decision E5) + road to port 10 km x 0.134 kg/t-km 89.993 t (source-workbook
                factor, unsourced, disclosed) = 1,567.494 t.
  M1-M4, S0, R1-R3  unchanged (M already carried the 90 kWh/t module).
  STATIC_V4[p]  += dMWh x 0.423 + dTRANSPORT_T (bottom-up anchors), so C_p is exactly R1b.
  STATIC_SRC_BASIS[p] += dMWh x STATIC_SRC_BASIS_FACTOR[p] + dTRANSPORT_T (documentary; the
                identity SRC - V4 = (factor - 0.423) x (aux - export + E_PROC) keeps holding).

Keys written: STATIC_R1B (new; the R1b values, documentation and base of the scenario
switch), STATIC_V4, STATIC_SRC_BASIS, E_PROC_MWH, TRANSPORT_T, E_PROC_ITEMS_R1C,
TRANSPORT_ITEMS_R1C, R1C_ITEMS (bottom-up item list, capture pathways), R1C_CONSTANTS,
R1C_SCENARIOS, R1C_NOTE.  REAGENT_T, residuals, regional table, hydrogen: unchanged.

Run from this directory:  python apply_r1c.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r1c_modules as RM                                     # noqa: E402

ANA = os.path.normpath(os.path.join(HERE, '..', '..'))
P2B2 = os.path.join(ANA, 'P2B2_anchors.json')
CAND = os.path.normpath(os.path.join(ANA, '..', '03_new_sources', 'CONDITIONING_ENERGY_CANDIDATES.md'))
LED_PATH = os.path.join(HERE, 'model_parameters.json')
ORDER, CAPTURE, CLASS = RM.ORDER, RM.CAPTURES, RM.CLASS
D_P = {'R1': 17678.0, 'R2': 17678.0, 'R3': 17650.0}          # as in carbon_model.py
AUX, EXP_NOCC, EXP_CC, CR = 24360.0, 43207.0, 30120.0, 0.90   # as in carbon_model.py
TOL = 1e-6

p2b2 = json.load(open(P2B2, encoding='utf-8'))
led = json.load(open(LED_PATH, encoding='utf-8'))
already = 'STATIC_R1B' in led
EF = led['EF_OFFICIAL']
Q = p2b2['basis']['captured_stream_0.9T']
assert EF == 0.423 and abs(Q - RM.Q_CAPTURED) < 1e-9 and abs(Q - CR * led['T_NAT']) < 1e-9

# ---------------------------------------------------------------- (0) the R1b state
if already:
    R1B = led['STATIC_R1B']
else:
    R1B = {'STATIC_V4': dict(led['STATIC_V4']), 'STATIC_SRC_BASIS': dict(led['STATIC_SRC_BASIS']),
           'E_PROC_MWH': dict(led['E_PROC_MWH']), 'TRANSPORT_T': dict(led['TRANSPORT_T']),
           'REAGENT_T': dict(led['REAGENT_T'])}
chain = p2b2['parameters_for_chain_stage']
for p in ORDER:                                   # R1b ledger == P2B2 (phase 2b)
    assert abs(R1B['STATIC_V4'][p] - chain['STATIC_V4'][p]) < 1e-9, p
    assert abs(R1B['STATIC_SRC_BASIS'][p] - chain['STATIC_SRC_BASIS'][p]) < 1e-9, p
    assert abs(R1B['E_PROC_MWH'][p] - chain['E_PROC_MWH_all13'][p]) < 1e-9, p
    assert abs(R1B['TRANSPORT_T'][p] - chain['TRANSPORT_T'][p]) < 1e-9, p
    assert abs(R1B['REAGENT_T'][p] - chain['REAGENT_T'][p]) < 1e-9, p
    assert abs(led['RESIDUAL_EXPECTED_R1B'][p] - chain['residual_expected'][p]) < 1e-9, p
    assert led['REAGENT_T'][p] == R1B['REAGENT_T'][p], p         # R1c does not touch reagents
print('(0) R1b ledger state equals P2B2_anchors.json (V4, SRC, E_PROC, TRANSPORT_T, REAGENT_T, C_p)')

# the candidates file is the cited source of every new constant
cand = open(CAND, encoding='utf-8').read()
for needle in ('**17.4** (7 barg)', '**16.0** (pressurised)', '**7** kWh/t CO2', '2.53',
               '**22.0** (HFO)', '**39.00** (Low P, pressurised)', '**111** kWh/t', '**9** (from 90 bara)',
               '**3 and 4% per 1000 km**', '**1 to 2%**'):
    assert needle in cand, f'citation anchor not found in CONDITIONING_ENERGY_CANDIDATES.md: {needle}'
print('    every new constant is found in 03_new_sources/CONDITIONING_ENERGY_CANDIDATES.md')

src = p2b2['basis']['source_MWh']
r1b_in = dict(E_PROC_MWH=R1B['E_PROC_MWH'], TRANSPORT_T=R1B['TRANSPORT_T'], REAGENT_T=R1B['REAGENT_T'],
              solvent_declared=led['REAGENT_T_SPLIT']['solvent_declared'])
B = RM.build('BASE', r1b_in)
EPROC, TRANS = B['eproc'], B['trans']
k = Q / 1000.0

# ---------------------------------------------------------------- (1) the named items
def item(p, key, kind='e'):
    lst = B['eproc_items'][p] if kind == 'e' else B['trans_items'][p]
    hit = [i for i in lst if i['key'] == key]
    return (hit[0]['MWh'] if kind == 'e' else hit[0]['t']) if hit else 0.0


SPEC = {   # task statement / design section 2 and 6, three decimals
    'U condenser + compressor 75 kWh/t': (item('U1', 'condenser') + item('U1', 'compressor'), 5036.936),
    'U tanker liquefaction 16 kWh/t': (item('U1', 'tanker_liquefaction'), 1074.546),
    'G capture + conditioning 90 kWh/t': (item('G2', 'capture_unit') + item('G2', 'condenser') + item('G2', 'compressor'), 6044.323),
    'G ship liquefaction 17.4 kWh/t': (item('G1', 'ship_liquefaction'), 1168.569),
    'G unloading 2.5 kWh/t': (item('G1', 'unloading'), 167.898),
    'G2 wellhead boost 7 kWh/t': (item('G2', 'wellhead_boost'), 470.114),
    'G ship fuel 22 kg/t': (item('G1', 'ship', 't'), 1477.501),
    'G road to port 10 km': (item('G1', 'road_to_port', 't'), 89.993),
    'G TRANSPORT_T': (TRANS['G1'], 1567.494),
    'SC +46 kWh/t': ((RM.val('compressor_high') - RM.val('compressor')) * k, 3089.321),
    'SP pipeline 20 kg/t': (RM.val('pipeline') * Q / 1000.0, 1343.183),
    'SIPCC ship 35 kg/t': (RM.val('ship_ipcc') * Q / 1000.0, 2350.570),
    'SL39 +21.6 kWh/t': ((RM.val('ship_liquefaction_high') - RM.val('ship_liquefaction')) * k, 1450.637),
    'SUL9 -7 kWh/t': ((RM.val('tanker_liquefaction') - RM.val('tanker_liquefaction_low')) * k, 470.114),
}
for name, (v, e) in SPEC.items():
    assert abs(v - e) < 5e-4, (name, v, e)
assert item('G1', 'wellhead_boost') == 0.0
print('(1) named items reproduce the task / design values to 3 decimals:')
for name, (v, e) in SPEC.items():
    print(f'      {name:<38}{v:>12,.4f}')

# (2) every E_PROC item is kWh/t x Q/1000 or a source-workbook MWh carried unchanged from R1b
for p in ORDER:
    for i in B['eproc_items'][p]:
        if i['kWh_per_t'] is not None:
            assert abs(i['MWh'] - i['kWh_per_t'] * k) < 1e-9, (p, i['key'])
        elif i['key'] == 'mineralization':
            assert abs(i['MWh'] - src['mineralization'][p]) < 1e-6, p
        elif i['key'] == 'synthesis':
            assert abs(i['MWh'] - src['ccu_synthesis']['U1' if p == 'U1' else 'U2']) < 1e-6, p
        else:
            assert i['key'] == 'recycling_process' and i['MWh'] == R1B['E_PROC_MWH'][p], (p, i['key'])
    for i in B['trans_items'][p]:
        assert i['t'] > 0, (p, i['key'])
print('(2) every E_PROC item = kWh/t x Q/1000 (named, cited) or a source-workbook MWh carried from R1b')

# (3) delta decomposition per pathway
dE = {p: EPROC[p] - R1B['E_PROC_MWH'][p] for p in ORDER}
dT = {p: TRANS[p] - R1B['TRANSPORT_T'][p] for p in ORDER}
exp_dE = {p: 0.0 for p in ORDER}
exp_dT = {p: 0.0 for p in ORDER}
for p in ('U1', 'U2a', 'U2b'):
    exp_dE[p] = (10.0 + 65.0 + 16.0) * k
exp_dE['G1'] = (17.4 + 2.5) * k
exp_dE['G2'] = (17.4 + 2.5 + 7.0) * k - 0.2 * 90.0 * k                 # dep 1.2 removed
for p in ('G1', 'G2'):
    exp_dT[p] = (22.0 + 0.134 * 10.0 - 20.0) * Q / 1000.0
for p in ORDER:
    assert abs(dE[p] - exp_dE[p]) < 1e-9 and abs(dT[p] - exp_dT[p]) < 1e-9, (p, dE[p], dT[p])
assert abs(R1B['E_PROC_MWH']['G2'] - 1.2 * src['capture_unit_90kWh_per_t']) < 1e-9
print('(3) dE_PROC / dTRANSPORT_T per pathway = the named items (G2 includes -0.2 x 6,044.323 MWh, dep 1.2 removed)')

V4 = {p: R1B['STATIC_V4'][p] + dE[p] * EF + dT[p] for p in ORDER}
FAC = led['STATIC_SRC_BASIS_FACTOR']
SRC = {p: R1B['STATIC_SRC_BASIS'][p] + dE[p] * FAC[p] + dT[p] for p in ORDER}

# (4) bottom-up item list of the nine capture pathways
def module_of(name):
    rules = [('Uncaptured fossil slip', '2', 'phi'), ('Reactor CO2 loss', '5b', 'phi'),
             ('Plant auxiliary electricity', '1', 'b_fix'),
             ('Electricity export with capture', '1 (baseline export, b_fix) + 2 (steam-extraction penalty, b_steam)', 'b_fix+b_steam'),
             ('Mineralization electricity', '5b', 'b_el'), ('Plant auxiliary fuel', '1', 'residual'),
             ('Process heat', '5b', 'residual'), ('NaCl reagent', '5b', 'residual'),
             ('NaHCO3 reagent', '5b', 'residual'), ('(NH4)2SO4', '5b', 'residual'), ('NH3 make-up', '5b', 'residual'),
             ('NH4Cl make-up', '5b', 'residual'), ('CaO input', '5b', 'residual'), ('Olivine ore', '5b', 'residual'),
             ('Serpentine ore', '5b', 'residual'), ('Carbide-slag handling', '5b', 'residual'),
             ('Steel-slag handling', '5b', 'residual'), ('Process water', '5b', 'residual'),
             ('Process / wash water', '5b', 'residual'), ('Mineral-product credit', '5b', 'residual'),
             ('Capture solvent burden', '2', 'b_reag'), ('Activated-carbon capture increment', '2', 'b_reag'),
             ('NaOH capture increment', '2', 'b_reag'), ('Ore transport', '4d', 'b_trans'),
             ('Slag transport', '4d', 'b_trans'), ('CCU process vent', '5c', 'phi'),
             ('Product substitution credit', '6', 'phi'), ('CCU synthesis electricity', '5c', 'b_el'),
             ('Hydrogen', '5c', 'b_h2'), ('Capital goods', '2 + 5c (capture and CCU equipment)', 'residual'),
             ('CO2 transport to the synthesis plant', '4c', 'b_trans'),
             ('Fixed-balance MWh remainder', '1', 'residual (derived, not summed)')]
    hits = [r for r in rules if name.startswith(r[0])]
    assert len(hits) == 1, name
    return hits[0][1], hits[0][2]


R1C_ITEMS = {}
for p in CAPTURE:
    out = []
    for it in p2b2['pathways'][p]['items']:
        nm = it['item']
        if nm.startswith('Capture-unit electricity') or nm.startswith('CO2 transport to storage'):
            continue                                 # replaced by the R1c module items below
        mod, grp = module_of(nm)
        assert grp == it['group'], (p, nm, grp, it['group'])
        out.append(dict(item=nm, value=it['value'], group=grp, module=mod, in_sum=it['in_sum'],
                        status='R1b item, unchanged', source=it['source']))
    for i in B['eproc_items'][p]:
        if i['key'] in ('mineralization', 'synthesis'):
            continue                                 # already in the P2B2 list at the same MWh
        out.append(dict(item=f'{i["label"]}, {i["kWh_per_t"]:g} kWh/t-CO2 x {Q:,.4f} t = {i["MWh"]:,.3f} MWh at 0.423',
                        value=i['MWh'] * EF, group='b_el', module=str(i['module']), in_sum=True,
                        status=('R1c: split of the R1b 90 kWh/t line' if (i['key'] in ('capture_unit', 'condenser', 'compressor')
                                                                          and CLASS[p] != 'ccu')
                                else ('R1c: split of the R1b 15 kWh/t line' if i['key'] == 'capture_unit'
                                      else 'R1c: new item')),
                        source=i['source']))
    for i in B['trans_items'][p]:
        if i['key'] in ('ore_slag_transport', 'road_tanker'):
            continue                                 # already in the P2B2 list at the same value
        out.append(dict(item=i['label'], value=i['t'], group='b_trans', module=str(i['module']), in_sum=True,
                        status='R1c: new item (replaces the R1b 20 kg/t CO2 transport)', source=i['source']))
    s = sum(o['value'] for o in out if o['in_sum'])
    assert abs(s - V4[p]) < TOL, (p, s, V4[p])
    R1C_ITEMS[p] = out
print('(4) bottom-up: the R1c item list of each capture pathway sums to the new STATIC_V4 (< 1e-6)')

# (5) seven-group closure at national conditions: residual unchanged vs R1b
def groups_national(p):
    F, T = led['F_NAT'], led['T_NAT']
    c, f = CLASS[p], F / T
    cap = p in CAPTURE
    b_fix = (AUX - EXP_NOCC) * EF
    b_steam = (EXP_NOCC - EXP_CC) * EF if cap else 0.0
    b_el = EPROC[p] * EF
    if c == 'ref':
        phi = F
    elif c == 'geo':
        phi = (1 - CR) * F
    elif c == 'min':
        phi = (1 - CR) * F + led['L_REACTOR'][p] * f
    elif c == 'ccu':
        phi = (1 - CR) * F + led['VENT'][p] * f - (led['QA'][p] - f * led['QB'][p])
    else:
        phi = F - D_P[p]
    return [b_fix, b_steam, b_el, phi, led['H2_T'].get(p, 0.0), led['REAGENT_T'][p], TRANS[p]]


RES = led['RESIDUAL_EXPECTED_R1B']
mx = max(abs((V4[p] - sum(groups_national(p))) - RES[p]) for p in ORDER)
assert mx < 1e-9, mx
print(f'(5) residual C_p of all 13 pathways unchanged vs R1b: max |C_p(R1c) - C_p(R1b)| = {mx:.2e}')

# (6) source-basis identity (documentary)
aux_s = led['SOURCE_ELECTRICITY_MWH']['plant_auxiliary']; exp_s = led['SOURCE_ELECTRICITY_MWH']['export_with_capture']
for p in ORDER:
    if p in CAPTURE:
        assert abs((SRC[p] - V4[p]) - (FAC[p] - EF) * (aux_s - exp_s + EPROC[p])) < TOL, p
    else:
        assert SRC[p] == R1B['STATIC_SRC_BASIS'][p] and V4[p] == R1B['STATIC_V4'][p], p
print('(6) STATIC_SRC_BASIS identity SRC - V4 = (factor - 0.423) x (aux - export + E_PROC) holds for the nine')

# (7) unchanged pathways
for p in ('S0', 'R1', 'R2', 'R3', 'M1', 'M2', 'M3', 'M4'):
    assert dE[p] == 0.0 and dT[p] == 0.0 and V4[p] == R1B['STATIC_V4'][p], p
print('(7) S0, M1-M4, R1-R3 unchanged')

# (8) every E_PROC item of every pathway appears once; conditioning items once per capture pathway
for p in ORDER:
    keys = [i['key'] for i in B['eproc_items'][p]] + [i['key'] for i in B['trans_items'][p]]
    assert len(keys) == len(set(keys)), p
    if p in CAPTURE:
        assert keys.count('compressor') == 1 and keys.count('capture_unit') == 1 and keys.count('condenser') == 1, p
print('(8) each named item appears exactly once per pathway; compression once per capture pathway')

# ---------------------------------------------------------------- write
new = dict(led)
new['STATIC_R1B'] = dict(R1B, note='phase-2b (R1b) anchors and terms (apply_r1b.py, P2B2_anchors.json), kept by '
                                   'apply_r1c.py: documentation of the R1b -> R1c step and base of the '
                                   'R1C_SCENARIO switch (scenario R1B); not read by the base model')
new['STATIC_V4'] = V4
new['STATIC_SRC_BASIS'] = SRC
new['E_PROC_MWH'] = EPROC
new['TRANSPORT_T'] = TRANS
new['E_PROC_ITEMS_R1C'] = B['eproc_items']
new['TRANSPORT_ITEMS_R1C'] = B['trans_items']
new['R1C_ITEMS'] = R1C_ITEMS
new['R1C_CONSTANTS'] = {kk: {'value': v[0], 'unit': v[1], 'source': v[2]} for kk, v in RM.C.items()}
new['R1C_SCENARIOS'] = {kk: v[0] for kk, v in RM.SCENARIOS.items()}
new['R1C_NOTE'] = (
    'R1c (2026-09-19, apply_r1c.py; BOUNDARY_DESIGN_R1c.md sections 1, 2, 6, decisions E1-E8): common capture + '
    'conditioning module 90 kWh/t (15 capture unit + 10 condenser + 65 compressor) for all nine capture pathways '
    '(U1/U2a/U2b +5,036.936 MWh); U road-tanker liquefaction 16 kWh/t (+1,074.546 MWh, analogy); G1/G2 '
    'Japan-oriented ship scenario: liquefaction 17.4 kWh/t (1,168.569 MWh), unloading 2.5 kWh/t (167.898 MWh), '
    'G2 wellhead boost 7 kWh/t (470.114 MWh), G1 none, dep 1.2 removed; G TRANSPORT_T ship fuel 22 kg/t '
    '(1,477.501, author-derived) + 10 km road to port (89.993) = 1,567.494 t. STATIC_V4 += dMWh x 0.423 + '
    'dTRANSPORT_T; C_p unchanged (RESIDUAL_EXPECTED_R1B). Declared scenarios: R1C_SCENARIOS, selected with the '
    'environment variable R1C_SCENARIO or carbon_model.set_scenario(); definitions and citations in '
    'r1c_modules.py and R1C_CONSTANTS. SENSITIVITIES_DECLARED is the R1b list (its U 90 kWh/t entry is the '
    'R1c base now). apply_r1b.py must not be re-run on this ledger (it would refuse: its idempotency check '
    'finds the R1c keys changed).')

if already:
    changed = [kk for kk in new if json.dumps(new[kk], sort_keys=True, ensure_ascii=False)
               != json.dumps(led.get(kk), sort_keys=True, ensure_ascii=False)]
    assert not changed, f'ledger already carries R1c but differs in {changed}'
    print('model_parameters.json already carries the R1c parameters; verified, nothing written')
else:
    with open(LED_PATH, 'w', encoding='utf-8') as fh:
        json.dump(new, fh, ensure_ascii=False, indent=1)
    print('model_parameters.json updated with the R1c parameters')

print(f'\n{"path":<5}{"R1b V4":>13}{"R1c V4":>13}{"d V4":>11}{"E_PROC R1b":>12}{"E_PROC R1c":>12}'
      f'{"TRANS R1b":>11}{"TRANS R1c":>11}{"SRC R1c":>13}')
for p in ORDER:
    print(f'{p:<5}{R1B["STATIC_V4"][p]:>13,.3f}{V4[p]:>13,.3f}{V4[p] - R1B["STATIC_V4"][p]:>+11,.3f}'
          f'{R1B["E_PROC_MWH"][p]:>12,.3f}{EPROC[p]:>12,.3f}{R1B["TRANSPORT_T"][p]:>11,.3f}{TRANS[p]:>11,.3f}'
          f'{SRC[p]:>13,.3f}')
