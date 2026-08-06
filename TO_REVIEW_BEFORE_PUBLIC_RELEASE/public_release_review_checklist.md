# Public-release review checklist

Work top to bottom. Do **not** make the repository public or mint a DOI until every item in
section 1 is checked.

## 1. Sensitive-information sweep

- [ ] No laboratory source workbooks (`.xlsb`, the CCU / mineralization / database
      workbooks) anywhere in the repository or its history.
- [ ] No absolute local paths, machine usernames, API tokens, credentials or e-mail
      signatures in code, configs or data files.
- [ ] No personal names other than the two authors. Earlier internal drafts referred to
      contributors by name; the shipped code, data and metadata must not.
- [ ] The only contact address present is the corresponding author's institutional address,
      which is already public in the manuscript.
- [ ] Japanese text present in `regional_source/build_regions.py` is limited to the names of
      official statistical sources, sheet names and prefecture names. Confirm no internal
      notes remain.
- [ ] `git log -p` and `git grep` scanned for accidental secrets or unpublished data.

## 2. Repository hygiene

- [ ] `LICENSE` (MIT for code, CC BY 4.0 for data) present at the repository root.
- [ ] `docs/DATA_AND_DOCUMENTATION_LICENSE.md` present.
- [ ] `CITATION.cff` present; the DOI line is filled after archival.
- [ ] `.zenodo.json` present and its author affiliations match the manuscript.
- [ ] `requirements.txt` reproduces the environment.
- [ ] `README.md` complete and the quickstart runs end to end from a clean clone.
- [ ] `cd calculation_code && python run_all.py` reproduces all 15 reference CSV files byte
      for byte and rebuilds the workbook with zero cell differences.

## 3. Licence and permission confirmations

- [ ] Co-author has agreed to the public release and to the licence terms.
- [ ] The institution's rules on releasing research outputs have been checked.
- [ ] The two funding programmes' data-management requirements have been checked
      (JPMJSC24E1, JPMEERF20253J01).
- [ ] The terms of use of the reproduced government statistics permit redistribution.

## 4. GitHub release

- [ ] Push to a **public** GitHub repository (only after sections 1 to 3 pass).
- [ ] Create a tagged release, `v1.0.0`.

## 5. Zenodo archival

- [ ] Enable the Zenodo-GitHub integration for the repository **before** publishing the
      release; Zenodo only archives releases created after the integration is switched on.
- [ ] Publish the GitHub release; Zenodo archives the tagged snapshot.
- [ ] Obtain the version DOI and the concept (all-versions) DOI.

## 6. Wire the DOI back in

- [ ] Insert the concept DOI into `README.md`, `CITATION.cff`, the manuscript **Data
      availability** statement, and the archive README shipped with the submission.
- [ ] Record the code version, archive version, manuscript version and both DOIs in
      `CHANGELOG.md`.
- [ ] Re-record the archive SHA-256 in the handover document.

## 7. Provenance record

- [ ] Note the git tag, the commit hash and both DOIs together with the manuscript revision
      they correspond to, and keep that note with the submission package.
