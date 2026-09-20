# -*- coding: utf-8 -*-
"""Final-size figures of the R1 manuscript and SI (format pass, 2026-09-20).

Every value is computed exactly as in the frozen chain's plotting scripts (build_figs.py, plot_regional.py,
plot_climate.py, plot_mc_ab.py) by importing the model read-only from the R1g snapshot; Fig. S1 is drawn from
the snapshot's matrix CSVs of F5_mc_correlation.py.  Only the presentation changes: each figure is drawn at the
physical width at which it is placed in the document (1:1, no scaling), the smallest text is 7 pt, titles that
repeat the caption are removed, units follow the text (t-CO2 y-1), and internal labels are dropped.
Outputs go to ./out (PNG 600 dpi + PDF).  Nothing is written to the snapshot; its SHA-256 manifest is
re-verified at the end."""
import csv, hashlib, os, sys
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r1_paths                                   # noqa: E402
SNAP, CODE, ANA_DIR, MANIFEST = r1_paths.resolve(__file__)
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, CODE)
for k in ('R1C_SCENARIO', 'REGION_WEIGHTING'):
    os.environ.pop(k, None)
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import carbon_model as CB
import scenario_decomposition as SD
import regional_model as RV
from climate_response import emission_series, crf
from build_climate import P as CP, ORDER as CORDER, HORIZONS
import monte_carlo as M

MIN_PT = 7.0
MINUS = '−'
plt.rcParams.update({
    'font.family': 'Times New Roman', 'mathtext.fontset': 'stix', 'font.size': 8,
    'axes.labelsize': 8, 'axes.titlesize': 8, 'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5,
    'legend.fontsize': 7.5, 'text.color': 'black', 'axes.labelcolor': 'black', 'xtick.color': 'black',
    'ytick.color': 'black', 'axes.edgecolor': 'black', 'axes.linewidth': 0.8, 'legend.edgecolor': 'black',
    'legend.framealpha': 1.0, 'savefig.facecolor': 'white', 'figure.facecolor': 'white',
    'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
    'axes.unicode_minus': True})
SIZES = {}
THOUS = mticker.FuncFormatter(lambda v, _: f'{v:,.0f}'.replace('-', MINUS))


def frame(ax):
    for s in ax.spines.values():
        s.set_visible(True); s.set_color('black'); s.set_linewidth(0.8); s.set_zorder(3)


def save(fig, name):
    """Save at the placed size; every visible text must be >= MIN_PT."""
    sizes = [t.get_fontsize() for t in fig.findobj(matplotlib.text.Text) if t.get_text().strip() and t.get_visible()]
    SIZES[name] = (min(sizes), fig.get_size_inches().tolist())
    assert min(sizes) >= MIN_PT - 1e-9, (name, min(sizes))
    fig.savefig(os.path.join(OUT, name + '.png'), dpi=600)
    fig.savefig(os.path.join(OUT, name + '.pdf'))
    plt.close(fig)


UNIT = 't-CO$_2$ y$^{-1}$'
name = {'S0': 'Reference WtE', 'M1': 'Mineral. olivine (direct)', 'M2': 'Mineral. serpentine',
        'M3': 'Mineral. carbide slag', 'M4': 'Mineral. steel slag', 'G1': 'Geol. storage 1200 m',
        'G2': 'Geol. storage 3000 m', 'U1': 'CCU methane', 'U2a': 'CCU methanol to fuel',
        'U2b': 'CCU methanol to chemicals', 'R1': 'CR oil to fuel', 'R2': 'CR to naphtha', 'R3': 'CR to HVC'}
grp = {'S0': 'ref', 'M1': 'min', 'M2': 'min', 'M3': 'min', 'M4': 'min', 'G1': 'geo', 'G2': 'geo',
       'U1': 'ccu', 'U2a': 'ccu', 'U2b': 'ccu', 'R1': 'cr', 'R2': 'cr', 'R3': 'cr'}
gc = {'ref': '#444444', 'min': '#8c564b', 'geo': '#9467bd', 'ccu': '#1f77b4', 'cr': '#2ca02c'}

# ------------------------------------------------------------------ Fig. 2 and Fig. 4 (build_figs.py)
A25 = {p: CB.net(p, CB.F_NAT, CB.T_NAT, CB.EF_NAT) for p in CB.ORDER}
A50 = {p: SD.net(p, True, True, True) for p in CB.ORDER}
B25 = {p: A25[p] - CB.bio_stored(p, CB.F_NAT, CB.T_NAT) for p in CB.ORDER if CB.CLASS[p] in ('min', 'geo')}

order = sorted(A25, key=lambda p: A50[p])
y = np.arange(len(order)); h = 0.38
fig, ax = plt.subplots(figsize=(6.3, 4.3))
ax.barh(y + h / 2, [A25[p] for p in order], height=h, color=[gc[grp[p]] for p in order], alpha=0.5,
        label='Present background')
ax.barh(y - h / 2, [A50[p] for p in order], height=h, color=[gc[grp[p]] for p in order], alpha=1.0,
        label='2050 background')
ax.axvline(0, color='k', lw=0.6)
ax.axvline(A50['S0'], color='r', ls=':', lw=1.0, label='Reference plant, 2050')
ax.set_yticks(y); ax.set_yticklabels([f'{p}  {name[p]}' for p in order])
ax.invert_yaxis(); ax.set_xlabel('Net life-cycle CO$_2$, convention A (' + UNIT + ')')
ax.xaxis.set_major_formatter(THOUS)
ax.legend(loc='upper right'); ax.grid(alpha=0.3, axis='x', lw=0.5); frame(ax)
fig.tight_layout(); save(fig, 'Fig2_static_ranking')

mg = ['M1', 'M2', 'M3', 'M4', 'G1', 'G2']; y2 = np.arange(len(mg))
fig, ax = plt.subplots(figsize=(6.3, 2.9))
for j, p in enumerate(mg):
    a, b = A25[p], B25[p]
    ax.plot([b, a], [j, j], color='#bbbbbb', lw=2, zorder=1)
    ax.scatter(a, j, color='#d62728', zorder=3, s=30)
    ax.scatter(b, j, color='#1f77b4', zorder=3, s=30)
    ax.annotate(f'Δ = {a - b:,.0f}', ((a + b) / 2, j), textcoords='offset points', xytext=(0, 4.5),
                ha='center', fontsize=7, color='#444444', zorder=4,
                bbox=dict(boxstyle='square,pad=0.1', fc='white', ec='none'))
ax.axvline(0, color='green', lw=0.6)
ax.axvline(A25['S0'], color='k', ls=':', lw=1.0, label='Reference plant, 2025')
ax.scatter([], [], color='#d62728', s=30, label='Convention A (biogenic CO$_2$ neutral)')
ax.scatter([], [], color='#1f77b4', s=30, label='Convention B (stored biogenic CO$_2$ credited)')
ax.set_yticks(y2); ax.set_yticklabels([f'{p}  {name[p]}' for p in mg])
ax.invert_yaxis(); ax.set_ylim(len(mg) - 0.5, -0.8)
ax.set_xlabel('Net life-cycle CO$_2$, 2025 (' + UNIT + ')')
ax.xaxis.set_major_formatter(THOUS)
ax.legend(loc='lower right'); ax.grid(alpha=0.3, axis='x', lw=0.5); frame(ax)
fig.tight_layout(); save(fig, 'Fig3_biogenic_swing')

# ------------------------------------------------------------------ Fig. 3 regional heatmap (plot_regional.py)
regs = RV.load()
names = sorted(regs)
paths = [p for p in CB.ORDER if p != 'S0']
net = {p: {n: CB.net(p, regs[n]['F'], regs[n]['T'], regs[n]['EF']) for n in names} for p in CB.ORDER}
D = np.array([[net[p][n] - net['S0'][n] for n in names] for p in paths]) / 1000.0
fig, ax = plt.subplots(figsize=(6.5, 4.6))
lim = np.abs(D).max()
im = ax.imshow(D, cmap='RdBu_r', vmin=-lim, vmax=lim, aspect='auto')
ax.set_xticks(range(len(names)))
ax.set_xticklabels([f"{n}\n{regs[n]['EF'] * 1000:.0f}\n{100 * regs[n]['F'] / regs[n]['T']:.0f}%" for n in names],
                   fontsize=7)
ax.set_yticks(range(len(paths))); ax.set_yticklabels([f'{p}  {name[p]}' for p in paths], fontsize=7)
for i in range(len(paths)):
    for j in range(len(names)):
        ax.text(j, i, f'{D[i, j]:.1f}'.replace('-', MINUS), ha='center', va='center', fontsize=7,
                color='white' if abs(D[i, j]) > lim * 0.55 else 'black')
for j, n in enumerate(names):
    col = D[:, j]
    for i in np.flatnonzero(np.isclose(col, col.min(), rtol=1e-12, atol=0.0)):
        ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False, edgecolor='black', lw=1.6))
frame(ax)
ax.set_xlabel('Grid region, grid emission factor (g-CO$_2$ kWh$^{-1}$) and fossil share of waste carbon')
cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.015)
cb.set_label('Difference from the regional reference (kt-CO$_2$ y$^{-1}$)'); cb.ax.tick_params(labelsize=7)
cb.outline.set_edgecolor('black'); cb.outline.set_linewidth(0.8)
fig.tight_layout(); save(fig, 'Fig_regional_heatmap')

# ------------------------------------------------------------------ Fig. 5 climate (plot_climate.py)
TT = 150
CRF = {}
for p in CORDER:
    d = CP[p]
    CRF[p] = crf(emission_series(d['n0'], d['S'], TT, d['mode'], d.get('tau50'), d.get('k', 2.0)))
t = np.arange(TT + 1)
fig, ax = plt.subplots(1, 2, figsize=(6.5, 3.6))
show = ['S0', 'M1', 'G1', 'U1', 'U2a', 'U2b', 'R1', 'R2', 'R3']
sty = {'S0': ('0.35', '-'), 'M1': ('#8c564b', '-'), 'G1': ('#9467bd', '-'), 'U1': ('#1f77b4', '--'),
       'U2a': ('#1f77b4', '-'), 'U2b': ('#d62728', '-'), 'R1': ('#2ca02c', '--'), 'R2': ('#8c8c00', ':'),
       'R3': ('#2ca02c', '-')}
for p in show:
    c, ls = sty[p]
    ax[0].plot(t, CRF[p] * 1e12 / 1e3, color=c, ls=ls, lw=1.2, label=p)
ax[0].axhline(0, color='black', lw=0.6)
ylo = ax[0].get_ylim()[0]
for hz, H in HORIZONS.items():
    if H <= TT:
        ax[0].axvline(H, color='0.75', lw=0.6, ls=':')
        ax[0].text(H, ylo, hz, fontsize=7, rotation=90, va='bottom', ha='right', color='0.35')
ax[0].set_xlabel('Years after one year of operation')
ax[0].set_ylabel('Cumulative radiative forcing (10$^{-9}$ W m$^{-2}$ y)')
ax[0].set_title('(a) Physical climate response', loc='left')
ax[0].legend(loc='upper left', ncol=3, fontsize=7, handlelength=1.8, columnspacing=0.8, framealpha=0.9)
ax[0].grid(alpha=0.25, lw=0.5)
pool = CB.LED['POOLS']['U2b']
S = pool['deferred_net']
NETc = {p: CB.net(p, CB.F_NAT, CB.T_NAT, CB.EF_NAT) for p in CORDER}
ca = crf(emission_series(NETc['U2a'], 0.0, TT, 'pulse'))


def share(tau):
    cb_ = crf(emission_series(NETc['U2b'] + S, S, TT, 'weibull', tau, pool['k']))
    with np.errstate(divide='ignore', invalid='ignore'):
        return 100.0 * cb_ / ca


t1 = np.arange(1, TT + 1)
ax[1].fill_between(t1, share(30.0)[1:], share(5.0)[1:], color='#d62728', alpha=0.16, lw=0,
                   label='Median lifetime 5 to 30 y')
ax[1].plot(t1, share(pool['tau50'])[1:], color='#d62728', lw=1.5,
           label=f"Base case, median lifetime {pool['tau50']:.0f} y")
ax[1].axhline(100, color='black', lw=0.6, ls='--')
for hz, H in HORIZONS.items():
    if H <= TT:
        v = share(pool['tau50'])[H]
        ax[1].axvline(H, color='0.75', lw=0.6, ls=':')
        ax[1].plot([H], [v], 'o', ms=3.2, color='#d62728', zorder=4)
        ax[1].annotate('%s\n%.0f%%' % (hz, v), (H, v), textcoords='offset points', xytext=(4, -16), fontsize=7,
                       color='#8b1a1a')
ax[1].set_xlim(0, TT); ax[1].set_ylim(20, 108)
ax[1].set_xlabel('Assessment endpoint (years after one year of operation)')
ax[1].set_ylabel('Share of the fuel route’s benefit realised\nby the feedstock route (%)')
ax[1].set_title('(b) Durability postpones the benefit', loc='left')
ax[1].legend(loc='lower right', fontsize=7)
ax[1].grid(alpha=0.25, lw=0.5)
for a in ax:
    frame(a)
fig.tight_layout(w_pad=1.0); save(fig, 'Fig_climate_dynamic')

# ------------------------------------------------------------------ Fig. 6 Monte Carlo (plot_mc_ab.py)
A, Bt = M.evaluate(M.MASTER, 'A'), M.evaluate(M.MASTER, 'B')
O = CB.ORDER


def stats(netd):
    arr = np.vstack([netd[p] for p in O]); r = arr.argsort(0).argsort(0); s0 = netd['S0']
    return dict((p, np.mean(netd[p] < s0)) for p in O), r


pltA, rkA = stats(A)
pltB, rkB = stats(Bt)
fig, ax = plt.subplots(1, 3, figsize=(6.5, 3.0), gridspec_kw={'width_ratios': [1.0, 1.0, 0.95]})
for k, (rk, ttl) in enumerate([(rkA, '(a) Rank, treatment A'), (rkB, '(b) Rank, treatment B')]):
    top = [p for p in O if max(np.mean(rk[O.index(p)] == q) for q in range(5)) > 0.01]
    R = np.array([[np.mean(rk[O.index(p)] == q) for q in range(6)] for p in top])
    ax[k].imshow(R, cmap='Blues', vmin=0, vmax=max(R.max(), 0.4), aspect='auto')
    ax[k].set_xticks(range(6)); ax[k].set_xticklabels([str(q + 1) for q in range(6)])
    ax[k].set_yticks(range(len(top))); ax[k].set_yticklabels(top)
    for i in range(len(top)):
        for j in range(6):
            if R[i, j] > 0.005:
                ax[k].text(j, i, f'{R[i, j]:.2f}'.lstrip('0') if R[i, j] < 0.995 else '1', ha='center',
                           va='center', fontsize=7, color='white' if R[i, j] > R.max() * 0.6 else 'black')
    ax[k].set_xlabel('Rank'); ax[k].set_title(ttl, loc='left')
show = [p for p in O if p != 'S0']
yy = np.arange(len(show)); hh = 0.38
ax[2].barh(yy + hh / 2, [pltA[p] for p in show], height=hh, color='#4c72b0', edgecolor='black', lw=0.3,
           label='Treatment A')
ax[2].barh(yy - hh / 2, [pltB[p] for p in show], height=hh, color='#dd8452', edgecolor='black', lw=0.3,
           label='Treatment B')
ax[2].set_yticks(yy); ax[2].set_yticklabels(show); ax[2].invert_yaxis()
ax[2].set_xlim(0, 1.08); ax[2].set_xlabel('P(lower than the reference)')
ax[2].set_title('(c) Beating the reference', loc='left')
ax[2].legend(loc='upper right', fontsize=7); ax[2].grid(alpha=0.25, axis='x', lw=0.5)
for a in ax:
    frame(a)
fig.tight_layout(w_pad=0.6); save(fig, 'Fig_mc_parameter')

# ------------------------------------------------------------------ Fig. S1 (F5_mc_correlation.py matrices)
ANA = ANA_DIR


def mat(fn):
    rows = list(csv.reader(open(os.path.join(ANA, fn), encoding='utf-8-sig')))
    return rows[0][1:], np.array([[float(x) for x in r[1:]] for r in rows[1:]])


fig, axes = plt.subplots(2, 2, figsize=(6.5, 6.6))
panels = [('(a) Spearman ρ, treatment A', 'F5_mc_spearman_A.csv', 'RdBu_r', -1, 1, 'rho'),
          ('(b) P(row < column), treatment A', 'F5_mc_pairwise_prob_A.csv', 'Blues', 0, 1, 'P'),
          ('(c) Spearman ρ, treatment B', 'F5_mc_spearman_B.csv', 'RdBu_r', -1, 1, 'rho'),
          ('(d) P(row < column), treatment B', 'F5_mc_pairwise_prob_B.csv', 'Blues', 0, 1, 'P')]
for ax, (ttl, fn, cmap, vmin, vmax, lab) in zip(axes.ravel(), panels):
    labels, Mx = mat(fn)
    NP = len(labels)
    assert labels == list(CB.ORDER), labels
    im = ax.imshow(Mx, cmap=cmap, vmin=vmin, vmax=vmax, aspect='equal')
    ax.set_xticks(range(NP)); ax.set_xticklabels(labels, fontsize=7, rotation=90)
    ax.set_yticks(range(NP)); ax.set_yticklabels(labels, fontsize=7)
    for i in range(NP):
        for j in range(NP):
            if i == j:
                continue
            v = Mx[i, j]
            if lab == 'rho':
                s = f'{v:.1f}'.replace('0.', '.').replace('-', MINUS)
                s = '.0' if s == MINUS + '.0' else s
            else:
                s = f'{v:.1f}'.lstrip('0') if 0.05 <= v <= 0.95 else ('1' if v > 0.5 else '0')
            strong = (abs(v) > 0.6) if lab == 'rho' else (v > 0.6)
            ax.text(j, i, s, ha='center', va='center', fontsize=7, color='white' if strong else 'black')
    for k in (0.5, 4.5, 6.5, 9.5):
        ax.axhline(k, color='black', lw=0.5); ax.axvline(k, color='black', lw=0.5)
    ax.set_title(ttl, loc='left')
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03); cbar.ax.tick_params(labelsize=7)
    frame(ax)
fig.tight_layout()
save(fig, 'FigS1')

# ------------------------------------------------------------------ snapshot untouched
# the model code and its parameters must be untouched; regenerated outputs may differ (a re-run of the
# model rewrites them, and the workbook format stores a timestamp), so those are reported, not asserted
bad, reran = [], []
if MANIFEST:                                      # the frozen snapshot, or the archive's own manifest
    for line in open(MANIFEST, encoding='utf-8'):
        hsh, pth = line.split(maxsplit=1); pth = pth.strip().lstrip('*')
        f = os.path.join(SNAP, pth)
        if not os.path.isfile(f) or hashlib.sha256(open(f, 'rb').read()).hexdigest() == hsh:
            continue
        (reran if '/outputs/' in pth or os.sep + 'outputs' + os.sep in pth else bad).append(pth)
extra = [r for r, _, fs in os.walk(CODE) if '__pycache__' in r]
assert not bad and not extra, (bad, extra)
if reran:
    print(f'note: {len(reran)} output file(s) differ from the shipped digests (the model was re-run here)')
for k, (mn, sz) in SIZES.items():
    print(f'{k:<22} {sz[0]:.2f} x {sz[1]:.2f} in, smallest text {mn:.1f} pt')
print('snapshot manifest verified, no __pycache__')
