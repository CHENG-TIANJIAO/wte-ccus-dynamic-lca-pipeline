# Time-resolved and region-sensitive climate assessment of thirteen CO2 pathways for municipal waste incineration

Complete data and calculation chain behind the manuscript *"Time-resolved and region-sensitive climate assessment of thirteen CO2 capture, utilization and recycling pathways for municipal waste incineration"*.

Thirteen carbon-management pathways for one modal Japanese municipal solid waste
incinerator (300 t d-1, 84,000 t y-1) are harmonized onto a single explicit fossil-carbon
balance with cradle-to-grave-symmetric substitution credits, resolved across the ten
Japanese electricity supply regions, extended with a CO2 impulse-response climate layer,
and propagated through a shared-draw Monte Carlo analysis.

> **Scope.** This repository is self-contained. The default run reads only files shipped
> here and reproduces every number, table and figure source file of the manuscript; the
> figures themselves are then rendered by the scripts in `figures/`, including Figure 1,
> which is drawn from the model parameters. Two optional provenance scripts re-derive
> shipped inputs from laboratory source workbooks that are not distributed; neither is
> needed for any result.

This version corresponds to revision R1 of the manuscript. What changed against v1.0.1 —
a unified modular system boundary for the nine capture pathways, three corrected inventory
items, the regional layer rebuilt from the facility-level national survey, and the declared
scenarios — is listed in [`CHANGELOG.md`](CHANGELOG.md).

## What it computes

1. **Deterministic model** (`code/carbon_model.py`) - the single authoritative
   implementation of the fossil-carbon balance, reading every constant from
   `code/model_parameters.json`. No coefficient is duplicated anywhere else.
2. **Regional layer** (`code/regional_model.py`, `code/reconcile_regional.py`) - the 130
   absolute pathway-region results and the 120 pairwise differences, reconciled against the
   national equation.
3. **Scenario decomposition** (`code/scenario_decomposition.py`, `code/regional_2050.py`) -
   the exact Shapley attribution of the 2025 to 2050 change over grid, waste carbon and
   hydrogen, across all eight background combinations.
4. **Climate layer** (`code/climate_response.py`, `code/build_climate.py`) - the CO2 impulse
   response and the cumulative radiative forcing of each pathway, validated against the
   closed-form integral of the same response.
5. **Uncertainty** (`code/monte_carlo.py`) - one 50,000-draw master matrix on which both
   chemical-recycling boundary treatments are evaluated, so any difference between them can
   only come from the boundary. 624 rank correlations.
6. **Hydrogen scenarios** (`code/hydrogen_scenarios.py`) - the three utilization pathways
   under five declared hydrogen-supply scenarios.
7. **Independent check** (`code/build_workbook.py`) - an Excel workbook that recomputes the
   governing equation from the raw input cells with live formulas, as a second
   implementation.
8. **Correlation and interaction analyses** (`analysis/`) - the matrices behind
   Supplementary Fig. S1 (pairwise rank correlation and win probability of every pathway
   pair) and Supplementary Table S29 (the interaction terms of the Shapley decomposition).
9. **Figures** (`figures/`) - Figure 1 from the model parameters and its layout definition,
   Figures 2 to 6 and Fig. S1 from the results, each drawn at the size at which it is
   placed in the manuscript.

## Quickstart

Linux and macOS:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt
export PYTHONDONTWRITEBYTECODE=1
python code/run_all.py                               # the model: every number and source file
python analysis/E5_shapley_interactions.py           # interaction terms (SI Table S29)
python analysis/F5_mc_correlation.py                 # correlation matrices (SI Fig. S1)
python figures/make_figs_R1.py                       # Figures 2 to 6 and Fig. S1
python figures/make_fig1_R1.py                       # Figure 1
```

Windows PowerShell:

```powershell
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r code/requirements.txt
$env:PYTHONDONTWRITEBYTECODE = "1"
python code/run_all.py                               # the model: every number and source file
python analysis/E5_shapley_interactions.py           # interaction terms (SI Table S29)
python analysis/F5_mc_correlation.py                 # correlation matrices (SI Fig. S1)
python figures/make_figs_R1.py                       # Figures 2 to 6 and Fig. S1
python figures/make_fig1_R1.py                       # Figure 1
```

The environment variable keeps Python from writing `__pycache__` anywhere in the tree, which
`make_figs_R1.py` requires: it re-verifies `MANIFEST_SHA256.txt` and treats a byte-code
directory in `code/` as a file that does not belong to the release. The variable is used
rather than `python -B` because `run_all.py` runs each step of the chain as a child process,
which `-B` on the entry point does not reach. Deleting `code/__pycache__` before the last two
commands has the same effect.

Python >= 3.11 with numpy, openpyxl, matplotlib and pandas; `code/requirements.txt` pins the
verified versions. No network access is needed. The model run takes a few minutes on an
ordinary laptop, most of it in the Monte Carlo. It rewrites `code/outputs/`, which is also
where the reference copies are shipped: after a run they must be identical to what was
shipped, with the two exceptions noted below.

## Expected results

| Check | Expected |
|---|---|
| Eq. 2 against Eq. 6, all 13 pathways | max abs difference 0 to 10 decimals (tolerance 1e-9 t) |
| Regional reconciliation, 130 absolute cells | max 0.000000 kt-CO2 per year |
| Shapley closure, 8 background combinations | 0 to 8 decimals |
| A/B draw difference for the 10 pathways the recycling boundary does not touch | exactly 0 |
| Workbook Eq. 2 sheet recomputed in Excel or LibreOffice | agrees with the model to 5e-7 t |
| 100-year cumulative forcing of a 1 kg CO2 pulse | 9.1721e-14 W m-2 y kg-1, against 9.1711e-14 for the closed-form integral, deviation 0.011 % |
| Static national result, reference plant / fuel-grade methanol | 18,737.1785 / -45,803.0134 t-CO2 per year |
| Static national result, direct olivine mineralization / steel-slag mineralization | 30,453.2334 / 81,898.0164 t-CO2 per year |
| `analysis/` matrices after a re-run | byte-identical to the shipped copies |
| Figures after a re-run | the PNG files are byte-identical to those embedded in the manuscript |

Under the pinned environment (Python 3.11.9, numpy 2.4.2, openpyxl 3.1.5, matplotlib 3.10.8,
pandas 3.0.1, x86-64) every reference CSV is regenerated byte for byte. Two shipped files are
expected to differ after a re-run without any value differing:
`code/outputs/Unified_calculation_workbook.xlsx`, whose container stores a timestamp, and any
`.pdf` figure, which records a creation date; the workbook is compared cell by cell instead.
This was verified by unpacking the release into a clean directory and running it there with
only the files inside it; the record of that run is in [`VERIFICATION.md`](VERIFICATION.md).
On other interpreter or BLAS builds the table above is the reproduction criterion: the
numerical results are what the release commits to, and exact byte identity of the text files
is not guaranteed across every build. See [`docs/reproducibility.md`](docs/reproducibility.md).

`code/outputs/Unified_calculation_workbook.xlsx` is written programmatically, so it stores
formulas but no cached results. Open it in Excel or LibreOffice, which recalculate on open. A
script that reads it with openpyxl and `data_only=True` returns None for the formula cells by
design.

## Layout

```
code/                 the complete chain; run_all.py is the single entry point
  model_parameters.json      every model constant, read by carbon_model.py
  region_waste_carbon.csv    ten-region composition profiles
  regional_source/           prefecture profiles and the optional re-derivation script
  outputs/                   the machine-readable results the chain reproduces
analysis/             the two analyses behind SI Fig. S1 and SI Table S29, and their matrices
figures/              the scripts that render Figure 1 and Figures 2 to 6 and Fig. S1,
                      and the typesetting post-processor applied to the manuscript file
inputs/               the two national survey files of the regional reconstruction, with
                      their digests and download record, and the reconstruction scripts
docs/                 reproducibility, data dictionary, documentation/data licence
MANIFEST_SHA256.txt   SHA-256 of the README and of every data, code and figure file; the
                      same paths and, except for the README, the same digests as the
                      verified release archive
VERIFICATION.md       the clean-room verification run of this content
```

## Citation

See [`CITATION.cff`](CITATION.cff). Archived at Zenodo:
https://doi.org/10.5281/zenodo.21830579 (concept DOI, all versions).

## Licence

Source code: MIT ([`LICENSE`](LICENSE)). Data files and documentation: CC BY 4.0
([`docs/DATA_AND_DOCUMENTATION_LICENSE.md`](docs/DATA_AND_DOCUMENTATION_LICENSE.md)).
The national waste-characterization statistics and the utility-level grid emission factors
reproduced in the input files are published by the Ministry of the Environment and the
Ministry of Economy, Trade and Industry of Japan and remain subject to their own terms of
use; the values are cited in the manuscript and the Supplementary Information.
