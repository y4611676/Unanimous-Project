# -*- coding: utf-8 -*-
"""G. 業務員績效：業績、客戶組合、毛利率。"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from ..charting import fig_to_base64
from ..enrich import enrich_sales_lines
from ..io_utils import fmt_money, fmt_pct
from ..loaders import DataBundle
from . import AnalysisResult, df_to_html, write_csv


def run(data: DataBundle, out_dir: Path) -> AnalysisResult:
    res = AnalysisResult(section_id="salesrep", title="G. 業務員績效")
    lines = enrich_sales_lines(data)
    if lines.empty or "busno" not in lines.columns or lines["busno"].isna().all():
        res.notes.append("無業務員（busno）資料。")
        return res

    # --- G1 業務員年度營收／毛利 ---
    lines2 = lines.copy()
    lines2["busno"] = lines2["busno"].astype(str).str.strip()
    lines2 = lines2[lines2["busno"] != ""]
    by_bus = lines2.groupby("busno", as_index=False).agg(
        revenue=("line_revenue", "sum"),
        margin=("line_margin", "sum"),
        orders=("salno", "nunique"),
        customers=("cusno", "nunique"),
        items=("prdno", "nunique"),
    )
    by_bus["margin_rate"] = by_bus["margin"] / by_bus["revenue"].replace(0, pd.NA)
    by_bus = by_bus.sort_values("revenue", ascending=False)

    res.csv_paths.append(write_csv(by_bus, out_dir, "salesrep_ranking.csv"))
    res.tables_html["業務員業績排行"] = df_to_html(by_bus, max_rows=30)
    res.kpis["業務員人數"] = f"{len(by_bus):,}"
    if len(by_bus) and by_bus["revenue"].sum():
        top1 = by_bus.iloc[0]
        res.kpis["最高業績業務員"] = str(top1["busno"])
        res.kpis["最高業績占比"] = fmt_pct(top1["revenue"] / by_bus["revenue"].sum())

    # 圖：前 15 位業務員營收 vs 毛利
    top = by_bus.head(15)
    fig, ax = plt.subplots(figsize=(11, max(4, len(top) * 0.35)))
    y = range(len(top))
    ax.barh(y, top["revenue"], color="steelblue", alpha=0.7, label="營收")
    ax.barh(y, top["margin"], color="darkorange", alpha=0.85, label="毛利")
    ax.set_yticks(list(y))
    ax.set_yticklabels(top["busno"])
    ax.invert_yaxis()
    ax.set_title("業務員 Top 15（營收 vs 毛利）")
    ax.legend()
    res.images_b64["salesrep_top"] = fig_to_base64(fig)

    # --- G2 客戶組合集中度（最大單一客戶佔該業務員營收比例） ---
    cust_by_bus = lines2.groupby(["busno", "cusno"], as_index=False)["line_revenue"].sum()
    mix = []
    for busno, g in cust_by_bus.groupby("busno"):
        total = g["line_revenue"].sum()
        top_share = (g["line_revenue"].max() / total) if total else 0
        n_cust = g["cusno"].nunique()
        mix.append({"busno": busno, "customers": n_cust, "top_cust_share": top_share})
    mix_df = pd.DataFrame(mix).sort_values("top_cust_share", ascending=False)
    res.tables_html["客戶組合集中度（愈高=靠大客戶）"] = df_to_html(mix_df, max_rows=20)
    res.csv_paths.append(write_csv(mix_df, out_dir, "salesrep_customer_mix.csv"))

    # --- G3 毛利率偏低警示（靠降價成交） ---
    low_margin = by_bus[(by_bus["revenue"] > 0) & (by_bus["margin_rate"] < by_bus["margin_rate"].median())].copy()
    low_margin = low_margin.sort_values("margin_rate").head(10)
    res.tables_html["毛利率偏低業務員（疑似靠降價）"] = df_to_html(low_margin)

    res.notes.append("客戶組合集中度：單一客戶佔該業務員總營收比例；>50% 代表過度依賴。")
    return res
