# MCI Survival — Shared Modeling Dataset (`v1`)

**Notebook:** [notebooks/03a_mci_survival_shared_modeling_dataset.ipynb](../notebooks/03a_mci_survival_shared_modeling_dataset.ipynb)
**Status:** 131/131 assertions passed. Input checksum verified. 401 participants preserved. Exactly **26 columns** in the specified order. All 17 existing frozen v1 artifacts byte-identical. Every generated artifact byte-identical across two clean-kernel runs.

One narrow, versioned modeling dataset that Person 2 (feature-combination analysis), Person 3 (alternative survival models), and Person 4 (centralized evaluation + NACC harmonization) can all load — so nobody re-joins raw ADNI data.

This report carries no build date and no runtime-generated content, so it hashes stably and can itself be recorded in the manifest.

---

## 1. Deliverables

**`outputs/03a_mci_survival_shared_modeling/`**

| File | Rows × Cols |
|---|---|
| `mci_survival_shared_modeling_dataset_v1.tsv` | **401 × 26** |
| `mci_survival_shared_modeling_data_dictionary_v1.tsv` | 26 × 11 |
| `mci_survival_analysis_set_counts_v1.tsv` | 8 × 9 |
| `mci_survival_shared_modeling_manifest_v1.json` | — |

Report: `reports/mci_survival_build4_shared_modeling_dataset_v1.md` (this file).

## 2. Input & provenance

- **Sole input:** `outputs/01c_mci_survival_cohort_freeze/mci_survival_primary_cohort_v1.tsv`
- **Checksum verified:** `a15e2cb8606f676b3bcfc4d23de72c752779836ce9406b04b01c84394a76e8ad` ✓ (the build refuses to continue on a mismatch).
- **No raw ADNI table re-joined.** No re-anchoring, no MCI/event/censoring redefinition, no exclusions, no imputation, no scaling, no winsorization, no feature selection, no model fitting, no CV folds, no cognitive or functional variables.

### Source-to-output column mapping

Sixteen columns are carried byte-for-byte from the frozen cohort under identical names; ten are derived in this build. The full mapping is recorded in the manifest under `source_to_output_column_mapping`.

| Output columns | Source | Note |
|---|---|---|
| `RID`, `anchor_date`, `time_to_event_or_censor_days`, `event_indicator`, `entry_age`, `APOE4_COUNT`, `ptau217`, `gfap`, `nfl`, `abeta42`, `abeta40`, `ratio_ab42_ab40`, `pre_anchor_dementia_n`, `qc_dementia_on_or_before_anchor` | same-named frozen column | carried, unmodified |
| `APOE4_CARRIER` | `APOE4_COUNT` | derived |
| `log_ptau217` / `log_gfap` / `log_nfl` | `ptau217` / `gfap` / `nfl` | derived, `numpy.log` |
| 8 × `eligible_*` | feature availability | derived from nonmissingness |

`sameday_dementia_at_anchor` is a distinct third QC field in the frozen cohort and is **not** carried — it was not requested.

## 3. The 26 columns (exact order)

| # | Column | Role | Missing/401 | Derivation |
|---:|---|---|---:|---|
| 1 | `RID` | identifier | 0 | carried |
| 2 | `anchor_date` | provenance | 0 | carried |
| 3 | `time_to_event_or_censor_days` | survival duration | 0 | carried (not recomputed) |
| 4 | `event_indicator` | survival event | 0 | carried (not recomputed) |
| 5 | `entry_age` | core predictor | 0 | carried |
| 6 | `APOE4_COUNT` | core predictor | 0 | carried |
| 7 | `APOE4_CARRIER` | core predictor *(derived)* | 0 | `(APOE4_COUNT >= 1).astype(int)` |
| 8 | `ptau217` | raw audit variable | 0 | carried |
| 9 | `log_ptau217` | core predictor *(derived)* | 0 | `np.log(ptau217)` |
| 10 | `gfap` | raw audit variable | 40 | carried |
| 11 | `log_gfap` | optional predictor *(derived)* | 40 | `np.log(gfap)` |
| 12 | `nfl` | raw audit variable | 40 | carried |
| 13 | `log_nfl` | optional predictor *(derived)* | 40 | `np.log(nfl)` |
| 14 | `abeta42` | raw audit variable | 2 | carried |
| 15 | `abeta40` | raw audit variable | 2 | carried |
| 16 | `ratio_ab42_ab40` | optional predictor | 2 | `abeta42 / abeta40` |
| 17 | `pre_anchor_dementia_n` | QC only | 0 | carried |
| 18 | `qc_dementia_on_or_before_anchor` | QC only | 0 | carried |
| 19–26 | `eligible_core` … `eligible_full_blood` | analysis-set flags | 0 | derived from availability |

All logarithms are **natural logs via `numpy.log`**. Every observed input to a log or ratio is asserted finite and strictly positive; missing inputs stay missing in the derived output. The recomputed amyloid ratio agrees with the frozen column at `rtol=1e-10, atol=1e-12` with **0 discrepancies** (max abs diff 9.7e-17, max rel diff 1.4e-15).

**Raw biomarker fields (`ptau217`, `gfap`, `nfl`, `abeta42`, `abeta40`) are retained for auditability**, not because they are the intended modeling form. See the prohibitions in §6.

## 4. Analysis sets

Each `eligible_*` flag is `1` when a participant has complete data for **core** (`entry_age + APOE4_COUNT + log_ptau217`, complete for all 401) **plus** the named markers. Flags are derived from observed nonmissingness — never manually assigned — and are strictly `{0,1}` integers.

| Flag | Required features | N | Events | Censored | participant_fraction | event_fraction |
|---|---|---:|---:|---:|---:|---:|
| `eligible_core` | core | **401** | **85** | 316 | 1.0 | 1.0 |
| `eligible_gfap` | core + `log_gfap` | 361 | 85 | 276 | 0.9002493765586035 | 1.0 |
| `eligible_nfl` | core + `log_nfl` | 361 | 85 | 276 | 0.9002493765586035 | 1.0 |
| `eligible_amyloid` | core + `ratio_ab42_ab40` | 399 | 83 | 316 | 0.9950124688279302 | 0.9764705882352941 |
| `eligible_gfap_nfl` | core + `log_gfap` + `log_nfl` | 361 | 85 | 276 | 0.9002493765586035 | 1.0 |
| `eligible_gfap_amyloid` | core + `log_gfap` + ratio | 359 | 83 | 276 | 0.8952618453865336 | 0.9764705882352941 |
| `eligible_nfl_amyloid` | core + `log_nfl` + ratio | 359 | 83 | 276 | 0.8952618453865336 | 0.9764705882352941 |
| `eligible_full_blood` | core + `log_gfap` + `log_nfl` + ratio | **359** | **83** | **276** | 0.8952618453865336 | 0.9764705882352941 |

`participant_fraction = n_participants / 401` and `event_fraction = n_events / 85`, stored as **full-precision numerics** in `mci_survival_analysis_set_counts_v1.tsv` — not rounded, not percentage strings.

### Why the numbers move the way they do

- **GFAP and NfL are missing for exactly the same 40 participants** (identical availability masks, same Quanterix draw). So `eligible_gfap`, `eligible_nfl`, and `eligible_gfap_nfl` are the *same* 361-person set, and adding NfL on top of GFAP costs nothing.
- **Exactly 2 participants are missing the amyloid ratio, and both are events** (RIDs 702 and 4240). That is the entire 85 → 83 event drop.
- **The two missing groups are disjoint** — no participant is missing both. Hence `full_blood = 401 − 40 − 2 = 359`.

## 5. Prior dementia — participants vs. diagnosis records

This has been miscommunicated before, so state it exactly:

| Level | Count | Meaning |
|---|---:|---|
| Anchor cohort **A** | **8** | eight **participants** with ≥1 dementia diagnosis strictly *before* their MCI anchor (Build 1 §6.1) |
| Frozen primary cohort **C** | **4** | four of those eight survive the cohort-C filters: RIDs **467, 4115, 4506, 4706** |
| Diagnosis **records** | **12** | those four carry 12 pre-anchor dementia diagnosis records in total (5 + 4 + 2 + 1) |
| Events among the four | **1** | RID 467 only |

**The previously reported "8" is a count of participants in anchor cohort A.** It is not a record count, and not a count within cohort C. The framing "8 records across 4 participants" is wrong at both levels and is not used anywhere in this build.

- `pre_anchor_dementia_n` — a **participant-level** field whose **value** is a diagnosis-**record** count.
- `qc_dementia_on_or_before_anchor` — a **participant-level binary flag**, equivalent to `pre_anchor_dementia_n > 0`.

**Neither field may be used as a model predictor, and neither may be used to filter this shared dataset.** They exist for QC traceability and for an explicitly-labelled sensitivity analysis only. All four participants are **retained**; adjudication is pending (see `reports/mci_survival_person1_handoff_v1.md`).

## 6. Downstream modeling protocol

**Documented here, deliberately not fitted.** This build performs no model fitting of any kind.

### Model ladder

```text
M0 = entry_age + APOE4_COUNT
M1 = entry_age + APOE4_COUNT + log_ptau217
```

M0 is the demographic/genetic reference. M1 adds the core plasma marker and is the model every biomarker extension is measured against.

### Candidate extensions

Extensions add any combination of:

```text
log_gfap
log_nfl
ratio_ab42_ab40
```

giving seven candidate extended models (3 single + 3 pairs + 1 triple).

### Rule 1 — refit M1 on the identical participant set

For **every** single-feature incremental comparison, refit M1 on **exactly the same participants** as the extended model. Comparing an extended model against an M1 fitted on a larger sample confounds the added feature with a changed sample and is not a valid incremental test.

| Comparison | Eligibility flag | N | Events |
|---|---|---:|---:|
| M1 vs. M1 + `log_gfap` | `eligible_gfap` | **361** | **85** |
| M1 vs. M1 + `log_nfl` | `eligible_nfl` | **361** | **85** |
| M1 vs. M1 + `ratio_ab42_ab40` | `eligible_amyloid` | **399** | **83** |

### Rule 2 — head-to-head ranking on one common subset

To rank **all** biomarker combinations against each other, use the common full-blood subset so every model sees identical data:

```text
eligible_full_blood == 1   ->   N = 359, events = 83, censored = 276
```

Ranking models fitted on different samples is not interpretable; rank only within this subset.

### Rule 3 — refitting after selection

Once a preferred feature set has been chosen, it **may** be refitted on the largest valid sample for its exact required features (e.g. a p-tau217 + amyloid model refits at N = 399). Report the selection sample and the final-fit sample separately.

### Prohibitions

- **Never** include both a raw and a log version of the same biomarker in one model (`ptau217` with `log_ptau217`, `gfap` with `log_gfap`, `nfl` with `log_nfl`). The raw fields exist for auditability.
- **Never** include `APOE4_COUNT` and `APOE4_CARRIER` in the same model — they encode the same variable and are collinear by construction.
- **Never** include `abeta42` or `abeta40` alongside `ratio_ab42_ab40`.
- **Never** use `RID`, `anchor_date`, the QC fields, or any `eligible_*` flag as a predictor.

### Reserved CV seed

`20260722` is reserved for **downstream** cross-validation. This build generates no folds and consumes no randomness.

## 7. Design guarantees (all asserted, 131/131)

- **All 401 participants preserved** — not reduced to any complete-case subset. Optional biomarkers are genuine `NA`.
- **No imputation** — every optional-marker NA count matches the frozen cohort exactly (gfap/nfl/log_gfap/log_nfl 40; abeta/ratio 2).
- **No scaling, standardization, or winsorization** — all raw carried columns byte-identical to the frozen cohort.
- **Outcome carried, not recomputed** — duration and event byte-faithful; durations strictly positive; 85/316 preserved.
- **QC fields carried faithfully**; flag ⇔ `n > 0`; 4 flagged participants **retained**.
- **No cognitive or functional variables, no CV folds, no model fitting, no feature selection.**
- **Deterministic** — no runtime timestamps, no randomness; the dataset, dictionary, counts table, manifest and report all reproduce byte-identically from a clean kernel.

## 8. Integrity

- **131/131 assertions passed.**
- **All 17 frozen v1 artifacts byte-identical** before and after; frozen primary cohort hash unchanged (`a15e2cb8…`).

| Output | SHA-256 |
|---|---|
| `mci_survival_shared_modeling_dataset_v1.tsv` | `521120e76418da5433d840d5301f2ed71686170a7b12a548ca631d950d314a3d` |
| `mci_survival_shared_modeling_data_dictionary_v1.tsv` | `f5e10f5755e109936c67d85fe567f80393d5490e6e67349a816750a2fa120ca2` |
| `mci_survival_analysis_set_counts_v1.tsv` | `2ded88850b629a74a08d05149a40239c20d15b1f1579080407a5550cf50e9995` |

The manifest records these three hashes plus the SHA-256 of this report. A manifest cannot contain its own final hash; verify it externally with `shasum -a 256`.

## 9. How downstream teams use it

```python
import pandas as pd
df = pd.read_csv("outputs/03a_mci_survival_shared_modeling/mci_survival_shared_modeling_dataset_v1.tsv", sep="\t")
assert len(df) == 401 and df.RID.is_unique

# filter to an analysis set with ONE column — no re-derivation of availability
gfap_set = df[df.eligible_gfap == 1]            # 361 / 85 events
full_set = df[df.eligible_full_blood == 1]      # 359 / 83 events  <- head-to-head subset

# duration = time_to_event_or_censor_days | event = event_indicator
# never use RID, anchor_date, QC fields, or eligible_* flags as predictors
# prior-dementia SENSITIVITY analysis only (never the primary filter):
#   df[~df.qc_dementia_on_or_before_anchor]      # drops the 4 flagged participants
```

The shared file is **not** pre-filtered — each team applies the eligibility flag their model needs. Missing optional biomarkers are genuine `NaN`, never imputed.

## 10. Reproduction

```bash
cd /Users/zoeyd/Desktop/Predict_AD_from_Biomarkers
Data/.venv/bin/python -m nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=900 \
  --output <scratch>/run.ipynb \
  notebooks/03a_mci_survival_shared_modeling_dataset.ipynb
```

Writing the executed copy to a scratch path keeps execution metadata out of the committed notebook. Environment: Python 3.14.0, pandas 3.0.1, numpy 2.4.3.

## 11. Scope note

This build does **not**: rejoin raw data · re-anchor · redefine MCI/event/censoring · exclude short-follow-up or prior-dementia participants · impute · scale · winsorize · select features · fit models · add cognitive or functional variables · generate CV folds · modify any Build 1–3 artifact.
