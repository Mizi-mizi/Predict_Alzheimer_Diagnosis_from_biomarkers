"""
Generate performance plots for the Alzheimer's pipeline:
  1. Regression scatter (actual vs predicted) for each of the 4 scores
  2. Confusion matrix — direct classifier (scores -> diagnosis)
  3. Confusion matrix — end-to-end (biomarkers -> diagnosis)
  4. Feature importances for each RF regressor
Saves PNGs to ./plots/.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, confusion_matrix

from final_v import (
    DATASETS, DIAGNOSIS_PATH, FEATURES, SCORE_COLS, ALL_FEATURES, DATA_DIR,
    train_rf_models, train_classifier, predict_scores, predict_severity,
)


PLOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
os.makedirs(PLOT_DIR, exist_ok=True)


def plot_regression_scatter():
    fig, axes = plt.subplots(2, 2, figsize=(11, 10))
    importances = {}

    for ax, d in zip(axes.flat, DATASETS):
        target = d["target"]
        df = pd.read_csv(d["path"])
        df.columns = df.columns.str.strip()
        feats = FEATURES[target]
        X = df[feats].fillna(df[feats].median())
        y = df[target]
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=300, random_state=42)
        model.fit(X_tr, y_tr)
        preds = model.predict(X_te)
        importances[target] = (feats, model.feature_importances_)

        mae = mean_absolute_error(y_te, preds)
        r2 = r2_score(y_te, preds)

        ax.scatter(y_te, preds, alpha=0.35, s=18, edgecolor="none")
        lo, hi = min(y_te.min(), preds.min()), max(y_te.max(), preds.max())
        ax.plot([lo, hi], [lo, hi], "r--", lw=1, label="y = x")
        ax.set_xlabel(f"Actual {target}")
        ax.set_ylabel(f"Predicted {target}")
        ax.set_title(f"{target} — MAE={mae:.2f}, R²={r2:.2f}")
        ax.legend(loc="best", fontsize=8)
        ax.grid(alpha=0.3)

    fig.suptitle("Random Forest regressor: actual vs predicted (held-out test)", fontsize=13)
    fig.tight_layout()
    path = os.path.join(PLOT_DIR, "regression_scatter.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved {path}")
    return importances


def plot_feature_importance(importances):
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, (target, (feats, imps)) in zip(axes.flat, importances.items()):
        order = np.argsort(imps)
        ax.barh([feats[i] for i in order], [imps[i] for i in order], color="steelblue")
        ax.set_title(f"{target} feature importance")
        ax.set_xlabel("importance")
        ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    path = os.path.join(PLOT_DIR, "feature_importance.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved {path}")


def _confusion_heatmap(ax, cm, labels, title, normalize=False):
    if normalize:
        row_sums = cm.sum(axis=1, keepdims=True)
        display = np.divide(cm.astype(float), row_sums,
                            out=np.zeros_like(cm, dtype=float),
                            where=row_sums != 0)
        vmax = 1.0
        fmt = lambda v, raw: f"{v:.1%}\n(n={raw})"
    else:
        display = cm
        vmax = cm.max() if cm.size else 1
        fmt = lambda v, raw: str(raw)

    im = ax.imshow(display, cmap="Blues", vmin=0, vmax=vmax)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    thresh = vmax / 2
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, fmt(display[i, j], cm[i, j]), ha="center", va="center",
                    color="white" if display[i, j] > thresh else "black", fontsize=9)
    return im


def plot_classifier_confusion():
    diag_df = pd.read_csv(DIAGNOSIS_PATH)
    diag_df.columns = diag_df.columns.str.strip()
    clf_df = diag_df[SCORE_COLS + ["DIAGNOSIS"]].dropna()
    X = clf_df[SCORE_COLS]
    y = clf_df["DIAGNOSIS"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    clf = LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42)
    clf.fit(X_tr, y_tr)
    preds = clf.predict(X_te)
    acc = (preds == y_te).mean()

    labels = sorted(y.unique())
    cm = confusion_matrix(y_te, preds, labels=labels)

    fig, ax = plt.subplots(figsize=(6, 5))
    _confusion_heatmap(ax, cm, labels, f"Scores → Diagnosis  (acc={acc:.1%})")
    fig.tight_layout()
    path = os.path.join(PLOT_DIR, "confusion_scores_to_dx.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved {path}")


def plot_end_to_end_confusion():
    bdx = os.path.join(DATA_DIR, "biomarker_dx.csv")
    if not os.path.exists(bdx):
        print(f"  skipping end-to-end plot — {bdx} missing (run build_biomarker_dx.py)")
        return

    models, medians = train_rf_models()
    clf, _ = train_classifier()

    df = pd.read_csv(bdx)
    sample = df.sample(n=min(500, len(df)), random_state=0).reset_index(drop=True)

    y_true, y_pred = [], []
    for _, row in sample.iterrows():
        ui = {f: row[f] for f in ALL_FEATURES}
        preds = predict_scores(models, medians, ui)
        sev, _ = predict_severity(clf, preds)
        y_true.append(str(row["DIAGNOSIS"]))
        y_pred.append(str(sev))

    labels = sorted(set(y_true) | set(y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    acc = np.mean(np.array(y_true) == np.array(y_pred))

    fig, ax = plt.subplots(figsize=(6, 5))
    _confusion_heatmap(ax, cm, labels,
                       f"Biomarkers → Diagnosis (end-to-end, row-normalized)\nacc={acc:.1%}  n={len(sample)}",
                       normalize=True)
    fig.tight_layout()
    path = os.path.join(PLOT_DIR, "confusion_biomarker_to_dx.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved {path}")


def main():
    print("Plotting regression scatter + feature importance...")
    importances = plot_regression_scatter()
    plot_feature_importance(importances)
    print("Plotting direct-classifier confusion matrix...")
    plot_classifier_confusion()
    print("Plotting end-to-end (biomarker → diagnosis) confusion matrix...")
    plot_end_to_end_confusion()
    print(f"\nAll plots saved under {PLOT_DIR}/")


if __name__ == "__main__":
    main()
