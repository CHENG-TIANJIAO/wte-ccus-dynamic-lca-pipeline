# Changelog

All notable changes to this pipeline are recorded here. The code version is mapped to the
associated manuscript revision below.

Zenodo concept DOI, resolving to the newest version and cited in the manuscript:
**https://doi.org/10.5281/zenodo.21830579**. Each release also receives its own version DOI,
listed on that record page; version DOIs are not repeated here, because a release cannot
contain the identifier that is minted from it.

## [1.2.0] - 2026-10-27

Revision R2 of the manuscript. The model, its parameters (ledger R1g), its inputs and every
result and figure of version 1.1.0 are unchanged; the 91 files of this version include the 86
of version 1.1.0 with identical content, apart from this README.

Added - `analysis/R2_time_sensitivity.py`, an analysis of the time dimension that evaluates the
unchanged model at more points than the two background states and four endpoints of 1.1.0:
- a background path, with the grid factor, the waste carbon and the hydrogen factor moved
  together in annual steps from their 2025 to their 2050 values
  (`R2_background_trajectory.csv`); the linear path is an illustration, not a forecast;
- a path-free sweep of the grid factor and the waste carbon over the whole range between
  their 2025 and 2050 values, with the hydrogen factor at either value
  (`R2_grid_waste_sweep.csv`), and the break-even of geological storage against the grid
  factor;
- cumulative radiative forcing and competition ranks at every annual endpoint from 2026 to
  2125 under both chemical-recycling treatments (`R2_endpoint_annual.csv`);
- a summary of the three (`R2_time_sensitivity_summary.md`).
The script checks itself against the shipped outputs: it reproduces the eight background
combinations of `Shapley_decomposition_audit.csv`, the four endpoints of
`Fig5_source_data.csv` and the published break-even of storage on the 2050 background, and
stops if any of them differs.

## [1.1.0] - 2026-09-29

Revision R1 of the manuscript. This version carries the
frozen parameter ledger R1g, which is the sole numerical authority of the revised manuscript
and its Supplementary Information; the intermediate ledgers R1a to R1f are development
states and are not published.

Changed - repository structure, so that the repository and the archive submitted with the
revision hold the same content in the same layout:
- `calculation_code/` is now `code/`, and the reference result files, which were at the
  repository root, are now in `code/outputs/` where the chain writes them. `requirements.txt`
  moved to `code/requirements.txt`.
- New `analysis/`: the two analyses behind Supplementary Fig. S1 and Supplementary Table S29,
  with the fourteen matrices they produce and the four comparison files of the original
  submission that they read. Both resolve their own directory, so they run from anywhere in
  the tree.
- New `figures/`: `make_fig1_R1.py` with its layout definition `fig1_layout.py`,
  `make_figs_R1.py` for Figures 2 to 6 and Fig. S1, the shared path resolver `r1_paths.py`,
  and the typesetting post-processor applied to the manuscript file. Figure 1 is now drawn
  from the model parameters by a script instead of by hand.
- New `inputs/`: the two files of the fiscal-2021 national municipal-waste survey used for
  the regional reconstruction, with their digests and download record, and the scripts and
  tables of the reconstruction and of its validation.
- New `MANIFEST_SHA256.txt` and `VERIFICATION.md`, replacing the earlier
  `ZIP_VERIFICATION.md`. `.gitattributes` now keeps every tracked file byte-identical on
  checkout, so those digests can be verified on any platform.
- `LICENSE` scopes the MIT licence to every `.py` file in the repository, which the move out
  of `calculation_code/` had left stale, and the CC BY 4.0 licence to the data files and the
  documentation.

Changed - model. The revision harmonizes the system boundary and corrects three inventory
items; every step is recorded in the ledger notes of `code/model_parameters.json` and
applied by the `apply_r1*.py` scripts kept beside it:
- A common capture and conditioning module of 90 kWh per t-CO2 (15 capture unit, 10
  condenser, 65 compressor) for all nine capture pathways, with family-specific downstream
  modules: road-tanker liquefaction for utilization, ship liquefaction, unloading and, for
  offshore injection, pumping to injection pressure for geological storage.
- Plant air-pollution-control and boiler chemicals removed from the mineralization pathways,
  which are outside the boundary of every pathway; all capture-pathway electricity taken
  from the source-basis MWh at one factor; CO2 transport on a tonne-kilometre basis; the
  capture-unit capital carried explicitly by the pathways that were missing it.
- Three inventory corrections: the M4 CaO factor to the quicklime value 1.12, the M1 olivine
  ore factor to 0.00786 instead of the talc proxy, and the R3 auxiliary electricity aligned
  with its anchor at 780.2034 MWh.
- The regional layer rebuilt from the facility-level national survey with tonnage weighting,
  validated against the 33 prefecture profiles that the first version reproduces.
- Declared discrete scenarios, selected with the environment variable `R1C_SCENARIO`
  (Supplementary Table S31), covering the alternatives that were considered and not adopted,
  among them the compressor-overlap upper bounds, the source-value M4 CaO factor, the R3
  high-value-chemical electricity, and the M4 process-water transcription.

Result of those changes: the reference plant is unchanged at 18,737.1785 t-CO2 per year,
while the static national result of fuel-grade methanol moves from -47,769.9264 to
-45,803.0134 t-CO2 per year. The revised values of all thirteen pathways are the ones in
`code/outputs/` and in the manuscript; any number from version 1.0.x should be read as
belonging to the original submission.

Also included: the correction of the first author's affiliation to the Environmental
Research Institute (commit 94a8769), which was made after 1.0.1 was released.

Verification: the content was unpacked into a clean directory and run there with only the
files inside it. The chain completed with no self-check failure, 85 of the 86 shipped files
were reproduced or read back byte for byte, the workbook rebuilt with zero cell and formula
differences, both analyses rewrote all fourteen published matrices byte for byte, and the
seven regenerated PNG figures are byte-identical to the figures embedded in the manuscript.
`VERIFICATION.md` is the record of that run.

Note on digests: `MANIFEST_SHA256.txt` identifies the content file by file; the digest of
the archive that GitHub and Zenodo generate from this tag depends on the container and is
not repeated here.

## [1.0.1] - 2026-08-07

Packaging release. No change to the model, the input data, the calculation chain or any
result; `calculation_code/` is byte-identical to 1.0.0.

Changed:
- Removed the pre-release review gate `TO_REVIEW_BEFORE_PUBLIC_RELEASE/` from the published
  repository. Its purpose was to be worked through before going public, which was done; the
  completed record is kept with the submission package rather than published.
- README and `CITATION.cff` now carry the minted concept DOI. In 1.0.0 these still held the
  pre-deposit placeholders, because the tag necessarily precedes the DOI that Zenodo mints
  from it.
- The reproduction statement is now scoped to the environment in which it was verified
  (Python 3.11.9, numpy 2.4.2, x86-64). Byte identity of the reference CSV files was
  observed there; the numerical checks in the README are what the release commits to on any
  build, since a different BLAS backend can change the sign of a floating-point zero without
  changing any result.

## [1.0.0] - 2026-08-07

First public release accompanying the manuscript *"Time-resolved and region-sensitive
climate assessment of thirteen CO2 capture, utilization and recycling pathways for
municipal waste incineration"* (original submission). The packaged archive
carries the internal model version 4.0.

Added:
- `calculation_code/carbon_model.py` - the single authoritative deterministic model,
  reading every constant from `model_parameters.json`.
- `calculation_code/regional_model.py`, `reconcile_regional.py` - the ten-region layer and
  its reconciliation against all 130 absolute pathway-region results.
- `calculation_code/scenario_decomposition.py`, `regional_2050.py` - exact Shapley
  attribution over grid, waste carbon and hydrogen, and the 2050 regional evaluation.
- `calculation_code/climate_response.py`, `build_climate.py` - the CO2 impulse-response
  climate layer, validated against the closed-form integral of the same response.
- `calculation_code/monte_carlo.py` - the single 50,000-draw master matrix evaluated under
  both chemical-recycling boundary treatments, and the 624 rank correlations.
- `calculation_code/hydrogen_scenarios.py` - the three utilization pathways under five
  declared hydrogen-supply scenarios.
- `calculation_code/build_workbook.py` - an independent Excel implementation with live
  formulas.
- `calculation_code/run_all.py` - single entry point regenerating every number, table and
  figure (Figures 2 to 6) from seed 20260702.
- Optional provenance scripts `derive_parameters.py` and `regional_source/build_regions.py`,
  neither of which is part of the default run.
- `docs/` - reproducibility, data dictionary, documentation and data licence.

Code - archive - manuscript mapping:

| Code version | Parameter ledger | Manuscript |
|---|---|---|
| 1.1.0 | R1g | revision R1 |
| 1.0.1 | model version 4.0 | original submission |
| 1.0.0 | model version 4.0 | original submission |
