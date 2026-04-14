# -*- coding: utf-8 -*-
"""F. 現金流 / 應收帳款：AR Aging、DSO、壞帳名單、月現金流。

注意：資料表 rereces / repays 使用 rlamt3 或 rlamt4 記錄金額（視系統設定），
      這裡採「非零者較大值」作為實際入帳金額。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..charting import fig_to_base64, month_axis
from ..enrich import enrich_sales_lines
from ..io_utils import fmt_money
from ..loaders import DataBundle
from . import AnalysisResult, df_to_html, write_csv


def _receipt_amount(row: pd.Series) -> float:
    a = float(row.get("rlamt3") or 0)
    b = float(row.get("rlamt4") or 0)
    return a if abs(a) >= abs(b) else b


def run(data: DataBundle, out_dir: Path) -> AnalysisResult:
    res = AnalysisResult(section_id="cashflow", title="F. 現金流與應收帳款")
    sale = data.sale.copy()
    rerece = data.rerece.copy()
    rereces = data.rereces.copy()
    repay = data.repay.copy()
    repays = data.repays.copy()

    if sale.empty:
        res.notes.append("無銷貨資料，無法計算 AR。")
        return res

    # --- 每張單的收款彙總 ---
    recv_merged = pd.DataFrame()
    if not rerece.empty and not rereces.empty:
        rereces = rereces.copy()
        rereces["amount"] = rereces.apply(_receipt_amount, axis=1)
        rece_by_rel = rereces.groupby("relno", as_index=False)["amount"].sum()
        recv_merged = rerece[["relno", "cusno", "rdate"]].merge(rece_by_rel, on="relno", how="left")
        recv_merged["amount"] = recv_merged["amount"].fillna(0.0)

    # 客戶應收 = Σsale.ttot − Σ收款金額（以匿名資料無明確對應到 salno，故以客戶為粒度）
    sale["ttot"] = pd.to_numeric(sale["ttot"], errors="coerce").fillna(0.0)
    by_cust_sale = sale.groupby("cusno", as_index=False).agg(
        billed=("ttot", "sum"),
        last_sale=("sdate", "max"),
        orders=("salno", "nunique"),
    )
    if not recv_merged.empty:
        by_cust_recv = recv_merged.groupby("cusno", as_index=False).agg(
            received=("amount", "sum"),
            last_recv=("rdate", "max"),
        )
    else:
        by_cust_recv = pd.DataFrame({"cusno": [], "received": [], "last_recv": []})
    ar = by_cust_sale.merge(by_cust_recv, on="cusno", how="left")
    ar["received"] = ar["received"].fillna(0.0)
    ar["outstanding"] = ar["billed"] - ar["received"]

    # --- F1 AR Aging（依最後購買日估算帳齡；匿名資料無明細逐筆到期日） ---
    ref = data.ref_date
    ar["days_since_last_sale"] = (ref - ar["last_sale"]).dt.days
    buckets = [("0-30", 0, 30), ("31-60", 31, 60), ("61-90", 61, 90),
               ("91-180", 91, 180), ("181-365", 181, 365), ("365+", 366, 10**6)]
    aging_rows = []
    only_out = ar[ar["outstanding"] > 0].copy()
    for label, lo, hi in buckets:
        mask = (only_out["days_since_last_sale"] >= lo) & (only_out["days_since_last_sale"] <= hi)
        aging_rows.append({
            "帳齡": label,
            "客戶數": int(mask.sum()),
            "未收金額": float(only_out.loc[mask, "outstanding"].sum()),
        })
    aging = pd.DataFrame(aging_rows)
    res.tables_html["應收帳齡分析"] = df_to_html(aging)
    res.csv_paths.append(write_csv(aging, out_dir, "ar_aging.csv"))

    # 長條圖
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(aging["帳齡"], aging["未收金額"], color="firebrick", alpha=0.7)
    ax.set_title("應收帳齡分布")
    ax.set_ylabel("未收金額")
    res.images_b64["ar_aging"] = fig_to_base64(fig)

    # --- F3 壞帳風險名單（未收 > 0 & 最近一年未交易） ---
    cutoff = ref - pd.Timedelta(days=365)
    bad = ar[(ar["outstanding"] > 0) & (ar["last_sale"] < cutoff)].copy()
    if not data.cust.empty:
        cols = [c for c in ("cusno", "cusnm", "area", "settle") if c in data.cust.columns]
        bad = bad.merge(data.cust[cols].drop_duplicates("cusno"), on="cusno", how="left")
    bad = bad.sort_values("outstanding", ascending=False)
    res.csv_paths.append(write_csv(bad, out_dir, "bad_debt_risk.csv"))
    res.tables_html["壞帳風險 Top 20"] = df_to_html(bad.head(20))
    res.kpis["疑似壞帳客戶"] = f"{len(bad):,}"
    res.kpis["疑似壞帳金額"] = fmt_money(float(bad["outstanding"].sum()))

    # --- F2 DSO（Days Sales Outstanding，整體近似） ---
    total_ar = float(only_out["outstanding"].sum())
    recent_sales = sale[sale["sdate"] >= (ref - pd.Timedelta(days=365))]["ttot"].sum()
    dso = (total_ar / recent_sales * 365) if recent_sales else float("nan")
    res.kpis["整體未收金額"] = fmt_money(total_ar)
    res.kpis["近似 DSO (天)"] = f"{dso:,.1f}" if not np.isnan(dso) else "-"

    # --- F4 月現金流（收 − 付） ---
    if not recv_merged.empty:
        rin = recv_merged.dropna(subset=["rdate"]).copy()
        rin["month"] = rin["rdate"].dt.to_period("M").dt.to_timestamp()
        in_m = rin.groupby("month", as_index=False)["amount"].sum().rename(columns={"amount": "in"})
    else:
        in_m = pd.DataFrame({"month": [], "in": []})

    if not repay.empty and not repays.empty:
        repays2 = repays.copy()
        repays2["amount"] = repays2.apply(_receipt_amount, axis=1)
        rp_by_rel = repays2.groupby("relno", as_index=False)["amount"].sum()
        rp_merged = repay[["relno", "rdate"]].merge(rp_by_rel, on="relno", how="left")
        rp_merged["amount"] = rp_merged["amount"].fillna(0.0)
        rp_merged = rp_merged.dropna(subset=["rdate"])
        rp_merged["month"] = rp_merged["rdate"].dt.to_period("M").dt.to_timestamp()
        out_m = rp_merged.groupby("month", as_index=False)["amount"].sum().rename(columns={"amount": "out"})
    else:
        out_m = pd.DataFrame({"month": [], "out": []})

    cf = in_m.merge(out_m, on="month", how="outer").fillna(0).sort_values("month")
    cf["net"] = cf["in"] - cf["out"]
    if not cf.empty:
        fig2, ax2 = plt.subplots(figsize=(12, 4.5))
        ax2.bar(cf["month"], cf["in"], width=20, label="收款", alpha=0.7, color="seagreen")
        ax2.bar(cf["month"], -cf["out"], width=20, label="付款", alpha=0.7, color="indianred")
        ax2.plot(cf["month"], cf["net"], color="black", marker="o", linewidth=1.5, label="淨現金流")
        ax2.axhline(0, color="grey", linewidth=0.5)
        ax2.set_title("月現金流（收 − 付）")
        ax2.set_ylabel("金額")
        month_axis(ax2, cf["month"])
        ax2.legend()
        res.images_b64["monthly_cashflow"] = fig_to_base64(fig2)
        cf_out = cf.copy()
        cf_out["month"] = cf_out["month"].dt.strftime("%Y-%m")
        res.csv_paths.append(write_csv(cf_out, out_dir, "monthly_cashflow.csv"))

    res.notes.append("AR 以『客戶層』彙總（匿名資料缺逐筆單據連結）；帳齡以客戶最後銷貨日距今天數分箱。")
    res.notes.append("收款金額取 rlamt3 / rlamt4 中絕對值較大者（視原系統哪欄記主金額）。")
    return res
