# Person 1 → Person 2 Handoff (`v1`)

**MCI → dementia survival cohort — frozen, validated, and ready for modeling.**
**Date:** 2026-07-11 · **Prepared by:** Person 1 (data/cohort owner)

---

# Modeling quick start

**Load this file:**
`outputs/01c_mci_survival_cohort_freeze/mci_survival_primary_cohort_v1.tsv`  *(tab-separated)*

**Sample size:**
**401** participants

**Events:**
**85** (316 censored)

**Duration column:**
`time_to_event_or_censor_days`

**Event column:**
`event_indicator`  *(1 = dementia observed, 0 = right-censored)*

**Baseline predictors:**
`entry_age`, `APOE4_COUNT`

**Primary biomarker:**
`ptau217`

**Do not:**
repeat raw-data joins · redefine the anchor · redefine event/censoring · drop short-follow-up censored participants from the primary analysis · substitute p-tau181 · substitute `age_at_anchor_approx` for `entry_age` · edit frozen v1.

```python
import pandas as pd
df = pd.read_csv("outputs/01c_mci_survival_cohort_freeze/mci_survival_primary_cohort_v1.tsv", sep="\t")
assert len(df) == 401 and df.RID.nunique() == 401
assert int((df.event_indicator == 1).sum()) == 85
assert df[["entry_age", "APOE4_COUNT", "ptau217"]].notna().all().all()
assert (df.time_to_event_or_censor_days > 0).all()
# Model 0: Surv(time_to_event_or_censor_days, event_indicator) ~ entry_age + APOE4_COUNT
# Model 1: Surv(time_to_event_or_censor_days, event_indicator) ~ entry_age + APOE4_COUNT + ptau217
```

**Model 0 and Model 1 use the identical 401 participants and 85 events** — `ptau217` is never missing, so adding it costs no sample. The comparison is not confounded by different participant sets.

---

## 1. Package contents

**`outputs/01c_mci_survival_cohort_freeze/`**

| Build | File | Rows × Cols |
|---|---|---|
| 1 | **`mci_survival_primary_cohort_v1.tsv`** ⭐ | 401 × 78 |
| 1 | `mci_survival_followup_cohort_v1.tsv` | 410 × 78 |
| 1 | `mci_survival_anchor_cohort_v1.tsv` | 535 × 78 |
| 1 | `mci_survival_exclusion_log_v1.tsv` | 535 × 25 |
| 1 | `mci_survival_cohort_flow_v1.tsv` | 13 × 5 |
| 1 | `mci_survival_freeze_provenance_v1.json` | — |
| 2 | `mci_survival_manual_qc_cases_v1.tsv` | 46 × 56 |
| 2 | `mci_survival_manual_qc_longitudinal_context_v1.tsv` | 362 × 40 |
| 2 | `mci_survival_manual_qc_form_v1.tsv` *(blank — awaiting review)* | 46 × 30 |
| 2 | `mci_survival_manual_qc_sampling_summary_v1.tsv` | 10 × 11 |
| 3 | `mci_survival_feature_missingness_v1.tsv` | 16 × 35 |
| 3 | `mci_survival_model_complete_case_counts_v1.tsv` | 42 × 18 |
| 3 | `mci_survival_feature_timing_v1.tsv` | 40 × 33 |
| 3 | `mci_survival_feature_scenario_counts_v1.tsv` | 12 × 19 |
| 3 | `mci_survival_ptau181_platform_availability_v1.tsv` | 4 × 14 |
| 4 | **`mci_survival_data_dictionary_v1.tsv`** | 78 × 18 |
| 4 | **`mci_survival_freeze_manifest_v1.json`** | — |

**`reports/`** — `mci_survival_build0_inventory_v1.md`, `..._build1_freeze_report_v1.md`, `..._build2_qc_guide_v1.md`, `..._build3_feature_audit_v1.md`, `..._primary_analysis_spec_v1.md`, `..._person1_handoff_v1.md` (this file).

**`notebooks/`** — `01c` (freeze) · `01d` (QC packet) · `01e` (feature audit) · `01f` (handoff). `01b` is the original audit, kept read-only for regression.

## 2. Authoritative file hierarchy

1. **`mci_survival_primary_cohort_v1.tsv`** — **THE modeling input.** Load this and nothing else.
2. `mci_survival_followup_cohort_v1.tsv` — the survival cohort (410). Use only if you deliberately model a different complete-case set.
3. `mci_survival_anchor_cohort_v1.tsv` — the full anchor cohort (535). Reference/QC.
4. `mci_survival_exclusion_log_v1.tsv` — why each of the 535 did or did not reach the primary cohort.
5. `mci_survival_data_dictionary_v1.tsv` — what every one of the 78 columns means.

Everything else is provenance, QC, or feasibility evidence.

## 3. Cohort flow

```
Total DXSUM participants                      3789
  Participants with >=1 dated MCI diagnosis   1801
  Participants with >=1 usable plasma draw    1615
A. Broad MCI plasma-anchor cohort              535
     - 125  no usable post-anchor follow-up  (EXCLUDED, never called "stable")
     -   0  invalid/non-positive follow-up
B. Survival-follow-up cohort                   410   (86 events, 324 censored)
     -   9  missing APOE4                     (1 of them is an event)
C. Primary complete-case cohort                401   (85 events, 316 censored)
```

The **B → C drop is entirely APOE4 missingness.** `entry_age` and `ptau217` have **zero** missingness in the survival cohort.

## 4. Exact counts

| | N | Events | Censored |
|---|---:|---:|---:|
| **Primary cohort (C)** | **401** | **85** | 316 |

Follow-up: median **425 days** (IQR 285–1121), range 1–3694. Events by 12 / 24 / 36 months: **15 / 33 / 55**.

## 5. Exact modeling columns

| Purpose | Column | Type | Notes |
|---|---|---|---|
| Duration | `time_to_event_or_censor_days` | float | strictly positive; days from anchor |
| Event | `event_indicator` | int | **1** = dementia, **0** = censored |
| Predictor | `entry_age` | float | years; **undated** (see caveats) |
| Predictor | `APOE4_COUNT` | float | 0 / 1 / 2 ε4 alleles |
| Predictor | `ptau217` | float | **raw pg/mL**, Fujirebio; **no transformation applied** |

`time_to_event_or_censor_months` = days / 30.4375 is provided for reporting. **Model the days column; do not model both.**

Only these **5** columns are marked `authoritative_for_modeling = TRUE` in the data dictionary. Everything else is provenance, QC, or a secondary candidate.

## 6. Raw vs derived

- **Raw** (as delivered by the source, sentinel-cleaned only): `entry_age`, `GENOTYPE`, `ptau217`, `gfap`, `nfl`, `abeta42`, `abeta40`, `CDRSB`, `MMSCORE`, `MOCA`, `FAQTOTAL`, all dates and viscodes.
- **Derived**: `APOE4_COUNT` (count of `'4'` in `GENOTYPE`), `ratio_ab42_ab40` (Aβ42/Aβ40), `time_to_event_or_censor_days`, `event_indicator`, all `*_offset_days`, all `*_src_row` indices, all flags.
- **No value has been transformed, scaled, winsorized, or imputed anywhere.**

## 7–9. Recommended load checks

```python
import pandas as pd
df = pd.read_csv("outputs/01c_mci_survival_cohort_freeze/mci_survival_primary_cohort_v1.tsv", sep="\t")

# shape and identity
assert df.shape == (401, 78)
assert df.RID.is_unique and df.RID.notna().all()          # participant-ID uniqueness

# outcome integrity
assert int((df.event_indicator == 1).sum()) == 85
assert set(df.event_indicator.unique()) <= {0, 1}
assert (df.time_to_event_or_censor_days > 0).all()

# missingness: predictors complete, secondaries deliberately not
assert df[["entry_age", "APOE4_COUNT", "ptau217"]].isna().sum().sum() == 0
assert df.gfap.isna().sum() == 40      # secondary missingness is EXPECTED and must not be imputed
```

## 10. Known caveats

1. **`entry_age` is UNDATED.** It is age at **study entry**, not at the anchor — and the anchor can be years later (median 0.14 y, 90th percentile 7.1 y). The source (`My_Table`) has **no date column**, so age-at-anchor is **not validly reconstructable**. No date or offset was fabricated. `age_at_anchor_approx` exists but rests on an **undocumented assumption** — **do not use it as the model's age variable.**
2. **Censoring is administrative.** No death or loss-to-follow-up table exists, so participants are censored at their last clinical visit. The censoring mechanism **may be informative**.
3. **`ptau217` is raw, right-skewed pg/mL.** A log transform is likely appropriate but is **your decision**, taken inside resampling folds.
4. **No sex, education, race, or comorbidity variables exist** anywhere in the source data. `entry_age` is the only demographic.
5. **Cognitive `-1` sentinel gap.** Raw MMSE (14) and FAQ (32) contain a `-1` *not-done* code that the `-4/-5` sentinel rule does not cover; sentinel cleaning is never applied to cognition. **No `-1` reached v1** — but fix the rule before adopting any cognitive variable.
6. **Cognition may be measured AFTER the anchor** (up to +88 days) under the current ±90 d nearest-alignment rule. See §12.

## 11. Unresolved QC — **read this before modeling**

### Eight participants have a dementia diagnosis BEFORE their MCI anchor

Frozen v1 **includes** them. They are **flagged, not excluded.**

| | N | Events |
|---|---:|---:|
| In the broad-anchor cohort (A) | **8** | — |
| In the survival cohort (B) | **5** | **2** |
| In the **primary cohort (C)** | **4** | **1** |

**The affected primary-cohort event is RID `467`** — verified from the artifacts. Its timeline: `CN ×4 (2006–08) → MCI ×2 (2010–11) → **Dementia ×5 consecutive visits (2012–2016)** → one MCI (2017-09-19, the anchor match) → Dementia (2018-09-21, counted as the EVENT)`.

**Why this matters:** for an *incident* MCI→dementia study, a post-anchor dementia code in someone with prior dementia may be **re-documentation of prevalent disease**, not incident progression. Counting it as incident biases the outcome upward — and biases it in the direction that **flatters p-tau217**, since prevalent dementia is exactly the state that drives p-tau217 highest.

**Status and rules:**
- These cases are **flagged but NOT automatically excluded**. Column: `qc_dementia_on_or_before_anchor`.
- **Human adjudication remains PENDING.** `mci_survival_manual_qc_form_v1.tsv` is **blank**; no completed reviewed QC form exists.
- **Frozen v1 must remain unchanged.**
- **RID 467 is NOT labelled invalid.** No case may be called definitively invalid without a completed team adjudication record.
- A prior-dementia exclusion **scenario** gives a primary cohort of **397 participants / 84 events** (recomputed from `mci_survival_feature_scenario_counts_v1.tsv`, not hard-coded). **This is a scenario, not a decision.**
- **Any revised cohort must be created as a NEW VERSION** — new notebook, new directory, new `_v2` filenames, citing the v1 hashes it derives from. Do not edit v1. See `reports/mci_survival_build2_qc_guide_v1.md` §11.

### Short follow-up — legitimate censoring, not "stable"

- **74** censored participants have their **censor date equal to the MCI visit used for anchor alignment** — their entire follow-up is the anchor-matching interval (**≤90 days by construction; median 12 days**).
- **62** survival-cohort participants have **≤30 days** of total observed follow-up.
- These are **legitimate right-censored observations under frozen v1.** They **must not be called stable** and **must not be dropped from the primary analysis** — ordinary censoring is precisely the mechanism that handles them correctly.
- **Excluding them would be a NEW methodological rule** requiring team approval. Threshold-based cohorts are **sensitivity scenarios only**, and conditioning inclusion on future follow-up is selection on post-baseline information.

## 12. Feasible secondary additions

| Addition | N | Events | Verdict |
|---|---:|---:|---|
| **+ GFAP** | **361** | **85** | Cheapest by far — loses 40 participants, **zero events**. On the anchor draw, single platform. |
| + Aβ42/Aβ40 ratio | 399 | 83 | Loses only 2 participants but **2 events**. Both components from the same raw row. |
| + MMSE (`MMSCORE`), on/before anchor | 337 | 81 | No leakage by construction; costs 4 events. |
| + FAQ (`FAQTOTAL`), ±90 d | 370 | 81 | Best coverage but **51 post-anchor values** (max +88 d). Measures *function*, not cognition. |

**No cognitive variable is approved as a primary predictor, and none has been selected.** Availability under every timing rule is in `mci_survival_model_complete_case_counts_v1.tsv`.

## 13. Infeasible / discouraged — based on data availability alone

| Addition | N | Events | Why |
|---|---:|---:|---|
| **+ p-tau181 (Quanterix)** | **1** | 1 | **No data.** Only 1 primary-cohort participant has p-tau181 within ±90 d of their anchor. |
| **+ p-tau181 (Roche)** | **3** | 1 | **No data.** Only 3. |
| + CDR-SB | 314 | **50** | Loses **35 of 85 events**. |
| + MoCA | 313 | **41** | Loses **44 of 85 events** — the most expensive option. |

**Do not combine the p-tau181 platforms** to boost N. They are separate assays and must remain separate; merging, averaging, converting, or prioritising them is not permitted.

## 14. Reproducibility

Reproduces the entire Person 1 package from the frozen source data. It **fails on any notebook error**.

```bash
cd /Users/zoeyd/Desktop/Predict_AD_from_Biomarkers
set -e
for nb in 01c_mci_survival_cohort_freeze \
          01d_mci_survival_manual_qc_packet \
          01e_mci_survival_feature_availability_audit \
          01f_mci_survival_handoff_package; do
  Data/.venv/bin/python -m nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=1200 "notebooks/${nb}.ipynb" || exit 1
done
```

`01b` is **not** rerun — it is the original audit, read only for a regression check. Environment: Python 3.14.0, pandas 3.0.1, numpy 2.4.3 (`Data/.venv`). Every notebook was executed twice from a clean kernel and produces **byte-identical** outputs (the manifest's `created_utc` is the sole documented exception).

## 15. Integrity — confirm your modeling input has not changed

```bash
shasum -a 256 outputs/01c_mci_survival_cohort_freeze/mci_survival_primary_cohort_v1.tsv
```

| File | SHA-256 |
|---|---|
| **`mci_survival_primary_cohort_v1.tsv`** ⭐ | `a15e2cb8606f676b3bcfc4d23de72c752779836ce9406b04b01c84394a76e8ad` |
| `mci_survival_followup_cohort_v1.tsv` | `8203a70f7cc8d03053070fa12bb90cf73bb6c20b09416aa61c2a7ba4b7c8086b` |
| `mci_survival_anchor_cohort_v1.tsv` | `64e66814726c2263281b25da01c8118f73f77e5e00354bdca2074400cb0aa6ee` |
| `mci_survival_exclusion_log_v1.tsv` | `a3eafebcdd3e392ba75a7e97da842966d6f8793ac1e43ce1817378c4857fe2ff` |
| `mci_survival_data_dictionary_v1.tsv` | `08465c1e129c67707155cee83373f302a40c5de5271d801a4a12af3f420f6b0a` |

**If the primary-cohort hash differs from the value above, your modeling input has changed — stop and reconcile before fitting anything.**

`mci_survival_freeze_manifest_v1.json` carries the SHA-256 of every source file, notebook, and output. It **cannot contain its own hash** (a file cannot hash itself), so verify it externally; note its hash changes on regeneration solely because of the `created_utc` field. Notebook hashes are recorded as `source_sha256` (a hash of the code cells), which is stable across executions — file hashes change whenever `nbconvert --inplace` rewrites stored outputs.

---

## Person 1 status

| | |
|---|---|
| **Computational handoff** | ✅ **COMPLETE.** The cohort is frozen, validated, documented, and reproducible. Person 2 can begin modeling immediately with no raw-data joins. |
| **Human prior-dementia adjudication** | ⏳ **PENDING.** 8 flagged cases (4 in the primary cohort, 1 event — RID 467) await clinical review. The QC form is blank. Frozen v1 is usable now; the adjudication may later motivate a **v2 sensitivity cohort** (~397 / 84). |
| **Downstream modeling** | ⛔ **NOT STARTED.** No model has been fitted; no hazard ratio, C-index, calibration, or risk group has been computed. That is Person 2's work. |

**9 scientific decisions are recorded as `UNRESOLVED`** in the manifest — prior dementia, post-anchor cognition, the `-1` sentinel rule, cognitive variable selection, biomarker transformation, prediction horizon, penalized vs ordinary Cox, minimum-follow-up sensitivity analyses, and risk-group definition. **Person 1 has deliberately answered none of them.**
