# -*- coding: utf-8 -*-
"""分析模組集合。每個模組暴露 run(data, out_dir) -> AnalysisResult。"""
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class AnalysisResult:
    """單一分析主題的輸出。"""

    section_id: str          # HTML anchor
    title: str               # 顯示標題
    kpis: dict[str, str] = field(default_factory=dict)   # 卡片
    images_b64: dict[str, str] = field(default_factory=dict)  # 名稱 -> data URI
    tables_html: dict[str, str] = field(default_factory=dict)  # 名稱 -> <table>
    csv_paths: list[Path] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)       # 小字說明 / 方法論


def df_to_html(df: pd.DataFrame, max_rows: int = 20, float_fmt: str = "{:,.2f}") -> str:
    """DataFrame → 乾淨的 HTML table（限制筆數，右對齊數字，千分位）。"""
    if df.empty:
        return "<p class='empty'>（無資料）</p>"
    show = df.head(max_rows).copy()
    # 時間欄位轉字串
    for c in show.columns:
        if pd.api.types.is_datetime64_any_dtype(show[c]):
            show[c] = show[c].dt.strftime("%Y-%m-%d")
    styler = show.style.format(float_fmt, na_rep="-", subset=show.select_dtypes("number").columns)
    styler = styler.hide(axis="index")
    html = styler.to_html(table_attributes='class="data"')
    if len(df) > max_rows:
        html += f"<p class='more'>共 {len(df):,} 筆，僅顯示前 {max_rows} 筆。</p>"
    return html


def write_csv(df: pd.DataFrame, out_dir: Path, name: str) -> Path:
    """統一寫出 UTF-8-SIG CSV（Excel 開得了中文）。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / name
    df.to_csv(p, index=False, encoding="utf-8-sig")
    return p
