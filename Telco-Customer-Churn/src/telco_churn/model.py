"""Training pipeline for Telco churn: three sklearn models, cross-validated AUC,
plus a fitted final pipeline saved for the Streamlit app to reuse.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from telco_churn.features import (
    add_engineered_features,
    all_feature_columns,
    split_X_y,
)


RANDOM_STATE = 42
ARTIFACT_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "churn_model.joblib"


def make_preprocessor() -> ColumnTransformer:
    """Numeric → StandardScaler, categorical → OneHotEncoder (ignore unseen)."""
    numeric, categorical = all_feature_columns()
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )


def make_models() -> dict[str, Pipeline]:
    """Return three candidate pipelines to benchmark.

    Logistic Regression sets a fast, interpretable baseline; Random Forest and
    Gradient Boosting typically squeeze 1–3 extra AUC points out of this dataset.
    """
    pre = make_preprocessor()
    return {
        "logistic_regression": Pipeline([
            ("pre", pre),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced",
                                       random_state=RANDOM_STATE)),
        ]),
        "random_forest": Pipeline([
            ("pre", pre),
            ("clf", RandomForestClassifier(n_estimators=300, max_depth=10,
                                           class_weight="balanced",
                                           random_state=RANDOM_STATE, n_jobs=-1)),
        ]),
        "gradient_boosting": Pipeline([
            ("pre", pre),
            ("clf", GradientBoostingClassifier(n_estimators=200, max_depth=3,
                                               random_state=RANDOM_STATE)),
        ]),
    }


@dataclass
class BenchmarkRow:
    model: str
    cv_auc_mean: float
    cv_auc_std: float
    test_auc: float


def benchmark(df: pd.DataFrame, *, test_size: float = 0.2, cv_splits: int = 5
              ) -> tuple[pd.DataFrame, dict[str, Pipeline], tuple]:
    """Cross-validate all candidate models, fit on the train split, report test AUC.

    Returns (results_df, fitted_pipelines, (X_train, X_test, y_train, y_test)).
    StratifiedKFold keeps the ~27% positive class balanced across folds — this
    matters because naive KFold can produce folds with no churners on small data.
    """
    df = add_engineered_features(df)
    X, y = split_X_y(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=RANDOM_STATE
    )

    cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=RANDOM_STATE)
    rows: list[BenchmarkRow] = []
    fitted: dict[str, Pipeline] = {}

    for name, pipe in make_models().items():
        cv_scores = cross_val_score(pipe, X_train, y_train, scoring="roc_auc",
                                    cv=cv, n_jobs=-1)
        pipe.fit(X_train, y_train)
        test_proba = pipe.predict_proba(X_test)[:, 1]
        from sklearn.metrics import roc_auc_score
        test_auc = roc_auc_score(y_test, test_proba)
        rows.append(BenchmarkRow(name, cv_scores.mean(), cv_scores.std(), test_auc))
        fitted[name] = pipe

    results = pd.DataFrame([r.__dict__ for r in rows]).sort_values(
        "cv_auc_mean", ascending=False
    ).reset_index(drop=True)

    return results, fitted, (X_train, X_test, y_train, y_test)


def fit_final(df: pd.DataFrame, model_name: str = "gradient_boosting") -> Pipeline:
    """Fit the chosen model on the full dataset and persist it to disk."""
    df = add_engineered_features(df)
    X, y = split_X_y(df)
    pipe = make_models()[model_name]
    pipe.fit(X, y)

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, ARTIFACT_PATH)
    return pipe


def load_model() -> Pipeline:
    """Load the persisted model for inference (used by the Streamlit app)."""
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"No model found at {ARTIFACT_PATH}. Run `fit_final()` first, e.g. "
            f"via `python -m telco_churn.model path/to/telco.csv`."
        )
    return joblib.load(ARTIFACT_PATH)


def predict_churn(pipe: Pipeline, customer: dict) -> float:
    """Return P(churn) for a single customer dict matching the raw Telco schema."""
    row = pd.DataFrame([customer])
    row = add_engineered_features(row)
    return float(pipe.predict_proba(row)[0, 1])


if __name__ == "__main__":
    import sys
    from telco_churn.cleaning import clean_telco_churn

    if len(sys.argv) < 2:
        print("usage: python -m telco_churn.model <path/to/Telco-Customer-Churn.csv>")
        raise SystemExit(1)

    raw = pd.read_csv(sys.argv[1])
    cleaned = clean_telco_churn(raw)
    results, _, _ = benchmark(cleaned)
    print("\nCross-validated benchmark:")
    print(results.to_string(index=False))
    best = results.iloc[0]["model"]
    print(f"\nFitting final model: {best}")
    fit_final(cleaned, best)
    print(f"Saved to {ARTIFACT_PATH}")
