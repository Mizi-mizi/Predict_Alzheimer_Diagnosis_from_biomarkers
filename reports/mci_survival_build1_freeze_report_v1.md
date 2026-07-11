# MCI Survival Cohort — Build 1 Freeze Report (`v1`)

**Specification:** `claude_spec_person1_mci_survival_cohort.md` — Person 1, Build 1.
**Date:** 2026-07-11
**Notebook:** [notebooks/01c_mci_survival_cohort_freeze.ipynb](../notebooks/01c_mci_survival_cohort_freeze.ipynb)
**Status:** ✅ **RECONCILED — COHORT FROZEN.** 65/65 assertions passed. All counts match the audit landmarks exactly. Outputs are byte-for-byte deterministic across two independent clean-kernel runs.

---

## 1. Final cohort counts

| Stage | N | Events | Censored | Audit target | Difference |
|---|---:|---:|---:|---:|---:|
| **A** — Broad MCI plasma-anchor | **535** | — | — | 535 | **0** |
| **B** — Survival-follow-up | **410** | **86** | 324 | 410 / 86 | **0 / 0** |
| **C** — Primary complete-case | **401** | **85** | 316 | 401 / 85 | **0 / 0** |

**Attrition, fully reconciled against the participant-level exclusion log:**

```
A  535
     − 125  no usable post-anchor follow-up   (excluded, NOT labelled "stable")
     −   0  invalid / non-positive follow-up
B  410      (86 events, 324 censored)
     −   9  missing APOE4                     (of which 1 is an event)
C  401      (85 events, 316 censored)
```

The B→C drop is **entirely** APOE4 missingness — recomputed, not assumed:

- APOE4 missing in the survival cohort: **9** — RIDs `7079, 10167, 10193, 10251, 10276, 10432, 10441, 10452, 10672`
- Of those, **exactly 1 is an event**: RID `10251` (hence 86 → 85 events)
- `entry_age` missing in the survival cohort: **0**
- `ptau217` missing in the survival cohort: **0**

## 2. Follow-up summary

| | Survival cohort (B, n=410) | Primary cohort (C, n=401) |
|---|---|---|
| Follow-up, median (IQR) days | 420 (229–1111) | 425 (285–1121) |
| Follow-up, median months | 13.8 | 14.0 |
| Follow-up range | 1 – 3694 d | 1 – 3694 d |
| Time-to-dementia among events, median (IQR) | 758 (414–1255) d | 759 (413–1268) d |
| Events by 12 / 24 / 36 months | 15 / 34 / 56 | 15 / 33 / 55 |
| Censored before 24 months | 215 | 207 |

Months use the single documented conversion **`days / 30.4375`** (= 365.25 / 12).

**Censoring is administrative.** No death or loss-to-follow-up table exists in the source data, so participants are censored at their last clinical visit. The censoring mechanism may therefore be **informative** — an inherited limitation, carried forward for the modeling team.

---

## 3. Exactly which rules were implemented

Every scientific rule is inherited **unchanged** from `01b_mci_survival_cohort_audit.ipynb`.

| Rule | Implementation |
|---|---|
| Diagnosis coding | `DXSUM.DIAGNOSIS`: `1=CN, 2=MCI, 3=Dementia`; blank → `unknown/other` (never an event, never a censor) |
| Same-day diagnosis conflict | collapse per `(RID, DATE)` keeping **highest severity** (76 rows collapsed) |
| Missing sentinels | `-4`, `-5` → `NaN` |
| Non-positive assay value | → `NaN` (0 such values found) |
| Diagnosis ↔ plasma alignment | **nearest** MCI diagnosis within **±90 days** (`merge_asof`, `direction="nearest"`) |
| Broad anchor | **earliest** plasma draw with **≥1 usable core assay** (p-tau217/Aβ42/Aβ40/NfL/GFAP) that aligns to MCI. Does **not** require p-tau217, APOE4, age, cognition, a complete panel, or any follow-up |
| Anchor tie-break | earliest plasma `DATE`; plasma pre-deduplicated to one row per `(RID, DATE)` (`keep="first"`); stable original row order. *The spec's secondary tie-breaks are inactive: there is at most one candidate row per (RID, plasma date), so the earliest-date rule fully determines the anchor.* |
| Time origin | plasma anchor date |
| Event | **first** dementia diagnosis **strictly after** the anchor (`DATE > anchor`) — this strict inequality is the leakage guard |
| Censoring | **last** post-anchor non-dementia (CN/MCI) diagnosis date |
| No usable post-anchor follow-up | **excluded** from the survival cohort — never labelled "stable" |
| Primary complete case | survival-eligible **+** `entry_age` **+** `APOE4_COUNT` **+** `ptau217` |
| Age | `entry_age` is authoritative and **undated**; age-at-anchor is **not** derived |
| Imputation / transformation | **none** |

**Code reuse.** `identify_broad_anchor` and `derive_survival` are reused **verbatim** — source-row provenance flows through `merge_asof` automatically or is recovered afterwards by exact `(RID, DATE)` key-joins against the de-duplicated diagnosis history. `align_scores` carries one **additive-only** change: it now also returns the matched score date. The regression assertion below proves the selected *values* are unchanged.

### Source-row provenance

Only `DXSUM` and `APOERES` ship a native ADNI row id (`ID`); **the UPENN plasma panel and `My_Table` have none.** So for every source table we generate:

> **`<prefix>_src_row`** = the **0-based positional index of the record in the raw CSV as delivered** (row 0 = first data row after the header), assigned **immediately after `pd.read_csv`, before any filtering, sorting, de-duplication or merging.**

Carried into every frozen table: `anchor_src_row` (plasma), `anchor_dx_src_row` / `anchor_dx_src_id` (matched MCI dx), `event_src_row` / `event_src_id`, `censor_src_row` / `censor_src_id`, `age_src_row`, `apoe_src_row` / `apoe_src_id`. Native ADNI ids are carried **in addition** wherever they exist, so any row can be traced either way.

---

## 4. Validation — 65 assertions, 65 passed, 0 failed

Assertions **recompute** their targets from source, deliberately using a different code path from the canonical functions, so they are a genuine test rather than a restatement.

| Group | Checks |
|---|---|
| Structure | one row per participant; no missing/duplicate RIDs; deterministic RID sort — in all 3 cohort tables **and** the exclusion log |
| Anchor | every anchor-matched diagnosis is **MCI** (re-read from the source, not the flag); every match within **±90 d** (max observed 90 d) |
| **No leakage** | anchor **==** the earliest eligible MCI-aligned draw for every participant, by **independent recomputation** of the full candidate universe; the candidate universe reproduces the anchor cohort exactly; later, more-complete draws were never preferred |
| Outcome | every survival participant has an event or censor date; **all follow-up strictly positive** (min 1 d); event/censor strictly after the anchor; **every event date is the first post-anchor dementia** (independent recomputation); no censored participant has *any* post-anchor dementia; event participants carry no censor date |
| Censoring | every censored participant is censored at their **last** post-anchor non-dementia visit (independent recomputation); every censoring diagnosis really is CN/MCI in the source |
| Not-stable guard | no-usable-follow-up participants are excluded, carry **no** `event_indicator`, and have no follow-up time |
| Primary cohort | `entry_age`, `APOE4_COUNT`, `ptau217` all nonmissing; `primary_eligible` depends on **nothing else** |
| Secondary independence | participants with missing GFAP (40), NfL (40), Aβ (2), CDRSB (87), MMSE (47), MOCA (88), FAQ (31) **are still retained** in the primary cohort |
| Provenance | every anchor / matched-dx / event / censor row is traceable to a source row; `age_source_date` is structurally absent |
| Reconciliation | exclusion log partitions the anchor cohort (401 + 9 + 125 = 535); flow ↔ log ↔ frozen-table counts agree exactly |
| Explicit checks | B→C drop **is** the 9 APOE4-missing; **exactly 1** of them is an event; `entry_age` and `ptau217` have **zero** missingness in the 410 |
| **Regression vs `01b`** | identical participant set; **0 differing cells** across 25 shared scientific columns × 535 participants |

The regression assertion is the strongest guarantee here: this freeze is not a second implementation with drifted rules — it **reproduces the validated audit exactly**.

---

## 5. Determinism

The notebook was executed end-to-end from a **clean kernel twice**. All five frozen tables are **byte-identical** (SHA-256):

| Output | Rows × Cols | SHA-256 |
|---|---|---|
| `mci_survival_anchor_cohort_v1.tsv` | 535 × 78 | `64e66814726c2263281b25da01c8118f73f77e5e00354bdca2074400cb0aa6ee` |
| `mci_survival_followup_cohort_v1.tsv` | 410 × 78 | `8203a70f7cc8d03053070fa12bb90cf73bb6c20b09416aa61c2a7ba4b7c8086b` |
| `mci_survival_primary_cohort_v1.tsv` | 401 × 78 | `a15e2cb8606f676b3bcfc4d23de72c752779836ce9406b04b01c84394a76e8ad` |
| `mci_survival_exclusion_log_v1.tsv` | 535 × 25 | `a3eafebcdd3e392ba75a7e97da842966d6f8793ac1e43ce1817378c4857fe2ff` |
| `mci_survival_cohort_flow_v1.tsv` | 13 × 5 | `39b88d1a9f6cc3e48dbb605f94a0f11a6be8bf3aa6e90a92b340a513b6b3c8f1` |

The provenance manifest is identical between runs **except** `created_utc` (verified by key-wise diff).

---

## 6. Discrepancies

**Count discrepancies: none.** All of 535 / 410 / 86 / 401 / 85 reproduce exactly, so **no** `mci_survival_count_discrepancy_v1.md` was created and the cohort is declared frozen.

Two items are nonetheless **raised for team decision** — neither changed any rule or count:

### 6.1 ⚠️ Eight participants have a dementia diagnosis *before* their MCI anchor — **flagged, not excluded**

Spec §2.5 requires that a dementia diagnosis **on or before** the anchor is never counted as incident progression, and that such cases are *"excluded **or** flagged for adjudication."* Build 0 identified that `01b` checks only for dementia **on** the anchor date, never **before** it. Recomputing here:

- Dementia **on** the anchor date: **0** participants (structurally impossible — a same-day dementia would be the *nearest* diagnosis, so the draw could not match as MCI).
- Dementia **strictly before** the anchor: **8** participants. These are Dementia → **reversion** → MCI-at-anchor trajectories.

| RID | anchor | prior dementia dx | in B? | in C? | event? | follow-up d |
|---|---|---:|:--:|:--:|:--:|---:|
| 467 | 2017-09-13 | 5 | ✅ | ✅ | **1** | 373 |
| 4115 | 2024-01-24 | 4 | ✅ | ✅ | 0 | 378 |
| 4506 | 2018-11-15 | 2 | ✅ | ✅ | 0 | 921 |
| 4706 | 2025-02-20 | 1 | ✅ | ✅ | 0 | 40 |
| 6976 | 2025-07-08 | 4 | — | — | — | — |
| 7070 | 2025-04-30 | 1 | — | — | — | — |
| 10251 | 2024-12-04 | 1 | ✅ | — | **1** | 436 |
| 10322 | 2024-12-02 | 1 | — | — | — | — |

Because the **locked v1 rules retain these participants**, Build 1 **flags** them (`qc_dementia_on_or_before_anchor`, `pre_anchor_dementia_n`) rather than excluding them — excluding would change a locked rule and needs team approval. Flagging is explicitly permitted by §2.5.

**Why this matters scientifically:** 5 of the 8 reach the survival cohort and **2 carry an "event"** that is plausibly a *re-diagnosis of prevalent dementia*, not incident progression. Within the **primary cohort**, exactly **one** event is affected — **RID 467** (RID 10251 is already out of C for missing APOE4).

**Impact if the team later decides to exclude them** (computed, **not applied**): A 535→527, B 410→405, events 86→84, C 401→397, primary events 85→84.

**Recommendation:** route all 8 into the Build 2 QC packet for human adjudication; they are already flagged in every frozen table.

### 6.2 p-tau181 — not integrated (per Build 1 decision)

`ptau181` is deliberately **absent** from the frozen schema. It exists only in `All_Subjects_FNIHBC_BLOOD_BIOMARKER_TRAJECTORIES_05Mar2026.csv` (long format; two platforms — `QX_plasma_ptau181` Quanterix/SIMOA and `Roche_plasma_ptau181` Elecsys), a sub-study overlapping only **40/535** anchor participants (**33/410** survival-eligible). Its absence has **no effect** on broad-anchor, survival, or primary eligibility. Any future p-tau181 secondary analysis would rest on ~33 participants with very few events and needs a documented platform + alignment decision — recorded here for later secondary-analysis review.

### 6.3 Minor timing caveat carried forward (no rule changed)

Baseline cognition is aligned with `direction="nearest"` within ±90 d, so a score may fall **up to +88 days *after*** the anchor (observed maximum). This is `01b`'s existing rule and is **unchanged**; Build 1 now exposes `cdrsb_offset_days`, `mmse_offset_days`, `moca_offset_days`, `faq_offset_days` so Build 3 can audit it. **No cognitive variable was selected.**

---

## 7. Confirmation: no scientific rule was changed

- ✅ Diagnosis codes, sentinels, non-positive-assay handling, ±90 d nearest-MCI alignment, ≥1-usable-core-assay broad anchor, earliest-eligible-plasma-date selection with stable tie-break, strictly-post-anchor event/censoring, no imputation — **all preserved verbatim**.
- ✅ Proven by the regression assertion: **0 differing cells** vs the `01b` master across 25 shared scientific columns × 535 participants.
- ✅ The only additions are **provenance and QC columns** (source-row ids, absolute day-diff, match type, cognition dates/offsets, pre-anchor-dementia flags, inclusion/exclusion fields). No addition participates in any inclusion rule.
- ✅ No prior artifact was overwritten. `01b`'s notebook and all of `outputs/01b_mci_survival_cohort_audit/` retain their original 2026-07-02 timestamps.

---

## 8. Output paths

**Frozen data** — `outputs/01c_mci_survival_cohort_freeze/`

| File | Contents |
|---|---|
| `mci_survival_anchor_cohort_v1.tsv` | Cohort **A**, 535 × 78 |
| `mci_survival_followup_cohort_v1.tsv` | Cohort **B**, 410 × 78 |
| `mci_survival_primary_cohort_v1.tsv` | Cohort **C** — **the authoritative modeling table**, 401 × 78 |
| `mci_survival_exclusion_log_v1.tsv` | 535 × 25 — final stage + reason for every anchor participant |
| `mci_survival_cohort_flow_v1.tsv` | 13 × 5 — cohort flow, reconciles exactly to the log |
| `mci_survival_freeze_provenance_v1.json` | Manifest: git commit/dirty, source SHA-256s, locked rules, parameters, counts, output SHA-256s, all 65 assertion results, environment |

**Report** — `reports/mci_survival_build1_freeze_report_v1.md` (this file)
**Notebook** — `notebooks/01c_mci_survival_cohort_freeze.ipynb`

### For the modeling owner (Person 2) — provisional, formalised in Build 4

```
file      : outputs/01c_mci_survival_cohort_freeze/mci_survival_primary_cohort_v1.tsv
N         : 401   (85 events, 316 censored)
duration  : time_to_event_or_censor_days     (months = days / 30.4375)
event     : event_indicator                  (1 = dementia, 0 = censored)
Model 0   : entry_age + APOE4_COUNT
Model 1   : entry_age + APOE4_COUNT + ptau217
```

Raw units are preserved; **no transformation, scaling or imputation has been applied** — those decisions belong to the modeling phase. `age_at_anchor_approx` is **provenance only and must not be used** as the model's age variable.

---

## 9. Reproduction

```bash
cd /Users/zoeyd/Desktop/Predict_AD_from_Biomarkers
Data/.venv/bin/python -m nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=900 \
  notebooks/01c_mci_survival_cohort_freeze.ipynb
```

Environment: Python 3.14.0, pandas 3.0.1, numpy 2.4.3. Recorded seed `20260711` (no sampling occurs in Build 1).
