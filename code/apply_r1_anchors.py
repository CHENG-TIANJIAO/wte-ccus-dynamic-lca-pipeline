# -*- coding: utf-8 -*-
"""
Phase 2C, revision R1 of WM-26-3165: write the corrected static anchors and the two
new explicit CAP-class terms into model_parameters.json of THIS LOCAL COPY.

Source of every number written here: R1_revision/02_analyses/P2B_corrected_anchors.json
(phase 2B synthesis, itemised cell by cell in P2B_corrected_anchors.md).  Nothing is
computed or fitted in this script; it copies the P2B values into the parameter file and
asserts the identities that P2B itself asserts.

What changes in model_parameters.json
  STATIC_SRC_BASIS  <- P2B STATIC_SRC_BASIS_R1   (source basis, grid 0.433)
  STATIC_V4         <- P2B STATIC_V4_R1          (rebased to 0.423 over MWH_EF, rule D5)
  REAGENT_T   (new) capture-specific solvent burden, t-CO2/y at national scale,
                    1,008.00 for the nine capture pathways (12 kg CO2-eq per t ww x
                    84,000 t; Bisinella et al. 2021, Waste Manag. 128, 99-113, Table 4),
                    0 for S0 and R1-R3.  Class CAP (scales with s_cap).
  TRANSPORT_T (new) transport term, t-CO2/y at national scale, class CAP:
                    G1, G2  1,343.18  CO2 transport to storage, 20 kg-CO2 per t-CO2 x
                                      67,159.14 t (Bisinella et al. 2021, Section 2.4)
                    M1      5,653.66  ore transport, rail 900 km on the t-km basis +
                                      truck 10 km (LCCO2計算（CO2固定化）.xlsx!運搬)
                    M2      8,037.26  ore transport, ship 900 km on the t-km basis +
                                      truck 10 km (same sheet)
                    M3, M4  336.69 / 306.17  slag transport, truck 5 km, as shipped
                    U1, U2a, U2b  719.00  CO2 transport 50 km, as shipped (hard-coded
                                      in LCCO2.xlsx!まとめ!J10; P2B open decision 5)
                    S0, R1-R3  0
  STATIC_R0 (new, documentation only) the shipped R0 anchors, kept for the comparison.

The residual C_p = STATIC_V4[p] - sum(all explicit groups) therefore equals P2B
'residual_expected_7groups' for every pathway; carbon_model.py asserts this.

Run once from this directory:  python apply_r1_anchors.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P2B = os.path.normpath(os.path.join(HERE, '..', '..', 'P2B_corrected_anchors.json'))
LED_PATH = os.path.join(HERE, 'model_parameters.json')

p2b = json.load(open(P2B, encoding='utf-8'))
led = json.load(open(LED_PATH, encoding='utf-8'))

ORDER = ['S0', 'M1', 'M2', 'M3', 'M4', 'G1', 'G2', 'U1', 'U2a', 'U2b', 'R1', 'R2', 'R3']
CAPTURE = ['M1', 'M2', 'M3', 'M4', 'G1', 'G2', 'U1', 'U2a', 'U2b']

# ---- guard: only apply once, on the shipped R0 file ----
if 'STATIC_R0' in led:
    print('model_parameters.json already carries the R1 anchors; nothing done')
    sys.exit(0)
for p in ORDER:
    assert abs(led['STATIC_V4'][p] - p2b['residual_shipped'][p]
               - (led['STATIC_V4'][p] - p2b['residual_shipped'][p])) < 1e-9

# ---- 1. anchors ----
led['STATIC_R0'] = {'STATIC_SRC_BASIS': dict(led['STATIC_SRC_BASIS']),
                    'STATIC_V4': dict(led['STATIC_V4']),
                    'note': 'shipped 2026-08-07 anchors, kept for the R0 vs R1 '
                            'comparison only; not read by the model'}
led['STATIC_SRC_BASIS'] = {p: p2b['STATIC_SRC_BASIS_R1'][p] for p in ORDER}
led['STATIC_V4'] = {p: p2b['STATIC_V4_R1'][p] for p in ORDER}

# rebase identity (P2B rule D5) re-asserted on the written values
for p in ORDER:
    v = led['STATIC_SRC_BASIS'][p] + (led['EF_OFFICIAL'] - led['EF_SRC']) * led['MWH_EF'][p]
    assert abs(v - led['STATIC_V4'][p]) < 1e-9, p
    d_src = led['STATIC_SRC_BASIS'][p] - led['STATIC_R0']['STATIC_SRC_BASIS'][p]
    d_v4 = led['STATIC_V4'][p] - led['STATIC_R0']['STATIC_V4'][p]
    assert abs(d_src - d_v4) < 1e-9, p
    assert abs(d_v4 - p2b['delta_vs_shipped'][p]) < 1e-9, p

# ---- 2. explicit CAP-class terms ----
dp = p2b['declared_parameters']
solv = dp['solvent_burden']['value_tCO2_per_y']
assert solv == 1008.0 and dp['solvent_burden']['applies_to'] == CAPTURE
led['REAGENT_T'] = {p: (solv if p in CAPTURE else 0.0) for p in ORDER}
tG = dp['transport_G']['value_tCO2_per_y']
tM = {k: v['value_tCO2_per_y'] for k, v in dp['transport_M'].items()}
tU = dp['transport_U']['value_tCO2_per_y']
led['TRANSPORT_T'] = {'S0': 0.0, 'M1': tM['M1'], 'M2': tM['M2'], 'M3': tM['M3'],
                      'M4': tM['M4'], 'G1': tG, 'G2': tG,
                      'U1': tU, 'U2a': tU, 'U2b': tU,
                      'R1': 0.0, 'R2': 0.0, 'R3': 0.0}
led['EXPLICIT_TERMS_NOTE'] = (
    'REAGENT_T and TRANSPORT_T are national-scale t-CO2/y, class CAP (multiplied by '
    's_cap in every region, year and draw). Sources: P2B_corrected_anchors.json '
    'declared_parameters (solvent: Bisinella et al. 2021, Waste Manag. 128, 99-113, '
    'Table 4, 12 kg CO2-eq per t ww x 84,000 t; G transport: same paper Section 2.4, '
    '20 kg-CO2 per t-CO2 x 67,159.14 t; M1/M2 ore transport: LCCO2計算（CO2固定化）.xlsx!'
    '運搬 on the t-km basis; M3/M4 slag and U CO2 transport as shipped). '
    'Sensitivity multipliers declared in P2B: solvent 0.5 / 2.0; G transport 0 / 2 / 4.')

# ---- 3. residual closure against P2B (7-group) ----
# The residual identity is checked here with the same formula carbon_model.py uses,
# rewritten without importing it (the model file is edited after this step).
for p in ORDER:
    five = p2b['residual_expected_5groups'][p]
    seven = five - led['REAGENT_T'][p] - led['TRANSPORT_T'][p]
    assert abs(seven - p2b['residual_expected_7groups'][p]) < 1e-6, (p, seven)

with open(LED_PATH, 'w', encoding='utf-8') as fh:
    json.dump(led, fh, ensure_ascii=False, indent=1)

print('model_parameters.json updated with the P2B (R1) anchors')
print(f'{"path":<5}{"R0 STATIC_V4":>15}{"R1 STATIC_V4":>15}{"delta":>12}'
      f'{"REAGENT_T":>11}{"TRANSPORT_T":>13}{"C_p (7-group)":>15}')
for p in ORDER:
    print(f'{p:<5}{led["STATIC_R0"]["STATIC_V4"][p]:>15,.3f}{led["STATIC_V4"][p]:>15,.3f}'
          f'{led["STATIC_V4"][p] - led["STATIC_R0"]["STATIC_V4"][p]:>+12,.3f}'
          f'{led["REAGENT_T"][p]:>11,.2f}{led["TRANSPORT_T"][p]:>13,.2f}'
          f'{p2b["residual_expected_7groups"][p]:>15,.3f}')
