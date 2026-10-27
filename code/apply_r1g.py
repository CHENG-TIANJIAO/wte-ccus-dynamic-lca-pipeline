# -*- coding: utf-8 -*-
"""
Revision R1g of the manuscript (2026-09-20): declared scenario SM4WATER, base unchanged.

  M4 process water: the calculation sheet charges 2,600 kg per 384.4 kg CO2 (LCCO2計算（CO2固定化）.xlsx!LCA計算!D81,
  I81 = 454,249.22 t/y, x AD22 0.00065 kg-CO2/kg = 295.26 t-CO2/y); the transcription of the source data gives
  30,600 kg (DB.xlsx!CCUS!N8).  The base keeps 2,600 (author decision R1f); SM4WATER uses 30,600:
  +454,249.22 x (30,600/2,600 - 1) x 0.00065 = +3,179.74 t-CO2/y into C_p of M4 (scenario C_p channel).

Only R1C_CONSTANTS and R1C_SCENARIOS of the ledger change (+ R1G_NOTE); no anchor, residual or base term.
Idempotent.  Run from this directory after apply_r1f.py:  python apply_r1g.py
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
led = json.load(open(LED_PATH, encoding='utf-8'))
assert 'R1F_NOTE' in led, 'apply_r1f.py must have been applied first'
mass, sheet, tr, fac = (RM.C[k][0] for k in ('m4_water_mass', 'm4_water_sheet', 'm4_water_transcribed', 'm4_water_factor'))
assert abs(mass - RM.C['m4_cao_mass'][0] * sheet / 200.0) < 1e-6
assert abs(mass * fac - 295.26) < 0.01                       # LCA計算!L81
assert abs(mass * (tr / sheet - 1.0) * fac - 3179.7445) < 1e-3
assert RM.SCENARIOS['SM4WATER'][1] == dict(m4_water=tr)

new = dict(led)
new['R1C_CONSTANTS'] = {k: {'value': v[0], 'unit': v[1], 'source': v[2]} for k, v in RM.C.items()}
new['R1C_SCENARIOS'] = {k: v[0] for k, v in RM.SCENARIOS.items()}
new['R1G_NOTE'] = ('R1g (2026-09-20, apply_r1g.py): declared scenario SM4WATER, M4 process water at the source-data '
                   'transcription 30,600 instead of the sheet value 2,600 kg per 384.4 kg CO2 (+3,179.74 t-CO2/y into '
                   'C_p of M4); base unchanged. R1C_CONSTANTS and R1C_SCENARIOS are owned by this step from now on.')
changed = [k for k in new if json.dumps(new[k], sort_keys=True, ensure_ascii=False)
           != json.dumps(led.get(k), sort_keys=True, ensure_ascii=False)]
assert set(changed) <= {'R1C_CONSTANTS', 'R1C_SCENARIOS', 'R1G_NOTE'}, changed
if not changed:
    print('model_parameters.json already carries R1g; verified, nothing written')
else:
    json.dump(new, open(LED_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('model_parameters.json updated with R1g:', changed)
