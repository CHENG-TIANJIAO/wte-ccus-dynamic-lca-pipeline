# -*- coding: utf-8 -*-
"""
Revision R1f of WM-26-3165 (author decision 2026-09-20): three items left "as shipped" in phase 2b
(P2B2_anchors.md section 9, items 3, 4 and 8) are corrected on top of the frozen R1e ledger.

  M4  CaO input: the source formula LCA計算!L71 = I71 x AE19 reads an unlabeled cell (0.422) beside the
      slag-handling factor; the table's own quicklime factor is AD36 = 1.12 kg-CO2 per kg (生石灰CaO).
      34,942.2477 t CaO x (1.12 - 0.422) = +24,389.69 t-CO2/y, into C_p.
  M1  Olivine ore: LCA計算!L29 = I29 x AD35 uses the talc factor (0.0334); the table's own olivine factor
      is AD28 = 0.00786 (カンラン石). 134,243.663 t x (0.00786 - 0.0334) = -3,428.58 t-CO2/y, into C_p.
      (Serpentine has no factor in the table; the talc proxy stays and is declared.)
  R3  Process electricity aligned with the anchor: the national R3 anchor is built on the pyrolysis-gas
      block (LCCO2計算（ケミカルリサイクル）.xlsx!LCA計算!I42 = 780.2034 MWh), while E_PROC[R3] carried the
      alternative block (I18 = 6,048 MWh), whose difference the residual absorbed.  E_PROC[R3] = 780.2034;
      the anchor is rebased with the aligned electricity by the rule of S0 and R1/R2 (+52.68 t, audit F1) and
      C_p no longer hides electricity;
      2050, regional and Monte Carlo values of R3 change through the scaling.  The alternative block is
      declared scenario SR3HVC.
Source workbooks are read (not modified) to assert every value.  Idempotent: a second run re-derives from
STATIC_R1E, asserts and writes nothing.  Run from this directory:  python apply_r1f.py
"""
import json
import os
import sys
import warnings

sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode = True
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r1c_modules as RM                                     # noqa: E402

LED_PATH = os.path.join(HERE, 'model_parameters.json')
led = json.load(open(LED_PATH, encoding='utf-8'))
ORDER = RM.ORDER
already = 'STATIC_R1E' in led
EF = led['EF_OFFICIAL']
TOL = 1e-6

# ---------------------------------------------------------------- source cells (read-only)
SRCDIR = r'F:\2024_張震_CCUS\04_成果物\LCCO2'
try:
    import openpyxl
    wm = openpyxl.load_workbook(os.path.join(SRCDIR, 'LCCO2計算（CO2固定化）.xlsx'), read_only=True, data_only=True)['LCA計算']
    wr = openpyxl.load_workbook(os.path.join(SRCDIR, 'LCCO2計算（ケミカルリサイクル） .xlsx'), read_only=True,
                                data_only=True)['LCA計算']
    cells = dict(I71=wm['I71'].value, AE19=wm['AE19'].value, AD36=wm['AD36'].value, AB36=wm['AB36'].value,
                 I29=wm['I29'].value, AD35=wm['AD35'].value, AD28=wm['AD28'].value, AB28=wm['AB28'].value,
                 R3_I42=wr['I42'].value, R3_I18=wr['I18'].value)
    assert cells['AB36'] == '生石灰CaO' and cells['AB28'].startswith('カンラン石'), (cells['AB36'], cells['AB28'])
    print('source cells read:', {k: v for k, v in cells.items() if not isinstance(v, str)})
except FileNotFoundError:
    cells = None
    print('source workbooks not available: using the recorded values')
I71, I29 = 34942.24765868887, 134243.66326201602
if cells:
    assert abs(cells['I71'] - I71) < 1e-6 and abs(cells['I29'] - I29) < 1e-6
    assert cells['AE19'] == 0.422 and cells['AD36'] == 1.12 and cells['AD35'] == 0.0334 and cells['AD28'] == 0.00786
    assert abs(cells['R3_I42'] / 1000 - RM.val('r3_gas_block')) < 1e-9 and cells['R3_I18'] / 1000 == 6048.0

dCaO = I71 * (1.12 - 0.422)
dOliv = I29 * (0.00786 - 0.0334)

R1E = led['STATIC_R1E'] if already else {'MWH_EF_R3': led['MWH_EF']['R3'],
    'STATIC_V4': dict(led['STATIC_V4']), 'STATIC_SRC_BASIS': dict(led['STATIC_SRC_BASIS']),
    'E_PROC_MWH': dict(led['E_PROC_MWH']), 'RESIDUAL_EXPECTED_R1D': dict(led['RESIDUAL_EXPECTED_R1D']),
    'R1C_ITEMS': led['R1C_ITEMS'], 'E_PROC_ITEMS_R1C': led['E_PROC_ITEMS_R1C']}
assert abs(R1E['STATIC_V4']['M4'] - 57508.3275) < 1e-3 and abs(R1E['STATIC_V4']['M1'] - 33881.8165) < 1e-3

r1b = led['STATIC_R1B']
B = RM.build('BASE', dict(E_PROC_MWH=r1b['E_PROC_MWH'], TRANSPORT_T=r1b['TRANSPORT_T'], REAGENT_T=r1b['REAGENT_T'],
                          solvent_declared=led['REAGENT_T_SPLIT']['solvent_declared']))
EPROC = B['eproc']
dE = {p: EPROC[p] - R1E['E_PROC_MWH'][p] for p in ORDER}
for p in ORDER:
    exp = RM.val('r3_gas_block') - 6048.0 if p == 'R3' else 0.0
    assert abs(dE[p] - exp) < 1e-9, (p, dE[p])
dV4 = {p: 0.0 for p in ORDER}
dV4['M4'], dV4['M1'] = dCaO, dOliv
# R3 anchor: the 0.433 -> 0.423 rebasing rule of S0 and R1/R2 (V4 = SRC + (0.423 - 0.433) x MWH_EF) is applied
# with the aligned electricity (audit AUDIT_R1f.md F1): MWH_EF[R3] = aux - export + E_PROC[R3]
MWH_EF_R3 = R1E.get('MWH_EF_R3', led['MWH_EF']['R3']) + dE['R3']
assert abs(led['STATIC_SRC_BASIS']['R1'] + (EF - 0.433) * led['MWH_EF']['R1'] - led['STATIC_V4']['R1']) < 1e-6
assert abs(R1E['STATIC_SRC_BASIS']['R3'] + (EF - 0.433) * (MWH_EF_R3 - dE['R3']) - R1E['STATIC_V4']['R3']) < 1e-6
dV4['R3'] = (EF - 0.433) * dE['R3']
dCp = dict(dV4)
dCp['R3'] = dV4['R3'] - dE['R3'] * EF              # the electricity leaves the residual, the rebasing enters the anchor
V4 = {p: R1E['STATIC_V4'][p] + dV4[p] for p in ORDER}
SRC = {p: R1E['STATIC_SRC_BASIS'][p] + (dV4[p] if p != 'R3' else 0.0) for p in ORDER}
RES = {p: R1E['RESIDUAL_EXPECTED_R1D'][p] + dCp[p] for p in ORDER}
print(f'M4 CaO {dCaO:+,.3f}; M1 olivine {dOliv:+,.3f}; R3 E_PROC {R1E["E_PROC_MWH"]["R3"]:,.3f} -> {EPROC["R3"]:,.4f} MWh '
      f'(anchor {dV4["R3"]:+,.3f}, C_p {dCp["R3"]:+,.3f})')

items = json.loads(json.dumps(R1E['R1C_ITEMS']))
hit = 0
for it in items['M4']:
    if it['item'].startswith('CaO input'):
        assert abs(it['value'] - I71 * 0.422) < 1e-3
        it['value'] = I71 * 1.12
        it['item'] = 'CaO input 520.29 kg per t-CO2 x 1.12 (quicklime)'
        it['status'] = 'R1f: factor corrected (0.422 -> 1.12)'
        hit += 1
for it in items['M1']:
    if it['item'].startswith('Olivine ore'):
        assert abs(it['value'] - I29 * 0.0334) < 1e-3
        it['value'] = I29 * 0.00786
        it['item'] = 'Olivine ore 1,799 kg per 900 kg CO2 x 0.00786 (olivine)'
        it['status'] = 'R1f: factor corrected (talc 0.0334 -> olivine 0.00786)'
        hit += 1
assert hit == 2
# reader-facing item labels (audit F5): declared proxies instead of 'not decided', no working-file language
import re as _re
for p in items:
    for it in items[p]:
        s = it['item']
        s = s.replace('(talc proxy, not decided)', '(talc as declared proxy)')
        s = s.replace('(whole output at the talc factor, not decided)', '(whole output displacing talc, declared proxy)')
        s = s.replace('(whole output x 0.00411, not decided)', '(whole output x 0.00411, declared proxy)')
        s = s.replace(' (explicit CAP term, recorded as decision)', '')
        s = s.replace('light oil / kerosene, 投入燃料', 'light oil, valued at the kerosene factor')
        s = s.replace('Plant auxiliary fuel (light oil), 239.115', 'Plant auxiliary fuel (light oil, valued at the kerosene factor), 239.115')
        s = s.replace('(capital workbook, CC part, 20-y divisor)', '(capital workbook, 20-year annualization)')
        assert 'not decided' not in s and not _re.search(r'[぀-ヿ一-鿿]', s), s
        it['item'] = s
for p in ('M1', 'M4'):
    s = sum(i['value'] for i in items[p] if i['in_sum'])
    assert abs(s - V4[p]) < TOL, (p, s, V4[p])

new = dict(led)
new['STATIC_R1E'] = dict(R1E, note='R1e anchors and terms, kept by apply_r1f.py as the base of the R1e -> R1f step')
new['STATIC_V4'] = V4
new['STATIC_SRC_BASIS'] = SRC
new['E_PROC_MWH'] = EPROC
new['MWH_EF'] = dict(led['MWH_EF'], R3=MWH_EF_R3)
new['E_PROC_ITEMS_R1C'] = B['eproc_items']
new['R1C_ITEMS'] = items
new['RESIDUAL_EXPECTED_R1F'] = RES
new['R1F_DELTA_CP'] = dCp
new['R1C_CONSTANTS'] = {k: {'value': v[0], 'unit': v[1], 'source': v[2]} for k, v in RM.C.items()}
new['R1C_SCENARIOS'] = {k: v[0] for k, v in RM.SCENARIOS.items()}
new['R1F_NOTE'] = ('R1f (2026-09-20, apply_r1f.py, author decision): M4 CaO factor 0.422 -> 1.12 (quicklime, table AD36; '
                   '+24,389.69 t); M1 olivine ore factor talc 0.0334 -> olivine 0.00786 (table AD28; -3,428.58 t); '
                   'E_PROC[R3] aligned with its anchor, 780.2034 MWh (pyrolysis-gas block), 6,048 MWh = scenario '
                   'SR3HVC; R3 anchor rebased with the aligned electricity (+52.68 t, audit F1); M4 CaO at the source '
                   'value 0.422 = scenario SM4CAO. Serpentine ore (talc proxy), mineral-product credits and the auxiliary-electricity '
                   'regression are kept and declared.')
LATER = ('R1C_CONSTANTS', 'R1C_SCENARIOS', 'R1G_NOTE') if 'R1G_NOTE' in led else ()   # owned by apply_r1g.py
if already:
    changed = [k for k in new if k not in LATER and json.dumps(new[k], sort_keys=True, ensure_ascii=False)
               != json.dumps(led.get(k), sort_keys=True, ensure_ascii=False)]
    assert not changed, f'ledger already carries R1f but differs in {changed}'
    print('model_parameters.json already carries R1f; verified, nothing written')
else:
    json.dump(new, open(LED_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('model_parameters.json updated with R1f')
for p in ('M1', 'M4', 'R3'):
    print(f'  {p}: V4 {R1E["STATIC_V4"][p]:,.3f} -> {V4[p]:,.3f}; residual {R1E["RESIDUAL_EXPECTED_R1D"][p]:,.3f} -> '
          f'{RES[p]:,.3f}')
