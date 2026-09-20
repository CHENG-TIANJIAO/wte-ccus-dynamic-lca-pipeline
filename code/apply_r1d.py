# -*- coding: utf-8 -*-
"""
Revision R1d of WM-26-3165: the corrections from the independent audit of R1c
(R1_revision/02_analyses/AUDIT_R1c_modules.md, section 5), written into
model_parameters.json of THIS LOCAL COPY on top of apply_r1c.py.  Idempotent: a
second run re-derives everything from STATIC_R1C, asserts, and writes nothing.

  A1  G1, G2    plant light-oil fuel 239.115 t/y added to C_p (it is in S0, M1-M4 and U
                already; the submitted G formula never read 廃棄物処理施設ーLCA計算!H7).
  A2  M1-M4, G1, G2  annualised capital of the capture unit 745.649 t/y added to C_p,
                so the common capture module (module 2) carries it in all nine capture
                pathways, as U already did (资本财计算.xlsx rows 9/10, CC part).
  A3  G2        ship mode: receiving-side pumping to the injection pressure 4.5 kWh/t
                (IEAGHG 2020-10 p. 25) REPLACES unloading 2.5 + wellhead boost 7 kWh/t
                = -5 kWh/t x Q (the boost stays in the pipeline scenario).
  A4  scenarios SU15 removed; SUC (U compressor removed) and SMC (M1/M3/M4 compressor
                removed) added as upper bounds of a possible compression overlap.
                Scenarios only; nothing in the base.
  B2  U1, U2a, U2b  author decision 2026-09-19: capital = capture unit only, for all nine;
                the synthesis-equipment capital (U1 1,269.243, U2 333.750) leaves C_p and
                becomes scenario SCAPU (its U1 list also holds calcium-looping capture
                equipment, audit R1d B3).  Scenario SL30: capital life 30 instead of 20.
  B1  R1C_ITEMS rebuilt so that every capture pathway's item list sums to STATIC_V4.

STATIC_V4[p] += dE_PROC x 0.423 + dC_p.  C_p changes by exactly A1 + A2; the expected
residuals are written as RESIDUAL_EXPECTED_R1D.  Run from this directory:
    python apply_r1d.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r1c_modules as RM                                     # noqa: E402

LED_PATH = os.path.join(HERE, 'model_parameters.json')
ORDER, CAPTURE, CLASS = RM.ORDER, RM.CAPTURES, RM.CLASS
TOL = 1e-6
led = json.load(open(LED_PATH, encoding='utf-8'))
already = 'STATIC_R1C' in led
assert 'STATIC_R1B' in led, 'apply_r1c.py must have run first'
EF, Q = led['EF_OFFICIAL'], RM.Q_CAPTURED
k = Q / 1000.0

R1C = led['STATIC_R1C'] if already else {'R1C_ITEMS': led['R1C_ITEMS'],
    'STATIC_V4': dict(led['STATIC_V4']), 'STATIC_SRC_BASIS': dict(led['STATIC_SRC_BASIS']),
    'E_PROC_MWH': dict(led['E_PROC_MWH']), 'TRANSPORT_T': dict(led['TRANSPORT_T']),
    'REAGENT_T': dict(led['REAGENT_T'])}
# the R1c anchors, as audited (AUDIT_R1c_modules.md section 1)
for p, v in (('G1', 5953.1746), ('G2', 6152.0329), ('U1', 23367.4892), ('U2a', -45469.2639)):
    assert abs(R1C['STATIC_V4'][p] - v) < 1e-3, p

r1b = led['STATIC_R1B']
B = RM.build('BASE', dict(E_PROC_MWH=r1b['E_PROC_MWH'], TRANSPORT_T=r1b['TRANSPORT_T'],
                          REAGENT_T=r1b['REAGENT_T'],
                          solvent_declared=led['REAGENT_T_SPLIT']['solvent_declared']))
EPROC, TRANS = B['eproc'], B['trans']
dE = {p: EPROC[p] - R1C['E_PROC_MWH'][p] for p in ORDER}
dT = {p: TRANS[p] - R1C['TRANSPORT_T'][p] for p in ORDER}
for p in ORDER:                                   # A3 is the only base change of the modules
    exp = (RM.val('ship_unload_pump') - RM.val('unloading') - RM.val('wellhead_boost')) * k if p == 'G2' else 0.0
    assert abs(dE[p] - exp) < 1e-9 and abs(dT[p]) < 1e-9, (p, dE[p], dT[p])
assert abs(dE['G2'] - (-5.0 * k)) < 1e-9
print(f'A3  G2 E_PROC {R1C["E_PROC_MWH"]["G2"]:,.3f} -> {EPROC["G2"]:,.3f} MWh ({dE["G2"]:+,.3f}; '
      f'{dE["G2"] * EF:+,.3f} t)')

FUEL = led['PLANT_FUEL_T']['value']
CAPC = RM.val('capture_capital')
cc = (777.789 * 3.01 + 3686.752 * 3.41) / 20.0                # capital workbook, CC part
assert abs(FUEL - 239.115) < 1e-3 and abs(cc - CAPC) < 1e-3, (FUEL, cc)
dC = {p: 0.0 for p in ORDER}
for p in ('G1', 'G2'):
    dC[p] += FUEL                                                                   # A1
for p in ('M1', 'M2', 'M3', 'M4', 'G1', 'G2'):
    dC[p] += CAPC                                                                   # A2
SYN = {'U1': RM.val('synthesis_capital_U1'), 'U2a': RM.val('synthesis_capital_U2'), 'U2b': RM.val('synthesis_capital_U2')}
for p in SYN:                               # B2 (author decision): capital = capture unit only, for all nine
    assert abs(led['CAPITAL_U'][p] - CAPC - SYN[p]) < 1e-3, p
    SYN[p] = led['CAPITAL_U'][p] - CAPC      # exact complement, so that C_p(U) = fuel + CAPC + remainder
    dC[p] -= SYN[p]
V4 = {p: R1C['STATIC_V4'][p] + dE[p] * EF + dC[p] for p in ORDER}
FAC = led['STATIC_SRC_BASIS_FACTOR']
SRC = {p: R1C['STATIC_SRC_BASIS'][p] + dE[p] * FAC[p] + dC[p] for p in ORDER}
RES0 = led['RESIDUAL_EXPECTED_R1B']
RES = {p: RES0[p] + dC[p] for p in ORDER}

# the residual of every G / U pathway is now fuel + capital + fixed-balance remainder
rem = led['FIXED_BALANCE_REMAINDER']['tCO2_at_0.423']
cap_u = led['CAPITAL_U']
for p in ('G1', 'G2'):
    assert abs(RES[p] - (FUEL + CAPC + rem)) < TOL, p
for p in ('U1', 'U2a', 'U2b'):
    assert abs(RES[p] - (FUEL + CAPC + rem)) < TOL, p     # synthesis capital removed (B2)
print(f'A1  G1/G2 C_p += light oil {FUEL:,.3f}')
print(f'A2  M1-M4, G1, G2 C_p += capture-unit capital {CAPC:,.3f} (U already: CC {CAPC:,.3f} + synthesis '
      f'{cap_u["U1"] - CAPC:,.3f} / {cap_u["U2a"] - CAPC:,.3f})')

new = dict(led)
new['STATIC_R1C'] = dict(R1C, note='R1c anchors and terms (apply_r1c.py), kept by apply_r1d.py as the base '
                                   'of the R1c -> R1d step; not read by the model')
new['STATIC_V4'] = V4
new['STATIC_SRC_BASIS'] = SRC
new['E_PROC_MWH'] = EPROC
new['E_PROC_ITEMS_R1C'] = B['eproc_items']
new['TRANSPORT_ITEMS_R1C'] = B['trans_items']
new['RESIDUAL_EXPECTED_R1D'] = RES

# bottom-up item list (audit R1d B1): module items rebuilt from the R1d build, C_p additions listed
ITEMS = {}
for p in CAPTURE:
    out = [dict(i) for i in R1C['R1C_ITEMS'][p] if not i['status'].startswith('R1c:')]
    for i in B['eproc_items'][p]:
        if i['key'] in ('mineralization', 'synthesis'):
            continue
        out.append(dict(item=f'{i["label"]}, {i["kWh_per_t"]:g} kWh/t-CO2 x {Q:,.4f} t = {i["MWh"]:,.3f} MWh at 0.423',
                        value=i['MWh'] * EF, group='b_el', module=str(i['module']), in_sum=True,
                        status='R1d: module item (r1c_modules.py)', source=i['source']))
    for i in B['trans_items'][p]:
        if i['key'] in ('ore_slag_transport', 'road_tanker'):
            continue
        out.append(dict(item=i['label'], value=i['t'], group='b_trans', module=str(i['module']), in_sum=True,
                        status='R1d: module item (r1c_modules.py)', source=i['source']))
    if CLASS[p] == 'geo':
        out.append(dict(item='Plant auxiliary fuel (light oil), 239.115', value=FUEL, group='residual', module='1',
                        in_sum=True, status='R1d: added (audit A1)', source=led['PLANT_FUEL_T'].get('source', '')))
    if CLASS[p] == 'ccu':
        out = [o for o in out if not o['item'].startswith('Capital goods')]
    if CLASS[p] in ('geo', 'min', 'ccu'):
        out.append(dict(item='Capital goods of the capture unit, annualised (capital workbook, CC part, 20-y divisor)',
                        value=CAPC, group='residual', module='2', in_sum=True, status='R1d: added (audit A2)',
                        source=RM.C['capture_capital'][2]))
    s = sum(o['value'] for o in out if o['in_sum'])
    assert abs(s - V4[p]) < TOL, (p, s, V4[p])
    ITEMS[p] = out
print('B1  R1C_ITEMS rebuilt: the item list of each capture pathway sums to the R1d STATIC_V4 (< 1e-6)')
new['R1C_ITEMS'] = ITEMS
new['CAPITAL_U'] = dict(led['CAPITAL_U'], placement='R1d: NOT in the base. The capture part (745.649) is '
                       'CAPITAL_CAPTURE_T, carried by all nine capture pathways; the synthesis part is declared '
                       'scenario SCAPU. Values kept as the R1b record (capture + synthesis).')
new['CAPITAL_CAPTURE_T'] = {'value': CAPC, 'applies_to': 'all nine capture pathways (inside C_p)',
                            'source': RM.C['capture_capital'][2]}
new['PLANT_FUEL_T'] = dict(led['PLANT_FUEL_T'], applies_to='S0 and the nine capture pathways (inside C_p); '
                           'G1/G2 from R1d (audit A1)')
new['R1C_CONSTANTS'] = {kk: {'value': v[0], 'unit': v[1], 'source': v[2]} for kk, v in RM.C.items()}
new['R1C_SCENARIOS'] = {kk: v[0] for kk, v in RM.SCENARIOS.items()}
new['R1D_NOTE'] = (
    'R1d (2026-09-19, apply_r1d.py; AUDIT_R1c_modules.md section 5): A1 G1/G2 plant light-oil fuel 239.115 '
    'into C_p; A2 capture-unit capital 745.649 into C_p of M1-M4, G1, G2 (U already carried it); A3 G2 ship '
    'mode: pumping to injection pressure 4.5 kWh/t replaces 2.5 + 7 (-5 kWh/t x Q); A4 scenario SU15 replaced '
    'by SUC and SMC (compressor-overlap upper bounds); B2 U synthesis capital out of C_p (scenario SCAPU), '
    'capital life 20 kept (scenario SL30). Residuals: RESIDUAL_EXPECTED_R1D. apply_r1c.py must not '
    'be re-run on this ledger.')

if already:
    changed = [kk for kk in new if json.dumps(new[kk], sort_keys=True, ensure_ascii=False)
               != json.dumps(led.get(kk), sort_keys=True, ensure_ascii=False)]
    assert not changed, f'ledger already carries R1d but differs in {changed}'
    print('model_parameters.json already carries R1d; verified, nothing written')
else:
    with open(LED_PATH, 'w', encoding='utf-8') as fh:
        json.dump(new, fh, ensure_ascii=False, indent=1)
    print('model_parameters.json updated with R1d')

print(f'\n{"path":<5}{"R1c V4":>13}{"R1d V4":>13}{"d":>11}{"residual R1d":>14}')
for p in ORDER:
    print(f'{p:<5}{R1C["STATIC_V4"][p]:>13,.3f}{V4[p]:>13,.3f}{V4[p] - R1C["STATIC_V4"][p]:>+11,.3f}{RES[p]:>14,.3f}')
