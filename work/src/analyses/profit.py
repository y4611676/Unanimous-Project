# -*- coding: utf-8 -*-
"""A. 毛利分析：月毛利、商品／客戶／分類毛利排行、負毛利品項。

毛利來源：sales1（明細）price × prqty − pcost × prqty，逐行加總。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from ..charting import fig_to_base64, month_axis
from ..enrich import enrich_sales_lines
from ..io_utils import fmt_money, fmt_pct
from ..loaders import DataBundle
from . import AnalysisResult, df_to_html, write_csv


def run(data: DataBundle, out_dir: Path) -> AnalysisResult:
    res = AnalysisResult(section_id="profit", title="A. 毛利與獲利")
    lines = enrich_sales_lines(data)
    if lines.empty:
        res.notes.append("無 sales1 明細資料。")
        return res

    # --- A1 月毛利趨勢 ---
    monthly = lines.dropna(subset=["month"]).groupby("month", as_index=False).agg(
        revenue=("line_revenue", "sum"),
        cost=("line_cost", "sum"),
        margin=("line_margin", "sum"),
    )
    monthly["margin_rate"] = monthly["margin"] / monthly["revenue"].replace(0, pd.NA)

    fig, ax1 = plt.subplots(figsize=(12, 4.8))
    ax1.bar(monthly["month"], monthly["revenue"], width=20, alpha=0.35, label="營收")
    ax1.bar(monthly["month"], monthly["margin"], width=20, alpha=0.75, label="毛利")
    ax1.set_ylabel("金額")
    ax2 = ax1.twinx()
    ax2.plot(monthly["month"], monthly["margin_rate"] * 100, color="darkred", marker="o", linewidth=1.5, label="毛利率(%)")
    ax2.set_ylabel("毛利率 (%)")
    ax1.set_title("月營收 vs 毛利 與毛利率")
    ax1.grid(True, alpha=0.3)
    month_axis(ax1, monthly["month"])
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    res.images_b64["monthly_margin"] = fig_to_base64(fig)

    m_out = monthly.copy()
    m_out["month"] = m_out["month"].dt.strftime("%Y-%m")
    res.csv_paths.append(write_csv(m_out, out_dir, "monthly_margin.csv"))

    total_rev = float(monthly["revenue"].sum())
    total_mar = float(monthly["margin"].sum())
    overall_rate = total_mar / total_rev if total_rev else float("nan")
    res.kpis["累計毛利"] = fmt_money(total_mar)
    res.kpis["整體毛利率"] = fmt_pct(overall_rate)

    # --- A2 商品毛利排行 / 負毛利 ---
    prod_agg = lines.groupby(["prdno", "prdnm"], as_index=False, dropna=False).agg(
        revenue=("line_revenue", "sum"),
        cost=("line_cost", "sum"),
        margin=("line_margin", "sum"),
        qty=("prqty", "sum"),
    )
    prod_agg["margin_rate"] = prod_agg["margin"] / prod_agg["revenue"].replace(0, pd.NA)
    top_margin = prod_agg.sort_values("margin", ascending=False).head(20)
    neg_margin = prod_agg[prod_agg["margin"] < 0].sort_values("margin")
    res.tables_html["毛利 Top 20 商品"] = df_to_html(top_margin, max_rows=20)
    res.tables_html["負毛利商品"] = df_to_html(neg_margin, max_rows=20)
    res.csv_paths.append(write_csv(prod_agg.sort_values("margin", ascending=False), out_dir, "product_margin.csv"))
    res.csv_paths.append(write_csv(neg_margin, out_dir, "product_negative_margin.csv"))
    res.kpis["負毛利商品數"] = f"{len(neg_margin):,}"

    # --- A3 客戶毛利排行 ---
    cust_agg = lines.groupby(["cusno", "cusnm"], as_index=False, dropna=False).agg(
        revenue=("line_revenue", "sum"),
        margin=("line_margin", "sum"),
        orders=("salno", "nunique"),
    )
    cust_agg["margin_rate"] = cust_agg["margin"] / cust_agg["revenue"].replace(0, pd.NA)
    top_cust = cust_agg.sort_values("margin", ascending=False).head(20)
    res.tables_html["毛利 Top 20 客戶"] = df_to_html(top_cust, max_rows=20)
    res.csv_paths.append(write_csv(cust_agg.sort_values("margin", ascending=False), out_dir, "customer_margin.csv"))

    # --- A4 分類毛利 ---
    if "classno" in lines.columns and lines["classno"].notna().any():
        class_agg = lines.groupby(["classno", "classnm"], as_index=False, dropna=False).agg(
            revenue=("line_revenue", "sum"),
            margin=("line_margin", "sum"),
            qty=("prqty", "sum"),
        )
        class_agg["margin_rate"] = class_agg["margin"] / class_agg["revenue"].replace(0, pd.NA)
        class_agg = class_agg.sort_values("margin", ascending=False)
        res.tables_html["商品分類毛利"] = df_to_html(class_agg, max_rows=20)
        res.csv_paths.append(write_csv(class_agg, out_dir, "class_margin.csv"))

    res.notes.append("毛利 = Σ(price × prqty) − Σ(pcost × prqty)，以 sales1 逐行計算。")
    res.notes.append("月趨勢圖：長條=營收／毛利，紅線=毛利率（右軸）。")
    return res
