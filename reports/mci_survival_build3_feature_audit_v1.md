# MCI Survival Cohort — Build 3 Feature Availability & Missingness Audit (`v1`)

**Specification:** `claude_spec_person1_mci_survival_cohort.md` — Person 1, Build 3.
**Date:** 2026-07-11
**Notebook:** [notebooks/01e_mci_survival_feature_availability_audit.ipynb](../notebooks/01e_mci_survival_feature_availability_audit.ipynb)
**Status:** ✅ 34/34 assertions passed. Frozen cohort **unchanged** (A=535, B=410/86, C=401/85). All ten Build 1 + Build 2 artifacts verified **byte-identical**. Outputs **deterministic** across two clean-kernel runs.

> **This build measures. It does not decide.** No model fitted, no imputation, no transformation, no cutoff, no cognitive variable selected, no p-tau181 platforms combined, no cohort revised.

This report keeps **data-availability findings** (what the data *is*) strictly separate from **scientific decisions that remain open for the team** (§10).

---

# PART I — DATA AVAILABILITY FINDINGS

## 1. Headline: the primary comparison is unusually clean

| Model | N | Events | % of B |
|---|---:|---:|---:|
| **M1 — age + APOE4** | **401** | **85** | 97.8 % |
| **M2 — age + APOE4 + p-tau217** | **401** | **85** | 97.8 % |

**M1 and M2 sit on the *identical* 401 participants.** Because `p-tau217` is **never missing** in the plasma panel, adding it costs **zero** participants and **zero** events. The study's whole point — *does p-tau217 add anything beyond age and APOE4?* — is therefore a **like-for-like comparison on the same people**, with **no complete-case confounding** between Model 0 and Model 1. That is a genuinely favourable property and worth stating plainly.

M2 reproduces the frozen primary cohort **exactly** (same N, same events, same participant IDs — asserted).

## 2. Per-variable availability (survival cohort, n = 410)

| Variable | Role | Available | % | Events avail. | In C (401) | Timing |
|---|---|---:|---:|---:|---:|---|
| `entry_age` | PRIMARY | 410 | 100 % | 86 | 401 | **UNDATED** |
| `APOE4_COUNT` | PRIMARY | 401 | 97.8 % | 85 | 401 | time-invariant |
| `ptau217` | PRIMARY | **410** | **100 %** | 86 | 401 | anchor draw (offset 0) |
| `gfap` | secondary | 367 | 89.5 % | **86** | 361 | anchor draw |
| `nfl` | secondary | 367 | 89.5 % | 86 | 361 | anchor draw |
| `abeta42` | secondary | 408 | 99.5 % | 84 | 399 | anchor draw |
| `abeta40` | secondary | 408 | 99.5 % | 84 | 399 | anchor draw |
| `ratio_ab42_ab40` | secondary | 408 | 99.5 % | 84 | 399 | anchor draw |
| `ptau181_qx` | secondary *(not in pipeline)* | **1** | **0.2 %** | 1 | 1 | FNIHBC, ±90 d |
| `ptau181_roche` | secondary *(not in pipeline)* | **3** | **0.7 %** | 1 | 3 | FNIHBC, ±90 d |
| `CDRSB` | cognition | 321 | 78.3 % | 51 | 314 | CDR, ±90 d |
| `MMSCORE` | cognition | 361 | 88.0 % | 82 | 354 | MMSE, ±90 d |
| `MOCA` | cognition | 322 | 78.5 % | 42 | 313 | MOCA, ±90 d |
| `FAQTOTAL` | cognition | 379 | 92.4 % | 82 | 370 | FAQ, ±90 d |
| `CDMEMORY` | **tier-2 candidate** | 321 | 78.3 % | 51 | 314 | CDR, ±90 d |
| `CDJUDGE` | **tier-2 candidate** | 321 | 78.3 % | 51 | 314 | CDR, ±90 d |

**A note on event availability.** `CDRSB` and `MOCA` are available for ~78 % of participants but only **51** and **42** of the 86 events. `MMSCORE` and `FAQTOTAL` retain **82** events each. For a survival model the **event** count is the binding constraint, not the participant count — so CDRSB and MOCA are substantially more expensive than their headline percentages suggest.

### Sentinel / validity accounting

The existing rule removes `-4` / `-5` sentinels and non-positive values **from plasma only**.

| Variable | Sentinels in source | Removed at the anchor draw | Negatives **retained** |
|---|---:|---:|---:|
| `gfap`, `nfl` | 451 each | **43 each** | 0 |
| `abeta42` / `abeta40` | 6 / 5 | 2 each | 0 |
| `ptau217` | **0** | 0 | 0 |

That fully explains the missingness: GFAP/NfL's 43 missing and Aβ's 2 missing are **entirely** sentinel removals. No non-positive plasma value existed. **No zero or negative value was newly reclassified as invalid.** Retained zeros are legitimate (`APOE4_COUNT` = 0 in 215 people; `FAQTOTAL` = 0 in 132; `CDRSB` = 0 in 21).

> ### ⚠️ Latent risk — a `-1` code exists that the sentinel rule does not cover
> The raw **MMSE** (14 rows), **FAQ** (32 rows), **CDMEMORY** and **CDJUDGE** (5 rows each) contain **`-1`** values, which are evidently a *not-done / missing* code. The pipeline's sentinel rule is `-4` / `-5` **only**, and sentinel cleaning is **never applied to cognition at all**.
>
> **No `-1` reached the frozen cohort** (`n_negative_retained = 0` for every variable — verified). So **v1 is not affected**. But this is luck, not design: had a participant's nearest cognitive visit carried `-1`, it would have entered the frozen table as a *valid score of −1*. **Flag for the team:** any pipeline that adopts a cognitive variable should first extend the sentinel rule to `-1`. This is a data-quality finding, not a v1 defect.

## 3. Aβ42/Aβ40 ratio — clean

`ratio_ab42_ab40 = AB42_F / AB40_F`. **Both components are columns of the same raw plasma row** (the selected anchor draw), so participant, draw, date and platform (Fujirebio) are **identical by construction** — a mismatch is structurally impossible.

| Check | Result |
|---|---|
| N with both components valid | 408 |
| Denominator == 0 / non-positive | **0 / 0** |
| Mismatched date or platform | **0** (impossible by construction) |
| Valid derived ratios | **408** (84 events) |
| Infinite / undefined ratios | **0** |
| Raw Aβ42, Aβ40 preserved | ✅ yes |
| Vendor `AB42_AB40_F` preserved separately | ✅ yes — max abs. difference vs recomputed = **5.0 × 10⁻⁵** (rounding only) |

## 4. p-tau181 — **mechanically unusable**, on both platforms

Platforms were kept **strictly separate**; nothing was converted, averaged, prioritised, or imputed (asserted).

| Platform | In FNIHBC | Any measurement ∩ B (410) | **Within ±90 d of the anchor** | Events |
|---|---:|---:|---:|---:|
| `ptau181_qx` (Quanterix / SIMOA) | 355 | 25 | **1** | 1 |
| `ptau181_roche` (Roche Elecsys) | 393 | 32 | **3** | 1 |
| either platform *(reported only)* | 406 | 33 | 3 | 1 |
| both platforms *(reported only)* | 342 | 24 | 1 | 1 |

Build 0 already found the FNIHBC sub-study barely overlaps the anchor cohort (40/535). This audit shows the situation is **far worse than participant-level overlap suggests**: of the 25–32 survival-cohort participants who have *any* p-tau181, essentially **none had it drawn within ±90 days of their plasma anchor**. A baseline covariate must be measured at baseline.

- **M3** (age + APOE4 + Quanterix p-tau181): **N = 1, events = 1.**
- **M4** (age + APOE4 + Roche p-tau181): **N = 3, events = 1.**

**This is a purely mechanical conclusion, so it is safe to state as one:** p-tau181 **cannot support any model** in this cohort, on either platform. It is not a close call and it is not a scientific judgement — there is no data. Any p-tau181 analysis would require a different anchor definition or a different source dataset entirely.

## 5. Cognitive timing — the live issue

Cognition is the **only** feature family where timing is a real question. `entry_age` is undated; APOE4 is time-invariant; every plasma biomarker sits *on* the anchor draw (offset = 0 by construction).

### Post-anchor measurements under the frozen ±90 d rule *(potential leakage)*

| Variable | Available | **Post-anchor** | Max positive offset |
|---|---:|---:|---:|
| `CDRSB` | 321 | **15** | +83 d |
| `MMSCORE` | 361 | **17** | +83 d |
| `MOCA` | 322 | **24** | +49 d |
| `FAQTOTAL` | 379 | **51** | +88 d |

These are **reported, not auto-invalidated**. A "baseline" cognitive score measured 88 days *after* the blood draw is a legitimate leakage concern for a prediction model, but the team decides — not the code.

### Availability under each timing rule (survival cohort, n = 410; **events in parentheses**)

| Variable | `nearest ±90 d` *(frozen)* | `on/before anchor` | `within ±30 d` | `same day only` |
|---|---|---|---|---|
| `CDRSB` | 321 (51) | **306 (51)** | 180 (26) | 75 **(3)** |
| `MMSCORE` | 361 (82) | **344 (82)** | 204 (46) | 79 **(4)** |
| `MOCA` | 322 (42) | 298 (40) | 302 (42) | 185 (18) |
| `FAQTOTAL` | 379 (82) | 328 (76) | 358 (82) | 216 (52) |

**The most useful finding in this build:** restricting cognition to **on-or-before the anchor** removes **100 % of the leakage** (post-anchor count → 0 by construction) and, for `CDRSB` and `MMSCORE`, costs **zero events** (51 → 51 and 82 → 82). The price is only 15 and 17 participants respectively. For those two variables, eliminating leakage is **nearly free**.

By contrast, **same-day-only is not viable** for CDRSB (3 events) or MMSCORE (4 events) — CDR and MMSE are simply administered on a different visit schedule from the blood draw. MOCA and FAQ are far more often same-day.

### Memory and executive candidates

**No validated memory or executive *composite* exists in the available data** — there is no ADAS-Cog, no RAVLT, no `UWNPSYCHSUM` (ADNI-MEM / ADNI-EF) in `Data/raw/`. The only single, documented fields are the **CDR box scores**:

- **`CDMEMORY`** — memory box (0–3)
- **`CDJUDGE`** — judgement & problem-solving box (0–3) — an **executive *proxy***, not a validated executive measure.

Both are **tier-2**: they exist in a table the pipeline already reads, but they are **not in the frozen pipeline**. Adopting them is a pipeline change requiring team approval. Because both come from the CDR form, their availability is identical to `CDRSB` — so **M9** (age + APOE4 + p-tau217 + memory + executive) has the same profile as any CDR-based model: **314 (50 events)** under the frozen rule, **299 (50)** on-or-before, **75 (3)** same-day.

## 6. Model-complete cohorts (universe = survival cohort, 410)

| Model | N | Events | % of B | Lost by |
|---|---:|---:|---:|---|
| M1 — age + APOE4 | 401 | 85 | 97.8 | APOE4 = 9 |
| **M2 — + p-tau217** ⭐ | **401** | **85** | 97.8 | APOE4 = 9 |
| M3 — + p-tau181 (Quanterix) | **1** | 1 | 0.2 | p-tau181 = 409 |
| M4 — + p-tau181 (Roche) | **3** | 1 | 0.7 | p-tau181 = 407 |
| M5 — + p-tau217 + GFAP | 361 | **85** | 88.0 | GFAP = 43 |
| M6 — + p-tau217 + Aβ42/Aβ40 | 399 | 83 | 97.3 | ratio = 2 |
| M8 — + p-tau217 + MMSCORE *(±90 d)* | 354 | 81 | 86.3 | MMSE = 49 |
| M8 — + p-tau217 + MMSCORE *(on/before)* | 337 | **81** | 82.2 | MMSE = 66 |
| M8 — + p-tau217 + FAQTOTAL *(±90 d)* | 370 | 81 | 90.2 | FAQ = 31 |
| M8 — + p-tau217 + CDRSB *(±90 d)* | 314 | 50 | 76.6 | CDR = 89 |
| M8 — + p-tau217 + MOCA *(±90 d)* | 313 | 41 | 76.3 | MOCA = 88 |
| M9 — + p-tau217 + CDMEMORY + CDJUDGE *(±90 d)* | 314 | 50 | 76.6 | CDR = 89 |

Full 42-row table (every variable × every timing rule, with follow-up quartiles and ≤30/90/180/365-day counts) is in `mci_survival_model_complete_case_counts_v1.tsv`.

**GFAP is the cheapest secondary addition by far: it loses 40 participants but *zero events* (85 → 85).**

---

# PART II — COHORT SENSITIVITY FEASIBILITY

All scenarios are **descriptive recomputations held in memory**. The frozen v1 cohort remains authoritative; **no revised cohort was created or saved**, and no frozen inclusion flag was touched (asserted).

| Scenario | Anchor | Survival | Events | Primary | Primary events | M2 N (ev) |
|---|---:|---:|---:|---:|---:|---|
| **S1 — Frozen v1** *(authoritative)* | 535 | 410 | 86 | 401 | 85 | 401 (85) |
| S2 — exclude prior dementia | 527 | 405 | **84** | 397 | **84** | 397 (84) |
| S3 — outcome ascertained ≥ 30 d | 535 | 349 | 86 | 342 | 85 | 342 (85) |
| S3 — ≥ 90 d | 535 | 329 | 86 | 325 | 85 | 325 (85) |
| S3 — ≥ 180 d | 535 | 314 | 86 | 310 | 85 | 310 (85) |
| S3 — ≥ 365 d | 535 | 286 | 86 | 284 | 85 | 284 (85) |
| S3 — ≥ 730 d | 535 | **195** | 86 | 194 | 85 | 194 (85) |
| S4 — exclude censor-is-anchor-visit | 535 | 336 | 86 | 330 | 85 | 330 (85) |

**S2 (prior dementia).** Recomputed from the flag — **not hard-coded** — and it lands exactly on Build 2's projection: 535→527, 410→405, 86→**84**, 401→397, 85→**84**. Only **5** of the 8 flagged participants are in the survival cohort and only **2** of those carry events (one of which is already outside C for missing APOE4). This is a **scenario, not an adjudication**; it awaits the Build 2 human review.

**S3 (minimum follow-up).** A participant qualifies if they had the event, **or** were event-free and observed to at least the threshold. **Removals are exclusively censored participants — no event is ever dropped, at any threshold** (asserted). The cost is steep: a 730-day requirement halves the cohort (410 → 195) while keeping all 86 events.

> **Methodological warning (required).** Conditioning inclusion on **future** follow-up is a form of selection on post-baseline information and can bias a prediction model. These restrictions **must not replace ordinary right-censoring** in the primary analysis without a separate, documented methodological decision. They are offered as **potential sensitivity analyses only**.

**S4 (censor-is-anchor-visit).** The 74 participants whose censoring visit *is* the MCI visit that defined their anchor (median follow-up 12 days). Excluding them drops B to 336 and M2 to 330, **with no event loss** (all 74 are censored).

Overlaps for the 74:

| Overlaps with | N |
|---|---:|
| follow-up ≤ 30 days | 61 |
| follow-up ≤ 90 days | **74** (all — guaranteed by construction: their follow-up *is* the ≤90 d anchor-matching offset) |
| prior-dementia history | 1 |
| primary complete-case (C) | 71 |

---

# PART III — SCIENTIFIC DECISIONS STILL REQUIRING THE TEAM

Availability findings above are facts. The following are **not** — they are judgements this build deliberately does **not** make.

| # | Open decision | What the data says | Who decides |
|---|---|---|---|
| 1 | **Is any post-anchor cognitive value acceptable?** | 15–51 participants per variable have cognition measured *after* the blood draw (up to +88 d). Restricting to on-or-before removes all of it and costs **0 events** for CDRSB/MMSCORE. | Team |
| 2 | **Should cognition be included at all?** | It is not part of the pre-specified primary model. Every cognitive variable costs events (best case: 85 → 81). | Team |
| 3 | **Which cognitive variable, and under which timing rule?** | MMSCORE and FAQTOTAL retain the most events (81–82); CDRSB and MOCA retain only 50 and 41. Build 3 **does not choose**. | Team |
| 4 | **Should prior-dementia cases be excluded from the primary analysis?** | 8 flagged; excluding them → C 397, events 84. Awaits the Build 2 human adjudication. | Team, after QC review |
| 5 | **Is any minimum-follow-up sensitivity analysis worth running?** | Feasible at every threshold with no event loss, but at large N cost and with real selection concerns. | Team (methodological) |
| 6 | **Should the `-1` code be added to the sentinel rule?** | v1 is unaffected, but the risk is live for any future cognitive variable. | Team |
| 7 | **Should CDMEMORY / CDJUDGE be adopted?** | They are the *only* memory/executive candidates that exist; CDJUDGE is a **proxy**, not a validated executive measure. Adopting them is a pipeline change. | Team |

**One conclusion *is* purely mechanical and is therefore stated as a finding, not a recommendation:** p-tau181 has **1 (Quanterix) / 3 (Roche)** anchor-aligned observations and **cannot support any model**. No scientific judgement is involved — the observations do not exist.

---

# PART IV — CANDIDATE SECONDARY ANALYSES, RANKED BY **FEASIBILITY ONLY**

**This ranking is about data, not predictive performance.** Nothing here says any of these models would work.

| Rank | Candidate secondary | N | Events | % of B retained | Timing quality | Platform consistency | Major caveat |
|---|---|---:|---:|---:|---|---|---|
| **1** | **+ GFAP** | 361 | **85** | 88 % | ✅ on the anchor draw (offset 0) | ✅ single (Quanterix) | Loses 40 participants but **zero events** — cheapest addition available |
| **2** | **+ Aβ42/Aβ40 ratio** | 399 | 83 | 97 % | ✅ on the anchor draw | ✅ single (Fujirebio, both components same row) | Loses only 2 participants, but 2 **events** |
| **3** | + MMSE (`MMSCORE`), on-or-before | 337 | 81 | 82 % | ✅ **no leakage** by construction | ✅ single instrument | Costs 4 events; cognition is not in the pre-specified model |
| **4** | + FAQ (`FAQTOTAL`), ±90 d | 370 | 81 | 90 % | ⚠️ **51 post-anchor** (max +88 d) | ✅ single instrument | Highest leakage of any cognitive variable; FAQ is *function*, not cognition |
| **5** | + NfL | 361 | 85 | 88 % | ✅ on the anchor draw | ✅ single (Quanterix) | Not in the pre-specified secondary set; same coverage as GFAP |
| **6** | + CDR-SB (`CDRSB`), on-or-before | 299 | 50 | 73 % | ✅ no leakage | ✅ single instrument | **Loses 35 of 85 events** — severe |
| **7** | + MoCA, ±90 d | 313 | 41 | 76 % | ⚠️ 24 post-anchor | ✅ single instrument | **Loses 44 of 85 events** — most expensive cognitive option |
| **8** | + CDMEMORY + CDJUDGE (memory + executive) | 314 | 50 | 77 % | ⚠️ 15 post-anchor | ✅ single instrument (CDR) | **Not in the frozen pipeline**; CDJUDGE is an executive *proxy*; loses 35 events |
| **✗** | + p-tau181 (Quanterix) | **1** | 1 | 0.2 % | ✗ almost never near the anchor | ✗ separate sub-study | **INFEASIBLE — no data** |
| **✗** | + p-tau181 (Roche) | **3** | 1 | 0.7 % | ✗ almost never near the anchor | ✗ separate sub-study | **INFEASIBLE — no data** |

---

## Outputs

`outputs/01c_mci_survival_cohort_freeze/`

| File | Rows × Cols |
|---|---|
| `mci_survival_feature_missingness_v1.tsv` | 16 × 35 |
| `mci_survival_model_complete_case_counts_v1.tsv` | 42 × 18 |
| `mci_survival_feature_timing_v1.tsv` | 40 × 33 |
| `mci_survival_feature_scenario_counts_v1.tsv` | 12 × 19 |
| `mci_survival_ptau181_platform_availability_v1.tsv` | 4 × 14 |

## Reproduction

```bash
cd /Users/zoeyd/Desktop/Predict_AD_from_Biomarkers
Data/.venv/bin/python -m nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=1200 \
  notebooks/01e_mci_survival_feature_availability_audit.ipynb
```

Environment: Python 3.14.0, pandas 3.0.1, numpy 2.4.3. Verified deterministic across two clean-kernel runs; all ten Build 1 + Build 2 artifacts hashed before and after and confirmed byte-identical.
