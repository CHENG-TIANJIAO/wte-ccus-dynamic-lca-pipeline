"""Manuscript Fig. 2 (static ranking) and Fig. 4 (biogenic swing).
The swing figure keeps its historical output filename Fig3_biogenic_swing.png;
the packaging step maps it to Fig4.png."""
import numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, os
from fig_style import apply as _apply, frame as _frame, save
_apply()

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import carbon_model as CB
import scenario_decomposition as SD

# All values are computed from the single authoritative model, never pasted.
A25 = {p: CB.net(p, CB.F_NAT, CB.T_NAT, CB.EF_NAT) for p in CB.ORDER}
A50 = {p: SD.net(p, True, True, True) for p in CB.ORDER}

# Convention B credits only NET-PERMANENT biogenic storage (CB.bio_stored):
# for mineralization the biogenic share of the reactor loss is not stored.
B25 = {p: A25[p] - CB.bio_stored(p, CB.F_NAT, CB.T_NAT)
       for p in CB.ORDER if CB.CLASS[p] in ('min', 'geo')}
B50 = {p: A50[p] - CB.bio_stored(p, SD.F50, SD.T50)
       for p in CB.ORDER if CB.CLASS[p] in ('min', 'geo')}

name={'S0':'Reference WtE','M1':'Mineral. olivine (dir.)','M2':'Mineral. serpentine',
 'M3':'Mineral. carbide slag','M4':'Mineral. steel slag','G1':'Geol. CCS 1200 m',
 'G2':'Geol. CCS 3000 m','U1':'CCU methane','U2a':'CCU MeOH→fuel',
 'U2b':'CCU MeOH→chemicals','R1':'CR oil→fuel',
 'R2':'CR →naphtha','R3':'CR →HVC'}
grp={'S0':'ref','M1':'min','M2':'min','M3':'min','M4':'min','G1':'geo','G2':'geo',
 'U1':'ccu','U2a':'ccu','U2b':'ccu','R1':'cr','R2':'cr','R3':'cr'}
gc={'ref':'#444','min':'#8c564b','geo':'#9467bd','ccu':'#1f77b4','cr':'#2ca02c'}
outdir=os.path.join(os.path.dirname(__file__),'outputs')

# ---- Fig 2: horizontal grouped bars, sorted by 2050 (conv A) ----
order=sorted(A25, key=lambda p:A50[p])          # best (lowest) at top after invert
y=np.arange(len(order)); h=0.38
fig,ax=plt.subplots(figsize=(8.2,6.2))
ax.barh(y+h/2,[A25[p] for p in order],height=h,color=[gc[grp[p]] for p in order],
        alpha=0.55,label='present grid')
ax.barh(y-h/2,[A50[p] for p in order],height=h,color=[gc[grp[p]] for p in order],
        alpha=1.0,label='2050 background')
ax.axvline(0,color='k',lw=.7); ax.axvline(A50['S0'],color='r',ls=':',lw=1,label='S0 2050 ref')
ax.set_yticks(y); ax.set_yticklabels([f"{p}  {name[p]}" for p in order],fontsize=8)
ax.invert_yaxis(); ax.set_xlabel('Net life-cycle CO$_2$ (t-CO$_2$/y) — convention A')
ax.set_title('Static net life-cycle CO$_2$ of the thirteen pathways')
ax.legend(fontsize=8,loc='upper right',framealpha=1.0); ax.grid(alpha=.3,axis='x')
_frame(ax)
plt.tight_layout(); save(os.path.join(outdir,'Fig2_static_ranking.png'))

# ---- Fig 3: biogenic A<->B dumbbell for M/G (2025) ----
mg=['M1','M2','M3','M4','G1','G2']; y2=np.arange(len(mg))
fig,ax=plt.subplots(figsize=(8,4.4))
for j,p in enumerate(mg):
    a,b=A25[p],B25[p]
    ax.plot([b,a],[j,j],color='#bbb',lw=2,zorder=1)
    ax.scatter(a,j,color='#d62728',zorder=3,s=55)   # A conservative
    ax.scatter(b,j,color='#1f77b4',zorder=3,s=55)   # B BECCS
    ax.annotate(f"Δ={a-b:,.0f}",((a+b)/2,j),textcoords='offset points',
                xytext=(0,7),ha='center',fontsize=7,color='#555')
ax.axvline(0,color='green',lw=.7); ax.axvline(A25['S0'],color='k',ls=':',lw=1,label='S0 2025 ref')
ax.scatter([],[],color='#d62728',label='A: ISO-neutral (main)')
ax.scatter([],[],color='#1f77b4',label='B: BECCS credit')
ax.set_yticks(y2); ax.set_yticklabels([f"{p} {name[p]}" for p in mg],fontsize=8)
ax.invert_yaxis(); ax.set_ylim(len(mg) - 0.5, -0.85)
ax.set_xlabel('Net life-cycle CO$_2$ 2025 (t-CO$_2$/y)')
ax.set_title('Effect of the biogenic-CO$_2$ convention on the storage pathways')
ax.legend(fontsize=8,loc='lower right'); ax.grid(alpha=.3,axis='x')
_frame(ax)
plt.tight_layout(); save(os.path.join(outdir,'Fig3_biogenic_swing.png'))
print('saved Fig2, Fig3 to',outdir)
