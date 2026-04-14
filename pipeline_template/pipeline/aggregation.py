"""Config-driven aggregation stage.

Replaces the seven hand-written groupby blocks in work/step2_aggregate.py
(lines 57-178). Each aggregation is declared in YAML:

    - name: monthly
      source: sales
      groupby: [ym]
      metrics:
        rev:   sum
        salno: nunique
      joins:                   # optional look-ups
        - source: customers
          on: cusno
          cols: [cusnm]
      derive_period:           # optional: build year/month/ym/yq from a date
        from: sdate

The engine only depends on what it's told; nothing is hard-coded.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .io_utils import save_csv


def _add_period_cols(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Build year/month/ym/yq columns from a date column.

    Extracted from work/step2_aggregate.py:43-54 and generalised — any date
    column can be expanded, not just ``sdate``/``pdate``.
    """
    if date_col not in df.columns:
        return df
    dt = pd.to_datetime(df[date_col], errors="coerce")
    df = df.copy()
    df["year"] = dt.dt.year
    df["month"] = dt.dt.month
    df["ym"] = dt.dt.to_period("M").astype(str)
    df["yq"] = dt.dt.to_period("Q").astype(str)
    return df


def _apply_joins(df: pd.DataFrame, joins: list[dict[str, Any]],
                 tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    for j in joins or []:
        # YAML 1.1 parses unquoted ``on:`` as boolean True. Accept both so
        # users don't have to quote the key.
        on_col = j.get("on", j.get(True))
        if not on_col:
            print(f"  ⚠️  join missing 'on' key: {j}")
            continue
        other = tables.get(j["source"])
        if other is None or other.empty:
            continue
        if on_col not in df.columns or on_col not in other.columns:
            continue
        cols = [on_col] + [c for c in j.get("cols", []) if c in other.columns]
        right = other[cols].drop_duplicates(on_col)
        df = df.merge(right, on=on_col, how="left")
    return df


def _run_single_aggregation(cfg: dict[str, Any],
                            tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    src = tables.get(cfg["source"])
    if src is None or src.empty:
        return pd.DataFrame()

    df = src.copy()

    period_cfg = cfg.get("derive_period")
    if period_cfg:
        df = _add_period_cols(df, period_cfg["from"])

    groupby = cfg.get("groupby", [])
    metrics = cfg.get("metrics", {})

    # Joins are applied AFTER the groupby so descriptive look-ups (cusnm, prdnm)
    # survive aggregation (matches the pattern in work/step2_aggregate.py:110-111).
    if not groupby or not metrics:
        return _apply_joins(df, cfg.get("joins", []), tables)

    agg_args = {}
    for out_col, spec in metrics.items():
        if isinstance(spec, str):
            agg_args[out_col] = (out_col, spec)
        elif isinstance(spec, dict):
            agg_args[spec.get("as", out_col)] = (spec["col"], spec["func"])
        elif isinstance(spec, list) and len(spec) == 2:
            agg_args[out_col] = (spec[0], spec[1])

    # Drop any metric that references a column not present so missing data
    # doesn't crash the whole run.
    agg_args = {k: v for k, v in agg_args.items() if v[0] in df.columns}
    if not agg_args:
        return pd.DataFrame()

    result = df.groupby(groupby, dropna=False).agg(**agg_args).reset_index()

    # Joins happen on the aggregated result so descriptive look-ups don't get
    # dropped by the groupby.
    result = _apply_joins(result, cfg.get("joins", []), tables)

    # Optional post-processing: share and cumulative share of a metric.
    share_of = cfg.get("share_of")
    if share_of and share_of in result.columns:
        total = result[share_of].sum()
        result["share"] = result[share_of] / total if total else 0
        result = result.sort_values(share_of, ascending=False).reset_index(drop=True)
        result["cum_share"] = result["share"].cumsum()

    # Optional simple ratios (post-aggregation computed columns).
    for spec in cfg.get("derived", []):
        try:
            result[spec["name"]] = result.eval(spec["formula"], engine="python").replace(
                [np.inf, -np.inf], np.nan
            )
        except Exception as e:  # pragma: no cover
            print(f"  ⚠️  aggregation derived '{spec['name']}' failed: {e}")

    sort_by = cfg.get("sort_by")
    if sort_by and sort_by in result.columns:
        result = result.sort_values(sort_by, ascending=cfg.get("ascending", False))

    return result


def run_aggregation(config: dict[str, Any],
                    cleaned: dict[str, pd.DataFrame],
                    out_dir: str) -> dict[str, pd.DataFrame]:
    """Run every aggregation under ``config['aggregations']`` and save CSVs."""
    results: dict[str, pd.DataFrame] = {}
    # Make cleaned sources addressable by name for joins.
    tables = dict(cleaned)
    for cfg in config.get("aggregations", []):
        name = cfg["name"]
        print(f"\n▶ aggregating: {name}")
        df = _run_single_aggregation(cfg, tables)
        if df.empty:
            print(f"  (skip) empty result")
            continue
        results[name] = df
        save_csv(df, out_dir, f"{name}.csv")
        print(f"  {name}.csv: {len(df)} rows")
        # Aggregated tables can feed later ones (e.g. join against a monthly summary).
        tables[name] = df
    return results
