"""Telco customer churn — cleaning, feature engineering, modeling, evaluation."""

from telco_churn.cleaning import clean_telco_churn
from telco_churn.features import add_engineered_features, split_X_y, all_feature_columns
from telco_churn.model import benchmark, fit_final, load_model, predict_churn
from telco_churn.evaluate import (
    score_pipeline,
    classification_text,
    roc_points,
    pr_points,
    feature_importance,
    threshold_sweep,
)

__all__ = [
    "clean_telco_churn",
    "add_engineered_features",
    "split_X_y",
    "all_feature_columns",
    "benchmark",
    "fit_final",
    "load_model",
    "predict_churn",
    "score_pipeline",
    "classification_text",
    "roc_points",
    "pr_points",
    "feature_importance",
    "threshold_sweep",
]
