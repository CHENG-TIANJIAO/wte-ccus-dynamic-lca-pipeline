# Verification — version 1.2.0 (revision R2, parameter ledger R1g)

Version 1.2.0 adds `analysis/R2_time_sensitivity.py` and its four output files and changes nothing
else in the model, its parameters, inputs, results or figures. It was verified on 2026-10-27 with
Python 3.11.9, numpy 2.4.2, openpyxl 3.1.5, matplotlib 3.10.8 and pandas 3.0.1 on Windows x86-64.

The repository was cloned into an empty directory and the Quickstart of the README was followed
there command for command, once with its Bash block and once, in a second clone, with its
PowerShell block. In both shells:

* All 91 digests of `MANIFEST_SHA256.txt` held in the fresh checkout.
* All six commands exited 0, the chain reported 0 self-check failures, and no byte-code directory
  was written.
* After the run, 90 of the 91 files were byte-identical, among them the four outputs of the new
  analysis. The exception is `code/outputs/Unified_calculation_workbook.xlsx`: its container
  stores a timestamp, and of its 8,344 cells the only one that differed is the provenance cell
  `7_Provenance!B10`, which records the operating-system build of the machine that wrote the file
  (Windows 10.0.26300 at this run, 10.0.26200 when the shipped copy was written). Every
  calculated cell is identical.
* The seven regenerated PNG figures are byte-identical to the figures of the manuscript.
* `analysis/R2_time_sensitivity.py` stops unless it reproduces the eight background combinations
  of `Shapley_decomposition_audit.csv`, the four endpoints of `Fig5_source_data.csv` and the
  published break-even of storage on the 2050 background; it passed. Its results were also
  recomputed independently from the same model code, from the definitions alone, and agreed in
  all 3,328 compared values and ranks.

The record of version 1.1.0 follows unchanged.

---

## Version 1.1.0 (revision R1, parameter ledger R1g)

Independent runs of this content were performed on 2026-09-20 and, after the last change to
Figure 1, repeated on 2026-09-29, with Python 3.11.9,
numpy 2.4.2, openpyxl 3.1.5, matplotlib 3.10.8 and pandas 3.0.1 on Windows x86-64: one in a
clean directory outside any working tree, and one in this repository.

## 1. Clean-directory run of the release archive

A ZIP archive holding the same content as this repository, in the same layout, was checked
as a container and then run in isolation.

1. The ZIP was inspected: unsafe paths none, duplicates none, non-ASCII names none, compiled
   bytecode none. 89 files, 16.55 MB.
2. It was extracted into an empty temporary directory outside the working tree.
3. `python code/run_all.py` was run there: exit code 0, 16 s, Monte Carlo N = 50,000, seed
   20260702, self-check failure counters 0.
4. Every file of `MANIFEST_SHA256.txt` was hashed again after the re-run.
5. The national results of the re-run were compared with the frozen number table of the
   revision.
6. `analysis/E5_shapley_interactions.py` and `analysis/F5_mc_correlation.py` were run in the
   extracted archive and the matrices they rewrote were compared with the shipped ones.
7. `figures/make_figs_R1.py` and `figures/make_fig1_R1.py` were run in the extracted archive
   and their output compared with the figures embedded in the manuscript.

Result:

* 85 of 86 files byte-identical after the re-run.
* `code/outputs/Unified_calculation_workbook.xlsx` not byte-identical (the file format stores
  a timestamp); every cell identical.
* Both analyses exited 0 and reproduced 14 matrices byte for byte, among them the four
  matrices Supplementary Fig. S1 is drawn from (`F5_mc_spearman_A/B.csv`,
  `F5_mc_pairwise_prob_A/B.csv`), the paired-versus-independent comparison of Supplementary
  Table S28, and the interaction terms of Supplementary Table S29
  (`E5_shapley_interactions.csv`, `E5_shapley_interactions_terms.csv`).
* Seven PNG figures reproduced the submitted figures byte for byte.

## 2. Runs of this repository

`python code/run_all.py`, then both analyses, then both figure scripts, in the repository as
it is committed. All five exited 0 and the chain reported 0 self-check failures. Result:

* All 15 reference CSV files in `code/outputs/` and all 14 matrices in `analysis/` are
  byte-identical to the digests of the release archive.
* `Unified_calculation_workbook.xlsx` rebuilt and compared cell by cell against the shipped
  copy: 8,344 cells compared, 0 differences. The shipped copy is kept, so that the bytes here
  are the bytes of the verified archive.
* The smallest text in every figure is 7.0 pt or larger at the placed size, and all seven
  PNG files are byte-identical to Figures 1 to 6 and Fig. S1 as submitted.
* `make_figs_R1.py` re-verified all 86 entries of `MANIFEST_SHA256.txt` with no difference in
  the model code, its parameters or its inputs.
* Key national results, convention A 2025 (t-CO2 per year): S0 18,737.1785, M1 30,453.2334,
  M4 81,898.0164, G1 6,937.9383, U2a -45,803.0134, R3 -7,468.3320 — identical to the frozen
  values of the revision.

The repository was then cloned into an empty directory and the Quickstart of the README was
followed there command for command, once with its Bash block and once, in a second clone,
with its PowerShell block. This is what a reader obtains from the released version:

* All 86 digests of `MANIFEST_SHA256.txt` hold in the fresh checkout, so no file changes on
  clone and the published digests can be verified on any platform.
* In both shells all five commands exited 0 with 0 self-check failures, no byte-code
  directory was written, and after the run 85 of the 86 files are byte-identical, the
  workbook being the only exception. The seven regenerated PNG figures are again
  byte-identical to the submitted figures.

## Scope and limitations

* Byte identity is reported for the environment above. A different interpreter or BLAS build
  can change the summation order of a reduction and with it the sign of a floating-point
  zero, which alters a text file without altering any result; the numerical checks in the
  README are what this release commits to on any build.
* `Unified_calculation_workbook.xlsx` and the figure PDFs are not byte-reproducible because
  both formats record a creation time; their content is compared instead.
* The two scripts in `analysis/` differ from the versions used during development only in
  (1) portable path resolution, so that they find the model and their own directory wherever
  this content is placed, and, in `F5_mc_correlation.py`, (2) conditional omission of an
  internal development-comparison block whose inputs are not part of the published analysis.
  Neither change affects any published output: the omitted block runs after all fourteen
  published matrices have been written, and every one of those matrices is reproduced byte
  for byte. Each file states this at the top.
* This repository carries the model, its inputs and the figure scripts, not the manuscript
  files. The manuscript, the Supplementary Information and the figure files are published with
  the article.
* The digest of a ZIP depends on the container, so the digest of the verification ZIP is not
  that of the archive GitHub and Zenodo generate from a tag; `MANIFEST_SHA256.txt` identifies
  the content itself, file by file, in either container.
