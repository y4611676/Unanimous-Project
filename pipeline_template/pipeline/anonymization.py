"""Config-driven anonymisation stage.

Replaces the hard-coded MONEY_COLS / DATE_COLS dictionaries and label tables in
work/step4_anonymize.py. Rules are declared per-table in YAML:

    anonymization:
      seed: 20240101
      money_scale:              # optional; default {min: 0.15, max: 2.8}
        mode: random            # or 'fixed'
        fixed: 0.37             # used when mode == 'fixed'
      date_shift_months: random # or an int like -42
      id_mappings:              # anonymise identifier columns consistently
        - col: cusno
          prefix: CUST
          label_col: cusnm      # optional paired name column
          label: Cust
      rules:
        monthly:                # table name as produced by the aggregation stage
          money_cols: [sales, purchases, gross_profit]
        sales:
          date_cols: [sdate]
          money_cols: [tot, price]
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from .io_utils import save_csv


def _idx_to_letters(i: int) -> str:
    """1 -> A, 26 -> Z, 27 -> AA ... (generalised from work/step4:77-78)."""
    if i < 26:
        return chr(65 + i)
    return chr(65 + i // 26 - 1) + chr(65 + i % 26)


def _choose_money_scale(rng: np.random.Generator, cfg: dict[str, Any]) -> float:
    mode = (cfg or {}).get("mode", "random")
    if mode == "fixed":
        return float(cfg.get("fixed", 1.0))
    # Same spirit as work/step4:32-38 — push the scale ≥40% away from 1.0.
    side = int(rng.integers(0, 2))
    if side == 0:
        return round(float(rng.uniform(0.15, 0.55)), 6)
    return round(float(rng.uniform(1.5, 2.8)), 6)


def _choose_date_shift(rng: np.random.Generator, spec: Any) -> int:
    if isinstance(spec, int):
        return spec
    direction = 1 if int(rng.integers(0, 2)) == 0 else -1
    return direction * int(rng.integers(24, 73))


def _build_id_maps(tables: dict[str, pd.DataFrame],
                   mappings: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Build one dict per configured identifier column, consistent across tables.

    The mapping is deterministic per ``seed`` because we sort values before
    assigning codes.
    """
    id_maps: dict[str, dict[str, str]] = {}
    name_maps: dict[str, dict[str, str]] = {}

    for m in mappings or []:
        col = m["col"]
        prefix = m.get("prefix", col.upper())
        label = m.get("label")
        label_col = m.get("label_col")

        # First pass: collect all unique ID values across every table that has
        # the ID column (ordering is deterministic after the sort below).
        seen: list[str] = []
        for tbl in tables.values():
            if tbl is None or tbl.empty or col not in tbl.columns:
                continue
            for v in tbl[col].dropna().astype(str).str.strip().unique():
                if v and v.lower() != "nan" and v not in seen:
                    seen.append(v)

        # Second pass: walk every table that has BOTH the ID column and the
        # label column, so a paired-name table can contribute even if another
        # table already introduced the IDs.
        name_pairs: dict[str, str] = {}
        if label and label_col:
            for tbl in tables.values():
                if tbl is None or tbl.empty:
                    continue
                if col not in tbl.columns or label_col not in tbl.columns:
                    continue
                pairs = (
                    tbl[[col, label_col]]
                    .dropna()
                    .astype(str)
                    .apply(lambda s: s.str.strip())
                )
                for _, row in pairs.iterrows():
                    cid, nm = row[col], row[label_col]
                    if cid and nm and nm.lower() != "nan":
                        name_pairs.setdefault(nm, cid)

        seen.sort()
        id_maps[col] = {v: f"{prefix}-{str(i + 1).zfill(3)}" for i, v in enumerate(seen)}

        if label and label_col and name_pairs:
            nm_map: dict[str, str] = {}
            for nm, orig_id in name_pairs.items():
                if orig_id in seen:
                    idx = seen.index(orig_id)
                    nm_map[nm] = f"{label}{_idx_to_letters(idx)}"
            name_maps[label_col] = nm_map

    return {"ids": id_maps, "names": name_maps}


def _anonymize_one(df: pd.DataFrame, rules: dict[str, Any],
                   scale: float, date_shift: int,
                   maps: dict[str, dict[str, str]]) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df = df.copy()

    for col, m in maps.get("ids", {}).items():
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().map(m).fillna(df[col])

    for col, m in maps.get("names", {}).items():
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().map(m).fillna(df[col])

    for col in rules.get("money_cols", []) or []:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce") * scale

    for col in rules.get("date_cols", []) or []:
        if col in df.columns:
            series = pd.to_datetime(df[col], errors="coerce")
            df[col] = series.apply(
                lambda x: x + relativedelta(months=date_shift) if pd.notna(x) else x
            )

    return df


def anonymize_tables(config: dict[str, Any],
                     tables: dict[str, pd.DataFrame],
                     out_dir: str) -> dict[str, pd.DataFrame]:
    """Apply anonymisation rules to every matching table and write CSVs."""
    cfg = config.get("anonymization") or {}
    if not cfg:
        return {}

    rng = np.random.default_rng(cfg.get("seed", 20240101))
    scale = _choose_money_scale(rng, cfg.get("money_scale") or {})
    date_shift = _choose_date_shift(rng, cfg.get("date_shift_months", "random"))
    maps = _build_id_maps(tables, cfg.get("id_mappings", []))

    print(f"\n▶ anonymization (scale={scale}, date_shift={date_shift} months)")

    rules_by_table = cfg.get("rules", {}) or {}
    out: dict[str, pd.DataFrame] = {}
    for name, df in tables.items():
        rules = rules_by_table.get(name, {})
        if not rules and not maps["ids"] and not maps["names"]:
            continue
        anon = _anonymize_one(df, rules, scale, date_shift, maps)
        out[name] = anon
        save_csv(anon, out_dir, f"{name}.csv")
        print(f"  {name} → {len(anon)} rows")
    return out
