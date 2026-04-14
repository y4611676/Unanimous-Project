# -*- coding: utf-8 -*-
"""共用 I/O 工具：多編碼 CSV 讀取、ID 正規化、數字格式化。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

ENCODINGS = ("big5", "cp950", "utf-8-sig", "utf-8")


def read_csv_enc(path: Path, **kwargs: Any) -> pd.DataFrame:
    """依 ENCODINGS 逐一嘗試；全部失敗才拋出最後一個錯誤。"""
    last: Exception | None = None
    for enc in ENCODINGS:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError as e:
            last = e
            continue
    if last:
        raise last
    raise OSError(f"無法讀取：{path}")


def strip_id(s: pd.Series) -> pd.Series:
    """ID 欄位常含尾隨空白（Big5 固定長度），統一去除。"""
    return s.astype(str).str.strip()


def fmt_money(v: float | int | None) -> str:
    """千分位整數金額。None / NaN 回傳 '-'。"""
    if v is None:
        return "-"
    try:
        if pd.isna(v):
            return "-"
    except (TypeError, ValueError):
        pass
    return f"{float(v):,.0f}"


def fmt_pct(v: float | None, digits: int = 1) -> str:
    if v is None:
        return "-"
    try:
        if pd.isna(v):
            return "-"
    except (TypeError, ValueError):
        pass
    return f"{float(v) * 100:.{digits}f}%"
