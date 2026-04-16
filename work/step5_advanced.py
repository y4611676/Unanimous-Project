"""
Step 5: Advanced Analytics → Excel Report
- Reads aggregated/ data from step2 (monthly, cust_agg, prod_agg, sale_full)
- Performs 6 advanced analyses beyond the basic step3 report:

    1. Seasonality Decomposition — split monthly sales into trend + seasonal + residual
       so you can tell if a dip is seasonal (expected) or a real problem.

    2. Customer Cohort Analysis — group customers by first-purchase month,
       track retention over time. Shows whether newer cohorts behave differently.

    3. Anomaly Detection — flag orders with unusual values (amount, qty, or price)
       using the IQR rule (outside Q1 - 1.5*IQR or Q3 + 1.5*IQR).

    4. Market Basket Analysis — find which products are frequently bought together.
       Output: top product pairs by co-occurrence count & lift score.

    5. Sales Forecast — simple exponential smoothing to project next 3 months.
       Good enough for directional planning; not a replacement for Prophet/ARIMA.

    6. Churn Risk Scoring — logistic regression on RFM features to estimate
       probability that each customer will lapse. Uses only pandas + sklearn.

Outputs one Excel file: advanced_analysis_report.xlsx

Design notes:
- No heavy dependencies (no Prophet, no statsmodels, no mlxtend).
- Reuses step3's styling helpers where possible for a consistent look.
- Every analysis degrades gracefully when data is insufficient (returns empty DF).
"""

import os, sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.chart import LineChart, BarChart, Reference


# ══════════════════════════════════════════════════════════
# Shared helpers (loader + styling reused from step3 conventions)
# ══════════════════════════════════════════════════════════

def load(folder, fname):
    """Read a CSV if it exists, otherwise return empty DataFrame — lets each
    analysis skip gracefully when a data source isn't available."""
    p = Path(folder) / fname
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, encoding="utf-8-sig")


# ══════════════════════════════════════════════════════════
# Analysis 1: Seasonality Decomposition
# ══════════════════════════════════════════════════════════

def seasonality_decomposition(monthly: pd.DataFrame) -> pd.DataFrame:
    """Additive decomposition: sales = trend + seasonal + residual.

    - Trend: centered 12-month moving average (smooths out year-over-year bumps)
    - Seasonal: average deviation of each calendar month from the trend,
                then normalized so the 12 values sum to ~0
    - Residual: whatever's left (real noise, one-off events)

    Why additive (not multiplicative)? Simpler, works well when seasonal swings
    are roughly constant in absolute terms. For businesses where seasonality
    grows with scale, multiplicative would be better — but that needs logs.

    Requires at least 13 months of data; returns empty DF if insufficient.
    """
    if monthly.empty or "sales" not in monthly.columns or len(monthly) < 13:
        return pd.DataFrame()

    df = monthly.sort_values("ym").reset_index(drop=True).copy()
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0)

    # Centered 12-month moving average — the "smooth" underlying trend.
    # min_periods=6 allows a partial trend at the edges rather than NaN.
    df["trend"] = df["sales"].rolling(window=12, center=True, min_periods=6).mean()

    # Detrended series = what's left after removing the trend. Contains
    # both the seasonal pattern and random noise.
    df["detrended"] = df["sales"] - df["trend"]

    # Seasonal component: average detrended value for each calendar month,
    # then subtract the overall mean so the 12 seasonal factors sum to ~0.
    df["month"] = df["ym"].astype(str).str[-2:].astype(int)
    month_avg = df.groupby("month")["detrended"].mean()
    month_avg = month_avg - month_avg.mean()
    df["seasonal"] = df["month"].map(month_avg)

    # Residual = actual − trend − seasonal. Big residuals flag real anomalies
    # (promotions, crises, etc.) worth investigating manually.
    df["residual"] = df["sales"] - df["trend"].fillna(0) - df["seasonal"].fillna(0)

    return df[["ym", "sales", "trend", "seasonal", "residual"]]


# ══════════════════════════════════════════════════════════
# Analysis 2: Customer Cohort Analysis
# ══════════════════════════════════════════════════════════

def cohort_analysis(sale_full: pd.DataFrame) -> pd.DataFrame:
    """Retention matrix: rows = cohort (first-purchase month),
                        columns = months since first purchase,
                        cells = # customers still active in that month.

    The first column (month 0) is always the full cohort size.
    Subsequent columns show how many of those customers came back in month 1, 2, …

    Reading the output:
    - Strong diagonal = healthy retention (same customers keep coming back)
    - Rapid drop-off = one-time buyers, need re-engagement
    - Cohorts getting worse over time = product/market fit degrading
    """
    if sale_full.empty or "cusno" not in sale_full.columns or "sdate" not in sale_full.columns:
        return pd.DataFrame()

    df = sale_full[["cusno", "sdate"]].dropna().copy()
    df["sdate"] = pd.to_datetime(df["sdate"], errors="coerce")
    df = df.dropna(subset=["sdate"])
    if df.empty:
        return pd.DataFrame()

    # Each customer's first purchase month defines which cohort they belong to.
    df["order_period"] = df["sdate"].dt.to_period("M")
    df["cohort"] = df.groupby("cusno")["order_period"].transform("min")

    # Cohort index = how many months since the customer's first purchase.
    # Index 0 is the month they joined, 1 is the next month, etc.
    df["cohort_index"] = (df["order_period"] - df["cohort"]).apply(lambda x: x.n)

    # Count unique active customers per (cohort, month-since-start) cell.
    cohort_pivot = (
        df.groupby(["cohort", "cohort_index"])["cusno"]
          .nunique()
          .unstack(fill_value=0)
    )

    # Convert Period index to string for CSV/Excel friendliness.
    cohort_pivot.index = cohort_pivot.index.astype(str)
    cohort_pivot = cohort_pivot.reset_index().rename(columns={"cohort": "cohort_month"})
    return cohort_pivot


# ══════════════════════════════════════════════════════════
# Analysis 3: Anomaly Detection (IQR-based outliers)
# ══════════════════════════════════════════════════════════

def anomaly_detection(sale_full: pd.DataFrame) -> pd.DataFrame:
    """Flag individual sale lines that look unusual on any of these axes:
       - rev (line revenue): promotions, bulk deals, data entry errors
       - prqty (quantity): bulk orders vs accidental double-entries
       - price (unit price): manual overrides, discount abuse

    Uses the classic IQR rule:
       outlier if value < Q1 - 1.5*IQR  or  value > Q3 + 1.5*IQR
    (Q1, Q3 = 25th, 75th percentile; IQR = Q3 - Q1.)

    Why IQR instead of z-score? Retail data is heavily right-skewed (a few
    huge orders). IQR is more robust — doesn't get distorted by the tail.

    Returns only the flagged rows, with a `flag` column listing which
    metric(s) tripped the rule.
    """
    if sale_full.empty:
        return pd.DataFrame()

    df = sale_full.copy()
    numeric_cols = [c for c in ["rev", "prqty", "price"] if c in df.columns]
    if not numeric_cols:
        return pd.DataFrame()

    df["flag"] = ""
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        # Compute bounds on non-null values only, otherwise quantile is NaN
        valid = df[col].dropna()
        if len(valid) < 4:  # need at least a handful of points for quartiles
            continue
        q1, q3 = valid.quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (df[col] < lo) | (df[col] > hi)
        # Append the column name to the flag so users see WHY a row was caught
        df.loc[mask, "flag"] = df.loc[mask, "flag"].where(
            df.loc[mask, "flag"] == "",
            df.loc[mask, "flag"] + ","
        ) + col

    # Keep only anomalies and the columns users actually care about
    flagged = df[df["flag"] != ""].copy()
    keep = [c for c in ["salno", "sdate", "cusno", "cusnm", "prdno", "prdnm",
                        "prqty", "price", "rev", "flag"] if c in flagged.columns]
    return flagged[keep].sort_values("flag")


# ══════════════════════════════════════════════════════════
# TODO (next pass): analyses 4-6 + sheet writers + main()
#   - market_basket_analysis()
#   - sales_forecast()
#   - churn_risk_scoring()
#   - sheet_* functions for each
#   - main() entry point
# ══════════════════════════════════════════════════════════
