"""
Fig. 3 (regional heatmap), regenerated from the corrected carbon-balance model.

Supersedes the earlier version, which was drawn from regional_engine.py and therefore
still showed the retracted result that capture increases emissions in two regions.
Every cell here comes from carbon_balance.net via regional_model.
"""
import numpy as np, os, sys
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fig_style import apply as _apply, frame as _frame, save
_apply()
import carbon_model as CB
import regional_model as RV

regs = RV.load()
names = sorted(regs)
paths = [p for p in CB.ORDER if p != 'S0']
label = {'M1': 'M1 Mineral. olivine', 'M2': 'M2 Mineral. serpentine',
         'M3': 'M3 Mineral. carbide slag', 'M4': 'M4 Mineral. steel slag',
         'G1': 'G1 Geol. storage 1200 m', 'G2': 'G2 Geol. storage 3000 m',
         'U1': 'U1 CCU methane', 'U2a': 'U2a CCU MeOH-fuel',
         'U2b': 'U2b CCU MeOH-chemicals',
         'R1': 'R1 CR oil-fuel', 'R2': 'R2 CR naphtha', 'R3': 'R3 CR HVC'}

net = {p: {n: CB.net(p, regs[n]['F'], regs[n]['T'], regs[n]['EF']) for n in names}
       for p in CB.ORDER}
# net difference relative to the region's own reference incinerator (kt-CO2/y)
D = np.array([[net[p][n] - net['S0'][n] for n in names] for p in paths]) / 1000.0

fig, ax = plt.subplots(figsize=(8.6, 5.4))
lim = np.abs(D).max()
im = ax.imshow(D, cmap='RdBu_r', vmin=-lim, vmax=lim, aspect='auto')

ax.set_xticks(range(len(names)))
ax.set_xticklabels([f"{n}\n{regs[n]['EF']*1000:.0f} / {100*regs[n]['F']/regs[n]['T']:.0f}%"
                    for n in names], fontsize=7.5)
ax.set_yticks(range(len(paths)))
ax.set_yticklabels([label[p] for p in paths], fontsize=8)
for i in range(len(paths)):
    for j in range(len(names)):
        ax.text(j, i, f'{D[i, j]:.1f}', ha='center', va='center', fontsize=6.4,
                color='white' if abs(D[i, j]) > lim * 0.55 else 'black')
# box every pathway that attains the regional minimum on unrounded values, so exact
# ties (the two oil-based recycling routes) are both marked
for j, n in enumerate(names):
    col = D[:, j]
    m = col.min()
    for i in np.flatnonzero(np.isclose(col, m, rtol=1e-12, atol=0.0)):
        ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False,
                                   edgecolor='black', lw=2.0))

_frame(ax)
ax.set_xlabel('Grid region  (grid emission factor, g-CO$_2$ kWh$^{-1}$  /  '
              'fossil share of waste carbon)', fontsize=8.5)
ax.set_title('Net difference relative to each region’s own reference incinerator\n'
             '(kt-CO$_2$ y$^{-1}$; negative = lower emissions than the regional reference; '
             'boxes mark the lowest value on unrounded results, all exact ties boxed)', fontsize=9.5)
cb = fig.colorbar(im, ax=ax, fraction=0.030, pad=0.02)
cb.set_label('kt-CO$_2$ y$^{-1}$ vs regional reference', fontsize=8)
cb.outline.set_edgecolor('black')
plt.tight_layout()
_d = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_d) if os.path.basename(_d) == 'regions' else _d
os.makedirs(os.path.join(_root, 'outputs'), exist_ok=True)
out = os.path.join(_root, 'outputs', 'Fig_regional_heatmap.png')
save(out)
print('saved', out)

print('\nCheck against Table 3 (capture benefit = reference - G1, kt-CO2/y):')
for n in names:
    b = (net['S0'][n] - net['G1'][n]) / 1000.0
    print(f'  {n:<10}{b:>7.2f}   G1 better than reference: {b > 0}')
print(f"\nreference spread {(max(net['S0'].values())-min(net['S0'].values()))/1000:.1f} kt ; "
      f"G1 spread {(max(net['G1'].values())-min(net['G1'].values()))/1000:.1f} kt")
