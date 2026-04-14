"""Tests for pipeline/cleaning.py — the config-driven clean stage."""

import csv
import pandas as pd

from pipeline.cleaning import clean_source


def _write_csv(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)


def test_clean_source_drops_duplicates_on_key(tmp_path):
    src = tmp_path / "raw"; src.mkdir()
    out = tmp_path / "out"
    _write_csv(src / "orders.csv", [
        ["order_id", "order_date", "amount"],
        ["O1", "2024-01-01", "100"],
        ["O2", "2024-02-01", "200"],
        ["O1", "2024-01-01", "100"],   # duplicate
    ])

    cfg = {
        "name": "orders", "file": "orders.csv",
        "date_cols": ["order_date"], "numeric_cols": ["amount"],
        "key_col": "order_id",
    }
    df = clean_source(cfg, str(src), str(out))
    assert len(df) == 2
    assert df["order_id"].is_unique
    # The cleaned CSV was written out.
    assert (out / "orders.csv").exists()


def test_clean_source_evaluates_derived_columns(tmp_path):
    src = tmp_path / "raw"; src.mkdir()
    out = tmp_path / "out"
    _write_csv(src / "sales.csv", [
        ["price", "qty"],
        ["10", "2"],
        ["5",  "4"],
    ])

    cfg = {
        "name": "sales", "file": "sales.csv",
        "numeric_cols": ["price", "qty"],
        "derived": [{"name": "total", "formula": "price * qty"}],
    }
    df = clean_source(cfg, str(src), str(out))
    assert df["total"].tolist() == [20, 20]


def test_clean_source_missing_file_returns_empty(tmp_path):
    out = tmp_path / "out"
    cfg = {"name": "nope", "file": "does_not_exist.csv"}
    df = clean_source(cfg, str(tmp_path), str(out))
    assert df.empty


def test_clean_source_converts_dates(tmp_path):
    src = tmp_path / "raw"; src.mkdir()
    out = tmp_path / "out"
    _write_csv(src / "events.csv", [
        ["ts"],
        ["2024-03-14"],
        ["bogus"],
    ])
    cfg = {"name": "events", "file": "events.csv", "date_cols": ["ts"]}
    df = clean_source(cfg, str(src), str(out))
    # Valid date is parsed; invalid coerces to NaT (not a crash).
    assert pd.api.types.is_datetime64_any_dtype(df["ts"])
    assert df["ts"].iloc[0] == pd.Timestamp("2024-03-14")
    assert pd.isna(df["ts"].iloc[1])
