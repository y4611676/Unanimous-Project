"""Config-driven analysis stage.

Provides reusable analytics that work/step3_analyze.py hard-coded around the
sales domain:

    - RFM scoring on any ``(customer, date, amount)`` triple
    - Pareto / cumulative-share ranking on any dimension + metric
    - Top-N extraction

Config shape::

    analysis:
      rfm:
        enabled: true
        source: sales           # cleaned table name
        customer_col: cusno
        date_col: sdate
        amount_col: tot
        output: rfm             # output table name
      pareto:
        - source: cust_agg      # can reference aggregated tables
          dimension: cusno
          metric: rev
          output: pareto_customers
      top_n:
        - source: prod_agg
          by: rev
          n: 20
          output: top20_products
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .io_utils import save_csv


def rfm_scores(df: pd.DataFrame, customer_col: str, date_col: str,
               amount_col: str, reference_date: pd.Timestamp | None = None,
               quantiles: int = 5) -> pd.DataFrame:
    """Compute Recency / Frequency / Monetary scores per customer.

    Generic replacement for the RFM block in work/step2/step3 that assumed
    cusno/sdate/tot.
    """
    if df.empty or customer_col not in df.columns:
        return pd.DataFrame()

    work = df[[customer_col, date_col, amount_col]].copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    work = work.dropna(subset=[date_col])
    if work.empty:
        return pd.DataFrame()

    ref = reference_date or work[date_col].max()
    grouped = work.groupby(customer_col).agg(
        recency_days=(date_col, lambda s: (ref - s.max()).days),
        frequency=(date_col, "count"),
        monetary=(amount_col, "sum"),
    ).reset_index()

    # Bucket into quantile scores 1..quantiles (higher = better, so flip recency).
    def _score(series: pd.Series, invert: bool = False) -> pd.Series:
        try:
            ranks = pd.qcut(series.rank(method="first"), quantiles, labels=False) + 1
        except ValueError:
            return pd.Series([quantiles] * len(series), index=series.index)
        return (quantiles + 1 - ranks) if invert else ranks

    grouped["R"] = _score(grouped["recency_days"], invert=True)
    grouped["F"] = _score(grouped["frequency"])
    grouped["M"] = _score(grouped["monetary"])
    grouped["RFM"] = grouped["R"].astype(str) + grouped["F"].astype(str) + grouped["M"].astype(str)
    grouped["RFM_score"] = grouped[["R", "F", "M"]].sum(axis=1)
    return grouped.sort_values("RFM_score", ascending=False).reset_index(drop=True)


def pareto(df: pd.DataFrame, dimension: str, metric: str) -> pd.DataFrame:
    """Sort by metric desc, compute share and cumulative share.

    Generalises the "80/20" blocks sprinkled across work/step3.
    """
    if df.empty or dimension not in df.columns or metric not in df.columns:
        return pd.DataFrame()
    result = df[[dimension, metric]].groupby(dimension, as_index=False).sum()
    total = result[metric].sum()
    result = result.sort_values(metric, ascending=False).reset_index(drop=True)
    result["share"] = result[metric] / total if total else 0
    result["cum_share"] = result["share"].cumsum()
    result["rank"] = np.arange(1, len(result) + 1)
    return result


def top_n(df: pd.DataFrame, by: str, n: int = 10) -> pd.DataFrame:
    if df.empty or by not in df.columns:
        return pd.DataFrame()
    return df.sort_values(by, ascending=False).head(n).reset_index(drop=True)


def run_analysis(config: dict[str, Any],
                 tables: dict[str, pd.DataFrame],
                 out_dir: str) -> dict[str, pd.DataFrame]:
    """Execute the configured analyses. ``tables`` includes both cleaned and
    aggregated results so analyses can target either layer."""
    results: dict[str, pd.DataFrame] = {}
    cfg = config.get("analysis") or {}

    rfm_cfg = cfg.get("rfm") or {}
    if rfm_cfg.get("enabled"):
        src = tables.get(rfm_cfg["source"], pd.DataFrame())
        out = rfm_scores(
            src,
            customer_col=rfm_cfg["customer_col"],
            date_col=rfm_cfg["date_col"],
            amount_col=rfm_cfg["amount_col"],
            quantiles=rfm_cfg.get("quantiles", 5),
        )
        if not out.empty:
            name = rfm_cfg.get("output", "rfm")
            results[name] = out
            save_csv(out, out_dir, f"{name}.csv")
            print(f"  rfm → {name}.csv ({len(out)} rows)")

    for p in cfg.get("pareto", []) or []:
        src = tables.get(p["source"], pd.DataFrame())
        out = pareto(src, p["dimension"], p["metric"])
        if not out.empty:
            name = p.get("output", f"pareto_{p['dimension']}")
            results[name] = out
            save_csv(out, out_dir, f"{name}.csv")
            print(f"  pareto → {name}.csv ({len(out)} rows)")

    for t in cfg.get("top_n", []) or []:
        src = tables.get(t["source"], pd.DataFrame())
        out = top_n(src, by=t["by"], n=t.get("n", 10))
        if not out.empty:
            name = t.get("output", f"top_{t['by']}")
            results[name] = out
            save_csv(out, out_dir, f"{name}.csv")
            print(f"  top_n → {name}.csv ({len(out)} rows)")

    return results
