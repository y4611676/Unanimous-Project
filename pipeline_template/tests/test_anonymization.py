"""Tests for pipeline/anonymization.py — determinism + cross-table consistency."""

import pandas as pd

from pipeline.anonymization import anonymize_tables


def _tables():
    orders = pd.DataFrame({
        "order_id":    ["O1", "O2", "O3"],
        "customer_id": ["C1", "C2", "C1"],
        "amount":      [100, 50, 30],
        "order_date":  pd.to_datetime(["2024-01-01", "2024-02-15", "2024-03-20"]),
    })
    customers = pd.DataFrame({
        "customer_id":   ["C1", "C2"],
        "customer_name": ["Alpha", "Beta"],
    })
    return {"orders": orders, "customers": customers}


_RULES = {
    "seed": 7,
    "money_scale": {"mode": "fixed", "fixed": 0.5},
    "date_shift_months": -6,
    "id_mappings": [
        {"col": "customer_id", "prefix": "CUST",
         "label_col": "customer_name", "label": "Cust"},
    ],
    "rules": {
        "orders":    {"money_cols": ["amount"], "date_cols": ["order_date"]},
        "customers": {},
    },
}


def test_id_map_is_consistent_across_tables(tmp_path):
    result = anonymize_tables({"anonymization": _RULES}, _tables(), str(tmp_path))

    # Same C1 should map to same CUST-xxx in both output tables.
    id_in_orders = result["orders"].loc[
        result["orders"]["customer_id"].str.startswith("CUST"),
        "customer_id",
    ].iloc[0]
    id_in_customers = result["customers"]["customer_id"].iloc[0]
    assert id_in_orders.startswith("CUST-")
    assert id_in_customers.startswith("CUST-")

    # Every original C1 row must now share the same anonymised id.
    mask = result["orders"]["order_id"].isin(["O1", "O3"])
    assert result["orders"].loc[mask, "customer_id"].nunique() == 1


def test_fixed_money_scale_is_applied(tmp_path):
    result = anonymize_tables({"anonymization": _RULES}, _tables(), str(tmp_path))
    # amount was 100, 50, 30 — at scale 0.5 we expect 50, 25, 15.
    assert sorted(result["orders"]["amount"].tolist()) == [15.0, 25.0, 50.0]


def test_date_shift_is_applied(tmp_path):
    result = anonymize_tables({"anonymization": _RULES}, _tables(), str(tmp_path))
    shifted = result["orders"]["order_date"].dt.strftime("%Y-%m").tolist()
    # -6 months: 2024-01 → 2023-07, 2024-02 → 2023-08, 2024-03 → 2023-09
    assert shifted == ["2023-07", "2023-08", "2023-09"]


def test_determinism_across_runs(tmp_path):
    first = anonymize_tables({"anonymization": _RULES}, _tables(), str(tmp_path / "a"))
    second = anonymize_tables({"anonymization": _RULES}, _tables(), str(tmp_path / "b"))
    pd.testing.assert_frame_equal(first["orders"], second["orders"])
    pd.testing.assert_frame_equal(first["customers"], second["customers"])


def test_name_labels_are_letter_suffixed(tmp_path):
    result = anonymize_tables({"anonymization": _RULES}, _tables(), str(tmp_path))
    names = sorted(result["customers"]["customer_name"].tolist())
    # Two customers → "CustA" and "CustB".
    assert names == ["CustA", "CustB"]
