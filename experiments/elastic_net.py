# %%
# Elastic Net: feature selection for CDRSB, FAQTOTAL, MOCA, MMSCORE
import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNetCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

L1_RATIOS = [0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99]


def run_enet(df, target):
    X = df.drop(columns=["RID", "DATE", target])
    y = df[target]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    enet = ElasticNetCV(
        l1_ratio=L1_RATIOS, cv=5, random_state=42, max_iter=10000
    )
    enet.fit(X_train, y_train)

    mae = mean_absolute_error(y_test, enet.predict(X_test))
    print(f"=== Elastic Net → {target} ===")
    print(f"Best alpha: {enet.alpha_:.6f}, Best l1_ratio: {enet.l1_ratio_}")
    print(f"R² on test set: {enet.score(X_test, y_test):.4f}")
    print(f"MAE on test set: {mae:.4f}")

    coef = pd.Series(enet.coef_, index=X.columns)
    selected = coef[coef != 0].sort_values(key=abs, ascending=False)
    print(f"\nSelected features ({len(selected)}):")
    print(selected)
    return enet, coef

# %%
# CDRSB
cdr_reg = pd.read_csv("../cleaned_data/cdr_reg.csv")
enet_cdr, coef_cdr = run_enet(cdr_reg, "CDRSB")

# %%
# FAQTOTAL
faq_reg = pd.read_csv("../cleaned_data/faq_reg.csv")
enet_faq, coef_faq = run_enet(faq_reg, "FAQTOTAL")

# %%
# MOCA
moca_reg = pd.read_csv("../cleaned_data/moca_reg.csv")
enet_moca, coef_moca = run_enet(moca_reg, "MOCA")

# %%
# MMSCORE
mmse_reg = pd.read_csv("../cleaned_data/mmse_reg.csv")
enet_mmse, coef_mmse = run_enet(mmse_reg, "MMSCORE")

# %%
