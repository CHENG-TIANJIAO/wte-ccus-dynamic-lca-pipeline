# -*- coding: utf-8 -*-
"""Fig. 1 of the R1 manuscript (the submitted figure): renders fig1_layout.py with matplotlib at its placed
size (6.5 x 6.0 in, 1:1; smallest text 7 pt, asserted).  The editable PowerPoint copy is make_fig1_pptx.py
from the same layout.  Nothing is written to the snapshot."""
import os
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))          # format_docx_R1 lives beside the manuscript scripts
import matplotlib                                     # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.patches import FancyBboxPatch         # noqa: E402
import fig1_layout as FL                              # noqa: E402
from format_docx_R1 import segments                   # noqa: E402


def mt(s):
    """Plain text -> matplotlib mathtext with subscripts and exponents."""
    out = []
    for line in s.split('\n'):
        seg = segments(line) or [(line, None)]
        out.append(''.join(p if v is None else ('$_{%s}$' % p if v == 'sub' else '$^{%s}$' % p.replace('−', '-'))
                           for p, v in seg))
    return '\n'.join(out)


plt.rcParams.update({'font.family': 'Times New Roman', 'mathtext.fontset': 'stix', 'font.size': FL.FS_BODY,
                     'savefig.facecolor': 'white', 'figure.facecolor': 'white'})
fig = plt.figure(figsize=(FL.W, FL.H))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, FL.W); ax.set_ylim(0, FL.H); ax.axis('off')
RS = 'round,pad=0,rounding_size=0.05'
for it in FL.build():
    k = it['kind']
    if k == 'band':
        ax.add_patch(FancyBboxPatch((it['x0'], it['y0']), it['x1'] - it['x0'], it['y1'] - it['y0'], boxstyle=RS,
                                    fc=it['col'], ec=it['col']))
        ax.text((it['x0'] + it['x1']) / 2, (it['y0'] + it['y1']) / 2, mt(it['text']), rotation=90, ha='center',
                va='center', color='white', fontsize=FL.FS_BAND, fontweight='bold')
    elif k == 'box':
        x0, y0, x1, y1, th, col = it['x0'], it['y0'], it['x1'], it['y1'], it['th'], it['col']
        ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle=RS, fc='white', ec=col, lw=1.1))
        ax.add_patch(FancyBboxPatch((x0, y1 - th), x1 - x0, th, boxstyle=RS, fc=col, ec=col, lw=1.1))
        ax.text((x0 + x1) / 2, y1 - th / 2, mt(it['title']), ha='center', va='center', color='white',
                fontsize=FL.FS_TITLE, fontweight='bold', linespacing=1.1)
        ax.text((x0 + x1) / 2, (y0 + y1 - th) / 2, mt('\n'.join(it['lines'])), ha='center', va='center',
                fontsize=FL.FS_BODY, linespacing=1.3)
    elif k == 'arrow':
        (a, b), (c, d) = it['pts']
        ax.annotate('', xy=(c, d), xytext=(a, b), arrowprops=dict(arrowstyle='-|>', color=it['col'], lw=1.0,
                    ls='--' if it['dash'] else '-', mutation_scale=8, shrinkA=0, shrinkB=0))
    elif k == 'line':
        ax.plot([p[0] for p in it['pts']], [p[1] for p in it['pts']], color=it['col'], lw=1.0,
                ls='--' if it['dash'] else '-')
    elif k == 'text':
        ax.text(it['x'], it['y'], mt(it['text']), fontsize=it['fs'], color=it['col'], ha=it['ha'], va=it['va'],
                bbox=dict(boxstyle='square,pad=0.05', fc='white', ec='none') if it['white'] else None)

sizes = [t.get_fontsize() for t in fig.findobj(matplotlib.text.Text) if t.get_text().strip()]
assert min(sizes) >= 7.0, min(sizes)
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
fig.savefig(os.path.join(HERE, 'out', 'Fig1_system_boundary.png'), dpi=600)
fig.savefig(os.path.join(HERE, 'out', 'Fig1_system_boundary.pdf'))
print('Fig1 %.1f x %.1f in, smallest text %.1f pt' % (FL.W, FL.H, min(sizes)))
