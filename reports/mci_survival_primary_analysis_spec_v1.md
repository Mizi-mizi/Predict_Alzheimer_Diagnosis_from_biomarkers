# MCI → Dementia Survival Study — Primary Analysis Specification (`v1`)

**Prepared by:** Person 1 (data/cohort owner) · **For:** Person 2 (modeling owner)
**Date:** 2026-07-11
**Frozen cohort:** `outputs/01c_mci_survival_cohort_freeze/` (v1)

This document defines the analysis **without fitting it**. Its purpose is to prevent silent redefinition of the population, the anchor, the outcome, or the inclusion rules. Every number below is recomputed from the frozen artifacts.

---

## 1. Research question

> **Among individuals with MCI, does baseline plasma p-tau217 improve prediction of time to dementia beyond entry age and APOE4 count?**

---

## 2. Study population

| Stage | Rule | N |
|---|---|---:|
| **A — Broad MCI plasma anchor** | Earliest eligible plasma draw with **≥1 usable core assay**, whose **nearest** diagnosis within **±90 days** is **MCI** | **535** |
| **B — Survival-follow-up** | A, **plus** ≥1 usable post-anchor diagnosis (an event or a valid censoring visit) | **410** (86 events) |
| **C — Primary complete-case** | B, **plus** nonmissing `entry_age`, `APOE4_COUNT`, `ptau217` | **401** (85 events) |

**Broad-anchor assay eligibility** requires only **one** usable assay among p-tau217 / Aβ42 / Aβ40 / NfL / GFAP. It does **not** require p-tau217, APOE4, age, cognition, a complete panel, or any follow-up — the anchor marks *when prediction begins*, so nothing downstream may influence it.

**The A → B drop (125)** is participants with **no usable post-anchor follow-up**. They are **excluded**, never labelled "stable".
**The B → C drop (9)** is **entirely APOE4 missingness** (`entry_age` and `ptau217` have **zero** missingness in B). One of the nine is an event, hence 86 → 85.

---

## 3. Baseline (the anchor)

The **plasma anchor date** is the survival time origin (`t = 0`).

- It is the **earliest** eligible draw. **A later or more complete plasma draw is never preferred.** Selecting a richer later draw would let future information determine baseline — the defining leakage failure this design exists to prevent.
- Tie-break: earliest plasma date; plasma is pre-deduplicated to one row per `(RID, date)`; stable original row order.
- Diagnosis alignment: **nearest** MCI diagnosis within **±90 days** (may fall before *or* after the draw; see `align_offset_days`).

---

## 4. Outcome

| Element | Definition |
|---|---|
| **Event** | The **first** dementia diagnosis occurring **strictly after** the anchor (`date > anchor_date`). `event_indicator = 1`. |
| **Event time** | Days from the anchor to that diagnosis. |
| **Censoring** | No post-anchor dementia → censor at the **last** post-anchor **non-dementia (CN/MCI)** diagnosis. `event_indicator = 0`. |
| **No usable post-anchor follow-up** | **Excluded from the survival cohort.** Never coded as `0`. |
| **Short follow-up** | **Retained as ordinary censoring in frozen v1.** A censored participant with 12 days of follow-up is a legitimate censored observation, not a "non-progressor". |

The strict `> anchor_date` inequality is the leakage guard. Censoring is **administrative** (last clinical visit) — no death or loss-to-follow-up table exists in the source data, so the censoring mechanism **may be informative**. Interpret survival estimates accordingly.

---

## 5. Primary comparison

```r
# Model 0 — reference
Surv(time_to_event_or_censor_days, event_indicator) ~ entry_age + APOE4_COUNT

# Model 1 — does p-tau217 add anything?
Surv(time_to_event_or_censor_days, event_indicator) ~ entry_age + APOE4_COUNT + ptau217
```

### Both models use **exactly the same 401 participants and 85 events**

This is important and was verified, not assumed. Because **`ptau217` is never missing** in the plasma panel, adding it to Model 0 causes **zero complete-case sample loss**. The two models are therefore fitted on an **identical participant set**, and any difference between them is attributable to the predictor — **not** to a different sample.

Had p-tau217 been missing for some participants, Model 0 and Model 1 would have been fitted on different people and the comparison would have been confounded by selection. It is not.

**Events per predictor:** 85 / 3 ≈ 28 — comfortable for an ordinary Cox model.

---

## 6. Secondary-analysis feasibility

Mechanically observed availability only. **None of this claims predictive value.**

### GFAP — the cheapest addition

- **361 participants, 85 events** — **all 85 primary events retained.**
- Loses 40 participants (all censored), **zero events**.
- Measured on the anchor draw (offset 0), single platform (Quanterix).
- **Feasible as a limited secondary addition. No predictive claim is made or implied.**

### Aβ42/Aβ40 ratio

- **399 participants, 83 events** (loses 2 participants and **2 events**).
- `ratio_ab42_ab40 = AB42_F / AB40_F`. **Both components come from the same raw plasma row** — same participant, draw, date and platform (Fujirebio) — so a compatibility mismatch is structurally impossible.
- 0 zero denominators, 0 non-positive denominators, 0 infinite/undefined ratios.
- Raw `abeta42` and `abeta40` are preserved and **must** remain so. The vendor's `AB42_AB40_F` is kept separately (agrees to 5×10⁻⁵) and must **not** be substituted.

### Cognition — no final variable is designated

Complete-case counts for `age + APOE4 + ptau217 + <cognition>`, **events in parentheses**:

| Variable | ±90 d *(current frozen rule)* | On/before anchor | ±30 d | Same-day only | Post-anchor values |
|---|---|---|---|---|---:|
| `MMSCORE` (MMSE, global) | 354 (81) | **337 (81)** | 202 (46) | 79 **(4)** | 17 (max +83 d) |
| `FAQTOTAL` (FAQ, **function**) | 370 (81) | 320 (75) | 350 (81) | 211 (51) | **51** (max +88 d) |
| `CDRSB` (CDR-SB, staging) | 314 (50) | 299 (50) | 178 (26) | 75 **(3)** | 15 (max +83 d) |
| `MOCA` (MoCA, global) | 313 (41) | 289 (39) | 294 (41) | 179 (17) | 24 (max +49 d) |
| `CDMEMORY` + `CDJUDGE` (tier-2) | 314 (50) | 299 (50) | 178 (26) | 75 (3) | 15 |

**Separations the team must keep in view:**
- **Current ±90 d values may be measured AFTER the blood draw** — up to **+88 days**. This is a genuine leakage concern for a *prediction* model.
- **On-or-before-anchor removes 100% of the leakage** and costs **zero events** for `MMSCORE` (82→82) and `CDRSB` (51→51).
- **Same-day-only is not viable** for CDRSB (3 events) or MMSCORE (4 events) — CDR and MMSE are administered on a different visit schedule from the blood draw.
- **Unresolved `-1` sentinel:** raw MMSE (14) and FAQ (32) contain a `-1` *not-done* code that the pipeline's `-4/-5` sentinel rule does **not** cover, and sentinel cleaning is never applied to cognition at all. **No `-1` reached frozen v1** — but the rule must be fixed before any cognitive variable is adopted.
- **No validated memory or executive composite exists** in the available data (no ADAS/RAVLT/UWNPSYCHSUM). `CDMEMORY` and `CDJUDGE` are CDR **box scores**; `CDJUDGE` is an executive **proxy**, not a validated executive measure, and neither is in the frozen pipeline.

**No cognitive variable is approved as a primary predictor. Build 3 deliberately did not choose one.**

### p-tau181 — not usable

| Platform | Any measurement ∩ cohort C | **Within ±90 d of the anchor** | Events |
|---|---:|---:|---:|
| Quanterix (SIMOA) | 25 | **1** | 1 |
| Roche (Elecsys) | 32 | **3** | 1 |

p-tau181 exists only in the FNIHBC sub-study, which barely overlaps this cohort — and of the participants who have *any* p-tau181, essentially **none had it drawn near their plasma anchor**. A baseline covariate must be measured at baseline.

**Platform-specific anchor-aligned availability is too small for a meaningful survival model.** Quanterix and Roche are kept **strictly separate**; **no platform merging, conversion, averaging, or prioritisation** is permitted. **Do not include p-tau181 in planned primary or routine secondary modeling.** This is a mechanical conclusion — the observations do not exist — not a scientific judgement.

---

## 7. Sensitivity scenarios — documented, **not adopted**

Frozen v1 remains the primary cohort. These are recomputed feasibility scenarios only.

| Scenario | Survival N | Events | Primary N | Primary events |
|---|---:|---:|---:|---:|
| **Frozen v1 (primary)** | **410** | **86** | **401** | **85** |
| Exclude any pre-anchor dementia history | 405 | 84 | **397** | **84** |
| Min. observed follow-up ≥ 30 d | 349 | 86 | 342 | 85 |
| ≥ 90 d | 329 | 86 | 325 | 85 |
| ≥ 180 d | 314 | 86 | 310 | 85 |
| ≥ 365 d | 286 | 86 | 284 | 85 |
| ≥ 730 d | 195 | 86 | 194 | 85 |
| Exclude censor-is-anchor-matching-visit | 336 | 86 | 330 | 85 |
| Alternative cognition timing | see §6 | | | |

> **Methodological warning.** Minimum-follow-up restrictions **condition on post-baseline information** (how long someone happened to be observed). That is selection on the future and can bias a prediction model. **They must not replace ordinary right-censoring in the primary survival analysis.** Ordinary censoring is precisely the mechanism that handles variable follow-up correctly. Run these only as explicitly-labelled sensitivity analyses, if at all.

---

## 8. Modeling decisions **intentionally deferred** to Person 2

Person 1 has deliberately not decided any of the following. Each is recorded as `UNRESOLVED` in `mci_survival_freeze_manifest_v1.json`.

| # | Deferred decision |
|---|---|
| 1 | **Ordinary vs penalized Cox** (85 events / 3 predictors ≈ 28 EPP — penalization is a judgement, not a data constraint) |
| 2 | **p-tau217 transformation** (raw pg/mL are right-skewed; a log transform is likely but is *your* call) |
| 3 | **Standardization / centering** |
| 4 | **Internal validation method** (bootstrap, cross-validation, …) |
| 5 | **Prediction horizon** (events by 12/24/36 months = 15/33/55 of 85) |
| 6 | **Calibration method** |
| 7 | **Risk-group thresholds** (no cutoff of any kind has been selected) |
| 8 | **Final prior-dementia adjudication** (human QC review pending — see the handoff report) |
| 9 | **Final cognition timing rule and `-1` sentinel rule** |

**No transformation, scaling, or imputation has been applied anywhere in Person 1's outputs.** All values are raw. If you standardize or impute, do it **inside resampling folds only**.

---

## 9. Non-negotiables

- **Do not** redefine the anchor, the event, or the censoring rule.
- **Do not** drop short-follow-up censored participants from the primary analysis (that is a new methodological rule requiring team approval).
- **Do not** substitute `age_at_anchor_approx` for `entry_age` — it rests on an undocumented assumption.
- **Do not** substitute p-tau181 for p-tau217.
- **Do not** edit frozen v1. Any revision is a **new version** in a new directory (see the handoff report).
