"""Unit tests for pipeline/analysis.py — RFM, Pareto, Top-N."""

import pandas as pd

from pipeline.analysis import pareto, rfm_scores, top_n


def _sample_orders() -> pd.DataFrame:
    return pd.DataFrame({
        "customer_id": ["A", "A", "A", "B", "B", "C"],
        "date":        ["2024-01-05", "2024-02-10", "2024-03-01",
                        "2024-01-15", "2024-02-20", "2024-03-25"],
        "amount":      [100, 80, 40, 50, 60, 200],
    })


def test_rfm_scores_shape_and_ordering():
    df = _sample_orders()
    rfm = rfm_scores(df, "customer_id", "date", "amount", quantiles=3)

    # One row per customer.
    assert set(rfm["customer_id"]) == {"A", "B", "C"}
    # Expected columns exist.
    for col in ("recency_days", "frequency", "monetary", "R", "F", "M", "RFM", "RFM_score"):
        assert col in rfm.columns
    # A has 3 orders, B has 2, C has 1 — frequency score must respect that.
    freq_by_cust = rfm.set_index("customer_id")["frequency"]
    assert freq_by_cust["A"] >= freq_by_cust["B"] >= freq_by_cust["C"]


def test_rfm_handles_empty_df():
    empty = pd.DataFrame(columns=["customer_id", "date", "amount"])
    assert rfm_scores(empty, "customer_id", "date", "amount").empty


def test_pareto_share_and_cum_share():
    df = pd.DataFrame({"cust": ["A", "B", "C", "D"], "rev": [40, 30, 20, 10]})
    result = pareto(df, "cust", "rev")

    # Sorted descending by metric.
    assert list(result["cust"]) == ["A", "B", "C", "D"]
    # Shares sum to 1.0.
    assert abs(result["share"].sum() - 1.0) < 1e-9
    # Cumulative share is monotonically non-decreasing and ends at 1.0.
    cs = list(result["cum_share"])
    assert cs == sorted(cs)
    assert abs(cs[-1] - 1.0) < 1e-9
    # Ranks are 1..N in order.
    assert list(result["rank"]) == [1, 2, 3, 4]


def test_pareto_handles_zero_total():
    df = pd.DataFrame({"cust": ["A", "B"], "rev": [0, 0]})
    result = pareto(df, "cust", "rev")
    # Total of zero shouldn't crash, and share column must still exist.
    assert "share" in result.columns


def test_top_n_returns_first_n_by_metric():
    df = pd.DataFrame({"x": list("abcde"), "v": [1, 5, 3, 2, 4]})
    result = top_n(df, by="v", n=3)
    assert list(result["x"]) == ["b", "e", "c"]
    assert len(result) == 3
