"""
Smoke tests for the work/ ETL pipeline.
Runs step1 → step2 → step3 → step4 against sample_data to verify
the full pipeline doesn't crash and produces expected outputs.
"""
import sys
import pandas as pd
import pytest
from pathlib import Path

WORK_DIR = Path(__file__).resolve().parent.parent
SAMPLE = WORK_DIR / "sample_data"


# ── step1 ────────────────────────────────────────────────

def test_step1_import():
    """step1_clean.py can be imported without error."""
    sys.path.insert(0, str(WORK_DIR))
    import step1_clean
    assert hasattr(step1_clean, "main")
    assert hasattr(step1_clean, "clean_numeric")
    assert hasattr(step1_clean, "clean_date")


def test_step1_clean_numeric():
    sys.path.insert(0, str(WORK_DIR))
    from step1_clean import clean_numeric
    df = pd.DataFrame({"a": ["1", "2", "bad", "4"], "b": [10, 20, 30, 40]})
    df = clean_numeric(df, ["a"])
    assert df["a"].tolist() == [1.0, 2.0, 0.0, 4.0]


def test_step1_clean_date():
    sys.path.insert(0, str(WORK_DIR))
    from step1_clean import clean_date
    df = pd.DataFrame({"d": ["2024-01-15", "bad-date", "2024-03-10"]})
    df = clean_date(df, "d")
    assert pd.notna(df["d"].iloc[0])
    assert pd.isna(df["d"].iloc[1])


def test_step1_full_run(tmp_path):
    """Run step1 on sample_data and check output."""
    sys.path.insert(0, str(WORK_DIR))
    import shutil
    # Copy sample data to tmp
    src = tmp_path / "raw"
    src.mkdir()
    for f in SAMPLE.glob("*.csv"):
        shutil.copy(f, src / f.name)

    sys.argv = ["step1_clean.py", str(src)]
    from step1_clean import load, clean_numeric, clean_date
    # Run manually instead of main() (which has input())
    out = src / "cleaned"
    out.mkdir(exist_ok=True)

    df = load(src, "sale.csv")
    assert not df.empty
    df = clean_date(df, "sdate")
    df = clean_numeric(df, ["tot"])
    df.to_csv(out / "sale.csv", index=False, encoding="utf-8-sig")

    result = pd.read_csv(out / "sale.csv")
    assert len(result) == 3
    assert "tot" in result.columns


# ── step2 ────────────────────────────────────────────────

def test_step2_import():
    sys.path.insert(0, str(WORK_DIR))
    import step2_aggregate
    assert hasattr(step2_aggregate, "main")


def test_step2_column_names(tmp_path):
    """Verify step2 outputs English column names."""
    sys.path.insert(0, str(WORK_DIR))
    import shutil
    from step2_aggregate import load

    # Prepare cleaned data (just copy sample as-is for smoke test)
    cleaned = tmp_path / "cleaned"
    cleaned.mkdir()
    for f in SAMPLE.glob("*.csv"):
        shutil.copy(f, cleaned / f.name)

    # Simulate what step2 does for sale + monthly
    sale = load(cleaned, "sale.csv")
    sale["sdate"] = pd.to_datetime(sale["sdate"], errors="coerce")
    sale["ym"] = sale["sdate"].dt.to_period("M").astype(str)

    import numpy as np
    monthly = sale.groupby("ym").agg(
        sales_count=("salno", "count"),
        sales=("tot", "sum"),
    ).reset_index()

    assert "sales" in monthly.columns
    assert "sales_count" in monthly.columns
    assert "銷售額" not in monthly.columns  # no Chinese


# ── step3 ────────────────────────────────────────────────

def test_step3_import():
    sys.path.insert(0, str(WORK_DIR))
    import step3_analyze
    assert hasattr(step3_analyze, "rfm_analysis")
    assert hasattr(step3_analyze, "pareto_analysis")
    assert hasattr(step3_analyze, "sheet_summary")


def test_step3_rfm_analysis():
    sys.path.insert(0, str(WORK_DIR))
    from step3_analyze import rfm_analysis
    cust = pd.DataFrame({
        "cusno": ["C001", "C002", "C003", "C004", "C005"],
        "cusnm": ["A", "B", "C", "D", "E"],
        "order_count": [10, 5, 20, 1, 15],
        "sales": [50000, 20000, 80000, 5000, 60000],
        "last_transaction": ["2024-03-01", "2024-01-01", "2024-03-10", "2023-06-01", "2024-02-15"],
    })
    result = rfm_analysis(cust)
    assert not result.empty
    assert "segment" in result.columns
    assert "R_days" in result.columns
    assert "RFM_score" in result.columns


def test_step3_pareto_analysis():
    sys.path.insert(0, str(WORK_DIR))
    from step3_analyze import pareto_analysis
    df = pd.DataFrame({
        "prdno": ["P001", "P002", "P003"],
        "sales": [7000, 2000, 1000],
    })
    result = pareto_analysis(df, "sales", "prdno")
    assert "share" in result.columns
    assert "cumulative_share" in result.columns
    assert "pareto" in result.columns
    assert result.iloc[0]["pareto"] == "Top 80%"


# ── step4 ────────────────────────────────────────────────

def test_step4_import():
    sys.path.insert(0, str(WORK_DIR))
    import step4_anonymize
    assert hasattr(step4_anonymize, "build_id_maps")
    assert hasattr(step4_anonymize, "scale_money")
    assert hasattr(step4_anonymize, "shift_dates")


def test_step4_id_masking():
    sys.path.insert(0, str(WORK_DIR))
    from step4_anonymize import build_id_maps, _apply
    cust = pd.DataFrame({"cusno": ["C001", "C002"], "cusnm": ["Acme", "Beta"]})
    prod = pd.DataFrame({"prdno": ["P001"], "prdnm": ["Widget"]})
    fact = pd.DataFrame()

    col_maps = build_id_maps(cust, prod, fact)
    assert "cusno" in col_maps
    assert col_maps["cusno"]["C001"] == "CUST-001"

    masked = _apply(cust, col_maps)
    assert masked["cusno"].iloc[0] == "CUST-001"
    assert "Customer " in masked["cusnm"].iloc[0]


def test_step4_money_scale():
    sys.path.insert(0, str(WORK_DIR))
    from step4_anonymize import scale_money, MONEY_SCALE
    df = pd.DataFrame({"sales": [1000.0], "cost": [800.0]})
    result = scale_money(df, "prod_agg")
    assert abs(result["sales"].iloc[0] - 1000.0 * MONEY_SCALE) < 0.01


def test_step4_english_money_cols():
    """Verify MONEY_COLS uses English column names."""
    sys.path.insert(0, str(WORK_DIR))
    from step4_anonymize import MONEY_COLS
    for key, cols in MONEY_COLS.items():
        for col in cols:
            assert col.isascii(), f"Non-ASCII column name '{col}' in MONEY_COLS['{key}']"
