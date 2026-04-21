"""K-means clustering on the six Safe Haven indicators.

The ranking answers "which country scores best?" under a given weighting.
Clustering answers a different question: "which countries behave similarly,
regardless of rank?" — useful when a user likes one country and wants a
shortlist of profile-alike alternatives.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


from .indicators import INDICATOR_FUNCS


RANDOM_STATE = 42


def _feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Extract the six indicator columns, drop rows missing all of them."""
    cols = [c for c in INDICATOR_FUNCS if c in df.columns]
    X = df[cols].copy()
    # Impute with column median so a single missing indicator doesn't drop a row
    X = X.fillna(X.median(numeric_only=True))
    return X


def choose_k(df: pd.DataFrame, k_range: range = range(2, 9)) -> pd.DataFrame:
    """Silhouette score for each k — higher is better, 0.2–0.5 is typical here.

    Sample size is small (~61 countries) so these scores are noisy; use them as
    a tiebreaker rather than a definitive answer.
    """
    X = _feature_matrix(df)
    Xs = StandardScaler().fit_transform(X)

    rows = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(Xs)
        rows.append({
            "k": k,
            "inertia": float(km.inertia_),
            "silhouette": float(silhouette_score(Xs, labels)) if k > 1 else np.nan,
        })
    return pd.DataFrame(rows)


def fit_clusters(df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """Assign each country to one of ``k`` clusters and attach a human label.

    Returns the input DataFrame with two new columns:
        - ``cluster`` (int): raw cluster id
        - ``cluster_label`` (str): descriptive tag derived from the cluster's
          mean indicator profile (e.g. "High stability, high English").
    """
    X = _feature_matrix(df)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    labels = km.fit_predict(Xs)

    out = df.copy()
    out["cluster"] = labels
    out["cluster_label"] = out["cluster"].map(_label_clusters(out, X.columns.tolist()))
    return out


def _label_clusters(df: pd.DataFrame, feature_cols: list[str]) -> dict[int, str]:
    """Build a short descriptive label per cluster using the highest / lowest
    indicator versus the global mean. Labels are approximate — they help users
    recognise the cluster, not claim formal semantics.
    """
    global_mean = df[feature_cols].mean()
    labels: dict[int, str] = {}

    pretty = {
        "political_stability": "stability",
        "energy_self_sufficiency": "energy independence",
        "healthcare_quality": "healthcare",
        "immigration_friendliness": "immigration",
        "english_prevalence": "English",
        "conflict_distance": "distance from conflict",
    }

    for cid, group in df.groupby("cluster"):
        gap = group[feature_cols].mean() - global_mean
        top = gap.idxmax()
        bottom = gap.idxmin()
        tag_parts = []
        if gap[top] > 5:
            tag_parts.append(f"strong {pretty.get(top, top)}")
        if gap[bottom] < -5:
            tag_parts.append(f"weak {pretty.get(bottom, bottom)}")
        labels[cid] = " · ".join(tag_parts) if tag_parts else "balanced profile"
    return labels


def similar_countries(df: pd.DataFrame, country: str, *, n: int = 5) -> pd.DataFrame:
    """Return the ``n`` closest countries by Euclidean distance in scaled space.

    More precise than "same cluster" when the user asks "countries that behave
    like X" — clusters can put similar countries on the boundary between two
    groups.
    """
    X = _feature_matrix(df)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    Xs = pd.DataFrame(Xs, index=df["country"].values, columns=X.columns)

    if country not in Xs.index:
        raise KeyError(f"Country not found in index: {country}")

    anchor = Xs.loc[country].values
    dists = np.linalg.norm(Xs.values - anchor, axis=1)
    order = np.argsort(dists)

    neighbours = Xs.index[order]
    # Skip self, take next n
    neighbours = [c for c in neighbours if c != country][:n]

    result = df[df["country"].isin(neighbours)].copy()
    # Preserve neighbour order
    result["__order__"] = result["country"].map({c: i for i, c in enumerate(neighbours)})
    result = result.sort_values("__order__").drop(columns="__order__")
    result["distance"] = [float(dists[order[i + 1]]) for i in range(len(result))]
    return result
