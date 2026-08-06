"""Shared figure style: black Times New Roman text, full black frame on all four sides."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def apply():
    plt.rcParams.update({
        'font.family': 'Times New Roman', 'mathtext.fontset': 'stix',
        'font.size': 9, 'text.color': 'black',
        'axes.labelcolor': 'black', 'axes.titlecolor': 'black',
        'xtick.color': 'black', 'ytick.color': 'black',
        'xtick.labelcolor': 'black', 'ytick.labelcolor': 'black',
        'axes.edgecolor': 'black', 'axes.linewidth': 1.0,
        'legend.edgecolor': 'black', 'legend.framealpha': 1.0,
        'savefig.facecolor': 'white', 'figure.facecolor': 'white',
    })

def frame(ax):
    """Close the axes box on all four sides in black, without covering the data."""
    for side in ('top', 'right', 'bottom', 'left'):
        s = ax.spines[side]
        s.set_visible(True)
        s.set_color('black')
        s.set_linewidth(1.0)
        s.set_zorder(3)
    ax.tick_params(colors='black', which='both')


def save(path_png, dpi=600):
    """Save the current figure as a high-resolution PNG (default 600 dpi, Elsevier
    combination-artwork grade) and as a vector PDF alongside it."""
    plt.savefig(path_png, dpi=dpi)
    plt.savefig(path_png[:-4] + '.pdf')
    print('saved', path_png, 'and .pdf, %d dpi' % dpi)
