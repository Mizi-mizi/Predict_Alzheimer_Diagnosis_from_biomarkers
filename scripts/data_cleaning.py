#%%
import pandas as pd
import numpy as np

# Match patients by RID, match visits by date within TOLERANCE window

#%%
# Amyloid read
amyread = pd.read_csv(
    "All_Subjects_AMYREAD_05Mar2026.csv",
    usecols=["RID", "SCANDATE", "CONGRU", "CONSENSRES"],
)
# CONGRU missing values fall back to CONSENSRES
amyread["CONGRU"] = amyread["CONGRU"].fillna(amyread["CONSENSRES"])
amyread = amyread.drop(columns=["CONSENSRES", "CONGRU"])
amyread.head()

#%%
# APOE genotype → count of ε4 alleles (main AD risk allele)
apoe = pd.read_csv("All_Subjects_APOERES_05Mar2026.csv", usecols=["RID", "GENOTYPE"])
apoe["APOE4_COUNT"] = apoe["GENOTYPE"].str.count("4")
apoe = apoe.drop(columns=["GENOTYPE"])
apoe.head()

#%%
# Blood biomarker trajectories — pivot from long to wide
biomarker = pd.read_csv(
    "All_Subjects_FNIHBC_BLOOD_BIOMARKER_TRAJECTORIES_05Mar2026.csv",
    usecols=["RID", "EXAMDATE", "TESTNAME", "TESTVALUE", "UNITS"],
)
# Normalize TESTNAME: remove spaces and lowercase (e.g. "Abeta 42"=="Abeta42", "NFL"=="NfL")
biomarker["TESTNAME"] = biomarker["TESTNAME"].str.replace(" ", "", regex=False).str.lower()
biomarker = biomarker.pivot_table(
    index=["RID", "EXAMDATE"], columns="TESTNAME", values="TESTVALUE", aggfunc="first"
).reset_index()
biomarker.columns.name = None
biomarker.head()

#%%
# CDR — keep only versions 1 and 2 (v3 is not a full interview)
cdr_orig = pd.read_csv(
    "All_Subjects_CDR_05Mar2026.csv", usecols=["RID", "VISDATE", "CDVERSION", "CDRSB"]
)
cdr = cdr_orig[cdr_orig["CDVERSION"].isin([1, 2])]
cdr.head()

#%%
faq = pd.read_csv(
    "All_Subjects_FAQ_05Mar2026.csv", usecols=["RID", "SOURCE", "FAQTOTAL"]
)
faq = faq.drop(columns="SOURCE")
faq.head()

#%%
mmse = pd.read_csv(
    "All_Subjects_MMSE_05Mar2026.csv", usecols=["RID", "VISDATE", "MMSCORE"]
)
mmse.head()

#%%
moca = pd.read_csv("All_Subjects_MOCA_05Mar2026.csv", usecols=["RID", "VISDATE", "MOCA"])
moca.head()

# %%
# Combine all dated tables by RID + date within TOLERANCE using merge_asof
TOLERANCE = pd.Timedelta("365 days")

# Rename date columns to a common DATE
amyread_m   = amyread.rename(columns={"SCANDATE": "DATE"}).copy()
biomarker_m = biomarker.rename(columns={"EXAMDATE": "DATE"}).copy()
cdr_m       = cdr.rename(columns={"VISDATE": "DATE"}).copy()
mmse_m      = mmse.rename(columns={"VISDATE": "DATE"}).copy()
moca_m      = moca.rename(columns={"VISDATE": "DATE"}).copy()

dated_dfs = [amyread_m, biomarker_m, cdr_m, mmse_m, moca_m]
for df in dated_dfs:
    df["DATE"] = pd.to_datetime(df["DATE"])
    df.dropna(subset=["DATE"], inplace=True)
    df.sort_values("DATE", inplace=True)
    df.drop_duplicates(subset=["RID", "DATE"], keep="first", inplace=True)

# Build unified RID+DATE index from all dated tables
all_dates = (
    pd.concat([df[["RID", "DATE"]] for df in dated_dfs])
    .drop_duplicates()
    .sort_values(["RID", "DATE"])
    .reset_index(drop=True)
)

# Cluster dates within TOLERANCE per patient → keep earliest date per cluster
all_dates["prev_date"] = all_dates.groupby("RID")["DATE"].shift(1)
all_dates["new_visit"] = (
    (all_dates["DATE"] - all_dates["prev_date"]) > TOLERANCE
) | all_dates["prev_date"].isna()
all_dates["visit_group"] = all_dates.groupby("RID")["new_visit"].cumsum()
all_dates = (
    all_dates.groupby(["RID", "visit_group"])["DATE"]
    .first()
    .reset_index()[["RID", "DATE"]]
    .sort_values("DATE")
    .reset_index(drop=True)
)

# Fuzzy-join each table onto the unified index
merged = all_dates.copy()
for df in dated_dfs:
    merged = pd.merge_asof(
        merged.sort_values("DATE"),
        df,
        on="DATE",
        by="RID",
        tolerance=TOLERANCE,
        direction="nearest",
    )

# Replace ADNI missing-value sentinel with NaN
merged = merged.replace(-4, np.nan)

# Collapse duplicate RID+DATE rows (take first non-null per column)
merged = merged.groupby(["RID", "DATE"], as_index=False).first()

# Undated tables: merge on RID only (deduplicated first)
merged = merged.merge(apoe.drop_duplicates(subset=["RID"]), on="RID", how="left")
merged = merged.merge(faq.drop_duplicates(subset=["RID"]), on="RID", how="left")

# Age is keyed on PTID — bridge via RID↔PTID map from CDR file
ages = pd.read_csv("All_Subjects_My_Table_05Mar2026.csv")
rid_ptid = pd.read_csv(
    "All_Subjects_CDR_05Mar2026.csv", usecols=["RID", "PTID"]
).drop_duplicates()
ages = ages.merge(rid_ptid, left_on="subject_id", right_on="PTID", how="inner")
ages = ages[["RID", "entry_age"]].drop_duplicates(subset=["RID"])
merged = merged.merge(ages, on="RID", how="left")

merged.head()

# %%
# Per-target subsets: keep rows with that score, drop other score columns, drop NaN
cdr_reg = merged[~merged["CDRSB"].isna()].drop(
    columns=["CDVERSION", "MMSCORE", "MOCA", "FAQTOTAL"]
).dropna()
cdr_reg.head()

# %%
faq_reg = merged[~merged["FAQTOTAL"].isna()].drop(
    columns=["CDVERSION", "CDRSB", "MOCA", "MMSCORE"]
).dropna()
faq_reg.head()

# %%
mmse_reg = merged[~merged["MMSCORE"].isna()].drop(
    columns=["CDVERSION", "CDRSB", "MOCA", "FAQTOTAL"]
).dropna()
mmse_reg.head()

#%%
moca_reg = merged[~merged["MOCA"].isna()].drop(
    columns=["CDVERSION", "CDRSB", "FAQTOTAL", "MMSCORE"]
).dropna()
moca_reg.head()

# %%
cdr_reg.to_csv("cdr_reg.csv", index=False)
faq_reg.to_csv("faq_reg.csv", index=False)
moca_reg.to_csv("moca_reg.csv", index=False)
mmse_reg.to_csv("mmse_reg.csv", index=False)

# %%
# Load diagnosis (1=CN, 2=MCI, 3=Dementia); keep most recent per patient
diagnosis = pd.read_csv(
    "All_Subjects_DXSUM_05Mar2026.csv", usecols=["RID", "EXAMDATE", "DIAGNOSIS"]
)
diagnosis = diagnosis.replace(-4, np.nan).dropna(subset=["DIAGNOSIS"])
diagnosis = diagnosis.sort_values("EXAMDATE").drop_duplicates(subset=["RID"], keep="last")
diagnosis["DIAGNOSIS"] = diagnosis["DIAGNOSIS"].map({1: "CN", 2: "MCI", 3: "Dementia"})

# Build (score, diagnosis) pairs for each cognitive measure
score_tables = [
    ("CDRSB",    merged[["RID", "CDRSB"]].dropna().merge(diagnosis[["RID", "DIAGNOSIS"]], on="RID", how="inner")),
    ("FAQTOTAL", merged[["RID", "FAQTOTAL"]].dropna().merge(diagnosis[["RID", "DIAGNOSIS"]], on="RID", how="inner")),
    ("MMSCORE",  merged[["RID", "MMSCORE"]].dropna().merge(diagnosis[["RID", "DIAGNOSIS"]], on="RID", how="inner")),
    ("MOCA",     merged[["RID", "MOCA"]].dropna().merge(diagnosis[["RID", "DIAGNOSIS"]], on="RID", how="inner")),
]

print("=== Mean scores by diagnosis group ===")
for name, df in score_tables:
    print(f"\n{name}:")
    print(df.groupby("DIAGNOSIS")[name].describe()[["count", "mean", "std"]].round(2))

# %%
# One-way ANOVA: do group means differ significantly?
from scipy import stats

print("=== One-way ANOVA (p-values) ===")
for name, df in score_tables:
    groups = [g[name].values for _, g in df.groupby("DIAGNOSIS")]
    f_stat, p_val = stats.f_oneway(*groups)
    print(f"{name}: F={f_stat:.2f}, p={p_val:.2e}")

# %%
# Box plots of each score grouped by diagnosis
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 4, figsize=(18, 5))
for ax, (name, df) in zip(axes, score_tables):
    df.boxplot(column=name, by="DIAGNOSIS", ax=ax)
    ax.set_title(name)
    ax.set_xlabel("Diagnosis")
plt.suptitle("Cognitive scores by diagnosis group")
plt.tight_layout()
plt.show()

# %%
# Diagnosis dataset: fuzzy-join cognitive scores with diagnosis by RID + date
diagnosis_dated = pd.read_csv(
    "All_Subjects_DXSUM_05Mar2026.csv", usecols=["RID", "EXAMDATE", "DIAGNOSIS"]
)
diagnosis_dated = diagnosis_dated.replace(-4, np.nan).dropna(subset=["DIAGNOSIS", "EXAMDATE"])
diagnosis_dated["DIAGNOSIS"] = diagnosis_dated["DIAGNOSIS"].map({1: "CN", 2: "MCI", 3: "Dementia"})
diagnosis_dated["DATE"] = pd.to_datetime(diagnosis_dated["EXAMDATE"])
diagnosis_dated = diagnosis_dated.drop(columns=["EXAMDATE"]).dropna(subset=["DATE"])
diagnosis_dated = diagnosis_dated.sort_values("DATE").drop_duplicates(subset=["RID", "DATE"], keep="first")

# Collect all dates from CDR, FAQ, MMSE, MOCA, and diagnosis
score_dfs = {
    "CDRSB": cdr.rename(columns={"VISDATE": "DATE"})[["RID", "DATE", "CDRSB"]],
    "FAQTOTAL": faq.merge(
        pd.read_csv("All_Subjects_FAQ_05Mar2026.csv", usecols=["RID"]).drop_duplicates(),
        on="RID",
    )[["RID", "FAQTOTAL"]],
    "MMSCORE": mmse.rename(columns={"VISDATE": "DATE"})[["RID", "DATE", "MMSCORE"]],
    "MOCA": moca.rename(columns={"VISDATE": "DATE"})[["RID", "DATE", "MOCA"]],
}

# Start from CDR dates as base (it has the most clinical relevance)
dx_base = cdr.rename(columns={"VISDATE": "DATE"})[["RID", "DATE", "CDRSB"]].copy()
dx_base["DATE"] = pd.to_datetime(dx_base["DATE"])
dx_base = dx_base.dropna(subset=["DATE"]).sort_values("DATE")
dx_base = dx_base.drop_duplicates(subset=["RID", "DATE"], keep="first")

# Fuzzy-join MMSE, MOCA onto CDR dates
for name, col in [("MMSCORE", mmse), ("MOCA", moca)]:
    df_m = col.rename(columns={"VISDATE": "DATE"}).copy()
    df_m["DATE"] = pd.to_datetime(df_m["DATE"])
    df_m = df_m.dropna(subset=["DATE"]).sort_values("DATE")
    df_m = df_m.drop_duplicates(subset=["RID", "DATE"], keep="first")
    dx_base = pd.merge_asof(
        dx_base.sort_values("DATE"), df_m,
        on="DATE", by="RID", tolerance=TOLERANCE, direction="nearest",
    )

# Fuzzy-join FAQ (no date loaded — merge on RID)
dx_base = dx_base.merge(faq.drop_duplicates(subset=["RID"]), on="RID", how="left")

# Fuzzy-join diagnosis by date
dx_base = pd.merge_asof(
    dx_base.sort_values("DATE"), diagnosis_dated,
    on="DATE", by="RID", tolerance=TOLERANCE, direction="nearest",
)

dx_reg = dx_base.copy()
dx_reg.to_csv("dx_reg.csv", index=False)
print(f"Shape: {dx_reg.shape}")
print(f"\nDiagnosis distribution:\n{dx_reg['DIAGNOSIS'].value_counts()}")
print(f"\nMissing values:\n{dx_reg.isna().sum()}")
dx_reg.head()

# %%
# Full model dataset: biomarkers + cognitive scores + diagnosis
full_cols = ["RID", "DATE", "ptau217_ratio", "nfl", "entry_age", "abeta42", "gfap",
             "CDRSB", "FAQTOTAL", "MMSCORE", "MOCA", "DIAGNOSIS"]
# Merge biomarkers from merged, cognitive scores + diagnosis from dx_reg
full_reg = dx_reg.merge(
    merged[["RID", "DATE", "ptau217_ratio", "nfl", "entry_age", "abeta42", "gfap"]],
    on=["RID", "DATE"], how="left",
)
full_reg = full_reg[[c for c in full_cols if c in full_reg.columns]]
full_reg.to_csv("full_reg.csv", index=False)
print(f"Shape: {full_reg.shape}")
print(f"\nMissing values:\n{full_reg.isna().sum()}")
full_reg.head()

# %%
# Logistic regression: predict diagnosis from cognitive scores
from sklearn.linear_model import LogisticRegressionCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt

dx_clean = dx_reg[["CDRSB", "FAQTOTAL", "MMSCORE", "MOCA", "DIAGNOSIS"]].dropna()

X_dx = dx_clean[["CDRSB", "FAQTOTAL", "MMSCORE", "MOCA"]]
y_dx = dx_clean["DIAGNOSIS"]

scaler_dx = StandardScaler()
X_dx_scaled = scaler_dx.fit_transform(X_dx)

X_dx_train, X_dx_test, y_dx_train, y_dx_test = train_test_split(
    X_dx_scaled, y_dx, test_size=0.2, random_state=42, stratify=y_dx
)

# Multinomial logistic regression with CV-tuned regularization
log_reg = LogisticRegressionCV(
    cv=5, solver="lbfgs", max_iter=10000, random_state=42,
)
log_reg.fit(X_dx_train, y_dx_train)

y_dx_pred = log_reg.predict(X_dx_test)
print(f"=== Logistic Regression (n={len(dx_clean)}) ===")
print(f"Accuracy: {accuracy_score(y_dx_test, y_dx_pred):.4f}")
print(f"\nClassification report:")
print(classification_report(y_dx_test, y_dx_pred))

# 5-Fold CV
kf = KFold(n_splits=5, shuffle=True, random_state=42)
acc_cv = cross_val_score(
    LogisticRegressionCV(cv=5, solver="lbfgs", max_iter=10000, random_state=42),
    X_dx_scaled, y_dx, cv=kf, scoring="accuracy",
)
print(f"5-Fold CV Accuracy: {acc_cv.mean():.4f} ± {acc_cv.std():.4f}")

# Confusion matrix
fig, ax = plt.subplots(figsize=(6, 5))
labels = sorted(y_dx.unique())
cm = confusion_matrix(y_dx_test, y_dx_pred, labels=labels)
im = ax.imshow(cm, cmap="Blues")
ax.set_xticks(range(len(labels)))
ax.set_yticks(range(len(labels)))
ax.set_xticklabels(labels)
ax.set_yticklabels(labels)
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title("Confusion Matrix")
for i in range(len(labels)):
    for j in range(len(labels)):
        ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                color="white" if cm[i, j] > cm.max() / 2 else "black")
plt.colorbar(im)
plt.tight_layout()
plt.show()

# %%
# Save models
import joblib

joblib.dump(log_reg, "logistic_regression_diagnosis.joblib")
joblib.dump(scaler_dx, "scaler_diagnosis.joblib")
print("Saved: logistic_regression_diagnosis.joblib, scaler_diagnosis.joblib")

# To load later:
# log_reg = joblib.load("logistic_regression_diagnosis.joblib")
# scaler_dx = joblib.load("scaler_diagnosis.joblib")

# %%
# Lasso regression: predict CDRSB from biomarkers + covariates
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

X = cdr_reg.drop(columns=["RID", "DATE", "CDRSB"])
y = cdr_reg["CDRSB"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

lasso = LassoCV(cv=5, random_state=42, max_iter=10000)
lasso.fit(X_train, y_train)

mae_orig = mean_absolute_error(y_test, lasso.predict(X_test))
print("Best alpha:", lasso.alpha_)
print("R² on test set:", lasso.score(X_test, y_test))
print("MAE on test set:", mae_orig)

coef = pd.Series(lasso.coef_, index=X.columns)
selected_features_lasso = ["ptau217_ratio", "nfl", "entry_age", "abeta42", "gfap"]
print("\nLasso selected features:")
print(coef[coef != 0].sort_values(key=abs, ascending=False))

# %%
# Elastic Net: blends L1 (Lasso) + L2 (Ridge) penalties for feature selection
from sklearn.linear_model import ElasticNetCV

enet = ElasticNetCV(
    l1_ratio=[0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99],  # mix of L1/L2
    cv=5, random_state=42, max_iter=10000,
)
enet.fit(X_train, y_train)

mae_enet = mean_absolute_error(y_test, enet.predict(X_test))
print("=== Elastic Net ===")
print(f"Best alpha: {enet.alpha_:.6f}, Best l1_ratio: {enet.l1_ratio_}")
print(f"R² on test set: {enet.score(X_test, y_test):.4f}")
print(f"MAE on test set: {mae_enet:.4f}")

coef_enet = pd.Series(enet.coef_, index=X.columns)
print(f"\nElastic Net selected features ({(coef_enet != 0).sum()}):")
print(coef_enet[coef_enet != 0].sort_values(key=abs, ascending=False))

# Compare Lasso vs Elastic Net feature selection
print("\n=== Feature Selection Comparison ===")
lasso_feats = set(coef[coef != 0].index)
enet_feats = set(coef_enet[coef_enet != 0].index)
print(f"Lasso only:       {lasso_feats - enet_feats or 'none'}")
print(f"Elastic Net only: {enet_feats - lasso_feats or 'none'}")
print(f"Both:             {lasso_feats & enet_feats}")

selected_features = selected_features_lasso  # default to Lasso; change if Elastic Net is better

# %%
# Random Forest on selected features to predict CDRSB
from sklearn.ensemble import RandomForestRegressor

X_selected = cdr_reg[selected_features]
X_sel_train, X_sel_test, y_sel_train, y_sel_test = train_test_split(
    X_selected, y, test_size=0.2, random_state=42
)

rf = RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1)
rf.fit(X_sel_train, y_sel_train)

rf_r2 = rf.score(X_sel_test, y_sel_test)
rf_mae = mean_absolute_error(y_sel_test, rf.predict(X_sel_test))
print("=== Random Forest (5 selected features) ===")
print(f"Features: {selected_features}")
print(f"R² on test set: {rf_r2:.4f}")
print(f"MAE on test set: {rf_mae:.4f}")

rf_imp = pd.Series(rf.feature_importances_, index=selected_features)
print("\nFeature importance:")
print(rf_imp.sort_values(ascending=False))

# %%
# Visualize a representative tree from the Random Forest
from sklearn.tree import plot_tree
import matplotlib.pyplot as plt

# Pick the tree with median test performance
tree_scores = []
for i, tree in enumerate(rf.estimators_):
    tree_scores.append(tree.score(X_sel_test, y_sel_test))
best_idx = max(range(len(tree_scores)), key=lambda i: tree_scores[i])

fig, ax = plt.subplots(figsize=(20, 10))
plot_tree(
    rf.estimators_[best_idx],
    feature_names=selected_features,
    filled=True,
    rounded=True,
    max_depth=3,  # limit depth for readability
    fontsize=10,
    ax=ax,
)
ax.set_title(f"Best tree (#{best_idx}, R²={tree_scores[best_idx]:.3f})")
plt.tight_layout()
plt.show()

# %%
# Assess Random Forest performance
from sklearn.model_selection import cross_val_score, cross_val_predict, KFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt

# Single split metrics
y_pred = rf.predict(X_sel_test)
print("=== Single Split ===")
print(f"R²:   {r2_score(y_sel_test, y_pred):.4f}")
print(f"MAE:  {mean_absolute_error(y_sel_test, y_pred):.4f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_sel_test, y_pred)):.4f}")

# 5-Fold CV
kf = KFold(n_splits=5, shuffle=True, random_state=42)
rf_cv = RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1)
r2_kf = cross_val_score(rf_cv, X_selected, y, cv=kf, scoring="r2")
mae_kf = -cross_val_score(rf_cv, X_selected, y, cv=kf, scoring="neg_mean_absolute_error")
print("\n=== 5-Fold CV ===")
print(f"R²:  {r2_kf.mean():.4f} ± {r2_kf.std():.4f}")
print(f"MAE: {mae_kf.mean():.4f} ± {mae_kf.std():.4f}")

# Cross-validated predictions for plots
preds_cv = cross_val_predict(rf_cv, X_selected, y, cv=kf)

# Predicted vs Actual plots
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].scatter(y_sel_test, y_pred, alpha=0.5)
axes[0].plot([y.min(), y.max()], [y.min(), y.max()], "r--")
axes[0].set_xlabel("Actual CDRSB")
axes[0].set_ylabel("Predicted CDRSB")
axes[0].set_title("Single Split: Predicted vs Actual")

axes[1].scatter(y, preds_cv, alpha=0.5)
axes[1].plot([y.min(), y.max()], [y.min(), y.max()], "r--")
axes[1].set_xlabel("Actual CDRSB")
axes[1].set_ylabel("Predicted CDRSB")
axes[1].set_title("5-Fold CV: Predicted vs Actual")

plt.tight_layout()
plt.show()

# Residual distribution
residuals = y.values - preds_cv
fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(residuals, bins=30, edgecolor="black")
ax.axvline(0, color="r", linestyle="--")
ax.set_xlabel("Residual (Actual - Predicted)")
ax.set_ylabel("Count")
ax.set_title("5-Fold CV Residual Distribution")
plt.tight_layout()
plt.show()

# %%
# Improve performance: tuned RF + Gradient Boosting + comparison
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import GradientBoostingRegressor

# 1. Tuned Random Forest via RandomizedSearchCV
rf_params = {
    "n_estimators": [200, 500, 1000],
    "max_depth": [3, 5, 10, 20, None],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 5],
    "max_features": ["sqrt", "log2", 0.5, 1.0],
}
rf_search = RandomizedSearchCV(
    RandomForestRegressor(random_state=42, n_jobs=-1),
    rf_params, n_iter=50, cv=5, scoring="r2", random_state=42, n_jobs=-1,
)
rf_search.fit(X_sel_train, y_sel_train)
rf_tuned = rf_search.best_estimator_

print("=== Tuned Random Forest ===")
print(f"Best params: {rf_search.best_params_}")
print(f"R² on test set: {rf_tuned.score(X_sel_test, y_sel_test):.4f}")
print(f"MAE on test set: {mean_absolute_error(y_sel_test, rf_tuned.predict(X_sel_test)):.4f}")

# 2. Gradient Boosting (often better than RF on tabular data)
gb_params = {
    "n_estimators": [100, 200, 500],
    "max_depth": [2, 3, 5],
    "learning_rate": [0.01, 0.05, 0.1, 0.2],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 5],
    "subsample": [0.7, 0.8, 0.9, 1.0],
}
gb_search = RandomizedSearchCV(
    GradientBoostingRegressor(random_state=42),
    gb_params, n_iter=50, cv=5, scoring="r2", random_state=42, n_jobs=-1,
)
gb_search.fit(X_sel_train, y_sel_train)
gb_tuned = gb_search.best_estimator_

print("\n=== Tuned Gradient Boosting ===")
print(f"Best params: {gb_search.best_params_}")
print(f"R² on test set: {gb_tuned.score(X_sel_test, y_sel_test):.4f}")
print(f"MAE on test set: {mean_absolute_error(y_sel_test, gb_tuned.predict(X_sel_test)):.4f}")

# 3. Try with all Lasso features (7) instead of 5
all_lasso_features = coef[coef != 0].index.tolist()
X_all_train = cdr_reg[all_lasso_features].loc[X_sel_train.index]
X_all_test = cdr_reg[all_lasso_features].loc[X_sel_test.index]
gb_all = GradientBoostingRegressor(**gb_search.best_params_, random_state=42)
gb_all.fit(X_all_train, y_sel_train)

print("\n=== Gradient Boosting (all 7 Lasso features) ===")
print(f"R² on test set: {gb_all.score(X_all_test, y_sel_test):.4f}")
print(f"MAE on test set: {mean_absolute_error(y_sel_test, gb_all.predict(X_all_test)):.4f}")

# Summary comparison
print("\n=== Model Comparison ===")
models = {
    "Lasso":               (lasso.score(X_test, y_test), mean_absolute_error(y_test, lasso.predict(X_test))),
    "RF (default)":        (rf_r2, rf_mae),
    "RF (tuned)":          (rf_tuned.score(X_sel_test, y_sel_test), mean_absolute_error(y_sel_test, rf_tuned.predict(X_sel_test))),
    "GB (tuned)":          (gb_tuned.score(X_sel_test, y_sel_test), mean_absolute_error(y_sel_test, gb_tuned.predict(X_sel_test))),
    "GB (7 features)":     (gb_all.score(X_all_test, y_sel_test), mean_absolute_error(y_sel_test, gb_all.predict(X_all_test))),
}
for name, (r2, mae) in models.items():
    print(f"{name:20s} — R²: {r2:.4f}, MAE: {mae:.4f}")

# %%
# Lasso on log-transformed CDRSB (log1p handles zeros)
y_log = np.log1p(cdr_reg["CDRSB"])

X_train_log, X_test_log, y_train_log, y_test_log = train_test_split(
    X_scaled, y_log, test_size=0.2, random_state=42
)

lasso_log = LassoCV(cv=5, random_state=42, max_iter=10000)
lasso_log.fit(X_train_log, y_train_log)

# MAE in original scale (expm1 inverts log1p)
mae_log = mean_absolute_error(
    np.expm1(y_test_log), np.expm1(lasso_log.predict(X_test_log))
)
print("=== Log-transformed CDRSB ===")
print("Best alpha:", lasso_log.alpha_)
print("R² on test set (log scale):", lasso_log.score(X_test_log, y_test_log))
print("MAE on test set (original scale):", mae_log)

coef_log = pd.Series(lasso_log.coef_, index=X.columns)
print("\nSelected features:")
print(coef_log[coef_log != 0].sort_values(key=abs, ascending=False))

print("\n=== Comparison (single split) ===")
print(f"Original CDRSB — R²: {lasso.score(X_test, y_test):.4f}, MAE: {mae_orig:.4f}, features: {(coef != 0).sum()}")
print(f"Log(1+CDRSB)   — R²: {lasso_log.score(X_test_log, y_test_log):.4f}, MAE: {mae_log:.4f}, features: {(coef_log != 0).sum()}")

# %%
# 5-Fold Cross-Validation
from sklearn.model_selection import cross_val_score, KFold
from sklearn.linear_model import Lasso
from sklearn.pipeline import make_pipeline

kf = KFold(n_splits=5, shuffle=True, random_state=42)

pipe_orig = make_pipeline(StandardScaler(), Lasso(alpha=lasso.alpha_, max_iter=10000))
r2_kf_orig  = cross_val_score(pipe_orig, X, y, cv=kf, scoring="r2")
mae_kf_orig = -cross_val_score(pipe_orig, X, y, cv=kf, scoring="neg_mean_absolute_error")

pipe_log = make_pipeline(StandardScaler(), Lasso(alpha=lasso_log.alpha_, max_iter=10000))
r2_kf_log = cross_val_score(pipe_log, X, y_log, cv=kf, scoring="r2")

mae_kf_log = []
for train_idx, test_idx in kf.split(X):
    pipe = make_pipeline(StandardScaler(), Lasso(alpha=lasso_log.alpha_, max_iter=10000))
    pipe.fit(X.iloc[train_idx], y_log.iloc[train_idx])
    pred_log = pipe.predict(X.iloc[test_idx])
    mae_kf_log.append(
        mean_absolute_error(np.expm1(y_log.iloc[test_idx]), np.expm1(pred_log))
    )

print("=== 5-Fold Cross-Validation ===")
print(f"Original CDRSB — R²: {r2_kf_orig.mean():.4f} ± {r2_kf_orig.std():.4f}, MAE: {mae_kf_orig.mean():.4f} ± {mae_kf_orig.std():.4f}")
print(f"Log(1+CDRSB)   — R²: {np.mean(r2_kf_log):.4f} ± {np.std(r2_kf_log):.4f}, MAE: {np.mean(mae_kf_log):.4f} ± {np.std(mae_kf_log):.4f}")

# %%
# Leave-One-Out CV: collect all predictions, compute metrics once (no per-fold R² warnings)
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import r2_score

loo = LeaveOneOut()

preds_orig = np.full(len(y), np.nan)
for train_idx, test_idx in loo.split(X):
    pipe = make_pipeline(StandardScaler(), Lasso(alpha=lasso.alpha_, max_iter=10000))
    pipe.fit(X.iloc[train_idx], y.iloc[train_idx])
    preds_orig[test_idx] = pipe.predict(X.iloc[test_idx])

preds_log = np.full(len(y_log), np.nan)
for train_idx, test_idx in loo.split(X):
    pipe = make_pipeline(StandardScaler(), Lasso(alpha=lasso_log.alpha_, max_iter=10000))
    pipe.fit(X.iloc[train_idx], y_log.iloc[train_idx])
    preds_log[test_idx] = pipe.predict(X.iloc[test_idx])

print("=== Leave-One-Out Cross-Validation ===")
print(f"Original CDRSB — R²: {r2_score(y, preds_orig):.4f}, MAE: {mean_absolute_error(y, preds_orig):.4f}")
print(f"Log(1+CDRSB)   — R²: {r2_score(y_log, preds_log):.4f}, MAE (original scale): {mean_absolute_error(np.expm1(y_log), np.expm1(preds_log)):.4f}")
# %%
