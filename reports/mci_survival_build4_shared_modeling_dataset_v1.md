# MCI Survival — Shared Modeling Dataset (`v1`)

**Notebook:** [notebooks/03a_mci_survival_shared_modeling_dataset.ipynb](../notebooks/03a_mci_survival_shared_modeling_dataset.ipynb)
**Date:** 2026-07-11
**Status:** ✅ 91/91 assertions passed. Input checksum verified. 401 participants preserved. Exactly **26 columns** in the specified order. All 17 existing frozen v1 artifacts byte-identical. Outputs deterministic across two clean-kernel runs.

One narrow, versioned modeling dataset that Person 2 (feature-combination analysis), Person 3 (alternative survival models), and Person 4 (centralized evaluation + NACC harmonization) can all load — so nobody re-joins raw ADNI data.

---

## 1. Deliverables

**`outputs/03a_mci_survival_shared_modeling/`**

| File | Rows × Cols |
|---|---|
| `mci_survival_shared_modeling_dataset_v1.tsv` | **401 × 26** |
| `mci_survival_shared_modeling_data_dictionary_v1.tsv` | 26 × 11 |
| `mci_survival_analysis_set_counts_v1.tsv` | 8 × 8 |
| `mci_survival_shared_modeling_manifest_v1.json` | — |

Report: `reports/mci_survival_build4_shared_modeling_dataset_v1.md` (this file).

## 2. Input & provenance

- **Sole input:** `outputs/01c_mci_survival_cohort_freeze/mci_survival_primary_cohort_v1.tsv`
- **Checksum verified:** `a15e2cb8606f676b3bcfc4d23de72c752779836ce9406b04b01c84394a76e8ad` ✓ (build refuses to continue on a mismatch).
- **No raw ADNI table re-joined.** No re-anchoring, no MCI/event/censoring redefinition, no exclusions, no imputation, no scaling, no feature selection, no model fitting, no CV folds.

### Prior-dementia QC-field mapping (confirmed unambiguous)

The two requested QC concepts map to **exactly** these frozen columns — no substitution:

| Requested | Frozen column | Type | Nonzero/True |
|---|---|---|---:|
| pre-anchor dementia count | `pre_anchor_dementia_n` | int | 4 |
| prior-dementia flag | `qc_dementia_on_or_before_anchor` | bool | 4 |

(`sameday_dementia_at_anchor` is a distinct third field and is **not** carried — it was not requested.)

## 3. The 26 columns (exact order)

| # | Column | Role | Missing/401 | Transform |
|---:|---|---|---:|---|
| 1 | `RID` | identifier *(never a predictor)* | 0 | none |
| 2 | `anchor_date` | provenance / harmonization | 0 | none |
| 3 | `time_to_event_or_censor_days` | outcome — duration | 0 | none (carried) |
| 4 | `event_indicator` | outcome — event (1=dementia, 0=censored) | 0 | none (carried) |
| 5 | `entry_age` | primary predictor | 0 | none |
| 6 | `APOE4_COUNT` | primary predictor | 0 | none |
| 7 | `APOE4_CARRIER` | primary predictor *(derived)* | 0 | `(APOE4_COUNT >= 1).astype(int)` |
| 8 | `ptau217` | primary predictor | 0 | none |
| 9 | `log_ptau217` | primary predictor *(derived)* | 0 | `np.log(ptau217)` |
| 10 | `gfap` | secondary predictor | 40 | none |
| 11 | `log_gfap` | secondary predictor *(derived)* | 40 | `np.log(gfap)` |
| 12 | `nfl` | secondary predictor | 40 | none |
| 13 | `log_nfl` | secondary predictor *(derived)* | 40 | `np.log(nfl)` |
| 14 | `abeta42` | secondary predictor | 2 | none |
| 15 | `abeta40` | secondary predictor | 2 | none |
| 16 | `ratio_ab42_ab40` | secondary predictor | 2 | `abeta42/abeta40` (carried from frozen) |
| 17 | `pre_anchor_dementia_n` | QC flag *(carried)* | 0 | none |
| 18 | `qc_dementia_on_or_before_anchor` | QC flag *(carried)* | 0 | none |
| 19 | `eligible_core` | eligibility flag | 0 | derived |
| 20 | `eligible_gfap` | eligibility flag | 0 | derived |
| 21 | `eligible_nfl` | eligibility flag | 0 | derived |
| 22 | `eligible_amyloid` | eligibility flag | 0 | derived |
| 23 | `eligible_gfap_nfl` | eligibility flag | 0 | derived |
| 24 | `eligible_gfap_amyloid` | eligibility flag | 0 | derived |
| 25 | `eligible_nfl_amyloid` | eligibility flag | 0 | derived |
| 26 | `eligible_full_blood` | eligibility flag | 0 | derived |

Derivations match Person 2's published primary analysis (`log_ptau217`, `APOE4_CARRIER`).

## 4. Eligibility flags = per-participant analysis-set membership

Each `eligible_*` flag is `1` when a participant has complete data for **core** (`entry_age + APOE4_COUNT + ptau217`, complete for all 401) **plus** the named markers; `amyloid := ratio_ab42_ab40` present. They materialize each complete-case analysis set, so a downstream team filters with **one column** and never re-derives availability.

| Flag | Predictors | N | Events | Censored | % of 401 |
|---|---|---:|---:|---:|---:|
| `eligible_core` | age + APOE4 + log p-tau217 | **401** | **85** | 316 | 100 |
| `eligible_gfap` | core + GFAP | 361 | 85 | 276 | 90.0 |
| `eligible_nfl` | core + NfL | 361 | 85 | 276 | 90.0 |
| `eligible_amyloid` | core + Aβ42/Aβ40 | 399 | 83 | 316 | 99.5 |
| `eligible_gfap_nfl` | core + GFAP + NfL | 361 | 85 | 276 | 90.0 |
| `eligible_gfap_amyloid` | core + GFAP + amyloid | 359 | 83 | 276 | 89.5 |
| `eligible_nfl_amyloid` | core + NfL + amyloid | 359 | 83 | 276 | 89.5 |
| `eligible_full_blood` | core + GFAP + NfL + amyloid | **359** | **83** | 276 | 89.5 |

`eligible_core` reproduces the frozen primary cohort exactly (401 / 85); `eligible_full_blood` = 359 / 83. Flags are strictly `{0,1}` and properly nested (asserted). These same counts are in `mci_survival_analysis_set_counts_v1.tsv`, reconciled row-by-row against the flag sums.

**Note for downstream teams:** GFAP and NfL are missing on the **same 40 participants** (both Quanterix), so `eligible_gfap`, `eligible_nfl`, and `eligible_gfap_nfl` are the identical 361-person set. Every event drop (85 → 83) comes from the 2 Aβ-missing participants.

## 5. Design guarantees (all asserted, 91/91)

- **All 401 participants preserved** — not reduced to any complete-case subset. Optional biomarkers are genuine `NA`.
- **No imputation** — every optional-marker NA count matches the frozen cohort exactly (gfap/nfl/log_gfap/log_nfl 40; abeta/ratio 2).
- **No scaling** — all raw carried columns byte-identical to the frozen cohort.
- **Outcome carried, not recomputed** — duration + event byte-faithful; durations strictly positive; 85/316 preserved.
- **QC fields carried faithfully**; the flag agrees with the count (`flag ⇔ n>0`); 4 flagged participants **retained** (adjudication pending).
- **No cognition, no CV folds, no model fitting, no feature selection.**
- **`RID` is documented as identifier-only, never a predictor.**

## 6. Integrity

- **91/91 assertions passed.**
- **All 17 frozen v1 artifacts byte-identical** before and after; frozen primary cohort hash unchanged (`a15e2cb8…`).
- **Deterministic:** all three TSVs byte-identical across two clean-kernel runs.

| Output | SHA-256 |
|---|---|
| `mci_survival_shared_modeling_dataset_v1.tsv` | `521120e76418da5433d840d5301f2ed71686170a7b12a548ca631d950d314a3d` |
| `mci_survival_shared_modeling_data_dictionary_v1.tsv` | `9ff1df31d93c40bd272d801c744d4d1ee0de0f1b3420ba5a92f5406b4da6c6e8` |
| `mci_survival_analysis_set_counts_v1.tsv` | `da724882a09e1d0460466613f26d5b40c8b63fbe37429950346241bd7b04d388` |

## 7. How downstream teams use it

```python
import pandas as pd
df = pd.read_csv("outputs/03a_mci_survival_shared_modeling/mci_survival_shared_modeling_dataset_v1.tsv", sep="\t")
assert len(df) == 401 and df.RID.is_unique

# filter to an analysis set with ONE column — no re-derivation of availability
gfap_set = df[df.eligible_gfap == 1]            # 361 / 85 events
full_set = df[df.eligible_full_blood == 1]      # 359 / 83 events

# duration = time_to_event_or_censor_days | event = event_indicator | never use RID as a predictor
# prior-dementia sensitivity: df[df.qc_dementia_on_or_before_anchor == False]   # drops the 4 flagged
```

The shared file is **not** pre-filtered — each team applies the eligibility flag their model needs. Missing optional biomarkers are genuine `NaN`, never imputed.

## 8. Reproduction

```bash
cd /Users/zoeyd/Desktop/Predict_AD_from_Biomarkers
Data/.venv/bin/python -m nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=600 \
  notebooks/03a_mci_survival_shared_modeling_dataset.ipynb
```

Environment: Python 3.14.0, pandas 3.0.1, numpy 2.4.3.

## 9. Scope note

This build does **not**: rejoin raw data · re-anchor · redefine MCI/event/censoring · exclude short-follow-up or prior-dementia participants · impute · scale · select features · fit models · add cognition · generate CV folds · modify any Build 1–3 artifact. The four prior-dementia-flagged participants remain in the dataset (flagged upstream; adjudication still pending — see `reports/mci_survival_person1_handoff_v1.md`).
