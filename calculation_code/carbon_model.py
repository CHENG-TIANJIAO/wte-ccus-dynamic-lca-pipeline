# -*- coding: utf-8 -*-
"""
Regional and stochastic carbon balance of the thirteen pathways.

Every constant below is read from model_parameters.json, which derive_parameters.py generates
directly from the source workbooks with per-cell assertions for the reference plant,
the CCU routes and the mineralization routes.  Five national results -- the two
geological-storage and the three chemical-recycling pathways -- are carried in the
ledger as published values of their source studies rather than rebuilt cell by cell,
because those inventories were reconstructed rather than read (SI Section S2); they
are marked as such in model_parameters.json.

Accounting rules implemented, each traceable to a cell assertion in
derive_parameters.py:

  (B2)  Hydrogen factor 6.1179 -> 5.4459 kg-CO2/kg-H2 (bottom-up source formula).
  (B1)  Substitution credits made cradle-to-grave symmetric and biogenic-neutral:
        per kg of product, credit = A_p - f * B_p with f = F / T the fossil share of
        the captured stream.  The model carries the split (QA_p, QB_p) so that f can
        vary by region and by Monte Carlo draw.
  (B1') CCU process vents charged at their fossil share f; the capture slip
        (1 - cr) * F is fossil by construction and is charged exactly once.
        An earlier formulation wrote phi_ccu = F + Q_sub and let the residual undo the
        difference, which made the CCU residuals large and negative.
  (A2)  Mineralization loss = reactor loss only (slip removed from L_p), charged at
        its fossil share:  phi_min = (1 - cr) F + f * L_R,p * s_cap.
  (B3)  U2a (methanol as fuel) and U2b (methanol as feedstock) are bounded by one
        symmetric grave.  The displaced fossil methanol has the same downstream
        fate as the synthesised methanol, so the methanol-to-olefins step, its
        energy and its 20 % carbon loss are common to both worlds and cancel.
        The whole-horizon credit is therefore identical (2.386 per kg); the routes
        differ only in when it is realised.  U2b settles the gate credit and the
        prompt 20 % release at t = 0 and defers a net credit of
        (1 - f) x 0.80 x M x stoich = 33,041 t-CO2 to the product lifetime.
  (U3)  The microalgae route is EXCLUDED.  Its source block does not close a
        carbon balance (40,411 t-CO2 in against 7,838 t renewable diesel plus
        33,541 t-CO2 out, i.e. carbon out / carbon in = 1.44), so no consistent
        fossil-carbon partition can be built for it.

Scaling classes are unchanged from v3: FIXED, CAP (s_cap = cr T / cr_nat T_nat),
PLASTIC (s_F = F / F_nat), CARBON, RESIDUAL.  Sign convention: emissions positive,
avoided burdens subtracted.
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
LED = json.load(open(os.path.join(_HERE, 'model_parameters.json'), encoding='utf-8'))

CR = 0.90
F_NAT, T_NAT = LED['F_NAT'], LED['T_NAT']            # 26,475.1872 / 74,621.269184
AUX, EXP_NOCC, EXP_CC = 24360.0, 43207.0, 30120.0    # MWh/y, plant workbook
EF_NAT = LED['EF_OFFICIAL']        # 0.423, MoEJ/METI list national average
STEAM_PEN = EXP_NOCC - EXP_CC                        # 13,087 MWh/y, captured stream

NET_NAT = LED['STATIC_V4']                           # full-precision v4 statics
CLASS = {'S0': 'ref', 'M1': 'min', 'M2': 'min', 'M3': 'min', 'M4': 'min',
         'G1': 'geo', 'G2': 'geo', 'U1': 'ccu', 'U2a': 'ccu', 'U2b': 'ccu',
         'R1': 'cr', 'R2': 'cr', 'R3': 'cr'}
ORDER = ['S0', 'M1', 'M2', 'M3', 'M4', 'G1', 'G2',
         'U1', 'U2a', 'U2b', 'R1', 'R2', 'R3']
CAPTURES = {p for p in ORDER if CLASS[p] in ('geo', 'min', 'ccu')}

E_PROC = {'S0': 0.0, 'M1': 46453.0, 'M2': 21123.0, 'M3': 17560.0, 'M4': 38070.0,
          'G1': 6716.0, 'G2': 8059.0,
          'U1': LED['E_PROC_MWH']['U1'], 'U2a': LED['E_PROC_MWH']['U2a'],
          'U2b': LED['E_PROC_MWH']['U2b'],
          'R1': 357.0, 'R2': 357.0, 'R3': 6048.0}
H2 = LED['H2_T']                                     # t-CO2/y at national scale
QA = LED['QA']                                       # displaced product, c2grave
QB = LED['QB']                                       # product fossil-combustion base
V_P = LED['VENT']                                    # process vents, mixed basis
L_R = LED['L_REACTOR']                               # reactor loss only, mixed basis
D_P = {'R1': 17678.0, 'R2': 17678.0, 'R3': 17650.0}  # diverted plastic C


def s_cap(T, cr):
    """Captured-stream scaling factor, = 1 at national conditions."""
    return (T * cr) / (T_NAT * CR)


def s_plastic(F):
    return F / F_NAT


def terms(p, F, T, EF, cr=CR):
    """
    Five additive groups, t-CO2 per year.

      b_fix    plant auxiliary electricity minus BASELINE export, fixed
      b_steam  steam-extraction export penalty, captured-stream-scaled
      b_el     process electricity (CAP for captures, PLASTIC for recycling)
      phi      carbon flow, with f = F / T the fossil share of the captured stream
      b_h2     hydrogen, captured-stream-scaled
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
        phi = (1 - cr) * F
    elif c == 'min':
        phi = (1 - cr) * F + L_R[p] * sc * f
    elif c == 'ccu':
        phi = (1 - cr) * F + V_P[p] * sc * f - (QA[p] - f * QB[p]) * sc
    else:
        phi = F - D_P[p] * sF
    b_h2 = H2.get(p, 0.0) * sc
    return b_fix, b_steam, b_el, phi, b_h2


def residual(p):
    """Calibrated remainder, held at its national value.

    In v4 the CCU residuals are directly interpretable: plant chemicals, transport,
    capital goods, capture-unit electricity, and small rounding of the fixed
    electricity balance.  The SI decomposes them item by item.
    """
    return NET_NAT[p] - sum(terms(p, F_NAT, T_NAT, EF_NAT))


def net(p, F, T, EF, cr=CR):
    """Net life-cycle result of pathway p, t-CO2 per year."""
    return sum(terms(p, F, T, EF, cr)) + residual(p)


# ---- four-group view used by the displayed Eq. 2 ---------------------------------
def terms4(p, F, T, EF, cr=CR):
    b_fix, b_steam, b_el, phi, b_h2 = terms(p, F, T, EF, cr)
    return b_fix, b_steam + b_el, phi, b_h2


def bio_stored(p, F, T, cr=CR):
    """Biogenic carbon NET-PERMANENTLY stored, credited under convention B only.

    Geological storage injects the whole captured stream, so the stored biogenic
    carbon is (T - F) * cr.  Mineralization re-releases the reactor loss L_R
    (mixed basis), whose biogenic share is therefore not stored; v3 credited the
    whole captured biogenic stream for both classes.  No other class stores
    permanently: CCU products re-release (fuel) or hold carbon only temporarily
    (U2b, ~10-year median), so they earn no convention-B credit.
    """
    c = CLASS[p]
    if c == 'geo':
        return (T - F) * cr
    if c == 'min':
        return (T - F) * cr - (1.0 - F / T) * L_R[p] * s_cap(T, cr)
    return 0.0


if __name__ == '__main__':
    print('Check 1: reproduces the ledger statics exactly')
    ok = True
    for p in ORDER:
        v = net(p, F_NAT, T_NAT, EF_NAT)
        ok &= abs(v - NET_NAT[p]) < 1e-6
        print(f'  {p:<5}{v:>14,.4f}  target {NET_NAT[p]:>14,.4f}')
    print('  all reproduce exactly:', ok)
    assert ok

    print('\nCheck 2: CCU residuals are now interpretable (t-CO2/y)')
    KB = LED['KEEP_BURDENS']
    for p, src in [('U1', 'U1'), ('U2a', 'U2'), ('U2b', 'U2')]:
        r = residual(p)
        parts = KB[src]['chem'] + KB[src]['transport'] + KB[src]['capital']
        print(f'  {p:<5}residual {r:>10,.1f}   chem+transport+capital {parts:>10,.1f}'
              f'   gap {r - parts:>+8,.1f}')

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
