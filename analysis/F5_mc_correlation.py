# -*- coding: utf-8 -*-
"""
Correlation structure among the thirteen
pathways in the component-level Monte Carlo, recomputed on the R1f draws of chain_r1.

Reads (read-only, chain_r1/calculation_code/outputs/):
  MonteCarlo_pathway_outputs_A.csv   50,000 draws x 13 pathways, t-CO2/y, treatment A
  MonteCarlo_pathway_outputs_B.csv   same, treatment B
  MonteCarlo_master_draws.csv        50,000 draws x 28 columns (27 sampled + derived fossil_C)
  MonteCarlo_summary_AB.csv          chain summary, used as cross-check of P(<reference)
  MonteCarlo_rank_correlations.csv   chain Spearman(input, pathway), used as cross-check
Reads (read-only, same folder): F_mc_key_pairs_paired_vs_independent.csv,
  F_mc_spearman_A.csv / _B.csv (the R0-based Task F results, for the R0 -> R1f comparison).

Writes (only into R1_revision/02_analyses/, prefix F5_):
  F5_mc_spearman_<T>.csv                       13 x 13 Spearman rho of pathway net results
  F5_mc_pairwise_prob_<T>.csv                  13 x 13 P(row < col), draw by draw (paired)
  F5_mc_all_pairs_paired_vs_independent_<T>.csv  78 unordered pairs: rho, paired P, independent P
  F5_mc_key_pairs_paired_vs_independent.csv    G1-S0, U2a-R1, U1-S0, M1-S0, both treatments
  F5_mc_pathway_vs_shared_inputs_A.csv         Spearman of each pathway with the ten shared inputs
  F5_mc_R0_vs_R1f_key_pairs.csv                the key-pair numbers of Task F (R0 draws) beside R1c
  F5_mc_R0_vs_R1f_spearman_delta_<T>.csv       13 x 13 rho(R1c) - rho(R0)
  F5_FigS1.png / F5_FigS1.pdf                  draft SI Fig. S1, 2 x 2, 600 dpi via the copy's fig_style
  F5_mc_runtime.txt                            timings, package versions, SHA-256 of the inputs

Independence approximation: column j is permuted with numpy default_rng(20260702)
(one permutation, the same for every pair).  Cross-check: the exact value implied by
the two marginals, P_ind = U / n^2 with U the Mann-Whitney statistic (by sorting).
This archive copy differs from the working-repository version only in (1) portable path resolution and (2) conditional omission of an internal development-comparison block whose F2 inputs are not part of the published analysis. Neither change affects the manuscript or Supplementary Information outputs: the omitted block runs after all fourteen published matrices have been written, and those matrices are byte-identical to the shipped ones (ZIP_VERIFICATION.md).
"""
import os, sys, time, hashlib
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
T0 = time.perf_counter()
# the archive is self-contained: no absolute root is needed
OUT = os.path.dirname(os.path.abspath(__file__))        # archive: <root>/analysis
CHAIN = os.environ.get('R1_CODE') or os.path.normpath(os.path.join(OUT, '..', 'code'))
OUTPUTS = os.path.join(CHAIN, 'outputs')
SEED = 20260702
NP = 13
ORDER = ['S0', 'M1', 'M2', 'M3', 'M4', 'G1', 'G2', 'U1', 'U2a', 'U2b', 'R1', 'R2', 'R3']
FAMILY = {'S0': 'ref', 'M1': 'min', 'M2': 'min', 'M3': 'min', 'M4': 'min', 'G1': 'geo',
          'G2': 'geo', 'U1': 'ccu', 'U2a': 'ccu', 'U2b': 'ccu', 'R1': 'cr', 'R2': 'cr', 'R3': 'cr'}
KEY_PAIRS = [('G1', 'S0'), ('U2a', 'R1'), ('U1', 'S0'), ('M1', 'S0')]
MASTER_COLS_R0 = ['throughput', 'grid_EF', 'capture_rate', 'H2_EF', 'elec_mult_ccu', 'elec_mult_cr',
                  'elec_mult_geo', 'elec_mult_min', 'elec_mult_ref'] + ['rem_mult_' + p for p in ORDER] + \
                 ['fossil_share', 'fossil_C']
MASTER_COLS_R1 = ['reag_mult', 'trans_mult_ccu', 'trans_mult_geo', 'trans_mult_min']
SHARED = ['fossil_C', 'fossil_share', 'throughput', 'grid_EF', 'capture_rate', 'H2_EF'] + MASTER_COLS_R1
timing = {}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


# ---------------------------------------------------------------- load
t = time.perf_counter()
IN_FILES = ['MonteCarlo_pathway_outputs_A.csv', 'MonteCarlo_pathway_outputs_B.csv',
            'MonteCarlo_master_draws.csv', 'MonteCarlo_summary_AB.csv', 'MonteCarlo_rank_correlations.csv']
HASHES = {f: sha256(os.path.join(OUTPUTS, f)) for f in IN_FILES}
A = pd.read_csv(os.path.join(OUTPUTS, IN_FILES[0]))
B = pd.read_csv(os.path.join(OUTPUTS, IN_FILES[1]))
M = pd.read_csv(os.path.join(OUTPUTS, IN_FILES[2]))
S = pd.read_csv(os.path.join(OUTPUTS, IN_FILES[3]))
RC = pd.read_csv(os.path.join(OUTPUTS, IN_FILES[4]))
timing['load'] = time.perf_counter() - t
n = len(A)
assert list(A.columns) == ['draw_id'] + ORDER, A.columns
assert list(B.columns) == ['draw_id'] + ORDER, B.columns
assert list(M.columns) == ['draw_id'] + MASTER_COLS_R0 + MASTER_COLS_R1, list(M.columns)
assert (A.draw_id.values == np.arange(n)).all() and (B.draw_id.values == A.draw_id.values).all()
assert (M.draw_id.values == A.draw_id.values).all()
print(f'draws n = {n}; master matrix {M.shape[1] - 1} columns '
      f'({len(MASTER_COLS_R0)} R0 + {len(MASTER_COLS_R1)} R1); draw_id aligned across A, B and master')
non_cr = [p for p in ORDER if FAMILY[p] != 'cr']
mx = np.abs(A[non_cr].values - B[non_cr].values).max()
print(f'A vs B, non-recycling pathways: max |A - B| = {mx:.3e} (expected 0)')
assert mx == 0.0
# chain summary must be reproduced by the draws themselves (median / P(<0))
for tr, df in (('A', A), ('B', B)):
    ref = S[S.treatment == tr].set_index('pathway')
    dmed = max(abs(np.median(df[p]) - ref.loc[p, 'median']) for p in ORDER)
    dneg = max(abs(np.mean(df[p] < 0) - ref.loc[p, 'P(net_negative)']) for p in ORDER)
    print(f'treatment {tr}: max |median(draws) - summary median| = {dmed:.2e} t; '
          f'max |P(<0) - summary| = {dneg:.2e}')
    assert dmed < 1e-3 and dneg < 1e-9


def p_less_paired(x, y):
    return float(np.mean(x < y))


def p_less_exact_indep(x, y):
    """P(X < Y) if X and Y were independent with the observed marginals (Mann-Whitney U / n^2)."""
    ys = np.sort(y)
    return float(np.mean((len(ys) - np.searchsorted(ys, x, side='right')) / len(ys)))


def p_less_shuffled(x, y, seed=SEED):
    rng = np.random.default_rng(seed)
    return float(np.mean(x < y[rng.permutation(len(y))]))


results = {}
offdiag = ~np.eye(NP, dtype=bool)
for tr, df in (('A', A), ('B', B)):
    X = df[ORDER]
    # (1) Spearman 13 x 13
    t = time.perf_counter()
    rho = X.corr(method='spearman')
    timing[f'spearman_{tr}'] = time.perf_counter() - t
    rho.round(6).to_csv(os.path.join(OUT, f'F5_mc_spearman_{tr}.csv'), index_label='pathway')
    # (2) pairwise P(row < col), paired
    t = time.perf_counter()
    V = X.values
    P = np.zeros((NP, NP))
    ties = np.zeros((NP, NP))
    for i in range(NP):
        for j in range(NP):
            if i != j:
                P[i, j] = np.mean(V[:, i] < V[:, j])
                ties[i, j] = np.mean(V[:, i] == V[:, j])
    timing[f'pairwise_{tr}'] = time.perf_counter() - t
    Pdf = pd.DataFrame(P, index=ORDER, columns=ORDER)
    Pdf.round(6).to_csv(os.path.join(OUT, f'F5_mc_pairwise_prob_{tr}.csv'), index_label='P(row<col)')
    closure = np.abs((P + P.T)[offdiag] - 1).max()
    print(f'treatment {tr}: max off-diagonal tie fraction = {ties.max():.2e}; '
          f'max |P(i<j) + P(j<i) - 1| = {closure:.2e}')
    # cross-check against MonteCarlo_summary_AB.csv P(<reference)
    ref = S[S.treatment == tr].set_index('pathway')['P(<reference)']
    d = max(abs(P[ORDER.index(p), 0] - ref[p]) for p in ORDER if p != 'S0')
    print(f'treatment {tr}: max |P(p<S0) - summary file P(<reference)| = {d:.2e}')
    assert d < 1e-9
    # all 78 unordered pairs: paired vs independent
    t = time.perf_counter()
    rows = []
    for a in range(NP):
        for b in range(a + 1, NP):
            pi, pj = ORDER[a], ORDER[b]
            x, y = V[:, a], V[:, b]
            pp = p_less_paired(x, y)
            ps = p_less_shuffled(x, y)
            pe = p_less_exact_indep(x, y)
            dif = x - y
            rows.append(dict(treatment=tr, i=pi, j=pj, family_i=FAMILY[pi], family_j=FAMILY[pj],
                             spearman_rho=rho.loc[pi, pj], pearson_r=np.corrcoef(x, y)[0, 1],
                             P_paired_i_lt_j=pp, P_shuffled_i_lt_j=ps, P_exact_indep_i_lt_j=pe,
                             paired_minus_independent=pp - pe,
                             sd_diff_paired=dif.std(ddof=1),
                             sd_diff_if_independent=np.sqrt(x.var(ddof=1) + y.var(ddof=1)),
                             median_diff=np.median(dif), diff_p2_5=np.percentile(dif, 2.5),
                             diff_p97_5=np.percentile(dif, 97.5)))
    allp = pd.DataFrame(rows)
    allp.to_csv(os.path.join(OUT, f'F5_mc_all_pairs_paired_vs_independent_{tr}.csv'), index=False,
                float_format='%.6f')
    timing[f'all_pairs_{tr}'] = time.perf_counter() - t
    results[tr] = dict(rho=rho, P=Pdf, allp=allp, V=V)

# (3) key comparisons, both treatments
t = time.perf_counter()
krows = []
for tr in ('A', 'B'):
    V = results[tr]['V']; rho = results[tr]['rho']
    for pi, pj in KEY_PAIRS:
        x, y = V[:, ORDER.index(pi)], V[:, ORDER.index(pj)]
        pp, ps, pe = p_less_paired(x, y), p_less_shuffled(x, y), p_less_exact_indep(x, y)
        dif = x - y
        reps = [p_less_shuffled(x, y, seed=SEED + k) for k in range(20)]
        krows.append(dict(
            treatment=tr, comparison=f'{pi} vs {pj}', quantity=f'P({pi} < {pj})',
            spearman_rho=rho.loc[pi, pj], pearson_r=np.corrcoef(x, y)[0, 1],
            P_paired=pp, P_independent_shuffle_seed20260702=ps,
            P_independent_shuffle_mean_20seeds=np.mean(reps), P_independent_shuffle_sd_20seeds=np.std(reps, ddof=1),
            P_independent_exact_from_marginals=pe,
            paired_minus_independent=pp - pe,
            n_draws_i_ge_j_paired=int(np.sum(x >= y)),
            binomial_SE_at_N50000=np.sqrt(pp * (1 - pp) / n),
            median_i=np.median(x), median_j=np.median(y),
            median_diff_i_minus_j=np.median(dif), diff_p2_5=np.percentile(dif, 2.5),
            diff_p97_5=np.percentile(dif, 97.5), diff_max=dif.max(), diff_min=dif.min(),
            sd_diff_paired=dif.std(ddof=1), sd_diff_if_independent=np.sqrt(x.var(ddof=1) + y.var(ddof=1)),
            sd_ratio_paired_over_independent=dif.std(ddof=1) / np.sqrt(x.var(ddof=1) + y.var(ddof=1)),
            unit='t-CO2 per year (medians, differences, sd); probabilities and rho dimensionless'))
key = pd.DataFrame(krows)
key.to_csv(os.path.join(OUT, 'F5_mc_key_pairs_paired_vs_independent.csv'), index=False, float_format='%.6f')
timing['key_pairs'] = time.perf_counter() - t

# (4) drivers: Spearman of each pathway with the ten shared / family inputs (treatment A)
drv = pd.concat([M[SHARED], A[ORDER]], axis=1).corr(method='spearman').loc[ORDER, SHARED]
drv.round(4).to_csv(os.path.join(OUT, 'F5_mc_pathway_vs_shared_inputs_A.csv'), index_label='pathway')
# cross-check against the chain's MonteCarlo_rank_correlations.csv (4 decimals there)
rcA = RC[RC.treatment == 'A'].set_index(['pathway', 'input_variable'])['spearman_coefficient']
dmax = 0.0
for p in ORDER:
    for v in SHARED:
        if (p, v) in rcA.index:
            dmax = max(dmax, abs(round(drv.loc[p, v], 4) - rcA[(p, v)]))
print(f'drivers: max |Spearman(here) - chain MonteCarlo_rank_correlations.csv| = {dmax:.2e} (4-decimal file)')
assert dmax < 1.5e-4

# (5) R0 (Task F) vs R1c (this run) comparison of the key pairs and the rho matrices
t = time.perf_counter()
key0 = pd.read_csv(os.path.join(OUT, 'F_mc_key_pairs_paired_vs_independent.csv'))
cmp_cols = ['spearman_rho', 'P_paired', 'P_independent_exact_from_marginals', 'paired_minus_independent',
            'sd_ratio_paired_over_independent', 'median_diff_i_minus_j', 'diff_p2_5', 'diff_p97_5']
crows = []
for (tr, comp), g1 in key.groupby(['treatment', 'comparison'], sort=False):
    g0 = key0[(key0.treatment == tr) & (key0.comparison == comp)]
    assert len(g0) == 1 and len(g1) == 1
    r = dict(treatment=tr, comparison=comp)
    for c in cmp_cols:
        r[c + '_R0'] = float(g0[c].iloc[0]); r[c + '_R1c'] = float(g1[c].iloc[0])
        r[c + '_delta'] = r[c + '_R1c'] - r[c + '_R0']
    crows.append(r)
cmp = pd.DataFrame(crows)
cmp.to_csv(os.path.join(OUT, 'F5_mc_R0_vs_R1f_key_pairs.csv'), index=False, float_format='%.6f')
rho_delta = {}
for tr in ('A', 'B'):
    r0 = pd.read_csv(os.path.join(OUT, f'F_mc_spearman_{tr}.csv'), index_col=0).loc[ORDER, ORDER]
    dd = results[tr]['rho'] - r0
    dd.round(6).to_csv(os.path.join(OUT, f'F5_mc_R0_vs_R1f_spearman_delta_{tr}.csv'), index_label='pathway')
    rho_delta[tr] = dd
timing['r0_vs_r1b'] = time.perf_counter() - t

# ---------------------------------------------------------------- print
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
for tr in ('A', 'B'):
    print(f'\n=== Spearman rho, treatment {tr} ===')
    print(results[tr]['rho'].round(2).to_string())
    print(f'\n=== P(row < col), treatment {tr} ===')
    print(results[tr]['P'].round(4).to_string())
    allp = results[tr]['allp']
    off = results[tr]['rho'].values[offdiag]
    ge5 = int((np.abs(off) >= 0.5).sum() // 2); lt1 = int((np.abs(off) < 0.1).sum() // 2)
    imin = np.unravel_index(np.argmin(np.where(offdiag, results[tr]['rho'].values, 9)), (NP, NP))
    imax = np.unravel_index(np.argmax(np.where(offdiag, results[tr]['rho'].values, -9)), (NP, NP))
    print(f'\ntreatment {tr}: off-diagonal rho range {off.min():.3f} ({ORDER[imin[0]]}-{ORDER[imin[1]]}) to '
          f'{off.max():.3f} ({ORDER[imax[0]]}-{ORDER[imax[1]]}); median {np.median(off):.3f}; '
          f'|rho| >= 0.5 in {ge5} of 78 pairs; |rho| < 0.1 in {lt1} of 78 pairs; '
          f'negative rho in {int((off < 0).sum() // 2)} pairs (min {off.min():.4f})')
    print(f'treatment {tr}: mean |paired - independent| over 78 pairs = '
          f'{allp.paired_minus_independent.abs().mean():.4f}; max = {allp.paired_minus_independent.abs().max():.4f}; '
          f'max |shuffle - exact| = {(allp.P_shuffled_i_lt_j - allp.P_exact_indep_i_lt_j).abs().max():.4f}; '
          f'max |r - rho| = {(allp.pearson_r - allp.spearman_rho).abs().max():.4f}')
    print(f'largest |paired - independent| shifts, treatment {tr}:')
    print(allp.reindex(allp.paired_minus_independent.abs().sort_values(ascending=False).index)
          .head(12)[['i', 'j', 'spearman_rho', 'P_paired_i_lt_j', 'P_exact_indep_i_lt_j',
                     'P_shuffled_i_lt_j', 'paired_minus_independent', 'sd_diff_paired',
                     'sd_diff_if_independent']].round(4).to_string(index=False))
    print(f'smallest sd ratios (paired / independent), treatment {tr}:')
    rr = allp.assign(ratio=allp.sd_diff_paired / allp.sd_diff_if_independent).sort_values('ratio')
    print(rr.head(8)[['i', 'j', 'spearman_rho', 'sd_diff_paired', 'sd_diff_if_independent', 'ratio']]
          .round(4).to_string(index=False))
    print(f'rho(R1c) - rho(R0), treatment {tr}: max |delta| = {np.abs(rho_delta[tr].values).max():.3f}; '
          f'cells with |delta| >= 0.05:')
    dd = rho_delta[tr]
    for a in range(NP):
        for b in range(a + 1, NP):
            if abs(dd.iloc[a, b]) >= 0.05:
                print(f'   {ORDER[a]}-{ORDER[b]}: R0 {results[tr]["rho"].iloc[a, b] - dd.iloc[a, b]:.3f} -> '
                      f'R1c {results[tr]["rho"].iloc[a, b]:.3f} (delta {dd.iloc[a, b]:+.3f})')
print('\n=== key pairs (R1c) ===')
print(key[['treatment', 'comparison', 'spearman_rho', 'P_paired', 'P_independent_shuffle_seed20260702',
           'P_independent_shuffle_mean_20seeds', 'P_independent_shuffle_sd_20seeds',
           'P_independent_exact_from_marginals', 'paired_minus_independent', 'n_draws_i_ge_j_paired',
           'binomial_SE_at_N50000', 'sd_ratio_paired_over_independent',
           'median_diff_i_minus_j', 'diff_p2_5', 'diff_p97_5', 'diff_max']].round(4).to_string(index=False))
print('\n=== key pairs, R0 (Task F) vs R1c ===')
print(cmp[['treatment', 'comparison', 'spearman_rho_R0', 'spearman_rho_R1c', 'P_paired_R0', 'P_paired_R1c',
           'P_independent_exact_from_marginals_R0', 'P_independent_exact_from_marginals_R1c',
           'paired_minus_independent_R0', 'paired_minus_independent_R1c',
           'median_diff_i_minus_j_R0', 'median_diff_i_minus_j_R1c']].round(4).to_string(index=False))
print('\n=== Spearman of pathway result vs shared inputs, treatment A (R1c) ===')
print(drv.round(2).to_string())

# ---------------------------------------------------------------- figure (copy's fig_style, 600 dpi)
t = time.perf_counter()
sys.path.insert(0, CHAIN)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import fig_style
assert os.path.dirname(os.path.abspath(fig_style.__file__)).lower() == CHAIN.lower(), fig_style.__file__
fig_style.apply()

fig, axes = plt.subplots(2, 2, figsize=(7.4, 7.6))
panels = [('(a) Spearman rho between pathway results, treatment A', results['A']['rho'].values, 'RdBu_r', -1, 1, 'rho'),
          ('(b) P(row pathway < column pathway), treatment A', results['A']['P'].values, 'Blues', 0, 1, 'P'),
          ('(c) Spearman rho between pathway results, treatment B', results['B']['rho'].values, 'RdBu_r', -1, 1, 'rho'),
          ('(d) P(row pathway < column pathway), treatment B', results['B']['P'].values, 'Blues', 0, 1, 'P')]
for ax, (ttl, Mx, cmap, vmin, vmax, lab) in zip(axes.ravel(), panels):
    im = ax.imshow(Mx, cmap=cmap, vmin=vmin, vmax=vmax, aspect='equal')
    ax.set_xticks(range(NP)); ax.set_xticklabels(ORDER, fontsize=6.5, rotation=90)
    ax.set_yticks(range(NP)); ax.set_yticklabels(ORDER, fontsize=6.5)
    for i in range(NP):
        for j in range(NP):
            if lab == 'P' and i == j:
                continue
            v = Mx[i, j]
            if lab == 'rho':
                s = f'{v:.2f}'
            else:
                s = f'{v:.2f}' if 0.005 <= v <= 0.995 else ('1' if v > 0.5 else '0')
            strong = (abs(v) > 0.6) if lab == 'rho' else (v > 0.6)
            ax.text(j, i, s, ha='center', va='center', fontsize=4.6, color='white' if strong else 'black')
    for k in (0.5, 4.5, 6.5, 9.5):
        ax.axhline(k, color='black', lw=0.5); ax.axvline(k, color='black', lw=0.5)
    ax.set_title(ttl, fontsize=8)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.ax.tick_params(labelsize=6.5)
    fig_style.frame(ax)
fig.text(0.5, 0.005, 'Draft, R1f-F (chain_r1, R1f draws). Lines separate families: S0 | M1-M4 | G1-G2 | '
         'U1-U2b | R1-R3. N = 50,000 draws, seed 20260702.', ha='center', fontsize=6.5)
plt.tight_layout(rect=(0, 0.015, 1, 1))
png = os.path.join(OUT, 'F5_FigS1.png')
fig_style.save(png, dpi=600)
timing['figure'] = time.perf_counter() - t
timing['total'] = time.perf_counter() - T0
with open(os.path.join(OUT, 'F5_mc_runtime.txt'), 'w', encoding='utf-8') as fh:
    for k, v in timing.items():
        fh.write(f'{k}: {v:.3f} s\n')
    fh.write(f'python {sys.version.split()[0]}, numpy {np.__version__}, pandas {pd.__version__}, '
             f'matplotlib {matplotlib.__version__}\n')
    fh.write(f'inputs: {OUTPUTS}\n')
    for f, h in HASHES.items():
        fh.write(f'sha256 {f}: {h}\n')
    fh.write(f'fig_style: {os.path.abspath(fig_style.__file__)}\n')
print('\nruntime (s):', {k: round(v, 3) for k, v in timing.items()})
for f, h in HASHES.items():
    print(f'sha256 {f}: {h[:16]}...')
print('saved', png)


# ---------------------------------------------------------------- R1c note (R0 -> R1b -> R1c)
def _p(k, t, c):
    return float(k[(k.treatment == t) & (k.comparison == c)].P_paired.iloc[0])


def _note():
    k0 = pd.read_csv(os.path.join(OUT, 'F_mc_key_pairs_paired_vs_independent.csv'))
    k1 = pd.read_csv(os.path.join(OUT, 'F2_mc_key_pairs_paired_vs_independent.csv'))
    k2 = pd.read_csv(os.path.join(OUT, 'F5_mc_key_pairs_paired_vs_independent.csv'))
    r1 = {t: pd.read_csv(os.path.join(OUT, f'F2_mc_spearman_{t}.csv'), index_col=0) for t in 'AB'}
    r2 = {t: pd.read_csv(os.path.join(OUT, f'F5_mc_spearman_{t}.csv'), index_col=0) for t in 'AB'}
    L = ['# Task F, R1c — correlation structure among pathways in the Monte Carlo, recomputed on the R1f draws',
         '',
         'Date: 2026-09-19. Script: `R1_revision/02_analyses/F5_mc_correlation.py` (a copy of `F2_mc_correlation.py` with '
         'the output prefix F5_ and this note appended). Inputs: `chain_r1/calculation_code/outputs/` after the R1c run '
         '(`chain_r1/run_all_R1c.log`; master matrix unchanged, 28 columns, seed 20260702, N = 50,000). Outputs: the '
         '`F5_*` files beside this note (same layout as `F2_*`; `F5_mc_R0_vs_R1f_*` compare with the R0 Task F files). '
         'Method, definitions and the draft SI figure are as in `F2_mc_correlation.md`; only the numbers change. '
         'Nothing in `chain_r1/` was written by this script.',
         '',
         '## 1. Key pairs, R0 → R1b → R1c',
         '',
         '| Treatment | Comparison | ρ R0 | ρ R1b | **ρ R1c** | P paired R0 | R1b | **R1c** | P independent (exact) R1c | '
         'paired − independent R1c | median difference R1b | **R1c** |',
         '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _, r in k2.iterrows():
        a = k0[(k0.treatment == r.treatment) & (k0.comparison == r.comparison)].iloc[0]
        b = k1[(k1.treatment == r.treatment) & (k1.comparison == r.comparison)].iloc[0]
        L.append(f'| {r.treatment} | {r.comparison} | {a.spearman_rho:.3f} | {b.spearman_rho:.3f} | **{r.spearman_rho:.3f}** | '
                 f'{a.P_paired:.4f} | {b.P_paired:.4f} | **{r.P_paired:.4f}** | {r.P_independent_exact_from_marginals:.4f} | '
                 f'{r.paired_minus_independent:+.4f} | {b.median_diff_i_minus_j:,.0f} | **{r.median_diff_i_minus_j:,.0f}** |')
    L += ['', '## 2. Largest changes of the 13 x 13 Spearman matrix, R1b → R1c', '']
    for t in 'AB':
        d = (r2[t] - r1[t])
        pairs = []
        for i, a in enumerate(d.index):
            for j, b in enumerate(d.columns):
                if j > i:
                    pairs.append((abs(d.loc[a, b]), a, b, r1[t].loc[a, b], r2[t].loc[a, b]))
        pairs.sort(reverse=True)
        L.append(f'Treatment {t}: max |Δρ| = {pairs[0][0]:.3f}; largest five: ' + '; '.join(
            f'{a}–{b} {x:.3f} → {y:.3f}' for _, a, b, x, y in pairs[:5]) + '.')
        L.append('')
    L += ['## 3. Reading',
          '',
          '- The dependence structure of R1b is preserved: every probability in Fig. 6 and SI Tables S18–S20 remains a paired '
          '(draw-by-draw) comparison, and the paired and independent probabilities of the key pairs still agree within the '
          'binomial error except where one pathway dominates (G1 vs S0 = 1 in both).',
          '- R1c moves the U medians up by about 2.6 kt (the 90 kWh/t module and the tanker liquefaction), which lowers '
          f'P(U1 < S0) from {_p(k1, "A", "U1 vs S0"):.4f} to {_p(k2, "A", "U1 vs S0"):.4f} and P(U2a < R1) from '
          f'{_p(k1, "A", "U2a vs R1"):.4f} to {_p(k2, "A", "U2a vs R1"):.4f}; G1 − S0 narrows by about 0.8 kt but stays '
          'negative in every draw.',
          '- The G pathways now carry more electricity inside E_PROC (liquefaction, unloading, G2 wellhead boost), so their '
          'rank correlation with the geo process-electricity multiplier rises (see `F5_mc_pathway_vs_shared_inputs_A.csv` '
          'and `P2C3_results_comparison.md` section 5).']
    open(os.path.join(OUT, 'F5_mc_correlation.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('written F5_mc_correlation.md')


if all(os.path.isfile(os.path.join(OUT, _f)) for _f in
       ('F2_mc_key_pairs_paired_vs_independent.csv', 'F2_mc_spearman_A.csv', 'F2_mc_spearman_B.csv')):
    _note()      # internal development note; its inputs are not part of this archive
