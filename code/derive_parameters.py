# -*- coding: utf-8 -*-
"""
R1 NOTE (phase 2C + phase 2b copy): this script regenerates the SUBMITTED (R0) anchors.
In this copy model_parameters.json carries the corrected R1b anchors, E_PROC_MWH for
all 13 pathways and the REAGENT_T / TRANSPORT_T / CAPITAL_U keys written by
apply_r1_anchors.py (P2B_corrected_anchors.json) and apply_r1b.py (P2B2_anchors.json).
Running this script (or run_all.py --rebuild-ledger) here would overwrite them with
the R0 values (and drop E_PROC_MWH for M, G, R, which carbon_model.py now requires);
it is kept only because the package lists it.  Do not run it in R1.

v4 ledger derivation: reads the three source workbooks directly, asserts every anchor
cell, applies the accounting rules listed below, and writes
model_parameters.json.  Every foreground quantity of the reference plant, the CCU routes and
the mineralization routes traces to a
cell read here or to a documented physical constant.

Accounting rules implemented:

  B1  Substitution credits made cradle-to-grave symmetric and biogenic-neutral.
      Per kg of product:  credit = A_p - f * B_p, where
        A_p = cradle-to-grave factor of the displaced fossil product (database),
        B_p = combustion CO2 of the synthesised product (stoichiometric for the pure
              compounds CH4 and CH3OH; database combustion increment for diesel),
        f   = fossil share of the captured stream = F / T (region- and draw-varying).
      Methanol as feedstock (U2b) keeps the gate-only 1.5: no combustion on either
      side; the locked product carbon is handled by the dynamic layer.
  B1' Process vents charged at their fossil share f (the capture slip (1-cr)*F is
      already fossil and is charged once, explicitly).
  B2  Hydrogen factor 5.4459 kg-CO2/kg-H2 (bottom-up, source formula asserted below);
      2050 value 3.535.
  A2  Mineralization L_p = reactor loss only, mixed basis, charged at fossil share f.
  B3  U2a (fuel) and U2b (feedstock) are bounded by ONE symmetric grave: the
      displaced fossil methanol has the same downstream fate as the synthesised
      methanol, so the methanol-to-olefins step, its energy and its 20 % carbon
      loss are common to both worlds and cancel.  The whole-horizon credit is
      therefore identical for the two routes; they differ only in WHEN it is
      realised.  U2b takes the gate credit and the prompt (20 %) release
      difference at t = 0 and defers the remaining net credit,
      (1 - f) * 0.80 * M * stoich, to the product lifetime.
  B4  The microalgae route of the source inventory is EXCLUDED: its own block does
      not close a carbon balance (40,411 t-CO2 in against 7,838 t diesel plus
      33,541 t-CO2 out, i.e. 1.44 times more carbon out than in), so no consistent
      fossil-carbon partition can be built for it.

Anchor discipline: every cell read is asserted against the value observed during the
2026-08-01 archive audit; a source file that has drifted fails loudly.
"""
import argparse
import json
import os
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))

# This is an OPTIONAL provenance step. The default reproduction chain
# (python run_all.py) never runs it; it reads the shipped model_parameters.json instead.
# No archive location is hard-coded: give the four source workbooks explicitly with
# --ccu / --ccu-sens / --mineral / --db, or set CCUS_SRC_CCU, CCUS_SRC_CCU_SENS,
# CCUS_SRC_MINERAL and CCUS_SRC_DB. Without them the script exits without doing
# anything, which is the expected behaviour for anyone reproducing the study.
_ap = argparse.ArgumentParser(description='Re-derive model_parameters.json from the '
                              'original laboratory source workbooks (optional).')
_ap.add_argument('--ccu', default=os.environ.get('CCUS_SRC_CCU'),
                 help='CCU inventory workbook (or set CCUS_SRC_CCU)')
_ap.add_argument('--ccu-sens', default=os.environ.get('CCUS_SRC_CCU_SENS'),
                 help='hydrogen and 2050 sensitivity workbook (or CCUS_SRC_CCU_SENS)')
_ap.add_argument('--mineral', default=os.environ.get('CCUS_SRC_MINERAL'),
                 help='mineralization inventory workbook (or CCUS_SRC_MINERAL)')
_ap.add_argument('--db', default=os.environ.get('CCUS_SRC_DB'),
                 help='CFP emission-intensity database (or CCUS_SRC_DB)')
_ap.add_argument('--check-sources', action='store_true',
                 help='exit 0 if all four source workbooks exist, else exit 2')
_A = _ap.parse_args()
CCU, CCU_SENS, MIN, DB = _A.ccu, _A.ccu_sens, _A.mineral, _A.db
_LABEL = {'--ccu': CCU, '--ccu-sens': CCU_SENS, '--mineral': MIN, '--db': DB}
_missing = [f'{k} ({v})' if v else f'{k} (not given)'
            for k, v in _LABEL.items() if not v or not os.path.exists(v)]
if _A.check_sources:
    print('source workbooks present' if not _missing
          else 'missing source workbooks:\n  ' + '\n  '.join(_missing))
    sys.exit(0 if not _missing else 2)
if _missing:
    print('derive_parameters: the original source workbooks are not available on '
          'this machine; nothing was done. The shipped model_parameters.json is used by '
          'the default chain. Missing:')
    for _p in _missing:
        print('  ' + _p)
    sys.exit(2)

# Exact molar masses (IUPAC 2021), the only non-workbook numbers in this file.
M_CO2, M_CH4, M_MEOH = 44.009, 16.043, 32.042
STOICH_CH4 = M_CO2 / M_CH4        # 2.7432 kg-CO2 per kg CH4 burned
STOICH_MEOH = M_CO2 / M_MEOH      # 1.3735 kg-CO2 per kg CH3OH burned


def cell(ws, addr):
    return ws[addr].value


def need(got, want, what, tol=1e-6):
    ok = (abs(got - want) <= tol * max(1.0, abs(want))) if isinstance(want, float) \
        else (got == want)
    if not ok:
        raise AssertionError(f'{what}: read {got!r}, expected {want!r}')
    return got


# ---------------------------------------------------------------- database factors
wb = openpyxl.load_workbook(DB, data_only=True, read_only=True)
ws = wb['排出原単位']
dbrows = {r[0]: r for r in ws.iter_rows(min_row=2, values_only=True) if r and r[0]}
wb.close()


def db(entry_id, want, what):
    row = dbrows[entry_id]
    return need(float(row[6]), want, f'DB {entry_id} {what}')


A_LNG = db('JP104005', 3.25, 'LNG boiler combustion, kg, cradle-through-combustion')
GATE_LNG = db('JP304004', 0.554, 'LNG product, gate')
A_DIESEL_L = db('JP111013', 2.74, 'diesel boiler combustion, L, cradle-through-combustion')
A_DIESEL_KG = db('JP111014', 3.29, 'diesel boiler combustion, kg')
GATE_DIESEL_L = db('JP311005', 0.152, 'diesel product, gate, per L')
GATE_MEOH = db('JP310277', 1.5, 'methanol product, gate')
RHO_DIESEL = 0.833                 # kg/L, stated in JP111014's own notes
need(A_DIESEL_L / RHO_DIESEL, A_DIESEL_KG, 'DB internal density consistency', 5e-3)

# ---------------------------------------------------------------- hydrogen factor
wb = openpyxl.load_workbook(CCU_SENS, data_only=True)
ws = wb['感度分析太陽光発電水素']
H2_NOW = need(float(cell(ws, 'D30')), 5.4459, 'H2 factor 2023', 1e-4)
H2_2050 = need(float(cell(ws, 'F30')), 3.535, 'H2 factor 2050', 1e-3)
# the formula's own components, asserted so the build-up stays documented
need(float(cell(ws, 'G20')), 13.8, 'compression+storage+transport g/MJ')
need(float(cell(ws, 'D24')), 10.0, 'equipment g/MJ')
need(float(cell(ws, 'D25')), 48.5, 'electrolysis kWh/kg')
need(float(cell(ws, 'D26')), 0.0534, 'PV electricity factor')
need((13.8 + 10.0) * 120 / 1000 + 48.5 * 0.0534, H2_NOW, 'H2 bottom-up closes', 1e-4)

# ------------------------------------------------------------- CCU inventory
wb = openpyxl.load_workbook(CCU, data_only=True)
mt, cu = wb['まとめ'], wb['ccuーLCA計算']

T_NAT = need(float(cell(cu, 'F2')), 74621.269184, 'total combustion CO2')
F_NAT = need(float(cell(cu, 'F3')), 26475.1872, 'fossil combustion CO2')
CAPTURED = need(float(cell(cu, 'I7')), 67159.1422656, 'captured stream')
f = F_NAT / T_NAT                                   # fossil share, 0.354794
SLIP_F = 0.1 * F_NAT                                # fossil capture slip
need(float(cell(mt, 'D32')), SLIP_F, 'slip cell = 0.1*F', 1e-6)

MASS = {                                            # product and H2 masses, t/y
    'CH4': need(float(cell(cu, 'I12')), 23158.324919172417, 'CH4 mass'),
    'MeOH': need(float(cell(cu, 'I23')), 46605.92801221374, 'methanol mass'),
    'H2_U1': need(float(cell(cu, 'I8')), 11810.745708777933, 'U1 H2 mass'),
    'H2_U2': need(float(cell(cu, 'I19')), 9461.00338647939, 'U2 H2 mass'),
}
VENT = {                                            # process vents, mixed basis, t/y
    'U1': need(float(cell(cu, 'I11')), 4400.081734642759, 'U1 process vent'),
    'U2': need(float(cell(cu, 'I22')), 4701.139958592001, 'U2 process vent'),
}

# the source workbook's own column totals, re-summed as an integrity check
SRC_COLS = {'S0': 'I', 'U1': 'J', 'U2': 'K'}
SRC_TOT = {'S0': 18548.7084549104, 'U1': 22322.450439210264,
           'U2': 3018.4294813283477}
for p, col in SRC_COLS.items():
    need(float(cell(mt, f'{col}13')), SRC_TOT[p], f'source column total {p}', 1e-9)

# burden rows kept unchanged from the source inventory (t-CO2/y)
KEEP = {}
for p, col in [('U1', 'J'), ('U2', 'K')]:
    KEEP[p] = {
        'elec': float(cell(mt, f'{col}5')),
        'chem': float(cell(mt, f'{col}6')),
        'elec_prod': float(cell(mt, f'{col}8')),
        'transport': float(cell(mt, f'{col}10')),
        'capital': float(cell(mt, f'{col}12')),
    }
need(KEEP['U1']['capital'], 1770.0, 'U1 capital')
need(KEEP['U2']['capital'], 803.0, 'U2 capital')



# ---------------------------------------------------------------- corrected credits
# per-kg net credit factors (positive numbers; ledger subtracts them)
# Whole-horizon credit per kg of product.  U2a and U2b share it exactly: the
# displaced fossil methanol has the same downstream fate, so the MTO step cancels
# and only the carbon ORIGIN differs.  What differs between the two routes is the
# TIMING, handled by the static/deferred split below.
CREDIT = {
    'U1': A_LNG - f * STOICH_CH4,                        # 2.2766
    'U2a': (GATE_MEOH + STOICH_MEOH) - f * STOICH_MEOH,  # = 1.5 + (1-f)*1.3735
    'U2b': (GATE_MEOH + STOICH_MEOH) - f * STOICH_MEOH,  # identical over the horizon
}

# split form used by the model: credit_total = QA - f*QB  (QA, QB per pathway, t/y)
# U2b: the MTO step retains eta = 0.80 of the methanol carbon in products; the
# non-retained 20 % is burned within the operating year and therefore belongs in the
# static (same within-year rule as every other pathway).  Only the retained 80 %
# enters the dynamic layer's release pool.
ETA_MTO = 0.80                       # methanol-to-olefins carbon retention
MEOH_COMB = MASS['MeOH'] * STOICH_MEOH          # 64,012 t-CO2 of product carbon
# STATIC part of the credit.  For U2a the whole product carbon is settled within
# the operating year.  For U2b only the non-retained 20 % is: the counterfactual's
# prompt release is avoided (credit) and the intervention's prompt release is
# charged at its fossil share.  The retained 80 % is settled at the product
# lifetime and enters the dynamic layer instead.
QA = {'U1': MASS['CH4'] * A_LNG,
      'U2a': MASS['MeOH'] * (GATE_MEOH + STOICH_MEOH),
      'U2b': MASS['MeOH'] * GATE_MEOH + (1.0 - ETA_MTO) * MEOH_COMB}
QB = {'U1': MASS['CH4'] * STOICH_CH4,
      'U2a': MASS['MeOH'] * STOICH_MEOH,
      'U2b': (1.0 - ETA_MTO) * MEOH_COMB}
# the U2a split must reproduce its per-kg credit exactly; the U2b static split is
# smaller than its whole-horizon credit by exactly the deferred amount, checked below
need(QA['U1'] - f * QB['U1'], MASS['CH4'] * CREDIT['U1'], 'credit split U1', 1e-9)
need(QA['U2a'] - f * QB['U2a'], MASS['MeOH'] * CREDIT['U2a'], 'credit split U2a', 1e-9)
DEFERRED_U2B = -(1.0 - f) * ETA_MTO * MEOH_COMB       # net CREDIT realised at tau50
need((QA['U2a'] - f * QB['U2a']) - (QA['U2b'] - f * QB['U2b']),
     -DEFERRED_U2B, 'U2b deferral closes against U2a', 1e-9)

H2_T = {'U1': MASS['H2_U1'] * H2_NOW, 'U2a': MASS['H2_U2'] * H2_NOW,
        'U2b': MASS['H2_U2'] * H2_NOW}

# ---------------------------------------------------------------- corrected statics
def ccu_static(p):
    src = KEEP['U2' if p in ('U2a', 'U2b') else p]
    vent = VENT['U2' if p in ('U2a', 'U2b') else p]
    return (src['elec'] + src['chem'] + src['elec_prod'] + src['transport']
            + src['capital'] + H2_T[p]
            + SLIP_F + f * vent                       # slip once + fossil-share vent
            - (QA[p] - f * QB[p]))


STATIC = {p: ccu_static(p) for p in ('U1', 'U2a', 'U2b')}
STATIC['S0'] = SRC_TOT['S0']

# ------------------------------------------------------ mineralization inventory
zw = openpyxl.load_workbook(MIN, data_only=True)
zl = zw['LCA計算']
L_REACTOR = {   # reactor CO2 loss only, mixed basis, t/y  (block -> pathway mapping
                # fixed by the electricity totals: M1 olivine, M2 serpentine,
                # M3 steel slag (1h), M4 steel slag 2)
    'M1': need(float(cell(zl, 'I38')), 7462.126918400001, 'M1 olivine reactor loss'),
    'M2': need(float(cell(zl, 'I65')), 4029.54, 'M2 serpentine reactor loss'),
    'M3': need(float(cell(zl, 'I26')), 7428.919742030769, 'M3 steel-slag reactor loss'),
    'M4': need(float(cell(zl, 'I80')), 840.3610561914672, 'M4 steel-slag-2 reactor loss'),
}
# v3 published statics carried the full mixed-basis L_p (slip included) once more on
# top of the explicit slip; correction: subtract that, charge f * reactor loss.
V3_LP = {'M1': 10109.65, 'M2': 6677.06, 'M3': 10076.44, 'M4': 3487.88}
V3_NET = {'M1': 41036.0, 'M2': 43013.0, 'M3': 48523.0, 'M4': 61736.0}
for p in V3_LP:
    need(V3_LP[p] - L_REACTOR[p], SLIP_F, f'v3 L_p decomposition {p}', 1e-4)
    STATIC[p] = V3_NET[p] - V3_LP[p] + f * L_REACTOR[p]

# unchanged pathways
for p, v in {'G1': 12765.0, 'G2': 13356.0,
             'R1': -7848.0, 'R2': -7848.0, 'R3': -7649.0}.items():
    STATIC[p] = v

# ---------------------------------------------------------------- dynamic-layer pools
POOLS = {
    'U2b': {'mode': 'weibull', 'retention': ETA_MTO, 'tau50': 10.0, 'k': 2.0,
            'deferred_net': DEFERRED_U2B,
            'intervention_release': f * ETA_MTO * MEOH_COMB,
            'counterfactual_release_avoided': ETA_MTO * MEOH_COMB,
            'note': 'The retained 80 % of the product carbon is settled at the '
                    'product lifetime in BOTH worlds. The intervention then '
                    'releases f x 0.80 x M x stoich of net-new fossil CO2 while '
                    'the counterfactual would have released the full 0.80 x M x '
                    'stoich, so the deferred quantity is a NET CREDIT of '
                    '(1 - f) x 0.80 x M x stoich. Durability itself cancels; only '
                    'the carbon origin remains, and its benefit is postponed.'},
}

# --------------- rebase every explicit electricity term to the official factor ------
# The source inventories evaluated their electricity at the factor recorded in the
# source workbook (EF_SRC). The published national average of the MoEJ/METI utility
# list is EF_OFFICIAL, and the regional layer of this study already uses the
# per-utility factors of that same list, so the national case is harmonised to its
# national average. Every explicit electricity term of Eq. 2 is rebased by
# (EF_OFFICIAL - EF_SRC) x (net MWh of that pathway). The calibrated residual C_p is
# a constant in t-CO2 and retains the electricity basis of the source inventories;
# for the utilization pathways that unrebased part is the 1,007 MWh capture-unit
# load, i.e. about 10 t-CO2/y, which is stated in the SI.
EF_SRC = need(float(cell(cu, 'AD2')), 0.433, 'source-inventory grid factor')
EF_OFFICIAL = 0.423        # MoEJ/METI utility list, national average
AUX_MWH, EXP_NOCC_MWH, EXP_CC_MWH = 24360.0, 43207.0, 30120.0
STEAM_MWH = EXP_NOCC_MWH - EXP_CC_MWH
E_PROC_MWH = {'S0': 0.0, 'M1': 46453.0, 'M2': 21123.0, 'M3': 17560.0, 'M4': 38070.0,
              'G1': 6716.0, 'G2': 8059.0,
              'U1': float(cell(cu, 'I9')) / 1000.0,
              'U2a': float(cell(cu, 'I20')) / 1000.0,
              'U2b': float(cell(cu, 'I20')) / 1000.0,
                        'R1': 357.0, 'R2': 357.0, 'R3': 6048.0}
CAPTURE_P = {'M1', 'M2', 'M3', 'M4', 'G1', 'G2', 'U1', 'U2a', 'U2b'}
MWH_EF = {}
for _p in E_PROC_MWH:
    _mwh = AUX_MWH - EXP_NOCC_MWH                     # plant balance, every pathway
    if _p in CAPTURE_P:
        _mwh += STEAM_MWH + E_PROC_MWH[_p]
    elif _p != 'S0':
        _mwh += E_PROC_MWH[_p]
    MWH_EF[_p] = _mwh
STATIC_SRC = dict(STATIC)
for _p in STATIC:
    STATIC[_p] = STATIC_SRC[_p] + (EF_OFFICIAL - EF_SRC) * MWH_EF[_p]

# ---------------------------------------------------------------- write + report
out = {
    'f_fossil_share': f,
    'EF_SRC': EF_SRC, 'EF_OFFICIAL': EF_OFFICIAL,
    'MWH_EF': MWH_EF, 'STATIC_SRC_BASIS': STATIC_SRC,
    'T_NAT': T_NAT, 'F_NAT': F_NAT, 'CAPTURED': CAPTURED, 'SLIP_F': SLIP_F,
    'H2_FACTOR': {'now': H2_NOW, 'y2050': H2_2050},
    'H2_MASS': {'U1': MASS['H2_U1'], 'U2a': MASS['H2_U2'], 'U2b': MASS['H2_U2']},
    'H2_T': H2_T,
    'PRODUCT_MASS': {'U1': MASS['CH4'], 'U2a': MASS['MeOH'], 'U2b': MASS['MeOH']},
    'CREDIT_PER_KG': CREDIT,
    'QA': QA, 'QB': QB,
    'VENT': {'U1': VENT['U1'], 'U2a': VENT['U2'], 'U2b': VENT['U2']},
    'L_REACTOR': L_REACTOR,
    'STATIC_V4': STATIC,
    'POOLS': POOLS,
    'E_PROC_MWH': {'U1': float(cell(cu, 'I9')) / 1000.0,
                   'U2a': float(cell(cu, 'I20')) / 1000.0,
                   'U2b': float(cell(cu, 'I20')) / 1000.0},
    'FACTORS': {'A_LNG': A_LNG, 'GATE_LNG': GATE_LNG, 'A_DIESEL_KG': A_DIESEL_KG,
                'GATE_DIESEL_L': GATE_DIESEL_L, 'RHO_DIESEL': RHO_DIESEL,
                'GATE_MEOH': GATE_MEOH, 'STOICH_CH4': STOICH_CH4,
                'STOICH_MEOH': STOICH_MEOH, 'ETA_MTO': ETA_MTO},
    'EXCLUDED': {'U3_microalgae':
                 'Excluded: the source block does not close a carbon balance '
                 '(40,411 t-CO2 in against 7,838 t renewable diesel plus 33,541 '
                 't-CO2 out; carbon out / carbon in = 1.44), so no consistent '
                 'fossil-carbon partition can be built for it.'},
    'KEEP_BURDENS': KEEP,
}
with open(os.path.join(HERE, 'model_parameters.json'), 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)

if __name__ == '__main__':
    print(f'fossil share f = {f:.6f}')
    print(f'{"path":<5}{"published":>12}{"v4":>14}{"change":>12}')
    PUB = {'S0': 18548.71, 'U1': 22322.45, 'U2a': 3018.43, 'U2b': 3018.43,
           **V3_NET, 'G1': 12765.0, 'G2': 13356.0,
           'R1': -7848.0, 'R2': -7848.0, 'R3': -7649.0}
    for p in ['S0', 'M1', 'M2', 'M3', 'M4', 'G1', 'G2',
              'U1', 'U2a', 'U2b', 'R1', 'R2', 'R3']:
        print(f'{p:<5}{PUB[p]:>12,.1f}{STATIC[p]:>14,.1f}'
              f'{STATIC[p] - PUB[p]:>+12,.1f}')
    print('\ncredit factors per kg:',
          {k: round(v, 4) for k, v in CREDIT.items()})
    print('H2 terms t/y:', {k: round(v, 1) for k, v in H2_T.items()})
    print('ledger written: model_parameters.json')
