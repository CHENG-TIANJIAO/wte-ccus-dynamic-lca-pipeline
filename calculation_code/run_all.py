# -*- coding: utf-8 -*-
"""
Single entry point for the complete calculation chain.

Run from this directory with no arguments:

    python run_all.py

The default run is fully self-contained: it reads the shipped parameter file
model_parameters.json and never accesses any file outside this directory. It will, in order:
  1. self-check the deterministic model (carbon_model, constants from
     model_parameters.json);
  2. build the fixed master draw matrix (seed 20260702, 50,000 draws, sorted variable
     order) and evaluate both chemical-recycling boundary treatments on it;
  3. write every machine-readable file: the master matrix, draw-level outputs A and B,
     the summary, the pairing audit, the 624 rank correlations, the Eq.2/Eq.6
     reconciliation, the Fig. 2 / Fig. 3 / Fig. 6 source data and the Shapley audit;
  4. reconcile Eq. 2 against all 130 absolute pathway-region results;
  5. rebuild the unified calculation workbook;
  6. self-check the physical climate layer (climate_response), evaluate the
     dynamic layer (build_climate) and write the hydrogen-supply scenarios;
  7. redraw Fig. 2, Fig. 3 (regional heat map), Fig. 4 (biogenic swing), Fig. 5
     (dynamic climate response, plus Fig5_source_data.csv) and Fig. 6.

Optional provenance step (authors only):

    python run_all.py --rebuild-ledger

re-derives model_parameters.json from the original laboratory source workbooks. It runs
only if every source workbook is present. Their locations may be given with
--ccu/--ccu-sens/--mineral/--db, which run_all.py forwards to derive_parameters.py.
The step is never part of the default run,
so the package reproduces on any machine without those workbooks.

Outputs are written to ./outputs. Requires numpy, openpyxl and matplotlib.
"""
import argparse
import os
import platform
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, 'outputs'), exist_ok=True)
os.chdir(HERE)
sys.path.insert(0, HERE)

STEPS = [
    ('model self-check', 'carbon_model.py'),
    ('Monte Carlo self-check', 'monte_carlo.py'),
    ('machine-readable exports', 'export_files.py'),
    ('regional reconciliation', 'reconcile_regional.py'),
    ('unified workbook', 'build_workbook.py'),
    ('climate-layer self-check', 'climate_response.py'),
    ('dynamic layer', 'build_climate.py'),
    ('hydrogen supply scenarios', 'hydrogen_scenarios.py'),
    ('regional results on the 2050 background', 'regional_2050.py'),
    ('figures 2 and 4', 'build_figs.py'),
    ('figure 3', 'plot_regional.py'),
    ('figure 5 + source data', 'plot_climate.py'),
    ('figure 6', 'plot_mc_ab.py'),
]


def _resolve(script):
    """plot_regional lives in regions/ in the repository but at top level in the
    submission package."""
    for cand in (os.path.join(HERE, script), os.path.join(HERE, 'regions', script)):
        if os.path.exists(cand):
            return cand
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--rebuild-ledger', action='store_true',
                    help='re-derive model_parameters.json from the original source '
                         'workbooks (authors only; requires those workbooks)')
    ap.add_argument('--ccu'); ap.add_argument('--ccu-sens')
    ap.add_argument('--mineral'); ap.add_argument('--db')
    args = ap.parse_args()
    LEDGER_OPTS = []
    for flag, val in (('--ccu', args.ccu), ('--ccu-sens', args.ccu_sens),
                      ('--mineral', args.mineral), ('--db', args.db)):
        if val:
            LEDGER_OPTS += [flag, val]

    import numpy
    print('Python %s | numpy %s | %s' % (sys.version.split()[0], numpy.__version__,
                                         platform.platform()))
    print('seed 20260702, N = 50,000, draw ids 0-49,999\n')

    steps = list(STEPS)
    if args.rebuild_ledger:
        led = _resolve('derive_parameters.py')
        if led is None:
            print('--rebuild-ledger requested but derive_parameters.py is missing')
            sys.exit(2)
        r = subprocess.run([sys.executable, led] + LEDGER_OPTS
                           + ['--check-sources'], cwd=HERE)
        if r.returncode != 0:
            print('--rebuild-ledger requested but the source workbooks are not '
                  'available; aborting without touching model_parameters.json')
            sys.exit(2)
        steps = [('ledger derivation', 'derive_parameters.py')] + steps

    failed = []
    for label, script in steps:
        path = _resolve(script)
        if path is None:
            failed.append(script)
            print('  MISSING: %s' % script)
            continue
        print('=== %s (%s) ===' % (label, script))
        argv = LEDGER_OPTS if script == 'derive_parameters.py' else []
        r = subprocess.run([sys.executable, path] + argv, cwd=HERE)
        if r.returncode != 0:
            failed.append(script)
            print('  FAILED: %s' % script)
    print()
    if failed:
        print('FAILED steps: %s' % failed)
        sys.exit(1)
    print('All steps completed. Outputs are in ./outputs')


if __name__ == '__main__':
    main()
