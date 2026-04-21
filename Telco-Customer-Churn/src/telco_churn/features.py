"""Feature engineering for the Telco churn dataset.

Keeps the model module focused on training — anything that transforms the
cleaned CSV into model-ready features lives here.
"""

from __future__ import annotations

import pandas as pd


TARGET = "Churn"
ID_COL = "customerID"

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]

CATEGORICAL_FEATURES = [
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add a handful of derived features that consistently help on this dataset."""
    out = df.copy()

    out["tenure_bucket"] = pd.cut(
        out["tenure"],
        bins=[-0.5, 6, 12, 24, 48, 1000],
        labels=["0-6m", "7-12m", "13-24m", "25-48m", "49m+"],
    ).astype(str)

    out["charges_per_month_of_tenure"] = out["TotalCharges"] / out["tenure"].clip(lower=1)

    out["has_online_security_backup"] = (
        (out["OnlineSecurity"] == "Yes") | (out["OnlineBackup"] == "Yes")
    ).astype(int)

    out["total_addons"] = (
        (out["OnlineSecurity"] == "Yes").astype(int)
        + (out["OnlineBackup"] == "Yes").astype(int)
        + (out["DeviceProtection"] == "Yes").astype(int)
        + (out["TechSupport"] == "Yes").astype(int)
        + (out["StreamingTV"] == "Yes").astype(int)
        + (out["StreamingMovies"] == "Yes").astype(int)
    )

    return out


ENGINEERED_NUMERIC = ["charges_per_month_of_tenure", "has_online_security_backup", "total_addons"]
ENGINEERED_CATEGORICAL = ["tenure_bucket"]


def split_X_y(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return the feature matrix and binary target (1 = churned)."""
    y = (df[TARGET] == "Yes").astype(int)
    drop_cols = [c for c in (ID_COL, TARGET) if c in df.columns]
    X = df.drop(columns=drop_cols)
    return X, y


def all_feature_columns() -> tuple[list[str], list[str]]:
    """Return (numeric, categorical) column lists for the ColumnTransformer."""
    numeric = NUMERIC_FEATURES + ENGINEERED_NUMERIC
    categorical = CATEGORICAL_FEATURES + ENGINEERED_CATEGORICAL
    return numeric, categorical
