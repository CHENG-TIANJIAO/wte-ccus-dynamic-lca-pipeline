# MoEJ FY2021 raw files — source record (regional tonnage weighting, W2a)

**Survey:** 環境省 一般廃棄物処理実態調査結果, 令和3年度（FY2021）調査結果
(Ministry of the Environment, Japan — Survey on the state of municipal solid waste treatment, FY2021).
**Official page:** https://www.env.go.jp/recycle/waste_tech/ippan/r3/index.html
(page title "令和３年度調査結果[環境省廃棄物処理技術情報]"; saved here as `r3_index.html`, 68,506 B).
Index of all survey years: https://www.env.go.jp/recycle/waste_tech/ippan/stats.html

**Downloaded:** 2026-09-20 00:09 JST (2026-09-19T15:09Z), HTTP 200, with curl.

| Local file | Link text on the page | Direct link | Bytes | SHA-256 |
|---|---|---|---:|---|
| `r3_shori_total_02.xlsx` | 全体集計結果（ごみ処理状況） (xls 274KB) | https://www.env.go.jp/recycle/waste_tech/ippan/r3/data/shori/total/02.xlsx | 280,247 | `b12aefdffcf1ec30c8b276281f28ac218e271eb577cb3715dc53a9af49d2aac5` |
| `r3_seibi_facility_01.xlsx` | 焼却施設 (xls 544KB) | https://www.env.go.jp/recycle/waste_tech/ippan/r3/data/seibi/facility/01.xlsx | 553,247 | `77a95fe0dbe53dc13ef579c9b49d9a9fcc5cbe523c7f49b37a5b28372abd0fe8` |

Both files are byte-identical to the copies fetched on 2026-08-08 that the phase-1 analysis
(`02_analyses/C_regional_weighting.py`) read, so the weights used in the chain come from exactly these files.

## What is used

| File / sheet | Cells | Meaning | Used for |
|---|---|---|---|
| `r3_shori_total_02.xlsx` / `ごみ処理概要` | A7:A53 | 47 prefecture names | join key |
| same | P3 = 直接焼却量, P6 = （ｔ）, **P7:P53** | direct incineration FY2021, t | **W2a weights** (region mean weighted by prefecture 直接焼却量) |
| same | P54 = `=SUM(P7:P53)` = **31,491,040 t** (A54 全国) | national total | share of national incineration per region |
| `r3_seibi_facility_01.xlsx` / `焼却` | rows 7–1066, G2 = 年間処理量, G6 = （t/年度）; BD–BJ = ごみ組成分析結果（乾ベース） | **1,060 facilities**, 47 prefectures; sum of 年間処理量 32,906,704 t/年度 | origin of the prefecture composition profiles; facility-level sensitivity W1 (`C_regional_weighting.md`) |

## Reconciliation (`reconcile_W2a.py`, log `reconcile_W2a.log`)

1. SHA-256 of both files as above.
2. 47 prefectures; P54 全国 = SUM(P7:P53) = 31,491,040 t; names identical to the chain's
   `regional_source/prefecture_waste_carbon.csv`.
3. Facility table: 1,060 facility rows, 47 prefectures.
4. For each of the 10 grid regions, the sum of 直接焼却量 and the share of the national total equal
   the chain's `region_waste_carbon.csv` columns `direct_incineration_FY2021_t` and
   `share_of_national_direct_incineration_pct` exactly.
5. 直接焼却量-weighted means of the 47 prefecture profiles reproduce the chain's regional
   plastic %, moisture %, fossil share of C %, CO₂ total and CO₂ fossil per t dry to within one unit of
   the last printed decimal (R1e tables, 2026-09-20: maximum 0.0063 pp; 7.1e-5 t/t) — the residual is
   the rounding of the prefecture CSV. The exact, unrounded rebuild of both the prefecture profiles and
   the regions is `02_analyses/R1e_regional/build_R1e.py`, whose outputs are the installed tables
   byte for byte.
6. Output: `W2a_weights_rebuilt.csv` (prefecture → region → 直接焼却量, weight within region, share of national).

## Prefecture profiles (R1e, 2026-09-20)

The regional base no longer uses the submitted compilation of the prefecture profiles, of which 14 of 47
could not be rebuilt from the facility table by any recorded rule (`02_analyses/R1e_regional/
VALIDATION_RESULT.md`). Since R1e all 47 profiles are rebuilt from `r3_seibi_facility_01.xlsx` by one
written rule (`02_analyses/R1e_regional/RULES_prefecture_composition.md`: simple mean of the 920
facilities with a reported composition; moisture over facilities with BM > 0) and weighted to the ten
regions with the prefecture 直接焼却量 of `r3_shori_total_02.xlsx`. The whole path from these two files to
the regional inputs is therefore reproducible. The submitted compilation is kept only as the unweighted
sensitivity (`region_waste_carbon_unweighted.csv`) and as `prefecture_waste_carbon_submitted.csv`.
