# Changelog

All notable changes to this pipeline are recorded here. The code version is mapped to the
associated manuscript revision below.

Zenodo concept DOI, resolving to the newest version and cited in the manuscript:
**https://doi.org/10.5281/zenodo.21830579**. Each release also receives its own version DOI,
listed on that record page; version DOIs are not repeated here, because a release cannot
contain the identifier that is minted from it.

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
municipal waste incineration"* (submitted to Waste Management). The packaged archive
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

| Code version | Archive version | Manuscript |
|---|---|---|
| 1.0.1 | 4.0 | Waste Management submission |
| 1.0.0 | 4.0 | Waste Management submission |
