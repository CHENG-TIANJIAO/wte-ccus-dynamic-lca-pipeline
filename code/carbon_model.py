# -*- coding: utf-8 -*-
"""
Regional and stochastic carbon balance of the thirteen pathways.

REVISION R1 (phase 2C and phase 2b, 2026-09-19).  This copy differs from the submitted
(R0) model in three respects, all driven by the itemised corrections of
R1_revision/02_analyses/P2B_corrected_anchors.md (phase 2) and P2B2_anchors.md
(phase 2b, authors' decisions D6-D13):

  (R1-a) The national anchors STATIC_V4 in model_parameters.json are the corrected
         P2B2 values (apply_r1_anchors.py, then apply_r1b.py).  Nine capture pathways
         change: the uncaptured slip and the capture-unit electricity that the G1/G2
         ledger counted a second time inside its chemicals block are removed once
         each; the air-pollution-control consumables that do not differ with and
         without capture are removed from every capture pathway (differential
         boundary, Bisinella et al. 2021) and the plant APC/boiler chemicals that
         M1-M4 alone had carried are placed outside the boundary for every pathway
         (D6); the capture solvent burden is declared, with the activated-carbon and
         NaOH capture-unit increments (D13); the placeholder G transport and the
         dimensionally wrong M1/M2 ore-transport formula are replaced by t-km values,
         as is the hard-coded CCU transport (D9).  R1d: capital goods = the
         capture unit only (CAPITAL_CAPTURE_T, all nine capture pathways).  R1f: M1 olivine and M4
         CaO factors corrected, R3 electricity aligned with its anchor (apply_r1f.py).
  (R1-b) Two further explicit groups, both class CAP (scale with s_cap):
           b_reag   capture solvent burden + capture-unit increments, REAGENT_T[p] x s_cap
           b_trans  transport (CO2 to storage, ore, slag, CO2 to the synthesis
                    plant), TRANSPORT_T[p] x s_cap
         They were part of the calibrated residual C_p in R0, where they were held
         constant across regions, years and draws.  terms() returns seven groups;
         terms4() keeps the four-group view of the displayed Eq. 2 by folding b_reag
         and b_trans into the captured-stream-scaled group (see terms4).
  (R1-c) Every electricity line of the nine capture pathways is evaluated at the
         official 0.423 t-CO2/MWh from its source MWh (D7).  E_PROC is read from the
         ledger for all 13 pathways (E_PROC_MWH: capture, compression and conversion
         electricity from source kWh; for U1/U2a/U2b it now includes the 15 kWh per
         t-CO2 capture line that R0 held constant inside C_p, D10a).  The calibrated
         residual therefore contains no electricity at any other basis; its only
         electricity-related content is the 11.017 MWh (4.66 t-CO2/y) difference
         between the workbook plant lines (24,348.90 / 30,119.91 MWh) and the rounded
         Eq. 2 constants AUX / EXP_CC.  For G1/G2 that remainder is the whole of C_p.

  (R1-d) R1c (unified modular boundary, BOUNDARY_DESIGN_R1c.md, apply_r1c.py): every
         capture pathway carries the common 90 kWh/t capture + conditioning module
         (15 capture unit + 10 condenser + 65 compressor); U adds liquefaction to the
         road-tanker state (16 kWh/t, analogy); G is the Japan-oriented ship scenario
         (liquefaction 17.4 + unloading 2.5 kWh/t, ship fuel 22 kg/t + 10 km road; G2
         wellhead boost 7 kWh/t, G1 none; the unsourced G2 dep = 1.2 is removed).
         E_PROC and TRANSPORT_T carry these items (E_PROC_ITEMS_R1C /
         TRANSPORT_ITEMS_R1C in the ledger); STATIC_V4 moved by dMWh x 0.423 +
         dtransport, so every residual C_p is exactly the R1b value.
         Declared discrete scenarios (pipeline, high compression, U 15 kWh/t, ...,
         CO2 losses) are selected with the environment variable R1C_SCENARIO or with
         set_scenario(name) (definitions in r1c_modules.py).  A CO2 loss is a fraction
         LOSS[p] of the captured stream; convention A charges its fossil share
         LOSS x cr x F inside phi, convention B additionally forfeits LOSS of the
         stored biogenic carbon (bio_stored), i.e. the full loss.  LOSS = 0 in the base.

Every other constant is read from model_parameters.json exactly as in R0, which
derive_parameters.py generates directly from the source workbooks with per-cell
assertions for the reference plant, the CCU routes and the mineralization routes.
The three chemical-recycling national results are carried in the ledger as published
values of their source studies rather than rebuilt cell by cell (SI Section S2); in R1
the nine capture anchors are itemised sums (P2B2_anchors.md section 4).

Accounting rules implemented, each traceable to a cell assertion in
derive_parameters.py:

  (B2)  Hydrogen factor 6.1179 -> 5.4459 kg-CO2/kg-H2 (bottom-up source formula).
  (B1)  Substitution credits made cradle-to-grave symmetric and biogenic-neutral:
        per kg of product, credit = A_p - f * B_p with f = F / T the fossil share of
        the captured stream.  The model carries the split (QA_p, QB_p) so that f can
        vary by region and by Monte Carlo draw.
  (B1') CCU process vents charged at their fossil share f; the capture slip
        (1 - cr) * F is fossil by construction and is charged exactly once.
  (A2)  Mineralization loss = reactor loss only (slip removed from L_p), charged at
        its fossil share:  phi_min = (1 - cr) F + f * L_R,p * s_cap.
  (B3)  U2a (methanol as fuel) and U2b (methanol as feedstock) are bounded by one
        symmetric grave; the whole-horizon credit is identical (2.386 per kg) and
        U2b defers a net credit of (1 - f) x 0.80 x M x stoich = 33,041 t-CO2 to the
        product lifetime.
  (U3)  The microalgae route is EXCLUDED (its source block does not close a carbon
        balance; carbon out / carbon in = 1.44).

Scaling classes: FIXED, CAP (s_cap = cr T / cr_nat T_nat), PLASTIC (s_F = F / F_nat),
CARBON, RESIDUAL.  Sign convention: emissions positive, avoided burdens subtracted.
"""
import copy
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
LED = json.load(open(os.path.join(_HERE, 'model_parameters.json'), encoding='utf-8'))

CR = 0.90
F_NAT, T_NAT = LED['F_NAT'], LED['T_NAT']            # 26,475.1872 / 74,621.269184
AUX, EXP_NOCC, EXP_CC = 24360.0, 43207.0, 30120.0    # MWh/y, plant workbook (rounded)
EF_NAT = LED['EF_OFFICIAL']        # 0.423, MoEJ/METI list national average
STEAM_PEN = EXP_NOCC - EXP_CC                        # 13,087 MWh/y, captured stream

NET_NAT = LED['STATIC_V4']                           # full-precision R1b statics
CLASS = {'S0': 'ref', 'M1': 'min', 'M2': 'min', 'M3': 'min', 'M4': 'min',
         'G1': 'geo', 'G2': 'geo', 'U1': 'ccu', 'U2a': 'ccu', 'U2b': 'ccu',
         'R1': 'cr', 'R2': 'cr', 'R3': 'cr'}
ORDER = ['S0', 'M1', 'M2', 'M3', 'M4', 'G1', 'G2',
         'U1', 'U2a', 'U2b', 'R1', 'R2', 'R3']
CAPTURES = {p for p in ORDER if CLASS[p] in ('geo', 'min', 'ccu')}

# R1b: capture, compression and conversion electricity from source kWh, all 13
# pathways (apply_r1b.py, P2B2_anchors.json E_PROC_MWH_all13)
E_PROC = {p: LED['E_PROC_MWH'][p] for p in ORDER}
H2 = LED['H2_T']                                     # t-CO2/y at national scale
QA = LED['QA']                                       # displaced product, c2grave
QB = LED['QB']                                       # product fossil-combustion base
V_P = LED['VENT']                                    # process vents, mixed basis
L_R = LED['L_REACTOR']                               # reactor loss only, mixed basis
D_P = {'R1': 17678.0, 'R2': 17678.0, 'R3': 17650.0}  # diverted plastic C
# R1: explicit CAP-class terms, t-CO2/y at national scale (apply_r1b.py)
REAG = LED['REAGENT_T']                              # solvent + capture-unit increments
TRANS = LED['TRANSPORT_T']                           # transport term
for _p in ORDER:                                     # every pathway must be listed
    assert _p in REAG and _p in TRANS and _p in E_PROC, _p
    assert (REAG[_p] > 0) == (_p in CAPTURES), _p    # solvent only with a capture unit
    assert (TRANS[_p] > 0) == (_p in CAPTURES), _p
assert E_PROC['S0'] == 0.0
# documentation constants (not used by the model): the fixed-balance remainder that
# the residual of every capture pathway keeps, and the R1b CCU capital CAPITAL_U (check 2/5 only; R1d base
# uses CAPITAL_CAPTURE_T)
# R1c: CO2-loss fraction of the captured stream (declared scenarios only; 0 in the base)
LOSS = {p: 0.0 for p in ORDER}
# ledger (base) values, kept so that set_scenario() can always return to the base
_LEDGER_BASE = {'NET_NAT': copy.deepcopy(LED['STATIC_V4']), 'E_PROC': dict(E_PROC),
                'REAG': copy.deepcopy(LED['REAGENT_T']), 'TRANS': copy.deepcopy(LED['TRANSPORT_T'])}
SCENARIO = 'BASE'
SCEN_CAP = {p: 0.0 for p in ORDER}         # R1d: capital change of the active scenario (inside C_p)
FIXED_BALANCE_REMAINDER_T = LED['FIXED_BALANCE_REMAINDER']['tCO2_at_0.423']   # -4.660
CAPITAL_U = {p: LED['CAPITAL_U'][p] for p in ('U1', 'U2a', 'U2b')}
PLANT_FUEL_T = LED['PLANT_FUEL_T']['value']                                   # 239.115
CAPITAL_CAPTURE_T = LED['CAPITAL_CAPTURE_T']['value']                         # 745.649 (R1d, A2)


def s_cap(T, cr):
    """Captured-stream scaling factor, = 1 at national conditions."""
    return (T * cr) / (T_NAT * CR)


def s_plastic(F):
    return F / F_NAT


def terms(p, F, T, EF, cr=CR):
    """
    Seven additive groups, t-CO2 per year.

      b_fix    plant auxiliary electricity minus BASELINE export, fixed
      b_steam  steam-extraction export penalty, captured-stream-scaled
      b_el     process electricity (CAP for captures, PLASTIC for recycling)
      phi      carbon flow, with f = F / T the fossil share of the captured stream
      b_h2     hydrogen, captured-stream-scaled
      b_reag   capture solvent burden + capture-unit increments, captured-stream-scaled
               (R1, zero for S0 / R)
      b_trans  transport, captured-stream-scaled (R1, zero for S0 / R)
    """
    c = CLASS[p]
    sc, sF, f = s_cap(T, cr), s_plastic(F), F / T
    b_fix = (AUX - EXP_NOCC) * EF
    if p in CAPTURES:
        b_steam = STEAM_PEN * sc * EF
        b_el = E_PROC[p] * sc * EF
    else:
        b_steam = 0.0
        b_el = E_PROC[p] * sF * EF if c == 'cr' else E_PROC[p] * EF
    if c == 'ref':
        phi = F
    elif c == 'geo':
        phi = (1 - cr) * F + LOSS[p] * cr * F          # R1c: fossil share of a CO2 loss
    elif c == 'min':
        phi = (1 - cr) * F + L_R[p] * sc * f
    elif c == 'ccu':
        phi = (1 - cr) * F + V_P[p] * sc * f - (QA[p] - f * QB[p]) * sc + LOSS[p] * cr * F
    else:
        phi = F - D_P[p] * sF
    b_h2 = H2.get(p, 0.0) * sc
    b_reag = REAG[p] * sc
    b_trans = TRANS[p] * sc
    return b_fix, b_steam, b_el, phi, b_h2, b_reag, b_trans


def residual(p):
    """Calibrated remainder, held at its national value.

    R1b: with every electricity line at 0.423 from source MWh and the solvent and
    transport terms explicit, the G1/G2 residual is nothing but the fixed-balance
    remainder (-4.66 t-CO2/y); the CCU residuals are the plant light-oil fuel
    (239.12) plus the capture-unit capital 745.65 (R1d; U synthesis capital out) minus
    that remainder; the mineralization residuals keep process heat, mineral reagents,
    ore or slag handling, water and the mineral-product credit, minus the remainder.
    S0 and R1/R2 are as shipped; R3 is rebased with its aligned electricity and M1/M4 carry
    the corrected factors (R1f, apply_r1f.py).  P2B2_anchors.md section 4 decomposes every one
    of them item by item; apply_r1b.py, apply_r1d.py and apply_r1f.py assert the composition.
    """
    return NET_NAT[p] - sum(terms(p, F_NAT, T_NAT, EF_NAT))


def net(p, F, T, EF, cr=CR):
    """Net life-cycle result of pathway p, t-CO2 per year."""
    return sum(terms(p, F, T, EF, cr)) + residual(p)


# ---- four-group view used by the displayed Eq. 2 ---------------------------------
def terms4(p, F, T, EF, cr=CR):
    """Four groups: fixed electricity; captured-stream-scaled burdens; carbon flow;
    hydrogen.

    R1 choice: b_reag and b_trans are folded into the SECOND group, which is
    therefore the whole captured-stream-scaled block (steam penalty, process
    electricity, solvent, transport) rather than the electricity part alone.  The
    sum of the four groups is unchanged in meaning (it is Eq. 2 without C_p), so every
    consumer of terms4() -- the regional reconciliation and its worked example --
    keeps closing exactly; consumers that need the seven groups separately
    (export_files.py, build_workbook.py) call terms()."""
    b_fix, b_steam, b_el, phi, b_h2, b_reag, b_trans = terms(p, F, T, EF, cr)
    return b_fix, b_steam + b_el + b_reag + b_trans, phi, b_h2


def bio_stored(p, F, T, cr=CR):
    """Biogenic carbon NET-PERMANENTLY stored, credited under convention B only.

    Geological storage injects the whole captured stream, so the stored biogenic
    carbon is (T - F) * cr.  Mineralization re-releases the reactor loss L_R
    (mixed basis), whose biogenic share is therefore not stored.  No other class
    stores permanently.
    """
    c = CLASS[p]
    if c == 'geo':
        return (T - F) * cr * (1.0 - LOSS[p])          # R1c: lost CO2 is not stored
    if c == 'min':
        return (T - F) * cr - (1.0 - F / T) * L_R[p] * s_cap(T, cr)
    return 0.0


def set_scenario(name='BASE'):
    """Switch the module to an R1c declared scenario (r1c_modules.SCENARIOS, or 'R1B'
    for the R1b state).  The changed items move E_PROC, TRANS, REAG and LOSS of the
    pathways they concern; the national anchor moves with them (dMWh x 0.423 +
    dtransport + dreagent + fossil share of the national loss), so C_p is unchanged.
    'BASE' restores the ledger values exactly."""
    global SCENARIO
    import r1c_modules as RM
    b0 = _LEDGER_BASE
    SCEN_CAP.update({p: 0.0 for p in ORDER})
    for p in ORDER:
        NET_NAT[p], E_PROC[p] = b0['NET_NAT'][p], b0['E_PROC'][p]
        REAG[p], TRANS[p], LOSS[p] = b0['REAG'][p], b0['TRANS'][p], 0.0
    SCENARIO = 'BASE'
    if name == 'BASE':
        return
    r1b = LED['STATIC_R1B']
    sc = RM.build(name, dict(E_PROC_MWH=r1b['E_PROC_MWH'], TRANSPORT_T=r1b['TRANSPORT_T'],
                             REAGENT_T=r1b['REAGENT_T'],
                             solvent_declared=LED['REAGENT_T_SPLIT']['solvent_declared']))
    for p in ORDER:
        dE = sc['eproc'][p] - b0['E_PROC'][p]
        dT = sc['trans'][p] - b0['TRANS'][p]
        dR = sc['reag'][p] - b0['REAG'][p]
        E_PROC[p], TRANS[p], REAG[p], LOSS[p] = sc['eproc'][p], sc['trans'][p], sc['reag'][p], sc['loss'][p]
        NET_NAT[p] = b0['NET_NAT'][p] + dE * EF_NAT + dT + dR + LOSS[p] * CR * F_NAT + sc['cap'][p]
    SCEN_CAP.update(sc['cap'])
    SCENARIO = name


_SCEN_ENV = os.environ.get('R1C_SCENARIO', 'BASE')
if _SCEN_ENV != 'BASE':
    set_scenario(_SCEN_ENV)
    print(f'carbon_model: R1c declared scenario {_SCEN_ENV!r} active (R1C_SCENARIO)')


if __name__ == '__main__':
    print('Check 1: reproduces the ledger statics exactly (R1b anchors)')
    ok = True
    for p in ORDER:
        v = net(p, F_NAT, T_NAT, EF_NAT)
        ok &= abs(v - NET_NAT[p]) < 1e-6
        print(f'  {p:<5}{v:>14,.4f}  target {NET_NAT[p]:>14,.4f}')
    print('  all reproduce exactly:', ok)
    assert ok

    print('\nCheck 2 (R1b): residual composition of the G and U pathways (t-CO2/y)')
    rem = FIXED_BALANCE_REMAINDER_T
    mx = 0.0
    for p in ('G1', 'G2'):
        r = residual(p)
        parts = CAPITAL_CAPTURE_T + PLANT_FUEL_T + rem                 # R1d: A1 + A2
        mx = max(mx, abs(r - parts))
        print(f'  {p:<5}residual {r:>10,.3f}   capture capital {CAPITAL_CAPTURE_T:,.3f} + light oil '
              f'{PLANT_FUEL_T:,.3f} + remainder {rem:,.3f} = {parts:>10,.3f}   gap {r - parts:>+10.3e}')
    for p in ('U1', 'U2a', 'U2b'):
        r = residual(p)
        parts = CAPITAL_CAPTURE_T + PLANT_FUEL_T + rem                 # R1d: capture capital only
        mx = max(mx, abs(r - parts))
        print(f'  {p:<5}residual {r:>10,.3f}   capture capital {CAPITAL_CAPTURE_T:,.3f} + light oil '
              f'{PLANT_FUEL_T:,.3f} + remainder {rem:,.3f} = {parts:>10,.3f}   gap {r - parts:>+10.3e}')
    print(f'  max gap = {mx:.3e}')
    assert mx < 1e-6

    print('\nCheck 3: credit factors per kg at national f')
    f = F_NAT / T_NAT
    for p in ('U1', 'U2a', 'U2b'):
        m = LED['PRODUCT_MASS'][p]
        print(f'  {p:<5}{(QA[p] - f * QB[p]) / m:.4f}')

    print('\nCheck 4: slip charged exactly once (min pathways, national)')
    for p in ('M1', 'M2', 'M3', 'M4'):
        phi = terms(p, F_NAT, T_NAT, EF_NAT)[3]
        expect = 0.1 * F_NAT + (F_NAT / T_NAT) * L_R[p]
        assert abs(phi - expect) < 1e-9, p
    print('  ok')

    print('\nCheck 5 (R1b + R1d + R1f): residual equals the P2B2 7-group expectation plus the R1d and R1f changes')
    exp = LED['RESIDUAL_EXPECTED_R1B']
    _p2b2 = os.path.normpath(os.path.join(_HERE, '..', '..', 'P2B2_anchors.json'))
    if os.path.exists(_p2b2):
        exp_json = json.load(open(_p2b2, encoding='utf-8'))['residual_expected_R1b']
        assert all(abs(exp_json[p] - exp[p]) < 1e-9 for p in ORDER)
        src = 'P2B2_anchors.json'
    else:
        src = 'ledger copy (P2B2_anchors.json not beside this copy)'
    # R1d (audit A1 + A2): P2B2 expectation + light oil (G) + capture-unit capital (M, G)
    exp_d = LED.get('RESIDUAL_EXPECTED_R1F', LED['RESIDUAL_EXPECTED_R1D'])
    dF = LED.get('R1F_DELTA_CP', {p: 0.0 for p in ORDER})             # R1f: M1, M4 factors; R3 electricity
    add = {p: (PLANT_FUEL_T if CLASS[p] == 'geo' else 0.0)
           + (CAPITAL_CAPTURE_T if CLASS[p] in ('geo', 'min') else 0.0)
           + (CAPITAL_CAPTURE_T - CAPITAL_U[p] if CLASS[p] == 'ccu' else 0.0) for p in ORDER}   # B2
    assert all(abs(exp_d[p] - exp[p] - add[p] - dF[p]) < 1e-6 for p in ORDER)
    mx = 0.0
    for p in ORDER:
        mx = max(mx, abs(residual(p) - exp_d[p]))
        print(f'  {p:<5}C_p {residual(p):>12,.4f}   P2B2 {exp[p]:>12,.4f} + R1d {add[p]:>8,.3f} + R1f {dF[p]:>9,.3f}')
    print(f'  max |C_p - (P2B2 + R1d + R1f)| = {mx:.3e}  ({src})')
    assert mx < 1e-6

    print('\nCheck 6 (R1b, documentary): source-basis identity of the nine capture pathways')
    SRC, FAC = LED['STATIC_SRC_BASIS'], LED['STATIC_SRC_BASIS_FACTOR']
    aux_s = LED['SOURCE_ELECTRICITY_MWH']['plant_auxiliary']
    exp_s = LED['SOURCE_ELECTRICITY_MWH']['export_with_capture']
    mx = 0.0
    for p in ORDER:
        if p in CAPTURES:
            ident = (FAC[p] - EF_NAT) * (aux_s - exp_s + LED['E_PROC_MWH'][p])
        else:
            ident = (LED['EF_SRC'] - EF_NAT) * LED['MWH_EF'][p]
        v4b = _LEDGER_BASE['NET_NAT'][p]
        mx = max(mx, abs((SRC[p] - v4b) - ident))
        print(f'  {p:<5}SRC - V4 {SRC[p] - v4b:>+10,.3f} at {FAC[p]:.3f}   '
              f'identity {ident:>+10,.3f}')
    print(f'  max |difference| = {mx:.3e}')
    assert mx < 1e-6

    print('\nCheck 7 (R1c): E_PROC and TRANSPORT_T are the sums of the named R1c items')
    EI, TI = LED['E_PROC_ITEMS_R1C'], LED['TRANSPORT_ITEMS_R1C']
    mx = 0.0
    for p in ORDER:
        se = sum(i['MWh'] for i in EI[p]); st = sum(i['t'] for i in TI[p])
        mx = max(mx, abs(se - LED['E_PROC_MWH'][p]), abs(st - LED['TRANSPORT_T'][p]))
        print(f'  {p:<5}E_PROC {LED["E_PROC_MWH"][p]:>11,.3f} MWh = ' +
              (' + '.join(f'{i["key"]} {i["MWh"]:,.3f}' for i in EI[p]) or '0') +
              f';  TRANSPORT_T {LED["TRANSPORT_T"][p]:,.3f} t = ' +
              (' + '.join(f'{i["key"]} {i["t"]:,.3f}' for i in TI[p]) or '0'))
    print(f'  max |ledger - item sum| = {mx:.3e}')
    assert mx < 1e-9

    print('\nCheck 8 (R1c): every declared scenario keeps C_p at its R1f value (capital and CaO scenarios move it by design); BASE is restored exactly')
    import r1c_modules as _RM
    active = SCENARIO
    mx = 0.0
    for _s in _RM.SCENARIO_ORDER + ['R1B']:
        set_scenario(_s)
        mx = max(mx, max(abs(residual(p) - exp_d[p] - SCEN_CAP[p]) for p in ORDER))   # capital scenarios move C_p
        mx = max(mx, max(abs(net(p, F_NAT, T_NAT, EF_NAT) - NET_NAT[p]) for p in ORDER))
    set_scenario(active)
    print(f'  {len(_RM.SCENARIO_ORDER) + 1} scenarios; max |C_p - R1f C_p (scenario C_p changes applied)| and |Eq. 2 - anchor| = {mx:.3e}; '
          f'active scenario {SCENARIO}')
    assert mx < 1e-6
    if active == 'BASE':
        assert all(NET_NAT[p] == _LEDGER_BASE['NET_NAT'][p] and E_PROC[p] == _LEDGER_BASE['E_PROC'][p]
                   for p in ORDER)
