"""Fig. 5: (a) cumulative radiative forcing of one annual cohort;
(b) how much of the fuel route's benefit the feedstock route has realised
at each assessment endpoint, with the product-lifetime sensitivity band."""
import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
import os
from fig_style import save
from climate_response import emission_series, crf
from build_climate import P, ORDER, NAME, HORIZONS, T, static

plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 9,
                     'text.color': 'black', 'axes.labelcolor': 'black',
                     'xtick.color': 'black', 'ytick.color': 'black',
                     'axes.edgecolor': 'black', 'axes.linewidth': 1.0})

TT = 150
CRF, SER = {}, {}
for p in ORDER:
    d = P[p]
    dE = emission_series(d['n0'], d['S'], TT, d['mode'], d.get('tau50'), d.get('k', 2.0))
    SER[p] = dE; CRF[p] = crf(dE)
t = np.arange(TT + 1)

fig, ax = plt.subplots(1, 2, figsize=(10.6, 4.4))

# ---- (a) CRF trajectories ----
show = ['S0', 'M1', 'G1', 'U1', 'U2a', 'U2b', 'R1', 'R2', 'R3']
sty = {'S0': ('0.35', '-'), 'M1': ('#8c564b', '-'), 'G1': ('#9467bd', '-'),
       'U1': ('#1f77b4', '--'), 'U2a': ('#1f77b4', '-'), 'U2b': ('#d62728', '-'),
       'R1': ('#2ca02c', '--'), 'R2': ('#8c8c00', ':'), 'R3': ('#2ca02c', '-')}
for p in show:
    c, ls = sty[p]
    ax[0].plot(t, CRF[p] * 1e12 / 1e3, color=c, ls=ls, lw=1.6, label=f'{p} {NAME[p]}')
ax[0].axhline(0, color='black', lw=0.8)
# endpoint labels sit at the BOTTOM edge so the legend (upper left) never covers them
_ylo = ax[0].get_ylim()[0]
for h, H in HORIZONS.items():
    if H <= TT:
        ax[0].axvline(H, color='0.75', lw=0.7, ls=':')
        ax[0].text(H, _ylo, h, fontsize=6.5, rotation=90,
                   va='bottom', ha='right', color='0.4')
ax[0].set_xlabel('Years after one year of plant operation')
ax[0].set_ylabel('Cumulative radiative forcing (10$^{-9}$ W m$^{-2}$ y)')
ax[0].set_title('(a) Physical dynamic climate response', fontsize=10)
ax[0].legend(fontsize=6.6, loc='upper left', framealpha=0.9, edgecolor='black')
ax[0].grid(alpha=0.25)

# ---- (b) how much of the fuel route's benefit the feedstock route has realised ----
# Both methanol routes carry the same whole-horizon credit; the feedstock route
# defers part of it to the product lifetime.  At a fixed endpoint it has therefore
# realised only a fraction of the fuel route's cumulative benefit, and that
# fraction rises towards one as the endpoint recedes.  The band shows how the
# fraction depends on the assumed median product lifetime.
import carbon_model as _CB
_pool = _CB.LED['POOLS']['U2b']
_S = _pool['deferred_net']
_NET = {p: _CB.net(p, _CB.F_NAT, _CB.T_NAT, _CB.EF_NAT) for p in ORDER}
_ca = crf(emission_series(_NET['U2a'], 0.0, TT, 'pulse'))
def _share(tau):
    cb = crf(emission_series(_NET['U2b'] + _S, _S, TT, 'weibull', tau, _pool['k']))
    with np.errstate(divide='ignore', invalid='ignore'):
        return 100.0 * cb / _ca

_t1 = np.arange(1, TT + 1)
_lo, _hi = _share(30.0)[1:], _share(5.0)[1:]
_base = _share(_pool['tau50'])[1:]
ax[1].fill_between(_t1, _lo, _hi, color='#d62728', alpha=0.16, lw=0,
                   label='median product lifetime 5 to 30 y')
ax[1].plot(_t1, _base, color='#d62728', lw=2.0,
           label=f"base case, median lifetime {_pool['tau50']:.0f} y")
ax[1].axhline(100, color='black', lw=0.8, ls='--')
ax[1].text(TT * 0.985, 100.8, 'full realisation', fontsize=6.8, ha='right',
           va='bottom', color='0.25')
for h, H in HORIZONS.items():
    if H <= TT:
        v = _share(_pool['tau50'])[H]
        ax[1].axvline(H, color='0.75', lw=0.7, ls=':')
        ax[1].plot([H], [v], 'o', ms=4.2, color='#d62728', zorder=4)
        ax[1].annotate('%s\n%.0f%%' % (h, v), (H, v),
                       textcoords='offset points', xytext=(6, -13),
                       fontsize=6.8, color='#8b1a1a')
ax[1].set_xlim(0, TT)
ax[1].set_ylim(20, 108)
ax[1].set_xlabel('Assessment endpoint (years after one year of plant operation)')
ax[1].set_ylabel('Share of the fuel route’s cumulative benefit\n'
                 'realised by the feedstock route (%)')
ax[1].set_title('(b) Durability postpones the benefit rather than creating it',
                fontsize=10)
ax[1].legend(fontsize=6.8, loc='lower right', framealpha=0.95, edgecolor='black')
ax[1].grid(alpha=0.25)

# competition ranking is still reported, in the machine-readable source data and
# SI Table S16, but it no longer needs a panel: only the three recycling routes
# reorder between the static basis and the fixed endpoints.
def competition_rank(vals, rtol=1e-12):
    """Standard competition ranking on unrounded values; only numerically identical
    results share the better rank (1,1,3,...)."""
    order = sorted(vals, key=lambda q: vals[q])
    def same(a, b):
        return abs(a - b) <= rtol * max(1.0, abs(a), abs(b))
    r, i = {}, 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and same(vals[order[j + 1]], vals[order[i]]):
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = i + 1
        i = j + 1
    return r

rk = {'static': competition_rank(static)}
for h, H in HORIZONS.items():
    rk[h] = competition_rank({p: CRF[p][H] for p in ORDER})
cols = ['static'] + list(HORIZONS)
moved = [p for p in ORDER if len({rk[c][p] for c in cols}) > 1]

for a in ax:
    for s in a.spines.values():
        s.set_visible(True); s.set_color('black'); s.set_linewidth(1.0)
plt.tight_layout()
out = os.path.join(os.path.dirname(__file__), 'outputs', 'Fig_climate_dynamic.png')
save(out); print('saved', out)
print('pathways that change rank:', ', '.join(moved))

# ---- Fig. 5 source data: static basis, CRF at every fixed endpoint, and ranks ----
import csv
fp = os.path.join(os.path.dirname(__file__), 'outputs', 'Fig5_source_data.csv')
with open(fp, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['pathway', 'name', 'static_tCO2_per_y']
               + [f'CRF_{h}_W_m2_y' for h in HORIZONS]
               + ['rank_static'] + [f'rank_{h}' for h in HORIZONS]
               + ['changes_rank']
               + [f'benefit_share_vs_U2a_{h}_pct' for h in HORIZONS])
    for p in ORDER:
        w.writerow([p, NAME[p], f'{static[p]:.4f}']
                   + [f'{CRF[p][H]:.6e}' for H in HORIZONS.values()]
                   + [rk['static'][p]] + [rk[h][p] for h in HORIZONS]
                   + ['yes' if p in moved else 'no']
                   + ([f'{_share(_pool["tau50"])[H]:.2f}' for H in HORIZONS.values()]
                      if p == 'U2b' else [''] * len(HORIZONS)))
print(f'  wrote {fp} ({len(ORDER)} rows)')
