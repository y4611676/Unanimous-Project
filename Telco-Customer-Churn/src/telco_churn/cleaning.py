"""Telco Churn dataset cleaning logic (shared with the notebook so it's testable and reproducible)."""

from __future__ import annotations

import pandas as pd


def clean_telco_churn(df_in: pd.DataFrame) -> pd.DataFrame:
    """Standard cleaning pipeline for the Telco Churn CSV; returns a new DataFrame."""
    out = df_in.copy()
    n0 = len(out)

    out.columns = out.columns.str.strip()

    obj_cols = out.select_dtypes(include="object").columns
    for c in obj_cols:
        out[c] = out[c].astype(str).str.strip()
        out[c] = out[c].replace({"": pd.NA, "nan": pd.NA})

    dup_mask = out["customerID"].duplicated()
    n_dup = int(dup_mask.sum())
    if n_dup:
        out = out.loc[~dup_mask].copy()

    out["TotalCharges"] = pd.to_numeric(out["TotalCharges"], errors="coerce")
    m_new = (out["tenure"] == 0) & out["TotalCharges"].isna()
    out.loc[m_new, "TotalCharges"] = out.loc[m_new, "MonthlyCharges"]
    med = out["TotalCharges"].median()
    out["TotalCharges"] = out["TotalCharges"].fillna(med)

    out = out[out["Churn"].isin(["Yes", "No"])].copy()
    out = out[out["gender"].isin(["Male", "Female"])].copy()

    out = out[out["tenure"] >= 0].copy()
    out = out[out["MonthlyCharges"] >= 0].copy()

    out["SeniorCitizen"] = (
        pd.to_numeric(out["SeniorCitizen"], errors="coerce").fillna(0).astype(int).clip(0, 1)
    )

    print(f"rows before cleaning: {n0}  →  after: {len(out)}  (dropped duplicate IDs: {n_dup})")
    return out
