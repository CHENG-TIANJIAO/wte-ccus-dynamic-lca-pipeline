# -*- coding: utf-8 -*-
"""
Monte Carlo on the v4 balance (carbon_model).

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

Same seed 20260702, same N = 50,000.
"""
import numpy as np

import carbon_model as CB

SEED = 20260702
N = 50000
ORDER = CB.ORDER
FAMILIES = ['ccu', 'cr', 'geo', 'min', 'ref']          # fixed, sorted: deterministic
F_SHARE_NAT = CB.F_NAT / CB.T_NAT


def build_master(seed=SEED, n=N):
    """Every random variable drawn once, in a fixed and explicitly sorted order.
    Column order is fixed and explicit so that the matrix is reproducible from the
    seed alone; the fossil share is appended after the other twenty-four."""
    rng = np.random.default_rng(seed)
    ln = lambda med, gsd: med * rng.lognormal(0.0, np.log(gsd), n)
    m = {}
    # The two INDEPENDENT waste variables are the combustion CO2 of the throughput
    # and the fossil share of that carbon; the fossil carbon is their product.
    # Both widths are measured, not chosen:
    #   T   GSD 1.013 = the spread of T_r across the ten regional composition
    #       profiles (72,792 to 76,130 t-CO2/y, reconciliation_regional.csv).
    #   f   GSD 1.106 = the spread of the fossil share of the carbon across the 47
    #       prefecture profiles (26.81 to 41.63 %, prefecture_waste_carbon.csv),
    #       which also covers the +11.2 % definitional sensitivity of the fossil
    #       rule and is wider than the ten-region spread (GSD 1.079).
    # The induced spread of F is then GSD 1.107, against a measured inter-regional
    # 1.093 -- slightly wider than the data, which is the intended direction.
    # An earlier version sampled F and f and derived T = F/f, which forced T to a
    # GSD of 1.145, eleven times the measured spread, and made T the largest rank
    # correlate of several pathways for no physical reason.
    m['throughput'] = ln(CB.T_NAT, 1.0129)                 # shared by all pathways
    m['grid_EF'] = ln(CB.EF_NAT, 1.06)                     # shared by all pathways
    m['capture_rate'] = rng.beta(CB.CR * 260, (1 - CB.CR) * 260, n)
    m['H2_EF'] = ln(1.0, 1.20)                             # multiplier on 5.4459
    for f in FAMILIES:
        m['elec_mult_' + f] = ln(1.0, 1.10)
    for p in ORDER:
        m['rem_mult_' + p] = ln(1.0, 1.15)
    m['fossil_share'] = ln(F_SHARE_NAT, 1.1062)            # shared by all pathways
    m['fossil_C'] = m['throughput'] * m['fossil_share']    # derived, no rng draw
    return m


MASTER = build_master()


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
            phi = (1 - cr) * F
        elif c == 'min':
            phi = (1 - cr) * F + CB.L_R[p] * sc * f
        elif c == 'ccu':
            phi = (1 - cr) * F + CB.V_P[p] * sc * f - (CB.QA[p] - f * CB.QB[p]) * sc
        else:
            phi = F - (CB.D_P[p] * sF if treatment == 'A' else 0.0)

        b_h2 = CB.H2.get(p, 0.0) * sc * mh2

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

        out[p] = b_fix + b_steam + b_el + phi + b_h2 + const * rem
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

    # The master matrix is regenerated for the thirteen-pathway set with the same
    # seed and the same fixed, sorted construction; the residual multipliers are
    # drawn one per pathway, so removing a pathway necessarily shifts the draws
    # that follow it. Both boundary treatments still read one and the same matrix,
    # which is what the pairing audit below verifies.
    det = {'fossil_C': np.array([CB.F_NAT]), 'throughput': np.array([CB.T_NAT]),
           'grid_EF': np.array([CB.EF_NAT]), 'capture_rate': np.array([CB.CR]),
           'H2_EF': np.array([1.0]), 'fossil_share': np.array([F_SHARE_NAT])}
    for f in FAMILIES:
        det['elec_mult_' + f] = np.array([1.0])
    for p in ORDER:
        det['rem_mult_' + p] = np.array([1.0])
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
