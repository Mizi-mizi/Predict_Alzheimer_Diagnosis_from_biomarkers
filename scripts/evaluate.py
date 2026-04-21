"""
End-to-end test: biomarkers -> predicted scores -> predicted diagnosis.
Compares predicted DIAGNOSIS against actual DIAGNOSIS on real patient rows
from Data/biomarker_dx.csv (built by build_biomarker_dx.py).
"""

import os
from collections import Counter
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from final_v import (
    train_rf_models, train_classifier,
    predict_scores, predict_severity,
    ALL_FEATURES, DATA_DIR,
)


N_SAMPLES = 200
RANDOM_STATE = 0
BIOMARKER_DX_PATH = os.path.join(DATA_DIR, "biomarker_dx.csv")


def main():
    if not os.path.exists(BIOMARKER_DX_PATH):
        raise SystemExit(
            f"{BIOMARKER_DX_PATH} not found. Run `python build_biomarker_dx.py` first."
        )

    print("Training models...")
    models, medians = train_rf_models()
    clf, _ = train_classifier()

    df = pd.read_csv(BIOMARKER_DX_PATH)
    print(f"\nLoaded {len(df)} biomarker+diagnosis rows.")
    sample = df.sample(n=min(N_SAMPLES, len(df)), random_state=RANDOM_STATE).reset_index(drop=True)
    print(f"Testing on {len(sample)} rows.\n")

    y_true, y_pred = [], []
    correct = 0

    for i, row in sample.iterrows():
        user_input = {f: row[f] for f in ALL_FEATURES}
        predicted_scores = predict_scores(models, medians, user_input)
        severity, proba = predict_severity(clf, predicted_scores)

        actual_dx = str(row["DIAGNOSIS"])
        pred_dx = str(severity)
        y_true.append(actual_dx)
        y_pred.append(pred_dx)
        hit = pred_dx == actual_dx
        correct += int(hit)

        if i < 15:
            mark = "OK  " if hit else "MISS"
            print(
                f"[{mark}] RID={row['RID']:>6} {row['DATE']}  "
                f"pred={pred_dx:<10} actual={actual_dx:<10} conf={max(proba):.1%}"
            )

    print("\n" + "=" * 60)
    print("  BIOMARKER -> DIAGNOSIS RESULTS")
    print("=" * 60)
    print(f"Accuracy: {correct}/{len(sample)} ({correct/len(sample):.1%})\n")

    print("Actual class distribution:  ", dict(Counter(y_true)))
    print("Predicted class distribution:", dict(Counter(y_pred)))

    print("\nClassification report:")
    print(classification_report(y_true, y_pred, zero_division=0))

    labels = sorted(set(y_true) | set(y_pred))
    print("Confusion matrix (rows=actual, cols=predicted):")
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    header = "           " + "".join(f"{l:>10}" for l in labels)
    print(header)
    for lbl, row in zip(labels, cm):
        print(f"  {lbl:<9}" + "".join(f"{v:>10}" for v in row))


if __name__ == "__main__":
    main()
