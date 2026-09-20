# Data dictionary

Reference result files in `code/outputs/`, which is also where the chain regenerates
them.

| File | Contents |
|---|---|
| `Fig2_source_data.csv` | static national result of the 13 pathways under both biogenic conventions |
| `Fig3_source_data.csv` | 130 absolute pathway-region results and the 120 plotted differences, each term of the governing equation separated |
| `Fig5_source_data.csv` | cumulative radiative forcing trajectories of the dynamic layer |
| `Fig6_source_data.csv` | Monte Carlo parameter summary plotted in Figure 6 |
| `reconciliation_regional.csv` | reconciliation of the national equation against every regional cell |
| `regional_2050.csv` | regional evaluation on the 2050 background under both grid regionalizations (260 rows) |
| `Shapley_decomposition_audit.csv` | all eight background combinations and the closure discrepancy |
| `Eq2_Eq6_reconciliation.csv` | deterministic equation against the Monte Carlo equation, all 13 pathways |
| `Hydrogen_supply_scenarios.csv` | the three utilization pathways under five hydrogen-supply scenarios |
| `MonteCarlo_master_draws.csv` | the complete 50,000-row master draw matrix, 25 columns |
| `MonteCarlo_pathway_outputs_A.csv` | draw-level results, recycling boundary treatment A |
| `MonteCarlo_pathway_outputs_B.csv` | draw-level results, recycling boundary treatment B |
| `MonteCarlo_summary_AB.csv` | summary statistics of both treatments |
| `MonteCarlo_pairing_audit.csv` | audit showing the 10 untouched pathways differ by exactly zero between treatments |
| `MonteCarlo_rank_correlations.csv` | the complete 24 x 13 x 2 = 624 rank-correlation set |
| `Unified_calculation_workbook.xlsx` | every inventory term with its class and scaling formula, recomputing the governing equation with live Excel formulas |

Model inputs, read by the chain:

| File | Contents |
|---|---|
| `code/model_parameters.json` | every model constant; the single source of coefficients |
| `code/region_waste_carbon.csv` | ten-region waste composition profiles |
| `code/regional_source/prefecture_waste_carbon.csv` | 47-prefecture composition profiles |

The matrices in `analysis/` are the source files of Supplementary Fig. S1 (the pairwise
rank correlations and win probabilities of every pathway pair, under both recycling boundary
treatments) and Supplementary Table S29 (the interaction terms of the Shapley
decomposition); each is written by the script of the same name in that directory.

The workbook stores formulas without cached results. Open it in Excel or LibreOffice, which
recalculate on open; reading it with openpyxl and `data_only=True` returns None for the
formula cells by design.
