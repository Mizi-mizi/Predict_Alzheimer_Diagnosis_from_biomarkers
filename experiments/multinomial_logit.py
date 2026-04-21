# %%
# Multinomial logistic regression: predict diagnosis from cognitive scores
# Classes: CN, MCI, Dementia — treated as unordered
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt

DX_ORDER = ["CN", "MCI", "Dementia"]
DX_TO_INT = {name: i for i, name in enumerate(DX_ORDER)}

# %%
# Load data, drop NaN, encode diagnosis as int
dx_reg = pd.read_csv("../cleaned_data/dx_reg.csv")
dx_clean = dx_reg[["CDRSB", "FAQTOTAL", "MMSCORE", "MOCA", "DIAGNOSIS"]].dropna()

X = dx_clean[["CDRSB", "FAQTOTAL", "MMSCORE", "MOCA"]]
y = dx_clean["DIAGNOSIS"].map(DX_TO_INT)

print(f"N samples: {len(dx_clean)}")
print(f"\nClass distribution:\n{dx_clean['DIAGNOSIS'].value_counts()}")

# %%
# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

# %%
# Fit multinomial logistic regression with CV-tuned regularization
mlr = LogisticRegressionCV(cv=5, solver="lbfgs", max_iter=10000, random_state=42, l1_ratios=(0,), use_legacy_attributes=True)
mlr.fit(X_train, y_train)

# %%
# Evaluate on test set
y_pred = mlr.predict(X_test)

print("=== Multinomial Logistic Regression Performance ===")
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print("\nClassification report:")
print(classification_report(y_test, y_pred, target_names=DX_ORDER, labels=list(range(len(DX_ORDER)))))

# 5-Fold CV
kf = KFold(n_splits=5, shuffle=True, random_state=42)
acc_cv = cross_val_score(
    LogisticRegressionCV(cv=5, solver="lbfgs", max_iter=10000, random_state=42, l1_ratios=(0,), use_legacy_attributes=True),
    X_scaled, y, cv=kf, scoring="accuracy",
)
print(f"\n5-Fold CV Accuracy: {acc_cv.mean():.4f} ± {acc_cv.std():.4f}")

# %%
# Confusion matrix
cm = confusion_matrix(y_test, y_pred, labels=list(range(len(DX_ORDER))))
fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(cm, cmap="Blues")
ax.set_xticks(range(len(DX_ORDER)))
ax.set_yticks(range(len(DX_ORDER)))
ax.set_xticklabels(DX_ORDER)
ax.set_yticklabels(DX_ORDER)
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title("Confusion Matrix — Multinomial Logistic")
for i in range(len(DX_ORDER)):
    for j in range(len(DX_ORDER)):
        ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                color="white" if cm[i, j] > cm.max() / 2 else "black")
plt.colorbar(im)
plt.tight_layout()
plt.show()

# %%
# Per-class coefficients (how each feature pushes toward each class)
for k, cls in enumerate(DX_ORDER):
    print(f"=== Class: {cls} ===")
    coefs = pd.Series(mlr.coef_[k], index=X.columns)
    print(coefs.sort_values(key=abs, ascending=False))
    print()

# %%
# Save model
import joblib
joblib.dump(mlr, "multinomial_diagnosis_model.joblib")
joblib.dump(scaler, "multinomial_scaler.joblib")
print("Saved: multinomial_diagnosis_model.joblib, multinomial_scaler.joblib")

# %%
# Ordinal-aware stats (even though model is unordered, we can still check ordering)
y_pred_int = np.array(y_pred)
y_test_int = np.array(y_test)
mae_ord = np.mean(np.abs(y_pred_int - y_test_int))
exact = np.mean(y_pred_int == y_test_int)
within_one = np.mean(np.abs(y_pred_int - y_test_int) <= 1)

print("=== Ordinal-Aware Metrics ===")
print(f"Exact match accuracy:     {exact:.4f}")
print(f"Off-by-one accuracy:      {within_one:.4f} (allows ±1 class error)")
print(f"Mean Absolute Error (MAE): {mae_ord:.4f} classes")

# %%
# Feature coefficient comparison across classes
coef_df = pd.DataFrame(
    {cls: mlr.coef_[k] for k, cls in enumerate(DX_ORDER)},
    index=X.columns,
)
print(coef_df)

fig, ax = plt.subplots(figsize=(8, 5))
coef_df.plot(kind="bar", ax=ax)
ax.axhline(0, color="black", linewidth=0.5)
ax.set_ylabel("Coefficient (standardized)")
ax.set_title("Feature coefficients across classes")
ax.legend(title="Class")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()

# %%
# Predicted class probability distributions
proba_test = mlr.predict_proba(X_test)
proba_df = pd.DataFrame(proba_test, columns=DX_ORDER)
proba_df["actual"] = [DX_ORDER[i] for i in y_test_int]

fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
for ax, cls in zip(axes, DX_ORDER):
    data = [proba_df[proba_df["actual"] == true_cls][cls].values for true_cls in DX_ORDER]
    ax.boxplot(data, labels=DX_ORDER)
    ax.set_title(f"P(predicted = {cls})")
    ax.set_xlabel("Actual class")
    ax.grid(True, alpha=0.3)
axes[0].set_ylabel("Predicted probability")
plt.suptitle("Predicted probability by actual class")
plt.tight_layout()
plt.show()

# %%
# Feature distributions by diagnosis (helps interpret coefficients)
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, col in zip(axes.flat, X.columns):
    data_by_dx = [dx_clean[dx_clean["DIAGNOSIS"] == dx][col].values for dx in DX_ORDER]
    ax.boxplot(data_by_dx, labels=DX_ORDER)
    ax.set_title(col)
    ax.grid(True, alpha=0.3)
plt.suptitle("Cognitive score distribution by diagnosis")
plt.tight_layout()
plt.show()

# %%
# Normalized confusion matrix (rows sum to 1 = per-class recall)
cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(len(DX_ORDER)))
ax.set_yticks(range(len(DX_ORDER)))
ax.set_xticklabels(DX_ORDER)
ax.set_yticklabels(DX_ORDER)
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title("Normalized Confusion Matrix (per-class recall)")
for i in range(len(DX_ORDER)):
    for j in range(len(DX_ORDER)):
        ax.text(j, i, f"{cm_norm[i, j]:.2f}", ha="center", va="center",
                color="white" if cm_norm[i, j] > 0.5 else "black")
plt.colorbar(im)
plt.tight_layout()
plt.show()

# %%
