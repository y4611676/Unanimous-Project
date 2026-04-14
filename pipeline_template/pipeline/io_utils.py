"""Generic I/O helpers shared by all pipeline stages.

Extracted from work/step1_clean.py (load, clean_numeric, clean_date, report)
and generalised so they don't assume any specific file or column name.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import pandas as pd


DEFAULT_ENCODING = "utf-8-sig"


def log(msg: str = "", level: str = "info") -> None:
    """Minimal stdout logger so the pipeline works without extra deps."""
    prefix = {
        "info": "",
        "warn": "⚠️  ",
        "ok": "✅ ",
        "step": "▶ ",
    }.get(level, "")
    print(f"{prefix}{msg}", file=sys.stdout, flush=True)


def load_csv(folder: str | Path, fname: str, encoding: str = DEFAULT_ENCODING) -> pd.DataFrame:
    """Read a CSV if it exists, else return an empty DataFrame.

    Mirrors the defensive behaviour from work/step1_clean.py:15-21 so missing
    sources don't crash the pipeline — downstream stages can check ``df.empty``.
    """
    p = Path(folder) / fname
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, encoding=encoding, on_bad_lines="skip")
    # Strip whitespace on all object/string columns
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()
            # Convert the literal string "nan" back to NaN
            df[col] = df[col].replace({"nan": pd.NA, "": pd.NA})
    return df


def save_csv(df: pd.DataFrame, folder: str | Path, fname: str,
             encoding: str = DEFAULT_ENCODING) -> Path:
    """Write CSV into ``folder`` (created if missing) and return the path."""
    out = Path(folder)
    out.mkdir(parents=True, exist_ok=True)
    p = out / fname
    df.to_csv(p, index=False, encoding=encoding)
    return p


def resolve_folder(arg: str | None, prompt: str) -> Path:
    """Return a Path, asking the user interactively if no arg given."""
    if arg:
        return Path(arg).expanduser().resolve()
    folder = input(prompt).strip()
    return Path(folder).expanduser().resolve()


def report_cleaning(name: str, n_before: int, n_after: int, issues: Iterable[str]) -> None:
    """Pretty-print cleaning stats (generalised from work/step1_clean.py:35-39)."""
    log(f"\n【{name}】")
    log(f"  原始筆數：{n_before}　清理後：{n_after}")
    for msg in issues:
        log(f"  {msg}", level="warn")
