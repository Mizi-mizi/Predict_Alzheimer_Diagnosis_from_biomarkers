# MCI Survival Cohort — Build 0 Inventory & Implementation Map (v1)

**Specification:** `claude_spec_person1_mci_survival_cohort.md` — Person 1, Build 0 only.
**Date:** 2026-07-11
**Author:** Claude Code (automated reconnaissance)
**Scope of this build:** repository reconnaissance only. **No cohort-building code was created, modified, or run. No scientific rule was changed. No new scientific decision was made.** Reading raw files and the existing audit outputs to build this map is inventory, not cohort construction.

---

## 0. Repository / Git state

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD commit | `b14bcdd` — "Initial commit" |
| Working tree | **dirty** |
| Untracked (relevant) | `notebooks/01_mci_24m_cohort_audit.ipynb`, `notebooks/01b_mci_survival_cohort_audit.ipynb`, `outputs/` |

Note: the survival-audit notebook and all of its outputs are **untracked** working-tree files (not yet committed). They are nonetheless the canonical prior artifacts and are treated as authoritative here. No files were deleted or overwritten.

**Environment (from notebook metadata + stored outputs):** Python 3.14.0; pandas 3.0.1; numpy 2.4.3; matplotlib 3.10.8. Interpreter with these packages: `Data/.venv/bin/python`. (System `python3` has **no** pandas — use the venv.)

---

## 1. Files inspected

### Code / notebooks
- `notebooks/01b_mci_survival_cohort_audit.ipynb` — **the canonical survival-cohort logic** (40 cells; read in full, code + stored outputs).
- `notebooks/01_mci_24m_cohort_audit.ipynb` — prior *binary* 24-month audit (the pivot's predecessor; inspected for shared logic and imports).
- `notebooks/cleaner.ipynb`, `notebooks/final_v.ipynb`, `final_v.py`, `scripts/*.py`, `experiments/*.py`, `models/*.joblib` — **legacy CN/MCI/Dementia classifier project** (multinomial/ordinal logit, lasso, elastic-net). **Unrelated** to the survival cohort; they do not define anchor/event/censoring and are not imported by `01b`. Excluded from the survival pipeline.

### Existing survival artifacts (prior audit output, `outputs/01b_mci_survival_cohort_audit/`)
Read/enumerated: `mci_survival_anchor_cohort_raw.csv` (535×52 — the master), `survival_cohort_flow_counts.csv`, `survival_cohort_summary.csv`, `anchor_definition_comparison.csv`, `survival_followup_event_summary.csv`, `survival_followup_descriptives.csv`, `survival_predictor_missingness.csv`, `survival_predictor_missingness_by_event.csv`, `survival_baseline_characteristics_by_event.csv`, `data_dictionary_mci_survival_study.csv`, `data_discovery_survival_summary.csv`, `diagnosis_harmonization_survival.csv`, `km_survival_estimate.csv`, `km_number_at_risk.csv`, plus 7 PNG figures.

### Raw source tables (`Data/raw/`) — headers inspected for all; profiled where relevant
`All_Subjects_DXSUM_05Mar2026.csv`, `..._UPENN_PLASMA_FUJIREBIO_QUANTERIX_...`, `..._APOERES_...`, `..._My_Table_...`, `..._CDR_...`, `..._MMSE_...`, `..._MOCA_...`, `..._FAQ_...`, `..._FNIHBC_BLOOD_BIOMARKER_TRAJECTORIES_...`, `..._BIOMARK_...`, `..._GENETIC_...`, `..._GENETIC_...`. (`BIOMARK` and `GENETIC` are specimen-collection metadata CRFs — **not** assay results — and are not used.)

**No dedicated demographic (`PTDEMOG`), sex, education, comorbidity, death, or withdrawal table exists** in `Data/raw/`. Confirmed by filename scan and by the audit's own probe (`Death/withdrawal/registry tables found: NONE`).

---

## 2. Source table → variable map

All longitudinal tables join on **`RID`** (integer). `PTID` is the human-readable ID. Diagnosis and plasma dates come from `EXAMDATE`; cognitive tables use `VISDATE`.

| Analysis variable | Source file | Raw field(s) | Derivation (as implemented in `01b`) | Status |
|---|---|---|---|---|
| Participant ID | DXSUM / plasma | `RID`, `PTID` | join key `RID`; `PTID` carried for readability | ✅ resolved |
| Plasma anchor date | UPENN_PLASMA | `EXAMDATE` | `pd.to_datetime`; earliest eligible draw | ✅ resolved |
| Matched MCI dx date | DXSUM | `EXAMDATE` | nearest MCI dx within ±90 d (`merge_asof`, direction="nearest") | ✅ resolved |
| Signed / abs day diff | derived | anchor − dx dates | `align_offset_days = (plasma − dx).days` | ✅ resolved |
| Same-day vs cross-visit | derived | — | `same_day_alignment = |offset| == 0` | ✅ resolved |
| Anchor source row id | UPENN_PLASMA | `ID` (row id) exists | **not currently carried** into master | ⚠️ Build 1 to emit |
| Matched-dx source row id | DXSUM | `ID` (row id) exists | **not currently carried** into master | ⚠️ Build 1 to emit |
| Baseline age | My_Table | `entry_age` | `entry_age` (undated); joined via `subject_id`(==`PTID`)→`RID` | ⚠️ resolved-with-caveat |
| Age source date | — | none in My_Table | proxy = earliest dated DXSUM visit (`study_entry_date_proxy`) | ⚠️ proxy only |
| Age timing diff from anchor | derived | — | `years_entry_to_anchor = (anchor − proxy)/365.25` | ⚠️ approx |
| Age at anchor (approx) | derived | — | `age_at_anchor_approx = entry_age + years_entry_to_anchor` (flagged) | ⚠️ approx, flagged |
| APOE4 count | APOERES | `GENOTYPE` | `str.count("4")`; drop-dup on `RID` | ✅ resolved |
| p-tau217 (raw) | UPENN_PLASMA | `pT217_F` | Fujirebio; sentinel/≤0 → NaN | ✅ resolved |
| p-tau217 assay id | UPENN_PLASMA | (implicit `_F`) | Fujirebio; no separate assay-id field | ✅ resolved |
| **p-tau181** | **FNIHBC trajectories** | `TESTVALUE` where `PLASMA_BIOMARKER∈{QX_plasma_ptau181, Roche_plasma_ptau181}` | **not loaded by `01b`; not in master** | ⚠️ **source found, not integrated — see §5** |
| GFAP | UPENN_PLASMA | `GFAP_Q` | Quanterix; sentinel/≤0 → NaN (`GFAP_F` Fujirebio also exists, unused) | ✅ resolved |
| NfL | UPENN_PLASMA | `NfL_Q` | Quanterix (`NfL_F` also exists, unused) | ✅ resolved |
| Aβ42 | UPENN_PLASMA | `AB42_F` | Fujirebio | ✅ resolved |
| Aβ40 | UPENN_PLASMA | `AB40_F` | Fujirebio | ✅ resolved |
| Aβ42/Aβ40 ratio | derived + vendor | `AB42_F/AB40_F`; vendor `AB42_AB40_F` | recomputed ratio + vendor column kept separately | ✅ resolved |
| Cognitive candidates | CDR / MMSE / MOCA / FAQ | `CDRSB`, `MMSCORE`, `MOCA`, `FAQTOTAL` | aligned to anchor ±90 d (`merge_asof` nearest); CDR restricted to `CDVERSION∈{1,2}` | ✅ resolved |
| Event indicator | DXSUM (follow-up) | `DIAGNOSIS` | first strictly post-anchor Dementia → 1, else 0 | ✅ resolved |
| First post-anchor dementia date | DXSUM | `EXAMDATE` | first `dx==Dementia` with `DATE > anchor` | ✅ resolved |
| Last non-dementia date (censor) | DXSUM | `EXAMDATE` | last post-anchor CN/MCI `DATE` when no event | ✅ resolved |
| Event/censor date, follow-up days | derived | — | `time_to_event_or_censor_days`; `_months` = /30.4375 | ✅ resolved |
| Event/censor source row id | DXSUM | `ID` exists | **not currently carried** | ⚠️ Build 1 to emit |

**Diagnosis coding (locked, re-verified in audit):** `DIAGNOSIS` `1=CN, 2=MCI, 3=Dementia`; blank → `unknown/other` (never used to define event or censor).

---

## 3. Existing cohort logic summary (as implemented in `01b`, unchanged)

**Configuration constants:** `MISSING_SENTINELS=[-4,-5]`; non-positive plasma concentration → NaN; `ALIGN_TOL_DAYS=90`; `DAYS_PER_YEAR=365.25`; `DAYS_PER_MONTH=30.4375`; `CORE_ASSAYS=[ptau217, abeta42, abeta40, nfl, gfap]` ("≥1 usable" for the broad anchor).

1. **Diagnosis harmonization & cleaning.** Parse `EXAMDATE`; map codes; drop rows without date or diagnosis; **collapse same-day records per RID keeping highest severity** (sort by `dx_code` ascending, `drop_duplicates(keep="last")`). Result: 15,935 dated visits / 3,763 participants.
2. **Plasma cleaning.** Sentinels & ≤0 → NaN (0 suspicious found); recompute `ratio_ab42_ab40`; `n_usable_core_assays` = count of non-null core assays; drop rows without date; de-duplicate `(RID,DATE)` keeping first (0 collapsed). 2,178 clean draws, all with ≥1 usable core assay.
3. **APOE / age.** `APOE4_COUNT` from `GENOTYPE`. `entry_age` joined via `subject_id`→`PTID`→`RID`. Study-entry proxy = earliest dated DXSUM visit.
4. **Broad MCI plasma anchor (Cohort A).** `identify_broad_anchor`: restrict plasma to `n_usable_core_assays ≥ 1`; `merge_asof` nearest to dated dx `by RID` within ±90 d; keep rows whose matched dx is **MCI**; **earliest plasma DATE per RID** (`sort_values(["RID","DATE"]).drop_duplicates("RID", keep="first")`). → **535** participants.
5. **Survival derivation (`derive_survival`).** Per participant, use **strictly post-anchor** diagnoses (leakage guard). If any post-anchor Dementia → **event=1** at first such date. Else if any post-anchor CN/MCI → **event=0**, censor at **last** such date. Else (no valid post-anchor dx) → **no usable follow-up → excluded** (not "stable"). Same-day dementia at anchor is inspected but **not** treated as a prospective event (0 cases found). Non-positive follow-up times are demoted to no-usable-follow-up.
6. **Master assembly.** One row per participant (535×52): anchor + plasma + age/APOE + anchor-aligned cognition + survival outcome + eligibility flags. Horizon flags at 365/730/1095 d.
7. **Cohort flags.** `survival_followup_eligible_flag`; `has_primary = eligible & entry_age.notna() & APOE4_COUNT.notna() & ptau217.notna()`; secondary flags for GFAP / amyloid-ratio / full-exploratory. **Feature completeness selects the model, never the anchor.**

**Cohorts defined:** A Broad anchor · B Survival-follow-up · C Primary-model-eligible · D GFAP-secondary · E Amyloid-ratio-secondary · F Full-exploratory.

---

## 4. Reusable functions (all in-notebook; **no external/helper module exists**)

Both notebooks import only stdlib + numpy/pandas/matplotlib — there is **no `src/` or helper package** to reuse. The canonical logic lives entirely in `01b` cells. Functions to lift into a Build 1 module (`notebooks/01c…` or a new module) essentially verbatim:

| Function | Role | Reuse verdict |
|---|---|---|
| `find_project_root(start)` | locate repo root by `Data/raw` | reuse as-is |
| `save_table(df, name)` | write CSV to OUT_DIR | adapt → TSV + versioned names |
| `clean_sentinels(s)` | −4/−5 → NaN | reuse as-is |
| `harmonize_diagnosis(code)` | 1/2/3 → CN/MCI/Dementia | reuse as-is |
| `identify_broad_anchor(plasma, dxh)` | Cohort A anchor | **reuse as-is (canonical)** |
| `derive_survival(anchor, dxh)` | event/censoring | **reuse as-is (canonical)** |
| `align_scores(anchor, score, …)` | ±90 d cognition/biomarker alignment to anchor | reuse; extend for p-tau181 join |
| `identify_prior_anchor(…)` | reproduce p-tau217-required prior anchor | reuse for discrepancy check |
| `km_estimate`, `n_at_risk` | KM feasibility (descriptive) | not needed for freeze (no modeling) |

---

## 5. Ambiguities / inconsistencies (surfaced, **not resolved** — for Build 1 team decision)

1. **"Baseline age" vs `entry_age` (undated).** Spec §2.7 requires nonmissing "baseline age" for the primary cohort. The source `My_Table` provides only `subject_id, entry_age` with **no datestamp**, so age-at-anchor is **not validly derivable** (the audit says so explicitly). The audit keeps `entry_age` as the labelled primary age (present for **410/410** survival-eligible) and adds a flagged `age_at_anchor_approx`. **Decision for Build 1:** confirm `entry_age` is the authoritative "baseline age" column (preserving the existing rule) and carry `age_at_anchor_approx` + `age_is_entry_age_fallback` as flagged provenance. No change made here.

2. **p-tau181 source exists but is a largely disjoint sub-study.** p-tau181 is **absent** from the primary UPENN plasma panel. It exists only in `FNIHBC_BLOOD_BIOMARKER_TRAJECTORIES` (long format) on two platforms — `QX_plasma_ptau181` (Quanterix/SIMOA, 355 RIDs) and `Roche_plasma_ptau181` (Elecsys, 393 RIDs); union = all **406** FNIHBC RIDs, 2,233 non-null values. **Overlap with the anchor cohort is only 40/535 (33/410 survival-eligible)** — 366 of 406 FNIHBC participants are not in the anchor cohort at all. **Implications:** (a) any p-tau181 secondary/model-complete analysis (spec Build 3 item "age+APOE4+p-tau181") would rest on ~33 survival-eligible participants with very few events; (b) integrating it requires a documented join decision (which platform is authoritative? align FNIHBC `EXAMDATE` to anchor within ±90 d like other assays?). **Decision deferred to Build 1/3.** Its absence must not exclude anyone from the primary cohort (spec §2.7).

3. **Anchor tie-break specification.** The audit's operative tie-break is **earliest plasma DATE, then stable original row order** (plasma is pre-deduplicated to one row per `(RID,DATE)` with `keep="first"`, and `merge_asof` selects the nearest dx per draw). The spec §2.2 fallback tie-breaks (smallest `|plasma−dx|`, then earlier dx date) are **not exercised** because there is at most one candidate row per (RID, plasma date). **Build 1 will preserve earliest-date + stable-order and record it in provenance**; the spec fallbacks are documented as inactive, not as a rule change.

4. **Output naming / directory & file format.** The existing convention is `outputs/<notebook_name>/…*.csv` with a **single flag-bearing master** (`mci_survival_anchor_cohort_raw.csv`), not the spec's **three split TSVs** (`…_anchor_cohort_v1.tsv`, `…_followup_cohort_v1.tsv`, `…_primary_cohort_v1.tsv`) + `…_exclusion_log_v1.tsv` + `…_cohort_flow_v1.tsv`. There is **no participant-level exclusion log** today (only an aggregate flow table). **Build 1 must** split the master into the three cohort tables, add a per-participant exclusion log (stage + reason), emit TSV `_v1` files, and add provenance sidecars — writing to a **new** directory (proposed `outputs/01c_mci_survival_cohort_freeze/`, per repo convention) so nothing is overwritten.

5. **Missing provenance/source-row-id columns.** Plasma, DXSUM all carry an `ID` row-identifier column that the current master does **not** propagate (anchor / matched-dx / event / censor source rows). Build 1 should carry these to satisfy spec §2.3 and the required-columns list.

6. **Administrative censoring only (documented limitation, not a fix).** No death/LTFU table exists, so censoring is at the last clinical visit. This is an inherited limitation to document in provenance; nothing to resolve at freeze time.

7. **Vendor selection for shared analytes.** For NfL/GFAP the audit uses Quanterix (`_Q`); Fujirebio (`_F`) variants also exist and are unused. p-tau217/Aβ use Fujirebio (`_F`). This is an existing, consistent choice — preserve and document; do not change.

**Every required primary variable has an identified source.** The only variable whose source is present but **not integrated** is the *secondary* p-tau181 (item 2). No required variable is unresolved to the point of being unlocatable.

---

## 6. Reproduction of the expected audit landmarks (535 / 410 / 86 / 401 / 85)

**Yes — all five landmarks are reproduced exactly by the existing artifact** `outputs/01b_mci_survival_cohort_audit/mci_survival_anchor_cohort_raw.csv` (535 rows × 52 cols) and the stored notebook outputs:

| Stage | Spec target | Existing artifact | Match |
|---|---:|---:|:--:|
| A — Broad MCI plasma-anchor | ~535 | **535** | ✅ |
| B — Survival-follow-up eligible | ~410 | **410** (86 events + 324 censored) | ✅ |
| Dementia events (survival cohort) | ~86 | **86** | ✅ |
| C — Primary complete-case (age+APOE4+p-tau217) | ~401 | **401** | ✅ |
| Events in primary cohort | ~85 | **85** | ✅ |

**Reconciliation of the B→C drop (410→401):** driven **entirely by APOE4 missingness** — `APOE4_COUNT` missing for 9 survival-eligible participants; `entry_age` missing for 0/410; `p-tau217` missing for 0/410. `410 − 9 = 401`. One of those 9 is an event, so events go `86 → 85`. Fully consistent; no unexplained discrepancy.

Supporting counts also reproduced: total DXSUM participants 3,789; ≥1 MCI diagnosis 1,801; no-usable-follow-up excluded 125; events by 12/24/36 mo = 15/34/56; median follow-up 420 d.

**Conclusion:** Build 1 should **recompute from source** and reconcile against these values (a discrepancy report is only triggered if recomputation diverges). Based on this reconnaissance, exact reproduction is expected.

---

## 7. Planned files for Builds 1–4

Directories: cohort/data outputs → **`outputs/01c_mci_survival_cohort_freeze/`** (follows the repo's `outputs/<notebook>/` convention; the spec's `results/` is mapped here to avoid a duplicate folder tree, per spec §5). Markdown reports → **`reports/`** (created in this build). All data outputs TSV, versioned `_v1`, with provenance sidecars. **Nothing existing is overwritten.**

**Build 1 — canonical freeze pipeline**
- `notebooks/01c_mci_survival_cohort_freeze.ipynb` (new; end-to-end from clean kernel)
- `outputs/01c_mci_survival_cohort_freeze/`: `mci_survival_anchor_cohort_v1.tsv`, `mci_survival_followup_cohort_v1.tsv`, `mci_survival_primary_cohort_v1.tsv`, `mci_survival_exclusion_log_v1.tsv`, `mci_survival_cohort_flow_v1.tsv` (+ provenance JSON sidecar/manifest)
- `reports/mci_survival_build1_freeze_report_v1.md`; conditional `reports/mci_survival_count_discrepancy_v1.md`

**Build 2 — manual QC packet**
- `outputs/01c_.../mci_survival_manual_qc_cases_v1.tsv`, `…_manual_qc_longitudinal_context_v1.tsv`, `…_manual_qc_form_v1.tsv`; `reports/mci_survival_build2_qc_guide_v1.md` (seed `20260711`)

**Build 3 — feature availability & missingness audit**
- `outputs/01c_.../mci_survival_feature_missingness_v1.tsv`, `…_model_complete_case_counts_v1.tsv`, `…_feature_timing_v1.tsv`; `reports/mci_survival_build3_feature_audit_v1.md`

**Build 4 — data dictionary, provenance, handoff**
- `outputs/01c_.../mci_survival_data_dictionary_v1.tsv`, `…_freeze_manifest_v1.json`; `reports/mci_survival_primary_analysis_spec_v1.md`, `reports/mci_survival_person1_handoff_v1.md`

---

## 8. Confirmation of Build 0 constraints

- ✅ **No cohort-building code changed, created, or executed.** Only reads/inspection + this report + creation of the empty `reports/` directory.
- ✅ **No existing notebook or result overwritten.**
- ✅ **No new scientific rule or decision made.** All ambiguities in §5 are surfaced for the team, not silently resolved.
- ✅ **Every required primary variable has an identified source** (p-tau181 — a *secondary* feature — is located but not yet integrated; flagged).
- ✅ **The 535/410/86/401/85 landmarks are reproducible** from the existing artifact (§6).

*Seed for later QC sampling (recorded now): `20260711`.*
