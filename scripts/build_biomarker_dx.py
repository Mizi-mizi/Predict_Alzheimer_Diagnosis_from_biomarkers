"""
Build Data/biomarker_dx.csv — biomarkers + DIAGNOSIS for end-to-end
(biomarker → diagnosis) pipeline testing.

Unions biomarker rows from the four score reg files (they share the same
biomarker columns), dedupes on RID+DATE, then joins DIAGNOSIS from
dx_reg.csv.
"""

import os
import pandas as pd

from final_v import ALL_FEATURES, DATA_DIR

SOURCES = ["cdr_reg.csv", "mmse_reg.csv", "moca_reg.csv", "faq_reg.csv"]
OUT_PATH = os.path.join(DATA_DIR, "biomarker_dx.csv")


def main():
    frames = []
    for name in SOURCES:
        df = pd.read_csv(os.path.join(DATA_DIR, name))
        df.columns = df.columns.str.strip()
        keep = ["RID", "DATE"] + [f for f in ALL_FEATURES if f in df.columns]
        frames.append(df[keep])

    biomarkers = pd.concat(frames, ignore_index=True)
    biomarkers["DATE"] = biomarkers["DATE"].astype(str)
    biomarkers = biomarkers.drop_duplicates(subset=["RID", "DATE"])

    dx = pd.read_csv(os.path.join(DATA_DIR, "dx_reg.csv"))
    dx.columns = dx.columns.str.strip()
    dx["DATE"] = dx["DATE"].astype(str)
    dx = dx[["RID", "DATE", "DIAGNOSIS"]].dropna(subset=["DIAGNOSIS"])

    merged = biomarkers.merge(dx, on=["RID", "DATE"], how="inner")
    merged = merged.dropna(subset=ALL_FEATURES + ["DIAGNOSIS"])

    merged.to_csv(OUT_PATH, index=False)
    print(f"Wrote {OUT_PATH}")
    print(f"  rows: {len(merged)}")
    print(f"  columns: {list(merged.columns)}")
    print(f"  DIAGNOSIS value counts:")
    print(merged["DIAGNOSIS"].value_counts().to_string())


if __name__ == "__main__":
    main()
