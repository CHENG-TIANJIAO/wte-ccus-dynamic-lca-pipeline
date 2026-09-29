# -*- coding: utf-8 -*-
"""Layout of Fig. 1 (system boundary and carbon-flow logic, unified modular boundary), shared by the
matplotlib renderer (make_fig1_R1.py, the submitted figure) and the editable PowerPoint copy
(make_fig1_pptx.py, the authors' editing source).  Coordinates in inches from the lower-left corner of a
6.5 x 6.0 in canvas.  Text is plain (CO2, t-CO2 y-1); each renderer applies subscripts and exponents with
format_docx_R1.segments.  Every number is read from the frozen R1g model or its module constants, except the
plant specification (84,000 t y-1, 300 t d-1, 280 d y-1) and the two well depths, which are labels of Table 1."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import r1_paths                                    # noqa: E402
SNAP, CODE, ANALYSIS, MANIFEST = r1_paths.resolve(__file__)
sys.path.insert(0, CODE)
for _k in ('R1C_SCENARIO', 'REGION_WEIGHTING'):
    os.environ.pop(_k, None)
import carbon_model as CB          # noqa: E402
import r1c_modules as RM           # noqa: E402

W, H = 6.5, 6.0
COL = {'wte': '#2c5f7c', 'cap': '#2e8b88', 'fam': '#6a5a93', 'acc': '#1f3a5a', 'flow': '#4d4d4d',
       'div': '#6a5a93', 'divtext': '#4a3a73'}
FS_BODY, FS_TITLE, FS_BAND, FS_SMALL = 7.3, 8.0, 7.5, 7.0


def build():
    C = lambda k: RM.C[k][0]
    N = lambda x: f'{x:,.0f}'
    g = lambda x: f'{x:g}'
    Q = CB.T_NAT * CB.CR
    REAG = CB.REAG['G1']
    assert all(abs(CB.REAG[p] - REAG) < 1e-9 for p in CB.CAPTURES)
    items = []
    band = lambda y0, y1, label, col: items.append(dict(kind='band', x0=0.08, y0=y0, x1=0.42, y1=y1, text=label, col=col))
    box = lambda x0, y0, x1, y1, title, lines, col: items.append(
        dict(kind='box', x0=x0, y0=y0, x1=x1, y1=y1, title=title, lines=lines, col=col,
             th=0.24 if '\n' not in title else 0.40))
    arrow = lambda x0, y0, x1, y1, dash=False, col=COL['flow']: items.append(
        dict(kind='arrow', pts=[(x0, y0), (x1, y1)], dash=dash, col=col))
    line = lambda pts, dash=False, col=COL['flow']: items.append(dict(kind='line', pts=pts, dash=dash, col=col))

    L, R = 0.52, W - 0.08
    # row 1: waste-to-energy
    y0, y1 = 5.00, 5.92
    band(y0, y1, 'Waste-to-energy', COL['wte'])
    box(L, y0, 3.12, y1, 'Municipal solid waste', [
        '84,000 t y-1 (300 t d-1, 280 d y-1)',
        'Composition: national survey, fiscal 2021',
        f'Fossil {N(CB.F_NAT)} | biogenic {N(CB.T_NAT - CB.F_NAT)} t-CO2 y-1'], COL['wte'])
    box(3.40, y0, R, y1, 'Incineration with energy recovery', [
        f'Combustion CO2 {N(CB.T_NAT)} t y-1; S0: all to the stack',
        f'Auxiliary electricity {N(CB.AUX)} MWh y-1',
        f'Export {N(CB.EXP_NOCC)} MWh y-1; {N(CB.EXP_CC)} with capture'], COL['wte'])
    arrow(3.12, (y0 + y1) / 2 - 0.1, 3.40, (y0 + y1) / 2 - 0.1)
    # row 2: common capture-and-conditioning module
    y0, y1 = 3.75, 4.68
    band(y0, y1, 'Capture', COL['cap'])
    box(L, y0, R, y1, 'Common capture-and-conditioning module (the nine capture pathways)', [
        f'Post-combustion MEA capture, capture rate {CB.CR * 100:.0f} %: {N(Q)} t-CO2 y-1, '
        'fossil and biogenic carbon together',
        f'Capture {g(C("capture_unit"))} + condenser {g(C("condenser"))} + compression {g(C("compressor"))} kWh per '
        f't-CO2; steam penalty {N(CB.STEAM_PEN)} MWh y-1',
        f'Capture solvent and reagents {N(REAG)} t-CO2 y-1; capture-unit capital {N(C("capture_capital"))} t-CO2 y-1'],
        COL['cap'])
    arrow(4.9, 5.00, 4.9, 4.68)
    # row 3: family-specific downstream modules
    y0, y1 = 2.05, 3.42
    band(y0, y1, 'Thirteen pathways', COL['fam'])
    wd = (R - L - 3 * 0.09) / 4
    xs = [L + i * (wd + 0.09) for i in range(4)]
    fam = [('Mineralization\nM1 to M4', ['Ore or slag by road', 'Carbonation reactor;', 'reactor loss re-emitted',
                                          'Carbonate product,', 'substitution credit']),
           ('Geological storage\nG1, G2', [f'Liquefaction {g(C("ship_liquefaction"))} kWh t-1',
                                           f'Ship {N(C("ship_distance"))} km, {g(C("ship_fuel"))} kg t-1',
                                           f'G1 unloading {g(C("unloading"))},',
                                           f'G2 pumping {g(C("ship_unload_pump"))} kWh t-1',
                                           'Injection 1,200 / 3,000 m']),
           ('Utilization\nU1, U2a, U2b', [f'Liquefaction {g(C("tanker_liquefaction"))} kWh t-1,',
                                          f'road tanker {g(C("road_km_U"))} km', 'Synthesis with H2',
                                          'Methane or methanol;', 'release after product life']),
           ('Chemical recycling\nR1 to R3', ['Plastics diverted', 'before combustion', 'Pyrolysis to fuel oil,',
                                             'naphtha or HVC', 'Product fate: A or B'])]
    for x, (t, lines) in zip(xs, fam):
        box(x, y0, x + wd, y1, t, lines, COL['fam'])
    for i in range(3):
        arrow(xs[i] + wd / 2, 3.75, xs[i] + wd / 2, y1)
    xr = xs[3] + wd / 2
    line([(1.2, 5.00), (1.2, 4.84), (W - 0.03, 4.84), (W - 0.03, 3.63), (xr, 3.63)], dash=True, col=COL['div'])
    arrow(xr, 3.63, xr, y1, dash=True, col=COL['div'])
    items.append(dict(kind='text', x=2.9, y=4.87, text='Plastics diverted before combustion (chemical recycling; no capture)',
                      fs=FS_SMALL, col=COL['divtext'], ha='center', va='bottom', white=True))
    # row 4: accounting
    y0, y1 = 0.62, 1.72
    band(y0, y1, 'Accounting', COL['acc'])
    wd3 = (R - L - 2 * 0.09) / 3
    xa = [L + i * (wd3 + 0.09) for i in range(3)]
    acc = [('Fossil-carbon partition\n(Eq. 1a)', ['Stack release + product release', '+ leakage + permanent storage;',
                                                  'each tonne counted once', 'Seven terms of Eq. 2, itemized']),
           ('Biogenic convention and\nproduct lifetime', ['A: biogenic CO2 climate-neutral', 'B: credited only when',
                                                        'permanently stored', 'Product carbon returns (Weibull)']),
           ('Dynamic and regional\nlayers', ['Cumulative radiative forcing', 'at 2030, 2050, 2100, 2125',
                                             'Ten grid regions; 2050 background', 'Monte Carlo, N = 50,000'])]
    for x, (t, lines) in zip(xa, acc):
        box(x, y0, x + wd3, y1, t, lines, COL['acc'])
    # the collector runs from the outermost connector to the outermost connector and no further
    ends = [xs[i] + wd / 2 for i in range(4)] + [xa[i] + wd3 / 2 for i in range(3)]
    line([(min(ends), 1.88), (max(ends), 1.88)])
    for i in range(4):
        line([(xs[i] + wd / 2, 2.05), (xs[i] + wd / 2, 1.88)])
    for i in range(3):
        arrow(xa[i] + wd3 / 2, 1.88, xa[i] + wd3 / 2, y1)
    # legend
    line([(L, 0.32), (L + 0.4, 0.32)])
    items.append(dict(kind='text', x=L + 0.48, y=0.32, text='CO2 or material flow', fs=FS_BAND, col='#000000',
                      ha='left', va='center', white=False))
    line([(2.6, 0.32), (3.0, 0.32)], dash=True, col=COL['div'])
    items.append(dict(kind='text', x=3.08, y=0.32, text='Plastics diverted before combustion', fs=FS_BAND,
                      col='#000000', ha='left', va='center', white=False))
    return items
