# -*- coding: utf-8 -*-
"""Where the model and its analysis outputs are, in the working repository and in the published archive.

Repository layout:  .../02_analyses/chain_r1/_snapshots/R1g_FROZEN_2026-09-20/{calculation_code, 02_analyses}
Archive layout:      <archive root>/{code, analysis, figures}

resolve() returns (root, code, analysis, manifest): the directory the files hang off, the model code, the
directory holding the analysis outputs the figures read, and the SHA-256 manifest to verify (or None).
The environment variable R1_MODEL_ROOT overrides the search."""
import os

SNAPSHOT = os.path.join('02_analyses', 'chain_r1', '_snapshots', 'R1g_FROZEN_2026-09-20')


def _kind(root):
    if os.path.isdir(os.path.join(root, 'calculation_code')):
        man = os.path.join(root, 'MANIFEST_SHA256.txt')
        return (root, os.path.join(root, 'calculation_code'), os.path.join(root, '02_analyses'),
                man if os.path.isfile(man) else None)
    if os.path.isdir(os.path.join(root, 'code')):
        man = os.path.join(root, 'MANIFEST_SHA256.txt')
        return (root, os.path.join(root, 'code'), os.path.join(root, 'analysis'),
                man if os.path.isfile(man) else None)
    return None


def resolve(start=None):
    here = os.path.dirname(os.path.abspath(start or __file__))
    cands = []
    env = os.environ.get('R1_MODEL_ROOT')
    if env:
        cands.append(os.path.abspath(env))
    up = here
    for _ in range(6):                                  # repository: .../R1_revision/<...>/figure_build
        cands.append(os.path.join(up, SNAPSHOT))
        cands.append(up)                                # archive: figures/.. is the archive root
        up = os.path.dirname(up)
    for c in cands:
        got = _kind(c)
        if got:
            return got
    raise SystemExit('neither the frozen snapshot nor an archive layout was found from ' + here)
