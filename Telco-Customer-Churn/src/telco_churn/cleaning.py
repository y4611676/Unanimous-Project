"""Telco Churn 資料集清理邏輯（與 notebook 共用，便於測試與重現）。"""

from __future__ import annotations

import pandas as pd


def clean_telco_churn(df_in: pd.DataFrame) -> pd.DataFrame:
    """Telco Churn CSV 的標準清理流程；回傳新 DataFrame。"""
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

    print(f"清理前列數: {n0} → 清理後: {len(out)}（剔除重複 ID: {n_dup}）")
    return out
