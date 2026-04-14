"""Tests for pipeline/aggregation.py — groupby engine + joins + YAML quirks."""

import pandas as pd

from pipeline.aggregation import run_aggregation


def _tables():
    orders = pd.DataFrame({
        "order_id":    ["O1", "O2", "O3", "O4"],
        "customer_id": ["C1", "C2", "C1", "C3"],
        "amount":      [100, 50, 80, 200],
        "order_date":  pd.to_datetime(
            ["2024-01-10", "2024-01-20", "2024-02-05", "2024-02-18"]
        ),
    })
    customers = pd.DataFrame({
        "customer_id":   ["C1", "C2", "C3"],
        "customer_name": ["Alpha", "Beta", "Gamma"],
    })
    return {"orders": orders, "customers": customers}


def test_groupby_with_metrics_and_share(tmp_path):
    cfg = {
        "aggregations": [{
            "name": "customer_agg",
            "source": "orders",
            "groupby": ["customer_id"],
            "metrics": {
                "revenue":     {"col": "amount",   "func": "sum"},
                "order_count": {"col": "order_id", "func": "count"},
            },
            "share_of": "revenue",
            "sort_by": "revenue",
        }]
    }
    result = run_aggregation(cfg, _tables(), str(tmp_path))["customer_agg"]
    # Sorted by revenue desc: C3=200, C1=180, C2=50.
    assert list(result["customer_id"]) == ["C3", "C1", "C2"]
    assert result.loc[result["customer_id"] == "C1", "revenue"].iloc[0] == 180
    # share and cum_share exist and sum to 1.
    assert abs(result["share"].sum() - 1.0) < 1e-9
    assert abs(result["cum_share"].iloc[-1] - 1.0) < 1e-9


def test_join_with_true_key_works(tmp_path):
    """YAML 1.1 parses unquoted ``on:`` as boolean True; engine must handle it."""
    cfg = {
        "aggregations": [{
            "name": "customer_agg",
            "source": "orders",
            "groupby": ["customer_id"],
            "metrics": {"revenue": {"col": "amount", "func": "sum"}},
            # Simulate what PyYAML produces when the user writes `on: customer_id`.
            "joins": [{"source": "customers", True: "customer_id",
                       "cols": ["customer_name"]}],
        }]
    }
    result = run_aggregation(cfg, _tables(), str(tmp_path))["customer_agg"]
    assert "customer_name" in result.columns
    # C1 joined to Alpha.
    name = result.loc[result["customer_id"] == "C1", "customer_name"].iloc[0]
    assert name == "Alpha"


def test_derive_period_adds_ym(tmp_path):
    cfg = {
        "aggregations": [{
            "name": "monthly",
            "source": "orders",
            "derive_period": {"from": "order_date"},
            "groupby": ["ym"],
            "metrics": {"revenue": {"col": "amount", "func": "sum"}},
        }]
    }
    result = run_aggregation(cfg, _tables(), str(tmp_path))["monthly"]
    assert set(result["ym"]) == {"2024-01", "2024-02"}
    # Jan = 100+50, Feb = 80+200.
    jan = result.loc[result["ym"] == "2024-01", "revenue"].iloc[0]
    feb = result.loc[result["ym"] == "2024-02", "revenue"].iloc[0]
    assert jan == 150 and feb == 280


def test_missing_source_returns_empty(tmp_path):
    cfg = {"aggregations": [{
        "name": "ghost", "source": "does_not_exist",
        "groupby": ["x"], "metrics": {"y": {"col": "z", "func": "sum"}},
    }]}
    result = run_aggregation(cfg, _tables(), str(tmp_path))
    assert "ghost" not in result
