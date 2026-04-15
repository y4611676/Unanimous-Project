"""Weighted composite scoring for the Safe Haven Index."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from .indicators import INDICATOR_FUNCS

# Equal weights by default — sliders in the Streamlit app override this.
DEFAULT_WEIGHTS: dict[str, float] = {name: 1.0 for name in INDICATOR_FUNCS}


def normalize_weights(weights: Mapping[str, float]) -> dict[str, float]:
    """Guarantee weights sum to 1 so ``score`` stays on a 0–100 scale.
    Missing keys default to 0 (the user zeroed them out)."""
    total = sum(max(0.0, w) for w in weights.values())
    if total == 0:
        return {k: 0 for k in weights}
    return {k: max(0.0, v) / total for k, v in weights.items()}


def compute_index(df: pd.DataFrame, weights: Mapping[str, float] | None = None) -> pd.DataFrame:
    """Combine per-indicator 0–100 scores into a single weighted index.

    Countries with missing indicator values are imputed with the *global
    median* of that indicator so a single missing datapoint doesn't
    disqualify a country from the ranking — but the imputation is
    transparent: ``data_completeness`` tells the reader how many of the
    six indicators were actually observed.
    """
    indicator_cols = [c for c in INDICATOR_FUNCS if c in df.columns]
    w = normalize_weights(weights or DEFAULT_WEIGHTS)

    work = df.copy()
    # Track completeness before imputing.
    work["data_completeness"] = work[indicator_cols].notna().sum(axis=1) / len(indicator_cols)
    # Impute with per-column median for scoring stability.
    for c in indicator_cols:
        work[c] = work[c].fillna(work[c].median())

    score = np.zeros(len(work))
    for c in indicator_cols:
        score = score + work[c].to_numpy() * w.get(c, 0)
    work["safe_haven_score"] = score.round(2)
    work["rank"] = work["safe_haven_score"].rank(ascending=False, method="min").astype(int)
    return work.sort_values("safe_haven_score", ascending=False).reset_index(drop=True)


def top_n(ranked: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    cols = ["rank", "country", "region", "safe_haven_score"] + [
        c for c in INDICATOR_FUNCS if c in ranked.columns
    ] + ["data_completeness"]
    return ranked.head(n)[[c for c in cols if c in ranked.columns]]
