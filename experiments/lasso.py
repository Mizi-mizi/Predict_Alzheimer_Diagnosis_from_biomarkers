# %%
# Lasso regression: predict CDRSB from biomarkers + covariates
import pandas as pd
import numpy as np
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

cdr_reg = pd.read_csv("../cleaned_data/cdr_reg.csv")


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
faq_reg = pd.read_csv("../cleaned_data/faq_reg.csv")


X = faq_reg.drop(columns=["RID", "DATE", "FAQTOTAL"])
y = faq_reg["FAQTOTAL"]

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
# Lasso regression: predict CDRSB from biomarkers + covariates

moca_reg = pd.read_csv("../cleaned_data/moca_reg.csv")


X = moca_reg.drop(columns=["RID", "DATE", "MOCA"])
y = moca_reg["MOCA"]

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
# %%
# Lasso regression: predict CDRSB from biomarkers + covariates

mmse_reg = pd.read_csv("../cleaned_data/mmse_reg.csv")


X = moca_reg.drop(columns=["RID", "DATE", "MMSE"])
y = moca_reg["MOCA"]

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