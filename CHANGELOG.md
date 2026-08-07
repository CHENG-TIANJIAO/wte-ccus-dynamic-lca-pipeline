# Changelog

All notable changes to this pipeline are recorded here. The code version is mapped to the
associated manuscript revision and the Zenodo DOI at release.

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
- `docs/` - reproducibility, data dictionary, documentation and data licence; release gate
  under `TO_REVIEW_BEFORE_PUBLIC_RELEASE/`.

Code - manuscript - DOI mapping:

| Code version | Archive version | Manuscript | Zenodo DOI |
|---|---|---|---|
| 1.0.0 | 4.0 | Waste Management submission | concept 10.5281/zenodo.21830579; version 10.5281/zenodo.21830580 |
