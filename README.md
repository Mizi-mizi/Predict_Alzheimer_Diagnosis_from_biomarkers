# Predict AD from Biomarkers

A research pipeline that predicts Alzheimer's disease severity from blood
biomarkers, APOE4 genotype, and age. Given a patient's biomarker panel, it
estimates four clinical scores (CDR-SB, MMSE, MoCA, FAQ), classifies the
patient into a severity category (CN / MCI / Dementia), and surfaces the
five most similar patients from a reference cohort.

> **Research tool only — not a clinical diagnostic.**

## How it works

1. **Four Random Forest regressors** map biomarkers → clinical scores.
   Each target uses a tailored feature subset (see `FEATURES` in
   [final_v.py](final_v.py#L37)):
   - `CDRSB`, `MMSCORE`, `MOCA` — ptau217, NfL, age, Aβ42, APOE4 count
     (plus GFAP for MMSE)
   - `FAQTOTAL` — age, APOE4 count
2. **A multinomial logistic classifier** maps the four predicted scores →
   diagnosis label.
3. At inference, the user is prompted for biomarker values (missing values
   fall back to training-set medians), and the pipeline returns predicted
   scores, a severity class with probabilities, and nearest neighbors in
   score space.

## Quick start

```bash
# 1. Train once — fits models on Data/cleaned/*.csv, saves models/pipeline.joblib
python scripts/train.py

# 2. Run inference interactively
python final_v.py
```

`final_v.py` requires the trained `models/pipeline.joblib` to exist; run
`scripts/train.py` first if it doesn't.

## Inputs

The interactive prompt asks for these biomarker values (leave blank to use
the training median):

| Feature | Units | Typical range (CN p5–p95) |
|---------|-------|---------------------------|
| `janssenptau217` | pg/mL | 0.023 – 0.145 |
| `nfl` | pg/mL | 2.81 – 40.61 |
| `gfap` | pg/mL | age-dependent (see `GFAP_BY_AGE` in [final_v.py](final_v.py#L176)) |
| `abeta42` | pg/mL | 29.17 – 54.78 |
| `entry_age` | years | — |
| `APOE4_COUNT` | alleles | 0 – 1 (range), 0–2 (possible) |

## Outputs

- Predicted scores on native scales (CDR-SB 0–18, MMSE 0–30, MoCA 0–30,
  FAQ 0–30)
- Severity class (`CN` / `MCI` / `Dementia`) with per-class probabilities
- Five nearest neighbors in (CDR-SB, MMSE, MoCA, FAQ) space with their
  recorded diagnosis

## Dependencies

Python 3 with `numpy`, `pandas`, `scikit-learn`, `joblib`.

## Notes

- Reference ranges in the report are computed empirically from cognitively
  normal (CN) patients in the training set.
- GFAP ranges are stratified by age bin because GFAP correlates with age
  (Pearson r ≈ 0.33 in CN).

## Acknowledgements

**Collaborators:** 

- Meixi Du 
- Jacob Kang
- Ishaanee Roy
- Berne Chu
- Lu Liu

**Data source:** Data used in preparation of this project were obtained
from the Alzheimer's Disease Neuroimaging Initiative (ADNI) database
(adni.loni.usc.edu). As such, the investigators within the ADNI
contributed to the design and implementation of ADNI and/or provided data
but did not participate in analysis or writing of this report.
