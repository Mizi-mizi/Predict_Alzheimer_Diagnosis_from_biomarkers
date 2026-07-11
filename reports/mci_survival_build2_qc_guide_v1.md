# MCI Survival Cohort — Build 2 Manual QC Guide (`v1`)

**Specification:** `claude_spec_person1_mci_survival_cohort.md` — Person 1, Build 2.
**Date:** 2026-07-11
**Notebook:** [notebooks/01d_mci_survival_manual_qc_packet.ipynb](../notebooks/01d_mci_survival_manual_qc_packet.ipynb)
**Status:** ✅ 34/34 assertions passed. **The frozen v1 cohort is unchanged** (A=535, B=410, C=401); all six Build 1 artifacts were verified **byte-identical** before and after this build.

> **This build reviews. It does not decide.** No participant was excluded, no cohort was revised, and every human-adjudication field in the form is **blank**. Warning flags are pointers for a reviewer — **never** automatic exclusions.

---

## 1. What is in the packet

| File | Rows × Cols | Purpose |
|---|---|---|
| `mci_survival_manual_qc_cases_v1.tsv` | 46 × 56 | One row per selected participant: strata, anchor, outcome, all warning flags, all source-row ids |
| `mci_survival_manual_qc_longitudinal_context_v1.tsv` | 362 × 40 | **Long format.** Every diagnosis and plasma row for every selected participant, annotated with why it was or was not used |
| `mci_survival_manual_qc_form_v1.tsv` | 46 × 30 | The reviewer's worksheet — **13 blank human-review fields** |
| `mci_survival_manual_qc_sampling_summary_v1.tsv` | 10 × 11 | Requested / eligible / priority-band / selected / shortfall / overlap per stratum |

**46 unique participants** (48 selected before de-duplication, 2 in more than one stratum). **362 context rows** — 288 diagnosis, 74 plasma.

---

## 2. How each sampling stratum was constructed

Seed **`20260711`**. Random strata use `np.random.default_rng([20260711, k])` over the **sorted** eligible RID array, so each stratum reproduces independently of the others. Ordered strata use a deterministic sort with `RID` as the final tie-break — no randomness at all. Re-running the sampler in the same notebook produced an identical selection (asserted).

| # | Stratum | Universe | Requested | Eligible | Priority band | Selected |
|---|---|---|---:|---:|---:|---:|
| **S0** | **mandatory — pre-anchor dementia** | anchor cohort | 8 | 8 | 8 | **8** |
| S1 | random — survival cohort | survival cohort | 10 | 410 | 410 | 10 |
| S2 | anchor near ±90 d boundary | anchor cohort | 10 | 535 | **26** | 10 |
| S3 | rapid progression | survival-cohort events | 10 | 86 | **2** | 10 |
| S4 | random — censored | censored | 10 | 324 | 324 | 10 |

- **S0** is derived **programmatically from the Build 1 flag** `qc_dementia_on_or_before_anchor` — never from a hard-coded RID list (asserted).
- **S2** is drawn from the **anchor cohort**, not the survival cohort: anchor-match quality is a property of the anchor, and two selected participants (2200, 6883) never reached the survival cohort — reviewing their anchor is still the point. All 10 selected fall inside the 70–90 d priority band (|offset| ≥ 82 d).
- **S3 has an important shortfall.** Only **2** participants in the entire cohort progressed within the 180-day priority band. Rather than refill from a scientifically different stratum, the stratum was **extended within its own ordering** — the 10 *fastest* progressors, whose event times run 167 → 349 days. **Treat "rapid progression" in this packet as "fastest available", not "≤180 d".**
- Strata were sampled from their natural universes and then de-duplicated, **preserving every applicable label** in the `strata` column (pipe-separated, sorted). Overlaps: RID `2180` (S1 + S4), RID `6696` (S2 + S4).

---

## 3. How to trace any derived value back to a raw row

Every derived date in the frozen cohort carries a **source-row id**. Because only `DXSUM` and `APOERES` ship a native ADNI `ID`, Build 1 generated a deterministic index for every table:

> **`<prefix>_src_row` = the 0-based positional index of the record in the raw CSV as delivered** (row `0` = first data row after the header), assigned immediately after `pd.read_csv`, **before** any filtering, sorting, de-duplication or merging.

To verify any value by hand:

```python
import pandas as pd
raw = pd.read_csv("Data/raw/All_Subjects_DXSUM_05Mar2026.csv")
raw.iloc[EVENT_SRC_ROW]        # <- the exact row that produced event_date
```

| Frozen column | Points at | Raw file |
|---|---|---|
| `anchor_src_row` | the selected plasma draw | `All_Subjects_UPENN_PLASMA_FUJIREBIO_QUANTERIX_05Mar2026.csv` |
| `anchor_dx_src_row` / `anchor_dx_src_id` | the matched MCI diagnosis | `All_Subjects_DXSUM_05Mar2026.csv` |
| `event_src_row` / `event_src_id` | the first post-anchor dementia diagnosis | `All_Subjects_DXSUM_05Mar2026.csv` |
| `censor_src_row` / `censor_src_id` | the last post-anchor non-dementia diagnosis | `All_Subjects_DXSUM_05Mar2026.csv` |
| `age_src_row` | the `entry_age` record | `All_Subjects_My_Table_05Mar2026.csv` |
| `apoe_src_row` / `apoe_src_id` | the APOE genotype record | `All_Subjects_APOERES_05Mar2026.csv` |

The notebook **round-trips every one of these ids back to the raw table for all 535 participants** and asserts the dates and diagnosis labels agree — so traceability is proven, not assumed. In the context table you never need to do this by hand: `source_table` + `source_row_id` are printed on every row, alongside the original `raw_EXAMDATE` and the raw assay values.

---

## 4. How to review an **anchor match**

Filter the context table to one `RID` and read it in date order. You will see **every** plasma draw and **every** diagnosis for that participant.

For each **plasma** row, `selection_reason` tells you exactly why it was or was not eligible:

- `SELECTED ANCHOR: earliest eligible draw (5/5 usable core assays; nearest dx = MCI at +6d)`
- `ALTERNATIVE eligible draw — NOT selected because it is LATER than the anchor (the earliest eligible draw always wins; completeness is never preferred)`
- `NOT ELIGIBLE: nearest diagnosis within ±90d is Dementia (-12d), not MCI`
- `NOT ELIGIBLE: no diagnosis within ±90d of this draw`
- `NOT ELIGIBLE: no usable core assay`

**What to check:**
1. Is the `ANCHOR` row genuinely the **earliest** draw carrying an `ALTERNATIVE eligible` or `SELECTED` tag? *(If an earlier draw is marked eligible, that is a bug — the context reason line says "INVESTIGATE".)*
2. Is the `MATCHED_MCI` diagnosis really the **nearest** MCI within ±90 d? Check `days_from_anchor` on competing MCI rows; any equally-close alternative is tagged `ALTERNATIVE eligible MCI match`.
3. Is `|day_difference|` acceptable clinically? 26 participants sit in the 70–90 d band; 10 of them are in this packet.
4. Was a later, richer draw passed over? That is **correct by design** — the anchor marks *when prediction begins*, so completeness must never influence it.

Set **`qc_anchor_status`** = `PASS` / `FAIL` / `UNCERTAIN`.

---

## 5. How to review **event and censoring** logic

The context table gives you the full post-anchor diagnosis history, so both rules are directly verifiable.

**Event (`event_status = 1`).** The event is the **first** dementia diagnosis **strictly after** the anchor.
- The `EVENT` row is tagged `SELECTED: first post-anchor dementia -> EVENT`.
- **Every earlier post-anchor diagnosis is shown** — scan them and confirm none is a dementia. Later dementia rows are tagged `not used: a later dementia (the event is the FIRST post-anchor dementia)`.

**Censor (`event_status = 0`).** The censor is the **last** post-anchor non-dementia (CN/MCI) visit.
- The `CENSOR` row is tagged `SELECTED: last post-anchor non-dementia -> CENSOR`.
- **Every post-anchor row is shown**, so you can confirm nothing qualifying comes later. Rows after the censor will be undated or unknown/other-coded, with the reason spelled out.
- A censored participant is **not "stable"** — they are simply unobserved after that date.

> ### ⚠️ Read this before reviewing censored cases
> **74 of the 324 censored participants (23%) are censored at the very MCI visit that defined their anchor** (flag `warn_censor_is_anchor_matching_visit`; role tag `MATCHED_MCI|CENSOR`). Their *entire* follow-up is the anchor→matched-MCI interval — **≤ 90 days by construction, median 12 days**. 62 survival-cohort participants have ≤ 30 days of follow-up in total.
>
> This is **algorithmically correct** (the diagnosis date *is* strictly after the anchor date) and no rule was broken. But such participants contribute almost no prospective information, and reviewers and the modeling team should know how much of cohort B is made of them. RID `4706` in this packet is an example (40 days of "follow-up", which is just the anchor→matched-MCI offset). **Flagged, not excluded** — the team decides whether a minimum-follow-up rule is warranted.

Set **`qc_outcome_status`** = `PASS` / `FAIL` / `UNCERTAIN`.

---

## 6. Why pre-anchor dementia matters, and how to adjudicate it

### The scientific problem

This study asks whether plasma p-tau217 predicts **incident** progression from MCI to dementia. That question presumes the participant **does not already have dementia** at the anchor.

If a participant carries a dementia diagnosis **before** the anchor and is later re-coded as dementia, the algorithm records an "event" — but that event may be **re-documentation of prevalent dementia**, not incident progression. Counting it as incident:

- **biases the outcome upward** (a prevalent case is guaranteed to "convert");
- **inflates the apparent predictive value of p-tau217**, because prevalent dementia is exactly the state that drives p-tau217 highest. **This biases the study in favour of its own hypothesis** — the most dangerous direction for a biomarker-prediction claim.

So each of these cases must be adjudicated by a human before the primary analysis is trusted.

### How Build 1 handles them (and why they are still in the cohort)

Spec §2.5 requires that dementia on/before the anchor is never counted as incident progression, and that such cases are *"excluded **or** flagged for adjudication."* Build 1 **flagged** them. Excluding them would have changed a locked scientific rule, which requires team approval. They therefore **remain in the frozen v1 cohort** and are routed here.

### What to look at

For each of the eight, the context table gives the **complete** diagnosis history: earliest diagnosis, every pre-anchor dementia record, everything between the last pre-anchor dementia and the anchor, the matched MCI, and all post-anchor records — each with date, code, label, `VISCODE2`, source-row id, and the adjudication fields `DXCONFID`, `DXNORM`, `DXMCI`, `DXAD`.

> **Limitation:** `DXCONFID` (and `DXNORM`/`DXMCI`/`DXAD`) are populated for only **42 of 288 (15%)** diagnosis rows in this packet — they exist mainly in earlier ADNI phases. For most of these participants **no diagnostic-confidence field is available**, so adjudication rests on the diagnosis sequence itself.

Ask:
1. How many pre-anchor dementia records are there — one isolated code, or a sustained run over years?
2. How long before the anchor was the last one (`days_last_pre_anchor_dementia_to_anchor`)?
3. What happened *between* that dementia and the anchor — a documented return to MCI/CN, or nothing?
4. Is the post-anchor dementia a **new** event, or the **resumption** of a pre-existing state?

Then set `qc_prior_dementia_history_status`, `qc_prior_dementia_record_plausibility`, `qc_incident_event_validity`, `qc_diagnostic_reversion_interpretation`, `qc_primary_cohort_recommendation`, `qc_sensitivity_analysis_recommendation`.

---

## 7. The eight mandatory cases — specific validation

**All 8 identified, all 8 included.** Of these:

| | N | Events |
|---|---:|---:|
| Reach the **survival** cohort (B) | **5** | **2** |
| Reach the **primary** cohort (C) | **4** | **1** |

**Affected primary-cohort event: RID `467` — exactly one.** (RID `10251`, the other pre-anchor-dementia event, is already outside cohort C because APOE4 is missing, so it affects only cohort B's event count.)

| RID | Anchor | Pre-anchor dementia dx | Last dementia → anchor | In B | In C | Event | Follow-up |
|---|---|---:|---:|:--:|:--:|:--:|---:|
| **467** | 2017-09-13 | **5** | 450 d | ✅ | ✅ | **1** | 373 d |
| 4115 | 2024-01-24 | 4 | 726 d | ✅ | ✅ | 0 | 378 d |
| 4506 | 2018-11-15 | 2 | 1331 d | ✅ | ✅ | 0 | 921 d |
| 4706 | 2025-02-20 | 1 | **4296 d** | ✅ | ✅ | 0 | 40 d |
| 6976 | 2025-07-08 | 4 | 719 d | — | — | — | — |
| 7070 | 2025-04-30 | 1 | 371 d | — | — | — | — |
| **10251** | 2024-12-04 | 1 | **30 d** | ✅ | — | **1** | 436 d |
| 10322 | 2024-12-02 | 1 | 35 d | — | — | — | — |

**If the team later excludes all eight** (computed, **not applied**): A 535 → 527 · B 410 → 405 (events 86 → **84**) · C 401 → 397 (events 85 → **84**).

### Three observable patterns — *descriptions, not adjudications*

These are what the timelines show. The reviewer confirms or overturns them; the code takes no position.

**(a) Sustained prevalent dementia, then a late MCI code** — RIDs `467`, `4115`, `4506`, `6976`.
RID **467** is the starkest: `CN ×4 (2006–08) → MCI ×2 (2010–11) → Dementia ×5 consecutive visits (2012, 2013, 2014, 2015, 2016) → MCI (2017-09-19, the anchor match) → Dementia (2018-09-21, counted as the EVENT) → Dementia (2019)`. Five consecutive years of dementia coding, one isolated MCI, then dementia again. **This is the single affected primary-cohort event.**

**(b) Screening-versus-baseline discrepancy** — RIDs `10251`, `10322` (and, at 371 d, `7070`).
Both show `Dementia` at the **screening** visit and `MCI` at the **baseline** visit ~30–35 days later:
RID **10251**: `Dementia (sc, 2024-11-04) → MCI (bl, 2024-12-06) → Dementia (m12, 2026-02-13, EVENT)`.
This looks like a screening/baseline coding discrepancy rather than a true clinical reversion — but only a reviewer can say so.

**(c) Isolated remote dementia code** — RID `4706`.
A single `Dementia` at m12 (2013-05-18), **11.8 years** before the anchor, surrounded by MCI/CN for the following twelve years. A plausible historical coding error — again, the reviewer decides.

---

## 8. Warning flags — prevalence across all 535 anchored participants

**A warning is not an exclusion.** It marks a case worth a human's eyes.

| Flag | N | Note |
|---|---:|---|
| `warn_cognitive_score_after_anchor` | 81 | **informational only** — baseline cognition uses nearest ±90 d and may fall *after* the anchor |
| `warn_censor_is_anchor_matching_visit` | 74 | *extra flag, beyond the 15 required* — see §5 |
| `warn_nonmonotonic_dx_sequence` | 48 | diagnosis severity decreases somewhere in the timeline |
| `warn_anchor_offset_70_90d` | 26 | anchor match near the ±90 d boundary |
| `warn_dementia_before_anchor` | **8** | **the mandatory adjudication stratum** |
| `warn_reversion_sequence_before_anchor` | 8 | dementia followed by a return to CN/MCI before the anchor |
| `warn_dementia_within_180d` | 2 | rapid progression |
| `warn_multiple_equally_close_mci` | 1 | two MCI visits equidistant from the anchor |
| `warn_dementia_within_30d` / `within_90d` | 0 | — |
| `warn_multiple_plasma_rows_on_anchor_date` | 0 | — |
| `warn_conflicting_dx_same_date` | 0 | — |
| `warn_event_and_censor_same_date` | 0 | — |
| `warn_missing_source_row_provenance` | 0 | **full provenance coverage** |

Also carried per participant: `n_pre_anchor_dementia_dx`, `days_last_pre_anchor_dementia_to_anchor`, `n_equally_close_mci_matches`, `n_plasma_rows_on_anchor_date`.

---

## 9. The QC form — allowed values

All 13 human fields ship **blank** (asserted). Nothing is auto-populated.

**General status** — `qc_anchor_status`, `qc_outcome_status`, `qc_overall_status`, `qc_prior_dementia_history_status`, `qc_diagnostic_reversion_interpretation`, `qc_sensitivity_analysis_recommendation`:
`PASS` · `FAIL` · `UNCERTAIN` · `NOT_REVIEWED`

**`qc_prior_dementia_record_plausibility`:**
`PLAUSIBLE_TRUE_DEMENTIA` · `LIKELY_CODING_OR_DATA_ERROR` · `INSUFFICIENT_INFORMATION` · `NOT_APPLICABLE`

**`qc_incident_event_validity`:**
`PLAUSIBLE_INCIDENT_PROGRESSION` · `LIKELY_REDIAGNOSIS_OF_PREVALENT_DEMENTIA` · `POSSIBLE_REVERSION_THEN_PROGRESSION` · `INSUFFICIENT_INFORMATION` · `NOT_APPLICABLE`

**`qc_primary_cohort_recommendation`:**
`RETAIN_PRIMARY` · `EXCLUDE_PRIMARY_RETAIN_SENSITIVITY` · `EXCLUDE_ALL_ANALYSES` · `REQUIRES_TEAM_ADJUDICATION` · `NOT_APPLICABLE`

Free text: `recommended_action`, `reviewer_name`, `review_date` (ISO `YYYY-MM-DD`), `reviewer_notes`.

For participants with no pre-anchor dementia, the four prior-dementia fields should be `NOT_APPLICABLE` — but that is the **reviewer's** entry, not the code's.

---

## 10. How to record completed reviews — **do not edit the blank form**

`mci_survival_manual_qc_form_v1.tsv` is a **frozen template**. Editing it in place destroys the provenance chain and makes the review irreproducible.

**Do this instead:**

1. **Copy** the form to a new, dated, reviewer-stamped file — never overwrite:
   ```
   outputs/01c_mci_survival_cohort_freeze/mci_survival_manual_qc_form_completed_<reviewer>_<YYYYMMDD>_v1.tsv
   ```
2. Fill in **only** the 13 human fields. Do not alter `RID`, dates, flags, or any derived column — those are the evidence being reviewed.
3. Keep one file per reviewer. If two reviewers disagree, keep **both** and resolve in a third adjudication file; do not silently overwrite.
4. Leave the original `mci_survival_manual_qc_form_v1.tsv` **byte-identical**. Its SHA-256 is recorded in the Build 2 outputs and can be re-verified at any time.

---

## 11. If the team decides to exclude participants — how to version the revision

**The v1 freeze must never be edited in place.** Build 1's outputs are hashed and referenced by the modeling team; mutating them would silently invalidate any analysis already run against them.

A revision is a **new version**, produced by a **new notebook**, written to a **new directory**:

```
notebooks/01e_mci_survival_cohort_freeze_v2.ipynb
outputs/01e_mci_survival_cohort_freeze_v2/
    mci_survival_primary_cohort_v2.tsv
    mci_survival_exclusion_log_v2.tsv          # new exclusion reason, e.g. "prevalent dementia at anchor (QC-adjudicated)"
    mci_survival_freeze_provenance_v2.json     # cites the v1 hashes it derives from
reports/mci_survival_v2_revision_report_v1.md  # v1 -> v2 diff: which RIDs, which rule, who approved
```

Required in any v2:
- the **completed QC form** that justifies each exclusion, cited by file and reviewer;
- an explicit **rule statement** (e.g. *"exclude participants with any dementia diagnosis strictly before the anchor"*) recorded as a **rule change with team approval** — Build 1's locked rules cannot be changed silently;
- a **participant-level diff** against v1 (added/removed RIDs, changed event counts);
- **both** cohorts kept on disk so the primary analysis can be reported on v1 with v2 as a **sensitivity analysis** (which is what `EXCLUDE_PRIMARY_RETAIN_SENSITIVITY` is for);
- the v1 hashes recorded in the v2 manifest so the lineage is provable.

**Do not** delete v1. **Do not** renumber v1's files. A frozen dataset that changes is not frozen.

---

## 12. Reproduction

```bash
cd /Users/zoeyd/Desktop/Predict_AD_from_Biomarkers
Data/.venv/bin/python -m nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=900 \
  notebooks/01d_mci_survival_manual_qc_packet.ipynb
```

Seed `20260711`. The notebook re-runs the sampler twice and asserts an identical selection; it also hashes all six Build 1 artifacts before and after execution and asserts they are unchanged.
