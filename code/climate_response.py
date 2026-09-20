"""
Physical dynamic climate layer: CO2 impulse-response -> atmospheric burden ->
radiative forcing -> cumulative radiative forcing at fixed endpoints.

This layer is PHYSICAL and is kept strictly separate from the normative
time-preference (discounting) layer. Discounting is a policy parameter, not a
property of the climate system.

IRF_CO2(u) = a0 + sum_j a_j exp(-u/tau_j)          (Joos et al., 2013, ACP 13, 2793-2825)
  a0=0.2173; (a1,tau1)=(0.2240, 394.4 y); (a2,tau2)=(0.2824, 36.54 y);
  (a3,tau3)=(0.2763, 4.304 y)
B_p(t)   = sum_{s<=t} dE_p(s) * IRF(t-s)           atmospheric burden (t-CO2)
RF_p(t)  = A_CO2 * B_p(t)                          radiative forcing (W m-2)
CRF_p(H) = INT_0^H RF_p(t) dt                      cumulative RF (W m-2 y)
                                                   (trapezoid rule on the annual grid)
A_CO2 = 1.7517e-15 W m-2 per kg-CO2 (IPCC AR5 radiative efficiency).
Validation: a 1 kg pulse must reproduce the closed-form integral of this same IRF,
agwp_analytic(100) = 9.1711e-14 W m-2 y kg-1, to better than 0.1 %.

Product carbon release uses a Weibull with an explicit MEDIAN lifetime tau50:
  F(t) = 1 - exp(-ln2 * (t/tau50)^k)               F(tau50) = 0.5 by construction
"""
import numpy as np

# ---- Joos et al. (2013) CO2 impulse response ----
A0 = 0.2173
AJ = np.array([0.2240, 0.2824, 0.2763])
TJ = np.array([394.4, 36.54, 4.304])
A_CO2 = 1.7517e-15          # W m-2 per kg-CO2 (IPCC AR5)
KG_PER_T = 1000.0

def irf(u):
    u = np.asarray(u, dtype=float)
    return A0 + sum(a * np.exp(-u / t) for a, t in zip(AJ, TJ))

# ---- product-carbon release ----
def weibull_release(tau50, k, T):
    """Annual release fractions f(t), t = 0..T, for a Weibull with median tau50."""
    t = np.arange(0, T + 1, dtype=float)
    F = 1.0 - np.exp(-np.log(2.0) * (t / tau50) ** k)
    f = np.diff(np.concatenate(([0.0], F)))
    return f

def emission_series(n0, S, T, mode='none', tau50=None, k=2.0):
    """
    Annual net emission series dE(t), t = 0..T, in t-CO2.
      n0    day-0 net emission excluding any temporary-storage credit
      S     carbon removed into product storage at t=0 and released later
      mode  'none'    permanent storage / no temporary product carbon
            'pulse'   released essentially at once (short-lived fuels)
            'weibull' product lifetime with median tau50 and shape k
    Mass balance: sum(dE) = n0 for every mode (checked in tests).
    """
    dE = np.zeros(T + 1)
    dE[0] = n0 - S
    if S == 0 or mode == 'none':
        return dE
    if mode == 'pulse':
        dE[0] += S                      # sub-annual release, same year
        return dE
    f = weibull_release(tau50, k, T)
    dE += S * f
    dE[0] -= S * f[0] * 0               # f already covers t=0..T
    return dE

def burden(dE):
    """Atmospheric burden B(t) = sum_{s<=t} dE(s) IRF(t-s)  (t-CO2)."""
    T = len(dE) - 1
    kern = irf(np.arange(0, T + 1))
    return np.convolve(dE, kern)[:T + 1]

def agwp_analytic(H):
    """Exact integral of the implemented impulse response over [0, H], per kg-CO2:
    A * INT_0^H IRF(u) du = A * [a0 H + SUM_j aj tau_j (1 - exp(-H/tau_j))].
    This is the closed form of the SAME parameterization used by irf(), so it is a
    self-consistent reference for the numerical scheme rather than an external one."""
    return A_CO2 * (A0 * H + sum(a * t * (1.0 - np.exp(-H / t))
                                 for a, t in zip(AJ, TJ)))

def crf(dE):
    """Cumulative radiative forcing series, W m-2 y (cumulative to each t).

    The forcing is integrated with the TRAPEZOID rule over the annual grid.  The
    earlier implementation used np.cumsum, i.e. H+1 full rectangles for a window of
    H years, which counts a whole year of forcing at t = 0 and overstates the
    integral: +1.4 % at H = 100 and +20 % at H = 5 against agwp_analytic().  The
    trapezoid rule reproduces the closed form to about 0.01 % at H = 100."""
    rf = A_CO2 * burden(dE) * KG_PER_T
    return np.concatenate(([0.0], np.cumsum(0.5 * (rf[1:] + rf[:-1]))))

# ---------------------------------------------------------------- validation
def _validate():
    T = 100
    pulse = np.zeros(T + 1); pulse[0] = 1e-3          # 1 kg = 1e-3 t
    got = crf(pulse)[-1]
    exp = agwp_analytic(T)                            # closed form of this same IRF
    assert abs(got - exp) / exp < 0.001, f'AGWP100 {got:.4e} vs analytic {exp:.4e}'
    # Weibull median property
    f = weibull_release(10.0, 2.0, 200)
    assert abs(f[:11].sum() - 0.5) < 0.02, f'median release {f[:11].sum():.3f}'
    # Mass balance: sum(dE) = n0 for every mode, and dE(0) = n0 - S.
    # This is checked on the SAME quantities the model runs on (R1c feedstock
    # methanol, U2b): the whole-horizon net is -45,469.26 t-CO2 per year
    # (STATIC_V4[U2a] after R1c, apply_r1c.py), of which -33,040.86 is a NET
    # CREDIT deferred to the product lifetime, leaving -12,428.40 in the operating
    # year.  Signs are negative because the deferred quantity is a credit, not a
    # stored emission; the arithmetic is identical.
    # (R0 used -47,769.93 / -14,729.07; phase 2 -48,092.12 / -15,051.26; R1b
    # -48,054.42 / -15,013.56; the deferred credit is unchanged in R1.)
    N0, S = -45469.2639, -33040.8606
    dE = emission_series(N0, S, 500, 'weibull', 10.0, 2.0)
    assert abs(dE.sum() - N0) / abs(N0) < 0.01, f'mass balance {dE.sum():.1f}'
    assert abs(dE[0] - (N0 - S)) < 1e-6, f'day-0 term {dE[0]:.4f}'
    return got, f[:11].sum(), (dE.sum(), dE[0])

if __name__ == '__main__':
    g, m, b = _validate()
    print('VALIDATION')
    a = agwp_analytic(100)
    print(f'  AGWP_100 of a 1 kg CO2 pulse : {g:.4e} W m-2 y kg-1  '
          f'(closed form of the same IRF {a:.4e}, dev {100*(g-a)/a:+.3f}%)')
    print(f'  Weibull median check (tau50=10): cumulative release by t=10 = {m:.3f}')
    print(f'  Mass balance U2b series: sum dE = {b[0]:,.0f} t-CO2 = whole-horizon '
          f'net; day-0 term {b[1]:,.0f} = operating-year static, the remaining '
          f'-33,041 being the deferred net credit')
