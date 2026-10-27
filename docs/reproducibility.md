# Reproducibility

## Environment

Python >= 3.11. `pip install -r code/requirements.txt` pins the verified versions
(numpy 2.4.2, openpyxl 3.1.5, matplotlib 3.10.8, pandas 3.0.1). No network access is needed
once the dependencies are installed.

## End to end

```bash
export PYTHONDONTWRITEBYTECODE=1                # Linux and macOS
python code/run_all.py                          # the model
python analysis/E5_shapley_interactions.py      # interaction terms, SI Table S29
python analysis/F5_mc_correlation.py            # correlation matrices, SI Fig. S1
python analysis/R2_time_sensitivity.py          # time dimension, SI Section S23
python figures/make_figs_R1.py                  # Figures 2 to 6 and Fig. S1
python figures/make_fig1_R1.py                  # Figure 1
```

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"              # Windows PowerShell
python code/run_all.py
python analysis/E5_shapley_interactions.py
python analysis/F5_mc_correlation.py
python analysis/R2_time_sensitivity.py
python figures/make_figs_R1.py
python figures/make_fig1_R1.py
```

The environment variable suppresses `__pycache__`, which `make_figs_R1.py` reports as a file
that does not belong to the release. `python -B` is not enough, because `run_all.py` runs
each step as a child process that does not inherit the flag.

Roughly ten minutes on an ordinary laptop, most of it in the 50,000-draw Monte Carlo. The
model writes to `code/outputs/`, the analyses beside their own scripts in `analysis/`, and
the figures to `figures/out/`.

## Determinism

Every stochastic step draws from a single master matrix built with the fixed seed
**20260702** in a sorted variable order, so the draws do not depend on the order in which
pathways are evaluated. Both chemical-recycling boundary treatments read that same matrix,
which is why any difference between them can only come from the boundary and not from the
sampling.

## Verification performed

The release content was unpacked into a clean temporary directory and run there with only
the files inside it, under Python 3.11.9 with the pinned library versions on Windows x86-64.
Result:

- The chain completed with no self-check failure, and 85 of the 86 shipped files were
  reproduced or read back byte for byte (version 1.1.0; for version 1.2.0, 90 of 91).
- `Unified_calculation_workbook.xlsx` rebuilt with zero cell and zero formula differences;
  only container timestamps differ, which is the one file that cannot be byte-identical.
- Both analyses ran in the unpacked directory and rewrote all 14 published matrices byte for
  byte, including the source files of SI Fig. S1 and SI Table S29.
- Figure 1 and Figures 2 to 6 and Fig. S1 were regenerated, and the seven PNG files are
  byte-identical to the figures embedded in the manuscript.

Byte identity is reported for that environment. A different interpreter build or a different
BLAS backend can change the summation order of a reduction and therefore the sign of a
floating-point zero, which is enough to alter a text file without altering any result. The
numerical checks in the README are what the release commits to and they hold regardless;
byte identity is the stronger statement that was observed, not a guarantee for every build.

`VERIFICATION.md` records that run, and `MANIFEST_SHA256.txt` lists the SHA-256 of every
file shipped here.

## What is fixed and what is configurable

Fixed in code and defining the published analysis: the Monte Carlo seed and draw count, the
Joos et al. (2013) impulse-response coefficients, the Weibull median lifetimes and shape,
the scaling classes, and the fossil share used to close the substitution credits. Every
numerical constant is read from `code/model_parameters.json`; nothing is
duplicated in the modules.

Configurable, and only for the optional provenance steps: the locations of the laboratory
source workbooks, via `--ccu` / `--ccu-sens` / `--mineral` / `--db` or the environment
variables `CCUS_SRC_CCU`, `CCUS_SRC_CCU_SENS`, `CCUS_SRC_MINERAL`, `CCUS_SRC_DB`, and
`--src` or `CCUS_SRC_WASTE` for the waste-characterization workbook.

## Optional provenance steps

Neither is part of the default run and each exits with a clear message when its source is
absent.

- `code/derive_parameters.py` re-derives `model_parameters.json` from the
  laboratory source workbooks with per-cell assertions.
- `code/regional_source/build_regions.py` re-derives the prefecture and region
  composition files from the national waste-characterization workbook.

The source workbooks are not distributed. The shipped `model_parameters.json` is the
authoritative input for every published number.
