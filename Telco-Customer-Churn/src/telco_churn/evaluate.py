"""Evaluation helpers: metric tables + diagnostic plots.

Kept separate from model.py so training stays lean and notebook cells can
import just what they render.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline


def score_pipeline(pipe: Pipeline, X, y) -> dict[str, float]:
    """Return headline metrics at the default 0.5 threshold plus AUC/PR-AUC."""
    proba = pipe.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    return {
        "roc_auc": roc_auc_score(y, proba),
        "pr_auc": average_precision_score(y, proba),
        "precision": tp / max(tp + fp, 1),
        "recall": tp / max(tp + fn, 1),
        "f1": 2 * tp / max(2 * tp + fp + fn, 1),
        "accuracy": (tp + tn) / (tp + tn + fp + fn),
        "n_churners": int(y.sum()),
        "n_total": int(len(y)),
    }


def classification_text(pipe: Pipeline, X, y) -> str:
    """sklearn's classification_report as a printable string."""
    pred = pipe.predict(X)
    return classification_report(y, pred, target_names=["retained", "churned"])


def roc_points(pipe: Pipeline, X, y) -> pd.DataFrame:
    """Return the ROC curve as a plottable DataFrame."""
    proba = pipe.predict_proba(X)[:, 1]
    fpr, tpr, thr = roc_curve(y, proba)
    return pd.DataFrame({"fpr": fpr, "tpr": tpr, "threshold": thr})


def pr_points(pipe: Pipeline, X, y) -> pd.DataFrame:
    """Return precision-recall curve points as a plottable DataFrame."""
    proba = pipe.predict_proba(X)[:, 1]
    precision, recall, thr = precision_recall_curve(y, proba)
    # precision_recall_curve returns one more precision/recall value than thresholds
    return pd.DataFrame({
        "precision": precision[:-1],
        "recall": recall[:-1],
        "threshold": thr,
    })


def feature_importance(pipe: Pipeline, top_n: int = 15) -> pd.DataFrame:
    """Extract feature importance from the fitted pipeline.

    Works for tree-based models (feature_importances_) and linear models
    (coef_). Column names come from the ColumnTransformer inside the pipeline.
    """
    pre = pipe.named_steps["pre"]
    clf = pipe.named_steps["clf"]
    feature_names = pre.get_feature_names_out()

    if hasattr(clf, "feature_importances_"):
        scores = clf.feature_importances_
        kind = "importance"
    elif hasattr(clf, "coef_"):
        scores = np.abs(clf.coef_.ravel())
        kind = "|coef|"
    else:
        raise ValueError(f"{type(clf).__name__} exposes neither feature_importances_ nor coef_")

    df = pd.DataFrame({"feature": feature_names, kind: scores})
    return df.sort_values(kind, ascending=False).head(top_n).reset_index(drop=True)


def threshold_sweep(pipe: Pipeline, X, y, thresholds=None) -> pd.DataFrame:
    """Return precision/recall/f1 at each candidate threshold — useful for
    picking a decision cutoff that matches the business cost of false
    positives vs false negatives.
    """
    if thresholds is None:
        thresholds = np.arange(0.1, 0.91, 0.05)

    proba = pipe.predict_proba(X)[:, 1]
    rows = []
    for t in thresholds:
        pred = (proba >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-9)
        rows.append({"threshold": round(float(t), 2),
                     "precision": precision, "recall": recall, "f1": f1,
                     "flagged": int(pred.sum())})
    return pd.DataFrame(rows)
