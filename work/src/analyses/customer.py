# -*- coding: utf-8 -*-
"""C. 客戶深度分析：RFM（評分版）、Pareto、生命週期、Cohort、地區、類型。"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..charting import fig_to_base64
from ..enrich import enrich_sales_lines
from ..io_utils import fmt_money, fmt_pct
from ..loaders import DataBundle
from . import AnalysisResult, df_to_html, write_csv


def _score_1_to_5(s: pd.Series, ascending: bool) -> pd.Series:
    """把分數切 5 等分 (1-5)。ascending=True 代表值愈高分數愈高。"""
    if s.nunique(dropna=True) < 5:
        # 分不出 5 級時用簡單 rank 再 clip
        ranks = s.rank(method="average", pct=True, ascending=ascending)
        return (ranks * 5).clip(1, 5).round().astype("Int64")
    try:
        q = pd.qcut(s, 5, labels=[1, 2, 3, 4, 5] if ascending else [5, 4, 3, 2, 1], duplicates="drop")
        return q.astype("Int64")
    except ValueError:
        ranks = s.rank(method="average", pct=True, ascending=ascending)
        return (ranks * 5).clip(1, 5).round().astype("Int64")


def run(data: DataBundle, out_dir: Path) -> AnalysisResult:
    res = AnalysisResult(section_id="customer", title="C. 客戶深度分析")
    lines = enrich_sales_lines(data)
    cust = data.cust.copy()
    if lines.empty:
        res.notes.append("無銷貨明細資料。")
        return res

    ref = data.ref_date
    cutoff = ref - pd.Timedelta(days=365)

    # --- 基礎：每客戶彙總（含毛利） ---
    cus_agg = lines.groupby("cusno", as_index=False).agg(
        last_purchase=("sdate", "max"),
        first_purchase=("sdate", "min"),
        frequency=("salno", "nunique"),
        monetary=("line_revenue", "sum"),
        margin=("line_margin", "sum"),
    )
    cus_agg["recency_days"] = (ref - cus_agg["last_purchase"]).dt.days
    if not cust.empty:
        cols = [c for c in ("cusno", "cusnm", "area", "kind") if c in cust.columns]
        cus_agg = cus_agg.merge(cust[cols].drop_duplicates("cusno"), on="cusno", how="left")

    # --- C4 RFM Score（1–5）---
    cus_agg["R_score"] = _score_1_to_5(-cus_agg["recency_days"], ascending=True)  # 愈新愈高
    cus_agg["F_score"] = _score_1_to_5(cus_agg["frequency"], ascending=True)
    cus_agg["M_score"] = _score_1_to_5(cus_agg["monetary"], ascending=True)
    cus_agg["RFM_sum"] = cus_agg[["R_score", "F_score", "M_score"]].sum(axis=1)

    def _segment(row: pd.Series) -> str:
        r, f, m = row["R_score"], row["F_score"], row["M_score"]
        if pd.isna(r) or pd.isna(f) or pd.isna(m):
            return "Unknown"
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions 黃金客"
        if r >= 4 and f >= 3:
            return "Loyal 忠實客"
        if r >= 4 and f <= 2:
            return "New 新客"
        if r <= 2 and f >= 3 and m >= 3:
            return "At Risk 流失中"
        if r <= 2 and f <= 2:
            return "Lost 已流失"
        return "Others"

    cus_agg["segment"] = cus_agg.apply(_segment, axis=1)
    res.csv_paths.append(write_csv(cus_agg.sort_values("monetary", ascending=False), out_dir, "rfm_scored.csv"))

    seg_summary = cus_agg.groupby("segment", as_index=False).agg(
        customers=("cusno", "count"),
        revenue=("monetary", "sum"),
        margin=("margin", "sum"),
    ).sort_values("revenue", ascending=False)
    res.tables_html["RFM 分群摘要"] = df_to_html(seg_summary)
    res.csv_paths.append(write_csv(seg_summary, out_dir, "rfm_segment_summary.csv"))

    # --- C1 Pareto 80/20 ---
    sorted_rev = cus_agg.sort_values("monetary", ascending=False).reset_index(drop=True)
    total_rev = sorted_rev["monetary"].sum()
    sorted_rev["cum_share"] = sorted_rev["monetary"].cumsum() / total_rev if total_rev else 0
    n_80 = int((sorted_rev["cum_share"] < 0.80).sum()) + 1 if total_rev else 0
    share_80 = n_80 / len(sorted_rev) if len(sorted_rev) else 0
    res.kpis["80% 營收來自客戶數"] = f"{n_80:,}"
    res.kpis["佔總客戶比例"] = fmt_pct(share_80)

    fig, ax1 = plt.subplots(figsize=(11, 4.5))
    ax1.bar(range(len(sorted_rev)), sorted_rev["monetary"], color="steelblue", alpha=0.6)
    ax2 = ax1.twinx()
    ax2.plot(range(len(sorted_rev)), sorted_rev["cum_share"] * 100, color="darkred")
    ax2.axhline(80, color="grey", linestyle="--", linewidth=0.8)
    ax1.set_xlabel("客戶（依營收排序）")
    ax1.set_ylabel("客戶營收")
    ax2.set_ylabel("累計占比 (%)")
    ax1.set_title("客戶 80/20 Pareto")
    res.images_b64["pareto"] = fig_to_base64(fig)

    # --- C2 新客 vs 回頭客月度占比 ---
    first_order_month = lines.groupby("cusno")["sdate"].min().dt.to_period("M").dt.to_timestamp()
    lines2 = lines.copy()
    lines2["first_month"] = lines2["cusno"].map(first_order_month)
    lines2["is_new_cust"] = lines2["month"] == lines2["first_month"]
    by_month = lines2.groupby("month").agg(
        total_rev=("line_revenue", "sum"),
        new_rev=("line_revenue", lambda s: s[lines2.loc[s.index, "is_new_cust"]].sum()),
    )
    by_month["repeat_rev"] = by_month["total_rev"] - by_month["new_rev"]
    by_month["new_share"] = by_month["new_rev"] / by_month["total_rev"].replace(0, pd.NA)

    fig2, ax = plt.subplots(figsize=(12, 4.5))
    ax.stackplot(by_month.index, by_month["new_rev"], by_month["repeat_rev"],
                 labels=["新客", "回頭客"], alpha=0.7)
    ax.set_title("新客 vs 回頭客 月營收組成")
    ax.set_ylabel("營收")
    ax.legend(loc="upper left")
    res.images_b64["new_vs_repeat"] = fig_to_base64(fig2)
    by_month_out = by_month.reset_index()
    by_month_out["month"] = by_month_out["month"].dt.strftime("%Y-%m")
    res.csv_paths.append(write_csv(by_month_out, out_dir, "new_vs_repeat.csv"))

    # --- C3 Cohort 留存（首購月 × 距首購月份 M+k）---
    lines3 = lines.dropna(subset=["sdate"]).copy()
    lines3["first_month"] = lines3["cusno"].map(first_order_month)
    lines3["period_m"] = (
        (lines3["month"].dt.year - lines3["first_month"].dt.year) * 12
        + (lines3["month"].dt.month - lines3["first_month"].dt.month)
    )
    cohort = (
        lines3.groupby(["first_month", "period_m"])["cusno"]
        .nunique()
        .reset_index()
        .pivot(index="first_month", columns="period_m", values="cusno")
        .fillna(0)
        .astype(int)
    )
    cohort_sizes = cohort.iloc[:, 0].replace(0, np.nan)
    cohort_pct = cohort.div(cohort_sizes, axis=0)
    # 取前 12 期
    if cohort_pct.shape[1] > 13:
        cohort_pct = cohort_pct.iloc[:, :13]
    if cohort_pct.shape[0] > 24:
        cohort_pct = cohort_pct.tail(24)

    fig3, ax3 = plt.subplots(figsize=(11, max(4, len(cohort_pct) * 0.25)))
    im = ax3.imshow(cohort_pct.values, aspect="auto", cmap="Blues", vmin=0, vmax=1)
    ax3.set_xticks(range(len(cohort_pct.columns)))
    ax3.set_xticklabels([f"M+{c}" for c in cohort_pct.columns])
    ax3.set_yticks(range(len(cohort_pct.index)))
    ax3.set_yticklabels([d.strftime("%Y-%m") for d in cohort_pct.index])
    ax3.set_title("Cohort 留存率（按首購月）")
    for y in range(cohort_pct.shape[0]):
        for x in range(cohort_pct.shape[1]):
            v = cohort_pct.values[y, x]
            if pd.notna(v):
                ax3.text(x, y, f"{v*100:.0f}", ha="center", va="center",
                         color="white" if v > 0.5 else "black", fontsize=7)
    fig3.colorbar(im, ax=ax3, shrink=0.7, label="留存率")
    res.images_b64["cohort"] = fig_to_base64(fig3)
    res.csv_paths.append(write_csv(cohort_pct.reset_index(), out_dir, "cohort_retention.csv"))

    # --- C5 地區分析 ---
    if "area" in cus_agg.columns and cus_agg["area"].notna().any():
        area_agg = cus_agg.groupby("area", as_index=False).agg(
            customers=("cusno", "count"),
            revenue=("monetary", "sum"),
            margin=("margin", "sum"),
        )
        area_agg["avg_per_cust"] = area_agg["revenue"] / area_agg["customers"]
        area_agg = area_agg.sort_values("revenue", ascending=False)
        res.tables_html["地區營收（Top 20）"] = df_to_html(area_agg, max_rows=20)
        res.csv_paths.append(write_csv(area_agg, out_dir, "area_revenue.csv"))

    # --- C6 客戶類型（kind） ---
    if "kind" in cus_agg.columns and cus_agg["kind"].notna().any():
        kind_agg = cus_agg.groupby("kind", as_index=False).agg(
            customers=("cusno", "count"),
            revenue=("monetary", "sum"),
            margin=("margin", "sum"),
        )
        kind_agg["avg_per_cust"] = kind_agg["revenue"] / kind_agg["customers"]
        kind_agg = kind_agg.sort_values("revenue", ascending=False)
        res.tables_html["客戶類型"] = df_to_html(kind_agg)
        res.csv_paths.append(write_csv(kind_agg, out_dir, "kind_revenue.csv"))

    # --- 未交易名單（延用舊分析） ---
    inactive = cus_agg[cus_agg["last_purchase"] < cutoff].copy()
    if not cust.empty:
        had_sale = set(cus_agg["cusno"].unique())
        never = cust[~cust["cusno"].isin(had_sale)][["cusno"] + (["cusnm"] if "cusnm" in cust.columns else [])].copy()
        never["last_purchase"] = pd.NaT
        never["monetary"] = 0.0
        never["frequency"] = 0
        inactive = pd.concat([inactive, never], ignore_index=True)
    res.csv_paths.append(write_csv(inactive.sort_values("cusno"), out_dir, "customers_no_trade_in_last_year.csv"))
    res.kpis["近一年未交易客戶"] = f"{len(inactive):,}"

    res.kpis["總客戶數（有銷貨）"] = f"{len(cus_agg):,}"
    res.kpis["平均客戶終身營收"] = fmt_money(cus_agg["monetary"].mean() if len(cus_agg) else 0)

    res.notes.append("RFM Score：各指標分 5 等分，R 愈新愈高、F 愈頻繁愈高、M 愈大愈高。")
    res.notes.append("分群規則：R≥4 & F≥4 & M≥4 → Champions；R≤2 & F≥3 → At Risk；R≤2 & F≤2 → Lost。")
    return res
