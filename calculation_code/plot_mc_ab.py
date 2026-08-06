"""Fig. 6, regenerated from the corrected model, showing both boundary treatments."""
import numpy as np, os
import matplotlib.pyplot as plt
from fig_style import apply as _apply, frame as _frame, save
_apply()
import carbon_model as CB
import monte_carlo as M

A, Bt = M.evaluate(M.MASTER,'A'), M.evaluate(M.MASTER,'B')
O = CB.ORDER


def stats(net):
    arr = np.vstack([net[p] for p in O]); r = arr.argsort(0).argsort(0); s0 = net['S0']
    return (dict((p, np.mean(r[i] == 0)) for i, p in enumerate(O)),
            dict((p, np.mean(net[p] < s0)) for p in O), r)


r1A, pltA, rkA = stats(A)
r1B, pltB, rkB = stats(Bt)

fig, ax = plt.subplots(1, 3, figsize=(13.2, 4.5),
                       gridspec_kw={'width_ratios': [1.0, 1.0, 0.9]})

# (a) rank acceptability, treatment A
for k, (rk, ttl) in enumerate([(rkA, '(a) Rank acceptability, treatment A'),
                               (rkB, '(b) Rank acceptability, treatment B')]):
    top = [p for p in O if max(np.mean(rk[O.index(p)] == q) for q in range(5)) > 0.01]
    R = np.array([[np.mean(rk[O.index(p)] == q) for q in range(6)] for p in top])
    im = ax[k].imshow(R, cmap='Blues', vmin=0, vmax=max(R.max(), 0.4), aspect='auto')
    ax[k].set_xticks(range(6)); ax[k].set_xticklabels([str(q + 1) for q in range(6)])
    ax[k].set_yticks(range(len(top))); ax[k].set_yticklabels(top, fontsize=8)
    for i in range(len(top)):
        for j in range(6):
            if R[i, j] > 0.005:
                ax[k].text(j, i, f'{R[i,j]:.2f}', ha='center', va='center', fontsize=6.6,
                           color='white' if R[i, j] > R.max() * 0.6 else 'black')
    ax[k].set_xlabel('Rank'); ax[k].set_title(ttl, fontsize=9.5)

# (c) P(<reference), both treatments
show = [p for p in O if p != 'S0']
y = np.arange(len(show)); h = 0.38
ax[2].barh(y + h / 2, [pltA[p] for p in show], height=h, color='#4c72b0',
           edgecolor='black', lw=0.4, label='treatment A')
ax[2].barh(y - h / 2, [pltB[p] for p in show], height=h, color='#dd8452',
           edgecolor='black', lw=0.4, label='treatment B')
ax[2].set_yticks(y); ax[2].set_yticklabels(show, fontsize=8); ax[2].invert_yaxis()
ax[2].set_xlim(0, 1.08); ax[2].set_xlabel('P(lower than the reference plant)')
ax[2].set_title('(c) Probability of beating the reference', fontsize=9.5)
ax[2].legend(fontsize=7.5, loc='upper right', framealpha=1.0); ax[2].grid(alpha=0.25, axis='x')

for a in ax:
    _frame(a)
plt.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs',
                   'Fig_mc_parameter.png')
save(out)
print('saved', out)
print('\nfamily P(rank 1):')
for t, r1 in (('A', r1A), ('B', r1B)):
    fam = {f_: sum(r1[p] for p in O if CB.CLASS[p] == f_)
           for f_ in ('min', 'geo', 'ccu', 'cr')}
    print(f'  {t}: ' + '  '.join(f'{k} {v:.2f}' for k, v in fam.items()))
