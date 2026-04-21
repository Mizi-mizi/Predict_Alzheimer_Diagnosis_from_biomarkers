"""
Alzheimer's Severity Prediction Pipeline
========================================
1. Trains 4 Random Forest models on score datasets (CDR, MMSE, MoCA, FAQ)
2. Trains a multinomial logistic classifier on the diagnosis dataset
3. Prompts the user for biomarker values
4. Predicts the 4 clinical scores and the severity class
5. Shows the 5 most similar patients from the reference dataset
"""

import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score, classification_report


# ── Configuration ─────────────────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "Data", "cleaned")
DATASETS = [
    {"path": os.path.join(DATA_DIR, "cdr_reg.csv"),  "target": "CDRSB"},
    {"path": os.path.join(DATA_DIR, "mmse_reg.csv"), "target": "MMSCORE"},
    {"path": os.path.join(DATA_DIR, "moca_reg.csv"), "target": "MOCA"},
    {"path": os.path.join(DATA_DIR, "faq_reg.csv"),  "target": "FAQTOTAL"},
]
DIAGNOSIS_PATH = os.path.join(DATA_DIR, "dx_reg.csv")
MODEL_DIR = os.path.join(ROOT_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "pipeline.joblib")

FEATURES = {
    "CDRSB":    ["janssenptau217", "nfl", "entry_age", "abeta42", "APOE4_COUNT"],
    "MMSCORE":  ["janssenptau217", "nfl", "gfap", "entry_age", "abeta42", "APOE4_COUNT"],
    "MOCA":     ["janssenptau217", "nfl", "entry_age", "abeta42", "APOE4_COUNT"],
    "FAQTOTAL": ["entry_age", "APOE4_COUNT"],
}
ALL_FEATURES = sorted({f for feats in FEATURES.values() for f in feats})
SCORE_COLS = ["CDRSB", "MMSCORE", "MOCA", "FAQTOTAL"]


# ── 1. Train Random Forest models ─────────────────────────────────────────
def train_rf_models():
    models, medians = {}, {}
    for d in DATASETS:
        target = d["target"]
        df = pd.read_csv(os.path.expanduser(d["path"]))
        df.columns = df.columns.str.strip()

        features = FEATURES[target]
        missing = [f for f in features if f not in df.columns]
        if missing:
            print(f"  Skipping {target} — missing columns: {missing}")
            continue

        X = df[features].fillna(df[features].median())
        y = df[target]
        medians[target] = df[features].median().to_dict()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        model = RandomForestRegressor(n_estimators=300, random_state=42)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        print(f"  {target:10} — Test MAE={mean_absolute_error(y_test, preds):.3f}, "
              f"R²={r2_score(y_test, preds):.3f}")

        models[target] = model
    return models, medians


# ── 2. Train diagnosis classifier ─────────────────────────────────────────
def train_classifier():
    diag_df = pd.read_csv(os.path.expanduser(DIAGNOSIS_PATH))
    diag_df.columns = diag_df.columns.str.strip()

    clf_df = diag_df[SCORE_COLS + ["DIAGNOSIS"]].dropna()
    X_clf = clf_df[SCORE_COLS]
    y_clf = clf_df["DIAGNOSIS"]

    X_train, X_test, y_train, y_test = train_test_split(
        X_clf, y_clf, test_size=0.2, random_state=42, stratify=y_clf
    )
    clf = LogisticRegression(
        solver="lbfgs", max_iter=1000, random_state=42
    )
    clf.fit(X_train, y_train)

    print(f"  Classifier test accuracy: {clf.score(X_test, y_test):.3f}")
    return clf, diag_df


# ── Persistence ───────────────────────────────────────────────────────────
def save_pipeline(models, medians, clf):
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({"models": models, "medians": medians, "clf": clf}, MODEL_PATH)
    print(f"  Saved pipeline to {MODEL_PATH}")


def load_pipeline():
    bundle = joblib.load(MODEL_PATH)
    diag_df = pd.read_csv(DIAGNOSIS_PATH)
    diag_df.columns = diag_df.columns.str.strip()
    return bundle["models"], bundle["medians"], bundle["clf"], diag_df


# ── 3. Collect user input ─────────────────────────────────────────────────
def prompt_user_input():
    print("\nEnter biomarker values (press Enter to use training median):")
    user_input = {}
    for feat in ALL_FEATURES:
        raw = input(f"  {feat}: ").strip()
        user_input[feat] = float(raw) if raw else None
    return user_input


# ── 4. Predict scores and severity ────────────────────────────────────────
def predict_scores(models, medians, user_input):
    predicted = {}
    for target, model in models.items():
        feats = FEATURES[target]
        row = {f: user_input.get(f) if user_input.get(f) is not None else medians[target][f]
               for f in feats}
        predicted[target] = round(float(model.predict(pd.DataFrame([row])[feats])[0]), 2)
    return predicted


def predict_severity(clf, predicted):
    score_row = pd.DataFrame([[predicted.get(c, 0) for c in SCORE_COLS]], columns=SCORE_COLS)
    return clf.predict(score_row)[0], clf.predict_proba(score_row)[0]


def find_similar_patients(diag_df, predicted, k=5):
    ref = diag_df[SCORE_COLS + ["DIAGNOSIS", "RID", "DATE"]].copy()
    for col in SCORE_COLS:
        ref[col] = pd.to_numeric(ref[col], errors="coerce")
    ref = ref.dropna(subset=SCORE_COLS)
    ref["distance"] = np.sqrt(sum(
        (ref[c] - predicted.get(c, 0)) ** 2 for c in SCORE_COLS
    ))
    return ref.nsmallest(k, "distance")[["RID", "DATE"] + SCORE_COLS + ["DIAGNOSIS", "distance"]]


# ── 5. Reporting ──────────────────────────────────────────────────────────
SCORE_LABELS = {
    "CDRSB":    ("CDR Sum of Boxes",        "0-18", "higher = worse"),
    "MMSCORE":  ("Mini-Mental State Exam",  "0-30", "lower = worse"),
    "MOCA":     ("Montreal Cog Assessment", "0-30", "lower = worse"),
    "FAQTOTAL": ("Functional Activities Q", "0-30", "higher = worse"),
}
INTERPRETATION = {
    "CN":       "No cognitive impairment detected.",
    "MCI":      "Mild Cognitive Impairment — monitor closely, not yet dementia.",
    "Dementia": "Dementia-level impairment — clinical follow-up strongly advised.",
}

# Reference ranges (p5 – p95) computed empirically from CN (cognitively
# normal) patients in the training set. Units reflect the dataset's native
# units for each assay.
NORMAL_RANGES = {
    "janssenptau217": (0.023, 0.145, "pg/mL"),
    "nfl":            (2.81,  40.61, "pg/mL"),
    "abeta42":        (29.17, 54.78, "pg/mL"),
    "APOE4_COUNT":    (0,     1,     "alleles"),
}

# GFAP correlates with age (Pearson r≈0.33 in CN); use age-binned ranges.
# Each entry: (age_low, age_high) -> (gfap_p5, gfap_p95) in pg/mL.
GFAP_BY_AGE = [
    ((0,  60),  (50.4,  129.0)),
    ((60, 70),  (57.4,  292.8)),
    ((70, 80),  (65.8,  355.8)),
    ((80, 200), (116.8, 447.3)),
]


def _gfap_range_for_age(age):
    if age is None:
        return None
    for (lo, hi), rng in GFAP_BY_AGE:
        if lo <= age < hi:
            return rng
    return None


def _format_range(feat, user_input):
    if feat == "gfap":
        rng = _gfap_range_for_age(user_input.get("entry_age"))
        if rng is None:
            return "normal: age-dependent (enter age)"
        return f"normal: {rng[0]} – {rng[1]} pg/mL  (for age {user_input['entry_age']:.0f})"
    entry = NORMAL_RANGES.get(feat)
    if not entry:
        return ""
    lo, hi, unit = entry
    return f"normal: {lo} – {hi} {unit}".rstrip()


def print_summary(user_input, predicted, severity, proba, classes, similar):
    print("\n" + "=" * 60)
    print("  PATIENT SUMMARY")
    print("=" * 60)

    print("\nBiomarker inputs used:")
    for k, v in user_input.items():
        val_str = f"{v}" if v is not None else "(median fallback)"
        print(f"  {k:22} {val_str:<20} {_format_range(k, user_input)}")

    print("\nPredicted clinical scores:")
    for col, (label, scale, direction) in SCORE_LABELS.items():
        val = predicted.get(col, float("nan"))
        print(f"  {label:30} {val:6.2f}   (scale {scale}, {direction})")

    print(f"\nSeverity classification: {severity}  (confidence {max(proba):.1%})")
    print("\nProbability per class:")
    for cls, prob in zip(classes, proba):
        bar = "█" * int(prob * 30)
        print(f"  {str(cls):12} {prob:.3f}  {bar}")

    print("\nInterpretation:")
    for cls, desc in INTERPRETATION.items():
        marker = ">>>" if cls == str(severity) else "   "
        print(f"  {marker} {cls:10} {desc}")

    print("\n5 most similar patients in reference dataset:")
    print(similar.to_string(index=False))

    print("\nNote: Research tool only. Not a clinical diagnosis.")
    print("=" * 60)


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Alzheimer's Severity Prediction Pipeline")
    print("=" * 60)

    if not os.path.exists(MODEL_PATH):
        raise SystemExit(
            f"\nNo trained pipeline at {MODEL_PATH}.\n"
            f"Run `python scripts/train.py` once to train and save, then re-run this script."
        )

    print(f"\n[1/3] Loading trained pipeline from {MODEL_PATH}...")
    models, medians, clf, diag_df = load_pipeline()

    print("\n[2/3] Collecting user input...")
    user_input = prompt_user_input()

    print("\n[3/3] Generating predictions...")
    predicted = predict_scores(models, medians, user_input)
    severity, proba = predict_severity(clf, predicted)
    similar = find_similar_patients(diag_df, predicted)

    print_summary(user_input, predicted, severity, proba, clf.classes_, similar)


if __name__ == "__main__":
    main()
