# -*- coding: utf-8 -*-
"""營收趨勢（原 analyze_business 的 analysis_1）。"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from ..charting import fig_to_base64, month_axis, save_fig
from ..io_utils import fmt_money
from ..loaders import DataBundle
from . import AnalysisResult, df_to_html, write_csv


def run(data: DataBundle, out_dir: Path) -> AnalysisResult:
    res = AnalysisResult(section_id="revenue", title="營收趨勢")

    sale = data.sale.copy()
    sale = sale.dropna(subset=["sdate"])
    sale["tot"] = pd.to_numeric(sale["tot"], errors="coerce").fillna(0.0)

    monthly = (
        sale.set_index("sdate")
        .groupby(pd.Grouper(freq="MS"))["tot"]
        .sum()
        .sort_index()
    )

    total = float(sale["tot"].sum())
    # 最近一年
    if data.ref_date is not pd.NaT and len(monthly):
        last12_start = data.ref_date - pd.DateOffset(months=12)
        last12 = monthly[monthly.index >= last12_start.replace(day=1)].sum()
    else:
        last12 = float("nan")

    # 圖
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(monthly.index, monthly.values, marker="o", linewidth=2, markersize=4)
    ax.set_title("月營收（tot 合計）")
    ax.set_xlabel("月份")
    ax.set_ylabel("營收")
    ax.grid(True, alpha=0.3)
    month_axis(ax, monthly.index)
    res.images_b64["monthly_revenue"] = fig_to_base64(plt.gcf())

    # 另外寫檔案
    fig2, ax2 = plt.subplots(figsize=(12, 4.5))
    ax2.plot(monthly.index, monthly.values, marker="o", linewidth=2, markersize=4)
    ax2.set_title("月營收（tot 合計）")
    ax2.set_xlabel("月份")
    ax2.set_ylabel("營收")
    ax2.grid(True, alpha=0.3)
    month_axis(ax2, monthly.index)
    save_fig(fig2, out_dir, "monthly_revenue_trend.png")

    # 最近 12 月表
    tbl = monthly.reset_index()
    tbl.columns = ["月份", "營收"]
    tbl["月份"] = tbl["月份"].dt.strftime("%Y-%m")
    res.tables_html["最近 12 個月"] = df_to_html(tbl.tail(12))
    csv = write_csv(tbl, out_dir, "monthly_revenue.csv")
    res.csv_paths.append(csv)

    res.kpis["累計營收"] = fmt_money(total)
    res.kpis["最近 12 個月營收"] = fmt_money(last12)
    res.kpis["資料月份數"] = f"{len(monthly):,}"
    res.notes.append("以銷貨單頭 sale.tot 按月彙總（不含稅與否依原系統設定）。")
    return res
