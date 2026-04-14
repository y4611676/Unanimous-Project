# -*- coding: utf-8 -*-
"""E. 供應商與進貨：集中度、廠商成本變動、進銷比對。"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from ..charting import fig_to_base64
from ..enrich import enrich_purchase_lines, enrich_sales_lines
from ..io_utils import fmt_money, fmt_pct
from ..loaders import DataBundle
from . import AnalysisResult, df_to_html, write_csv


def run(data: DataBundle, out_dir: Path) -> AnalysisResult:
    res = AnalysisResult(section_id="supplier", title="E. 供應商與進貨")
    p_lines = enrich_purchase_lines(data)
    s_lines = enrich_sales_lines(data)

    if p_lines.empty:
        res.notes.append("無進貨明細。")
        return res

    # --- E1 供應商集中度 ---
    by_fac = p_lines.groupby(["facno", "facnm"], as_index=False, dropna=False).agg(
        purchase=("line_cost", "sum"),
        orders=("purno", "nunique"),
        items=("prdno", "nunique"),
    ).sort_values("purchase", ascending=False)
    total = by_fac["purchase"].sum()
    if total > 0:
        by_fac["share"] = by_fac["purchase"] / total
        by_fac["cum_share"] = by_fac["share"].cumsum()

    res.csv_paths.append(write_csv(by_fac, out_dir, "supplier_ranking.csv"))
    top5_share = by_fac.head(5)["share"].sum() if "share" in by_fac.columns else 0
    top10_share = by_fac.head(10)["share"].sum() if "share" in by_fac.columns else 0
    res.kpis["前 5 大廠商進貨占比"] = fmt_pct(top5_share)
    res.kpis["前 10 大廠商進貨占比"] = fmt_pct(top10_share)
    res.kpis["總廠商數"] = f"{len(by_fac):,}"
    res.tables_html["廠商採購排行 Top 20"] = df_to_html(by_fac.head(20))

    # Pareto 圖
    if "cum_share" in by_fac.columns:
        fig, ax1 = plt.subplots(figsize=(11, 4.5))
        xs = range(len(by_fac))
        ax1.bar(xs, by_fac["purchase"], color="steelblue", alpha=0.6)
        ax2 = ax1.twinx()
        ax2.plot(xs, by_fac["cum_share"] * 100, color="darkred")
        ax2.axhline(80, color="grey", linestyle="--", linewidth=0.8)
        ax1.set_title("供應商採購 Pareto")
        ax1.set_xlabel("供應商（依採購金額排序）")
        ax1.set_ylabel("採購金額")
        ax2.set_ylabel("累計占比 (%)")
        res.images_b64["supplier_pareto"] = fig_to_base64(fig)

    # --- E2 同商品跨時間／跨廠商的進貨單價變動 ---
    if "price" in p_lines.columns:
        # 以年為粒度，看每個商品的平均採購單價
        pl = p_lines.dropna(subset=["pdate", "prdno"]).copy()
        pl["year"] = pl["pdate"].dt.year
        pl = pl[pl["price"] > 0]
        if not pl.empty:
            cost_trend = pl.groupby(["prdno", "year"], as_index=False)["price"].mean()
            # 找有 2 年以上資料且最高最低差 > 10%
            piv = cost_trend.pivot(index="prdno", columns="year", values="price")
            piv = piv.dropna(thresh=2)
            if not piv.empty:
                piv["min"] = piv.min(axis=1)
                piv["max"] = piv.max(axis=1)
                piv["pct_change"] = (piv["max"] - piv["min"]) / piv["min"]
                movers = piv.sort_values("pct_change", ascending=False).head(30).reset_index()
                if not data.prod.empty:
                    movers = movers.merge(
                        data.prod[["prdno", "prdnm"]].drop_duplicates("prdno"),
                        on="prdno", how="left",
                    )
                res.tables_html["成本波動最大商品 Top 30"] = df_to_html(movers, max_rows=30)
                res.csv_paths.append(write_csv(movers, out_dir, "cost_drift.csv"))

    # --- E3 進銷比對（數量） ---
    if not s_lines.empty:
        s_qty = s_lines.groupby("prdno", as_index=False)["prqty"].sum().rename(columns={"prqty": "sold_qty"})
        p_qty = p_lines.groupby("prdno", as_index=False)["prqty"].sum().rename(columns={"prqty": "purchased_qty"})
        bal = p_qty.merge(s_qty, on="prdno", how="outer").fillna(0)
        bal["purchased_qty"] = pd.to_numeric(bal["purchased_qty"], errors="coerce").fillna(0)
        bal["sold_qty"] = pd.to_numeric(bal["sold_qty"], errors="coerce").fillna(0)
        bal["diff"] = bal["purchased_qty"] - bal["sold_qty"]
        bal["sell_through"] = bal["sold_qty"] / bal["purchased_qty"].replace(0, pd.NA)
        if not data.prod.empty:
            bal = bal.merge(
                data.prod[["prdno", "prdnm"]].drop_duplicates("prdno"),
                on="prdno", how="left",
            )

        # 進多賣少（purchased >> sold，sell_through < 0.5）
        over_buy = bal[(bal["purchased_qty"] >= 10) & (bal["sell_through"] < 0.5)].sort_values("diff", ascending=False)
        # 賣多沒進（purchased < sold）→ 可能庫存吃老本，未補貨
        under_buy = bal[bal["diff"] < -5].sort_values("diff")

        res.csv_paths.append(write_csv(over_buy, out_dir, "overstocked.csv"))
        res.csv_paths.append(write_csv(under_buy, out_dir, "underreplenished.csv"))
        res.tables_html["進多賣少 Top 20"] = df_to_html(over_buy.head(20))
        res.tables_html["賣多沒補 Top 20"] = df_to_html(under_buy.head(20))

    res.notes.append("集中度：前 5/10 大廠商佔採購金額比例（愈高風險愈大，斷鏈衝擊愈強）。")
    res.notes.append("成本波動：以「同商品各年平均採購單價最大跌到最小的百分比」衡量。")
    return res
