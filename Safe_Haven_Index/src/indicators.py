"""Compute the six Safe Haven indicators and normalize each to 0–100.

Every indicator function returns a DataFrame with columns ``[iso3, score]``
where higher = safer / more desirable for the "safe haven" framing.
"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd

from .fetch import (
    fetch_indicator,
    load_conflict_zones,
    load_english_proficiency,
    load_snapshot,
)


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def minmax_to_100(s: pd.Series, lo: float | None = None, hi: float | None = None) -> pd.Series:
    """Linear rescale to 0..100. ``lo``/``hi`` override the data range so
    scores stay comparable across refreshes (e.g. political stability always
    uses its theoretical -2.5..+2.5 band regardless of the sample)."""
    s = pd.to_numeric(s, errors="coerce")
    lo = s.min() if lo is None else lo
    hi = s.max() if hi is None else hi
    if hi == lo:
        return pd.Series(50.0, index=s.index)
    return ((s.clip(lo, hi) - lo) / (hi - lo) * 100).round(2)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0088
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Indicator 1: Political Stability (WB PV.EST)
# ---------------------------------------------------------------------------

def political_stability(live: bool = False) -> pd.DataFrame:
    df = fetch_indicator("PV.EST", live=live)
    df = df.rename(columns={"value": "raw"})
    # WGI estimates range roughly -2.5..+2.5; clamp there to keep scale stable.
    df["score"] = minmax_to_100(df["raw"], lo=-2.5, hi=2.5)
    return df[["iso3", "score"]]


# ---------------------------------------------------------------------------
# Indicator 2: Energy Self-Sufficiency (derived from EG.IMP.CONS.ZS)
# ---------------------------------------------------------------------------

def energy_self_sufficiency(live: bool = False) -> pd.DataFrame:
    """``EG.IMP.CONS.ZS`` is net energy imports as % of consumption.
    Negative values = net exporter (good). We cap at ±100 so strong
    exporters (Norway, UAE) and heavy importers (Japan, Singapore) get
    sensible endpoints without a single outlier distorting the scale.
    """
    df = fetch_indicator("EG.IMP.CONS.ZS", live=live).rename(columns={"value": "raw"})
    # Self-sufficiency = 100 - imports%. Negative imports (exporter) caps at +100.
    df["self_sufficiency"] = (100 - df["raw"]).clip(-100, 200)
    df["score"] = minmax_to_100(df["self_sufficiency"], lo=-100, hi=200)
    return df[["iso3", "score"]]


# ---------------------------------------------------------------------------
# Indicator 3: Healthcare quality (life expectancy + health expenditure)
# ---------------------------------------------------------------------------

def healthcare_quality(live: bool = False) -> pd.DataFrame:
    le = fetch_indicator("SP.DYN.LE00.IN", live=live).rename(columns={"value": "life_exp"})
    sp = fetch_indicator("SH.XPD.CHEX.PC.CD", live=live).rename(columns={"value": "spend"})
    df = le.merge(sp, on="iso3", how="outer")
    # Life expectancy typically 50..85; log-spend handles the long tail.
    le_score = minmax_to_100(df["life_exp"], lo=50, hi=85)
    spend_score = minmax_to_100(np.log1p(df["spend"]), lo=math.log1p(20), hi=math.log1p(12000))
    # 70/30 split: outcome weighs more than spend.
    df["score"] = (0.7 * le_score + 0.3 * spend_score).round(2)
    return df[["iso3", "score"]].dropna(subset=["score"])


# ---------------------------------------------------------------------------
# Indicator 4: Immigration friendliness (net migration rate per 1k)
# ---------------------------------------------------------------------------

def immigration_friendliness() -> pd.DataFrame:
    """We ship a ``net_migration_per_1k`` column in the snapshot because the
    WB absolute figure (``SM.POP.NETM``) needs a population denominator to
    be comparable. Range roughly -10..+15 covers the world."""
    snap = load_snapshot()
    snap["score"] = minmax_to_100(snap["net_migration_per_1k"], lo=-10, hi=15)
    return snap[["iso3", "score"]]


# ---------------------------------------------------------------------------
# Indicator 5: English prevalence
# ---------------------------------------------------------------------------

def english_prevalence() -> pd.DataFrame:
    """Based on EF English Proficiency Index + native/official flag.

    Not a WB indicator — shipped as ``english_proficiency.csv``. Countries
    absent from the reference file get a conservative default so they're
    penalised without being dropped from the ranking.
    """
    snap = load_snapshot()
    ep = load_english_proficiency()
    df = snap[["iso3"]].merge(ep[["iso3", "epi_score"]], on="iso3", how="left")
    df["epi_score"] = df["epi_score"].fillna(35)  # "low proficiency" default
    df["score"] = minmax_to_100(df["epi_score"], lo=30, hi=100)
    return df[["iso3", "score"]]


# ---------------------------------------------------------------------------
# Indicator 6: Distance from conflict hotspots (haversine from capital)
# ---------------------------------------------------------------------------

def conflict_distance() -> pd.DataFrame:
    """Minimum great-circle distance from the country's capital to any
    hotspot in ``conflict_zones.csv``. Farther = safer.

    The dampened log transform means a capital 100 km from a hotspot scores
    much lower than one 5,000 km away — but 5,000 km vs. 15,000 km matters
    less, which matches intuition (once you're safely far, extra distance
    adds little).
    """
    snap = load_snapshot()
    zones = load_conflict_zones()
    distances = []
    for _, c in snap.iterrows():
        if pd.isna(c["capital_lat"]) or pd.isna(c["capital_lon"]):
            distances.append(np.nan)
            continue
        d_min = min(
            haversine_km(c["capital_lat"], c["capital_lon"], z["lat"], z["lon"])
            for _, z in zones.iterrows()
        )
        distances.append(d_min)
    snap = snap.assign(min_conflict_km=distances)
    snap["score"] = minmax_to_100(
        np.log1p(snap["min_conflict_km"]),
        lo=math.log1p(0), hi=math.log1p(15000),
    )
    return snap[["iso3", "score"]]


# ---------------------------------------------------------------------------
# Master assembly
# ---------------------------------------------------------------------------

INDICATOR_FUNCS = {
    "political_stability":     political_stability,
    "energy_self_sufficiency": energy_self_sufficiency,
    "healthcare_quality":      healthcare_quality,
    "immigration_friendliness": immigration_friendliness,
    "english_prevalence":      english_prevalence,
    "conflict_distance":       conflict_distance,
}

INDICATOR_LABELS = {
    "political_stability":     "政治穩定度",
    "energy_self_sufficiency": "能源自給率",
    "healthcare_quality":      "醫療品質",
    "immigration_friendliness": "移民友善度",
    "english_prevalence":      "英語普及率",
    "conflict_distance":       "距離衝突熱點",
}


def build_all(live: bool = False) -> pd.DataFrame:
    """Run every indicator and return a wide DataFrame keyed by iso3."""
    snap = load_snapshot()[["iso3", "country", "region"]]
    for name, fn in INDICATOR_FUNCS.items():
        try:
            df = fn(live=live) if "live" in fn.__code__.co_varnames else fn()
        except TypeError:
            df = fn()
        snap = snap.merge(df.rename(columns={"score": name}), on="iso3", how="left")
    return snap
