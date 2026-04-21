"""
Generate performance plots for the ordinal diagnosis model (Step3/Ordinal.py).
Retrains the same Frank & Hall ordinal classifier and saves PNGs to ./plots/.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    roc_curve, auc,
)


HERE = os.path.dirname(os.path.abspath(__file__))
DX_PATH = os.path.join(HERE, "..", "cleaned_data", "dx_reg.csv")
PLOT_DIR = os.path.join(HERE, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

DX_ORDER = ["CN", "MCI", "Dementia"]
DX_TO_INT = {name: i for i, name in enumerate(DX_ORDER)}
FEATURES = ["CDRSB", "FAQTOTAL", "MMSCORE", "MOCA"]


class OrdinalLogisticRegression:
    def __init__(self, n_classes):
        self.n_classes = n_classes
        self.clfs = []

    def fit(self, X, y):
        self.clfs = []
        for k in range(self.n_classes - 1):
            y_bin = (y > k).astype(int)
            clf = LogisticRegression(max_iter=10000, random_state=42)
            clf.fit(X, y_bin)
            self.clfs.append(clf)
        return self

    def predict_proba(self, X):
        probs_gt = np.column_stack([c.predict_proba(X)[:, 1] for c in self.clfs])
        probs = np.zeros((X.shape[0], self.n_classes))
        probs[:, 0] = 1 - probs_gt[:, 0]
        for k in range(1, self.n_classes - 1):
            probs[:, k] = probs_gt[:, k - 1] - probs_gt[:, k]
        probs[:, -1] = probs_gt[:, -1]
        probs = np.clip(probs, 0, 1)
        probs /= probs.sum(axis=1, keepdims=True)
        return probs

    def predict(self, X):
        return self.predict_proba(X).argmax(axis=1)


def save(fig, name):
    path = os.path.join(PLOT_DIR, name)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved {path}")


def plot_confusion(y_true, y_pred, title, fname, normalize=False):
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(DX_ORDER))))
    if normalize:
        cm_show = cm.astype(float) / cm.sum(axis=1, keepdims=True)
        fmt = lambda v: f"{v:.2f}"
        vmax = 1.0
    else:
        cm_show = cm
        fmt = lambda v: str(int(v))
        vmax = cm.max()
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm_show, cmap="Blues", vmin=0, vmax=vmax)
    ax.set_xticks(range(len(DX_ORDER)))
    ax.set_yticks(range(len(DX_ORDER)))
    ax.set_xticklabels(DX_ORDER)
    ax.set_yticklabels(DX_ORDER)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    thresh = vmax / 2
    for i in range(len(DX_ORDER)):
        for j in range(len(DX_ORDER)):
            ax.text(j, i, fmt(cm_show[i, j]), ha="center", va="center",
                    color="white" if cm_show[i, j] > thresh else "black")
    fig.colorbar(im)
    save(fig, fname)


def plot_coef_bar(model):
    coef_df = pd.DataFrame(
        {f"P(>{DX_ORDER[k]})": c.coef_[0] for k, c in enumerate(model.clfs)},
        index=FEATURES,
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    coef_df.plot(kind="bar", ax=ax)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("Coefficient (standardized)")
    ax.set_title("Feature coefficients across ordinal thresholds")
    ax.legend(title="Threshold")
    plt.xticks(rotation=30, ha="right")
    save(fig, "coefficients.png")


def plot_proba_by_actual(model, X_test, y_test):
    proba = model.predict_proba(X_test)
    proba_df = pd.DataFrame(proba, columns=DX_ORDER)
    proba_df["actual"] = [DX_ORDER[i] for i in y_test]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    for ax, cls in zip(axes, DX_ORDER):
        data = [proba_df[proba_df["actual"] == t][cls].values for t in DX_ORDER]
        ax.boxplot(data, tick_labels=DX_ORDER)
        ax.set_title(f"P(predicted = {cls})")
        ax.set_xlabel("Actual class")
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("Predicted probability")
    fig.suptitle("Predicted probability by actual class")
    save(fig, "proba_by_actual.png")


def plot_feature_distribution(dx_clean):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, col in zip(axes.flat, FEATURES):
        data = [dx_clean[dx_clean["DIAGNOSIS"] == dx][col].values for dx in DX_ORDER]
        ax.boxplot(data, tick_labels=DX_ORDER)
        ax.set_title(col)
        ax.grid(True, alpha=0.3)
    fig.suptitle("Cognitive score distribution by diagnosis")
    save(fig, "feature_distribution.png")


def plot_error_histogram(y_true, y_pred):
    diff = np.array(y_pred) - np.array(y_true)
    fig, ax = plt.subplots(figsize=(6, 4))
    bins = np.arange(diff.min() - 0.5, diff.max() + 1.5, 1)
    ax.hist(diff, bins=bins, color="steelblue", edgecolor="black")
    ax.axvline(0, color="red", linestyle="--", linewidth=1)
    ax.set_xlabel("predicted class − actual class  (0 = correct)")
    ax.set_ylabel("count")
    mae = np.mean(np.abs(diff))
    within_one = np.mean(np.abs(diff) <= 1)
    ax.set_title(f"Ordinal error distribution  (MAE={mae:.3f}, ±1 acc={within_one:.1%})")
    ax.grid(True, alpha=0.3)
    save(fig, "error_histogram.png")


def plot_threshold_roc(model, X_test, y_test):
    fig, ax = plt.subplots(figsize=(6, 5))
    for k, clf in enumerate(model.clfs):
        y_bin = (y_test > k).astype(int)
        scores = clf.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_bin, scores)
        ax.plot(fpr, tpr, label=f"P(>{DX_ORDER[k]})  AUC={auc(fpr, tpr):.3f}")
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.7)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("ROC per ordinal threshold")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    save(fig, "threshold_roc.png")


def plot_cv_accuracy(X_scaled, y):
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    accs = []
    for tr, te in kf.split(X_scaled):
        m = OrdinalLogisticRegression(len(DX_ORDER))
        m.fit(X_scaled[tr], y.values[tr])
        accs.append(accuracy_score(y.values[te], m.predict(X_scaled[te])))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(range(1, 6), accs, color="steelblue")
    ax.axhline(np.mean(accs), color="red", linestyle="--",
               label=f"mean = {np.mean(accs):.3f}")
    ax.set_ylim(0, 1)
    ax.set_xlabel("Fold")
    ax.set_ylabel("Accuracy")
    ax.set_title(f"5-fold CV accuracy  ({np.mean(accs):.3f} ± {np.std(accs):.3f})")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    save(fig, "cv_accuracy.png")


def main():
    dx_reg = pd.read_csv(DX_PATH)
    dx_clean = dx_reg[FEATURES + ["DIAGNOSIS"]].dropna()
    X = dx_clean[FEATURES]
    y = dx_clean["DIAGNOSIS"].map(DX_TO_INT)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    model = OrdinalLogisticRegression(len(DX_ORDER))
    model.fit(X_tr, y_tr.values)
    y_pred = model.predict(X_te)
    acc = accuracy_score(y_te, y_pred)
    print(f"Test accuracy: {acc:.4f}")
    print(classification_report(y_te, y_pred, target_names=DX_ORDER,
                                labels=list(range(len(DX_ORDER)))))

    print("\nGenerating plots...")
    plot_confusion(y_te.values, y_pred,
                   f"Confusion Matrix — Ordinal  (acc={acc:.1%})",
                   "confusion_matrix.png")
    plot_confusion(y_te.values, y_pred,
                   "Normalized Confusion Matrix (per-class recall)",
                   "confusion_matrix_normalized.png", normalize=True)
    plot_coef_bar(model)
    plot_proba_by_actual(model, X_te, y_te.values)
    plot_feature_distribution(dx_clean)
    plot_error_histogram(y_te.values, y_pred)
    plot_threshold_roc(model, X_te, y_te.values)
    plot_cv_accuracy(X_scaled, y)

    print(f"\nAll plots saved to {PLOT_DIR}/")


if __name__ == "__main__":
    main()
