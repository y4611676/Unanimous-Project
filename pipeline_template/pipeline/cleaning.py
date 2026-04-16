"""Config-driven cleaning stage.

Replaces the per-file hard-coded blocks in work/step1_clean.py (lines 52-160).
Each source is described declaratively:

    - name: sales
      file: sale.csv
      date_cols: [sdate]
      numeric_cols: [tot, price]
      key_col: salno           # optional; used to drop duplicates
      derived:                 # optional; simple computed columns
        - {name: rev, formula: "price * prqty"}
      checks:                  # optional; surfaced as warnings
        - {type: non_negative, col: tot}
        - {type: non_zero, col: price}
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .io_utils import load_csv, report_cleaning, save_csv


def _to_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def _to_datetime(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c].astype(str).str[:10], errors="coerce")
    return df


def _apply_derived(df: pd.DataFrame, derived: list[dict[str, Any]]) -> pd.DataFrame:
    """Evaluate simple column-level formulas against the DataFrame.

    Uses pandas ``DataFrame.eval`` so expressions can only reference columns
    and basic arithmetic — no arbitrary Python exec.
    """
    for spec in derived or []:
        name, formula = spec["name"], spec["formula"]
        try:
            df[name] = df.eval(formula, engine="python")
        except Exception as e:  # pragma: no cover - surfaced to the user
            print(f"  ⚠️  derived '{name}' failed: {e}")
    return df


def _run_checks(df: pd.DataFrame, checks: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for chk in checks or []:
        kind, col = chk.get("type"), chk.get("col")
        if col not in df.columns:
            continue
        if kind == "non_negative":
            n = (df[col] < 0).sum()
            if n:
                issues.append(f"{col}: {n} negative value(s)")
        elif kind == "non_zero":
            n = (df[col] == 0).sum()
            if n:
                issues.append(f"{col}: {n} zero value(s)")
        elif kind == "not_null":
            n = df[col].isna().sum()
            if n:
                issues.append(f"{col}: {n} null value(s)")
    return issues


def clean_source(source_cfg: dict[str, Any], src_dir: str, out_dir: str) -> pd.DataFrame:
    """Clean a single source described by ``source_cfg`` and save to ``out_dir``.

    Returns the cleaned DataFrame (empty if the source file does not exist).
    """
    name = source_cfg["name"]
    fname = source_cfg["file"]

    df = load_csv(src_dir, fname)
    if df.empty:
        print(f"  (skip) {fname} not found in {src_dir}")
        return df

    n_before = len(df)
    df = _to_datetime(df, source_cfg.get("date_cols", []))
    df = _to_numeric(df, source_cfg.get("numeric_cols", []))
    df = _apply_derived(df, source_cfg.get("derived", []))

    issues = _run_checks(df, source_cfg.get("checks", []))

    key_col = source_cfg.get("key_col")
    if key_col and key_col in df.columns:
        dup = df.duplicated(subset=[key_col]).sum()
        if dup:
            issues.append(f"{dup} duplicate(s) on {key_col} (keeping the first)")
        df = df.drop_duplicates(subset=[key_col], keep="first")

    report_cleaning(name, n_before, len(df), issues)
    save_csv(df, out_dir, fname)
    return df


def run_cleaning(config: dict[str, Any], src_dir: str, out_dir: str) -> dict[str, pd.DataFrame]:
    """Clean every source listed under ``config['sources']``."""
    results: dict[str, pd.DataFrame] = {}
    for src in config.get("sources", []):
        results[src["name"]] = clean_source(src, src_dir, out_dir)
    return results
