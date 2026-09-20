# -*- coding: utf-8 -*-
"""
Monte Carlo on the v4 balance (carbon_model), revision R1.

Two features of the sampling design deserve an explicit note:

  1. The waste stream is described by TWO independent sampled variables, the
     combustion CO2 of one year of throughput (T) and the fossil share of that
     carbon (f); the fossil carbon F = T f is derived from them.  Three quantities
     that satisfy F = T f cannot all be sampled independently, and which two are
     chosen decides both the induced spread of the third and the meaning of the
     rank correlations.  T and f are chosen because both have a measured spread in
     the shipped regional data, and F does not have one independent of them.
     Their widths are taken from that data (see build_master); the fossil share
     also carries the +11.2 % definitional sensitivity of the fossil rule.
     Because the three are algebraically tied, the rank correlations of F should
     be read as the correlations of a derived quantity, and the sensitivity
     statement in the paper is made on the two sampled variables.

  2. The draw evaluation uses the same terms as the deterministic model: vents and
     reactor losses at their fossil share, credits in the split form QA - f * QB,
     and hydrogen as a multiplier on the 5.4459 kg-CO2 per kg-H2 base.

R1 addition.  The two explicit CAP-class groups of carbon_model.terms() carry their
own lognormal multipliers, sampled like the process-electricity multipliers (median
1, shared at a declared level) and with the width the residual class had in R0
(GSD 1.15), because in R0 these items were inside the residual and perturbed at
that width:
     reag_mult          one draw shared by all nine capture pathways: the solvent
                        burden is one declared figure for one capture unit
     trans_mult_<fam>   one draw per capture family (geo, min, ccu): CO2 shipping,
                        ore transport and CO2 trucking are different systems
The four new columns are appended AFTER the R0 columns in the master matrix, so the
first 24 columns (and every R0 draw of every R0 variable) are identical draw for draw
to the submitted matrix; only the model that reads them changed.  The declared wide
sensitivities of the two terms (solvent x0.5 / x2, transport x0 / x2 / x4, ore
transport x0.5 / x2, CO2 losses, U transport 719, U 90 kWh/t) are run
deterministically in compare_P2C2.py (P2C2_sensitivities.csv), not through these
multipliers; the multipliers (GSD 1.15) are deliberately narrower than those ranges.

R1b (phase 2b) note.  Nothing in the sampling changes: the matrix is the same 28
columns from the same seed.  The model it reads now carries E_PROC from source kWh
for all 13 pathways, so for U1/U2a/U2b the process-electricity multiplier
elec_mult_ccu also perturbs the 15 kWh per t-CO2 capture line that R0 held constant
inside the residual (D10a), and reag_mult multiplies the whole REAGENT_T (solvent +
the two capture-unit increments).  The G1/G2 residual is -4.66 t-CO2/y, so rem_mult
on those two pathways is immaterial.

R1c note.  Nothing in the sampling changes (same 28 columns, same seed).  The model it
reads carries the R1c items inside E_PROC (common 90 kWh/t module for all nine capture
pathways, U tanker liquefaction, G ship liquefaction / unloading / wellhead boost) and
TRANSPORT_T (G ship fuel + road leg), so elec_mult_<family> now also perturbs those
electricity items and trans_mult_geo the ship leg.  The CO2-loss term of the declared
loss scenarios (carbon_model.LOSS, zero in the base) enters phi exactly as in the
deterministic model; the Monte Carlo is run for the base only.

R1d note.  Sampling unchanged.  The G2 ship-mode receiving side is now pumping to
injection pressure 4.5 kWh/t (in place of unloading 2.5 + wellhead boost 7); the plant
light oil (G1/G2) and the capture-unit capital (all nine capture pathways) sit in the
constant residual C_p and are not sampled; U synthesis capital is outside the base.

Same seed 20260702, same N = 50,000.
"""
import numpy as np

import carbon_model as CB

SEED = 20260702
N = 50000
ORDER = CB.ORDER
FAMILIES = ['ccu', 'cr', 'geo', 'min', 'ref']          # fixed, sorted: deterministic
CAP_FAMILIES = ['ccu', 'geo', 'min']                   # families with a capture unit
F_SHARE_NAT = CB.F_NAT / CB.T_NAT
GSD_CAP_TERMS = 1.15                                   # R1 solvent / transport width
GSD_T = 1.0109736508779386                     # R1e: T_r spread, W2a regions (R0/R1d 1.0129)
GSD_F = 1.1031141542916696                     # R1e: fossil share, 47 rebuilt prefectures (R0/R1d 1.1062)


def build_master(seed=SEED, n=N):
    """Every random variable drawn once, in a fixed and explicitly sorted order.
    Column order is fixed and explicit so that the matrix is reproducible from the
    seed alone; the fossil share is appended after the other twenty-four R0 columns,
    and the four R1 multipliers after the derived fossil carbon."""
    rng = np.random.default_rng(seed)
    ln = lambda med, gsd: med * rng.lognormal(0.0, np.log(gsd), n)
    m = {}
    # The two INDEPENDENT waste variables are the combustion CO2 of the throughput
    # and the fossil share of that carbon; the fossil carbon is their product.
    # Both widths are measured, not chosen, with one formula: GSD = exp(sample standard
    # deviation of ln x, ddof = 1) (R1_revision/02_analyses/R1e_regional/build_R1e.py, R1e_gsd.json;
    # the same formula reproduces the R0 constants 1.0129 and 1.1062 from the submitted data).
    #   T   GSD_T = 1.0110: spread of T_r across the ten tonnage-weighted (W2a) regions of
    #       the R1e rebuild (72,981 to 76,154 t-CO2/y, reconciliation_regional.csv).  R0/R1d used
    #       1.0129, from the submitted unweighted regional table.
    #   f   GSD_F = 1.1031: spread of the fossil share of the carbon across the 47
    #       prefecture profiles rebuilt from the MoEJ FY2021 facility table (26.81 to 42.39 %,
    #       prefecture_waste_carbon.csv), wider than the ten-region spread (GSD 1.074).
    #       R0/R1d used 1.1062.
    # The induced spread of F is then GSD 1.104, against a measured inter-regional
    # 1.084 -- slightly wider than the data, which is the intended direction.
    # Medians T_NAT and F_SHARE_NAT, the seed and the column order are unchanged in R1e.
    m['throughput'] = ln(CB.T_NAT, GSD_T)                  # shared by all pathways (R1e)
    m['grid_EF'] = ln(CB.EF_NAT, 1.06)                     # shared by all pathways
    m['capture_rate'] = rng.beta(CB.CR * 260, (1 - CB.CR) * 260, n)
    m['H2_EF'] = ln(1.0, 1.20)                             # multiplier on 5.4459
    for f in FAMILIES:
        m['elec_mult_' + f] = ln(1.0, 1.10)
    for p in ORDER:
        m['rem_mult_' + p] = ln(1.0, 1.15)
    m['fossil_share'] = ln(F_SHARE_NAT, GSD_F)             # shared by all pathways (R1e)
    m['fossil_C'] = m['throughput'] * m['fossil_share']    # derived, no rng draw
    # ---- R1: multipliers of the two explicit CAP-class groups (appended) ----
    m['reag_mult'] = ln(1.0, GSD_CAP_TERMS)                # shared by capture pathways
    for f in CAP_FAMILIES:
        m['trans_mult_' + f] = ln(1.0, GSD_CAP_TERMS)
    return m


MASTER = build_master()


def unit_master():
    """The deterministic point: every sampled variable at its median / national value
    and every multiplier at one.  Used by the Eq. 2 vs Eq. 6 checks."""
    det = {'fossil_C': np.array([CB.F_NAT]), 'throughput': np.array([CB.T_NAT]),
           'grid_EF': np.array([CB.EF_NAT]), 'capture_rate': np.array([CB.CR]),
           'H2_EF': np.array([1.0]), 'fossil_share': np.array([F_SHARE_NAT]),
           'reag_mult': np.array([1.0])}
    for f in FAMILIES:
        det['elec_mult_' + f] = np.array([1.0])
    for p in ORDER:
        det['rem_mult_' + p] = np.array([1.0])
    for f in CAP_FAMILIES:
        det['trans_mult_' + f] = np.array([1.0])
    return det


def evaluate(master, treatment):
    """Evaluate all pathways on the master draws. Only the recycling boundary
    differs between treatments A and B."""
    F, T = master['fossil_C'], master['throughput']
    EF, cr, mh2 = master['grid_EF'], master['capture_rate'], master['H2_EF']
    f = F / T                                              # sampled fossil share
    sc = (T * cr) / (CB.T_NAT * CB.CR)                     # captured-stream scaling
    sF = F / CB.F_NAT                                      # diverted-plastic scaling
    out = {}
    for p in ORDER:
        c = CB.CLASS[p]
        fam = master['elec_mult_' + c]
        rem = master['rem_mult_' + p]
        cap = p in CB.CAPTURES

        b_fix = (CB.AUX - CB.EXP_NOCC) * EF
        b_steam = CB.STEAM_PEN * sc * EF if cap else 0.0
        if cap:
            b_el = CB.E_PROC[p] * sc * EF * fam
        elif c == 'cr':
            b_el = CB.E_PROC[p] * sF * EF * fam
        else:
            b_el = CB.E_PROC[p] * EF * fam

        if c == 'ref':
            phi = F
        elif c == 'geo':
            phi = (1 - cr) * F + CB.LOSS[p] * cr * F          # R1c loss (0 in the base)
        elif c == 'min':
            phi = (1 - cr) * F + CB.L_R[p] * sc * f
        elif c == 'ccu':
            phi = ((1 - cr) * F + CB.V_P[p] * sc * f - (CB.QA[p] - f * CB.QB[p]) * sc
                   + CB.LOSS[p] * cr * F)
        else:
            phi = F - (CB.D_P[p] * sF if treatment == 'A' else 0.0)

        b_h2 = CB.H2.get(p, 0.0) * sc * mh2

        # R1: explicit CAP-class solvent and transport terms with their multipliers
        if cap:
            b_reag = CB.REAG[p] * sc * master['reag_mult']
            b_trans = CB.TRANS[p] * sc * master['trans_mult_' + c]
        else:
            b_reag = 0.0
            b_trans = 0.0

        # calibrated residual at national conditions, same construction as the
        # deterministic model; under treatment B the diverted-carbon credit is not
        # taken, so the national anchor shifts by D_p.
        nat = list(CB.terms(p, CB.F_NAT, CB.T_NAT, CB.EF_NAT))
        if c == 'cr' and treatment == 'B':
            nat[3] += CB.D_P[p]
            base = CB.NET_NAT[p] + CB.D_P[p]
        else:
            base = CB.NET_NAT[p]
        const = base - sum(nat)

        out[p] = (b_fix + b_steam + b_el + phi + b_h2 + b_reag + b_trans
                  + const * rem)
    return out


def summarise(net):
    arr = np.vstack([net[p] for p in ORDER])
    ranks = arr.argsort(axis=0).argsort(axis=0)
    s0 = net['S0']
    rows = []
    for i, p in enumerate(ORDER):
        v = net[p]
        rows.append([p, np.median(v), np.percentile(v, 2.5), np.percentile(v, 97.5),
                     np.mean(v < s0), np.mean(ranks[i] == 0), np.mean(v < 0)])
    return rows, ranks


if __name__ == '__main__':
    print('Master matrix: %d variables x %d draws, seed %d' % (len(MASTER), N, SEED))

    # The master matrix keeps the R0 construction for its first 24 columns; the four
    # R1 multipliers are appended after them, so the R0 draws are unchanged.  Both
    # boundary treatments read one and the same matrix, which the pairing audit
    # below verifies.
    det = unit_master()
    dA = evaluate(det, 'A')
    mx = max(abs(float(dA[p][0]) - CB.net(p, CB.F_NAT, CB.T_NAT, CB.EF_NAT))
             for p in ORDER)
    print(f'Eq.2 vs Eq.6 at national conditions, all multipliers one: '
          f'max |diff| = {mx:.10f}')
    assert mx < 1e-9

    A, B = evaluate(MASTER, 'A'), evaluate(MASTER, 'B')
    mx = max(np.abs(A[p] - B[p]).max() for p in ORDER if CB.CLASS[p] != 'cr')
    print(f'A/B pairing, non-recycling pathways: max |A - B| = {mx:.10f}')
    assert mx == 0.0

    print('\ntreatment A medians and rank-1 probability:')
    rows, ranks = summarise(A)
    for r in rows:
        print(f'  {r[0]:<5}median {r[1]:>12,.0f}   2.5% {r[2]:>12,.0f}   '
              f'97.5% {r[3]:>12,.0f}   P(rank 1) {r[5]:.3f}   P(<0) {r[6]:.3f}')
