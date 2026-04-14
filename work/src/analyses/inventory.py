# -*- coding: utf-8 -*-
"""B. 商品與庫存：ABC 分析、呆料金額化、庫存週轉、安全庫存告警、缺貨偵測。"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..charting import fig_to_base64
from ..enrich import enrich_sales_lines
from ..io_utils import fmt_money
from ..loaders import DataBundle
from . import AnalysisResult, df_to_html, write_csv


def run(data: DataBundle, out_dir: Path) -> AnalysisResult:
    res = AnalysisResult(section_id="inventory", title="B. 商品與庫存")
    prod = data.prod.copy()
    lines = enrich_sales_lines(data)

    if prod.empty:
        res.notes.append("無 prod 主檔。")
        return res

    prod["qty"] = pd.to_numeric(prod["qty"], errors="coerce").fillna(0.0)
    prod["pcost"] = pd.to_numeric(prod["pcost"], errors="coerce").fillna(0.0)
    prod["safeqty"] = pd.to_numeric(prod.get("safeqty", 0), errors="coerce").fillna(0.0)

    # --- B1 ABC 分析（依營收） ---
    if not lines.empty:
        by_prod = lines.groupby("prdno", as_index=False).agg(
            revenue=("line_revenue", "sum"),
            qty_sold=("prqty", "sum"),
        )
        by_prod = by_prod.sort_values("revenue", ascending=False).reset_index(drop=True)
        total = by_prod["revenue"].sum()
        by_prod["cum_revenue"] = by_prod["revenue"].cumsum()
        by_prod["cum_share"] = by_prod["cum_revenue"] / total if total else 0
        by_prod["abc_class"] = np.where(
            by_prod["cum_share"] <= 0.80, "A",
            np.where(by_prod["cum_share"] <= 0.95, "B", "C"),
        )
        by_prod = by_prod.merge(
            prod[["prdno", "prdnm", "classno", "qty", "pcost"]].drop_duplicates("prdno"),
            on="prdno",
            how="left",
        )

        res.csv_paths.append(write_csv(by_prod, out_dir, "abc_analysis.csv"))

        # Pareto 圖
        fig, ax1 = plt.subplots(figsize=(11, 4.5))
        ax1.bar(range(len(by_prod)), by_prod["revenue"], color="steelblue", alpha=0.6)
        ax1.set_xlabel("商品（依營收排序）")
        ax1.set_ylabel("營收")
        ax2 = ax1.twinx()
        ax2.plot(range(len(by_prod)), by_prod["cum_share"] * 100, color="darkred")
        ax2.axhline(80, color="grey", linestyle="--", linewidth=0.8)
        ax2.axhline(95, color="grey", linestyle=":", linewidth=0.8)
        ax2.set_ylabel("累計營收占比 (%)")
        ax1.set_title("商品 ABC 分析（Pareto）")
        res.images_b64["abc_pareto"] = fig_to_base64(fig)

        # 分類統計
        counts = by_prod["abc_class"].value_counts().reindex(["A", "B", "C"]).fillna(0).astype(int)
        rev_share = by_prod.groupby("abc_class")["revenue"].sum() / total if total else pd.Series()
        summary = pd.DataFrame({
            "類別": counts.index,
            "品項數": counts.values,
            "營收占比": [f"{(rev_share.get(c, 0) * 100):.1f}%" for c in counts.index],
        })
        res.tables_html["ABC 分類彙總"] = df_to_html(summary)
        res.kpis["A 類品項數"] = f"{int(counts.get('A', 0)):,}"
        res.kpis["C 類品項數"] = f"{int(counts.get('C', 0)):,}"

    # --- B2 呆料金額化（>365 天無進出 × 庫存 × 成本） ---
    ref = data.ref_date
    has_date = prod["lastin"].notna() | prod["lastout"].notna()
    last_act = prod[["lastin", "lastout"]].max(axis=1)
    prod["last_activity"] = last_act
    prod["idle_days"] = (ref - last_act).dt.days
    stale_mask = has_date & (prod["idle_days"] > 365)
    stale = prod[stale_mask].copy()
    stale["dead_value"] = stale["qty"] * stale["pcost"]
    stale = stale.sort_values("dead_value", ascending=False)

    keep_cols = [c for c in ("prdno", "prdnm", "classno", "qty", "pcost", "dead_value",
                             "lastin", "lastout", "last_activity", "idle_days", "isstock") if c in stale.columns]
    res.csv_paths.append(write_csv(stale[keep_cols], out_dir, "products_stale_over_one_year.csv"))
    dead_total = float(stale["dead_value"].sum())
    res.kpis["呆料金額"] = fmt_money(dead_total)
    res.kpis["呆料品項數"] = f"{len(stale):,}"
    res.tables_html["呆料 Top 20（金額）"] = df_to_html(stale[keep_cols].head(20))

    # --- B3 庫存週轉率（按分類） ---
    if not lines.empty and "classno" in lines.columns:
        cogs_by_class = lines.groupby("classno", as_index=False)["line_cost"].sum().rename(
            columns={"line_cost": "cogs"}
        )
        stock_by_class = prod.assign(stock_value=prod["qty"] * prod["pcost"]).groupby(
            "classno", as_index=False
        )["stock_value"].sum()
        turn = cogs_by_class.merge(stock_by_class, on="classno", how="outer").fillna(0)
        turn["turnover"] = np.where(turn["stock_value"] > 0, turn["cogs"] / turn["stock_value"], np.nan)
        # 補分類名稱
        if not data.classes.empty:
            turn = turn.merge(
                data.classes[["classno", "classnm"]].drop_duplicates("classno"),
                on="classno", how="left",
            )
        turn = turn.sort_values("turnover", ascending=False, na_position="last")
        res.tables_html["分類庫存週轉率"] = df_to_html(turn, max_rows=20)
        res.csv_paths.append(write_csv(turn, out_dir, "class_turnover.csv"))

    # --- B4 安全庫存告警（qty < safeqty 且 safeqty > 0） ---
    safe_breach = prod[(prod["safeqty"] > 0) & (prod["qty"] < prod["safeqty"])].copy()
    cols_b4 = [c for c in ("prdno", "prdnm", "classno", "qty", "safeqty", "pcost", "isstock") if c in safe_breach.columns]
    safe_breach["shortage"] = safe_breach["safeqty"] - safe_breach["qty"]
    safe_breach = safe_breach.sort_values("shortage", ascending=False)
    res.csv_paths.append(write_csv(safe_breach[cols_b4 + ["shortage"]], out_dir, "safety_stock_breach.csv"))
    res.kpis["安全庫存破線品項"] = f"{len(safe_breach):,}"
    res.tables_html["安全庫存告警 Top 20"] = df_to_html(safe_breach[cols_b4 + ["shortage"]].head(20))

    # --- B5 可能缺貨（isstock=Y & qty<=0 & 近一年有銷量） ---
    if "isstock" in prod.columns and not lines.empty:
        recent = lines[lines["sdate"] >= (ref - pd.Timedelta(days=365))]
        recent_sold = recent.groupby("prdno", as_index=False)["prqty"].sum().rename(columns={"prqty": "qty_sold_1y"})
        oos = prod[(prod["isstock"].astype(str).str.strip() == "Y") & (prod["qty"] <= 0)].copy()
        oos = oos.merge(recent_sold, on="prdno", how="inner")
        cols_b5 = [c for c in ("prdno", "prdnm", "classno", "qty", "safeqty", "pcost", "qty_sold_1y") if c in oos.columns]
        oos = oos.sort_values("qty_sold_1y", ascending=False)
        res.csv_paths.append(write_csv(oos[cols_b5], out_dir, "out_of_stock_with_recent_sales.csv"))
        res.kpis["疑似缺貨品項"] = f"{len(oos):,}"
        res.tables_html["疑似缺貨 Top 20"] = df_to_html(oos[cols_b5].head(20))

    res.notes.append("ABC：A=累積營收≤80%，B=≤95%，C=其餘。")
    res.notes.append("呆料金額 = 庫存 qty × 成本 pcost；僅列入最後進出日距今 > 365 天的品項。")
    res.notes.append("週轉率（近似）= Σ(銷貨成本) / Σ(現有庫存成本)；值愈高愈好。")
    return res
