# -*- coding: utf-8 -*-
"""H. 時間序列：下期營收預測（線性 + 3 月移動平均）、季節分解、異常月偵測。

為了避免重量級依賴（Prophet/ARIMA），預測用簡易線性迴歸 + 移動平均，
並以同月年比（YoY）與 z-score 做異常檢測。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..charting import fig_to_base64, month_axis
from ..io_utils import fmt_money
from ..loaders import DataBundle
from . import AnalysisResult, df_to_html, write_csv


def run(data: DataBundle, out_dir: Path) -> AnalysisResult:
    res = AnalysisResult(section_id="forecast", title="H. 預測與異常偵測")
    sale = data.sale.copy()
    if sale.empty:
        return res
    sale = sale.dropna(subset=["sdate"])
    sale["tot"] = pd.to_numeric(sale["tot"], errors="coerce").fillna(0.0)
    monthly = (
        sale.set_index("sdate").groupby(pd.Grouper(freq="MS"))["tot"].sum().sort_index()
    )
    if len(monthly) < 6:
        res.notes.append("月份太少（<6），無法做有意義的預測。")
        return res

    # --- H1 下月營收預測（線性迴歸 + 3 月移動平均） ---
    y = monthly.values.astype(float)
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    trend_next = intercept + slope * len(y)

    # 季節性係數：近 3 年同月份的平均相對於整體平均
    s = pd.Series(y, index=monthly.index)
    last_month = monthly.index[-1].month
    same_month = s[s.index.month == ((last_month % 12) + 1)]  # 下個月的歷史平均
    seasonal = same_month.mean() / s.mean() if s.mean() else 1.0
    seasonal = float(seasonal) if not np.isnan(seasonal) else 1.0

    ma3 = s.rolling(3).mean().iloc[-1] if len(s) >= 3 else s.mean()
    forecast_next = 0.5 * trend_next * seasonal + 0.5 * ma3

    next_month_date = monthly.index[-1] + pd.DateOffset(months=1)
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(monthly.index, y, marker="o", linewidth=1.5, label="實績")
    ax.plot(monthly.index, intercept + slope * x, linestyle="--", color="grey", label="線性趨勢")
    ax.plot([monthly.index[-1], next_month_date], [y[-1], forecast_next],
            marker="*", markersize=12, color="red", linewidth=2, label="下月預測")
    ax.set_title(f"月營收 + 下月預測 ({next_month_date.strftime('%Y-%m')})")
    ax.set_ylabel("營收")
    ax.grid(True, alpha=0.3)
    month_axis(ax, list(monthly.index) + [next_month_date])
    ax.legend()
    res.images_b64["forecast"] = fig_to_base64(fig)

    res.kpis["下月預測營收"] = fmt_money(float(forecast_next))
    res.kpis["季節性調整係數"] = f"{seasonal:.2f}"
    res.kpis["線性月增量"] = fmt_money(float(slope))

    # --- H2 季節性：月份平均 ---
    monthly_avg = s.groupby(s.index.month).mean()
    fig2, ax2 = plt.subplots(figsize=(9, 4))
    ax2.bar(monthly_avg.index, monthly_avg.values, color="steelblue", alpha=0.7)
    ax2.set_xticks(range(1, 13))
    ax2.set_xlabel("月份")
    ax2.set_ylabel("平均營收")
    ax2.set_title("季節性：各月份平均營收")
    res.images_b64["seasonality"] = fig_to_base64(fig2)

    # --- H3 異常月偵測：z-score ---
    mean, std = s.mean(), s.std()
    z = (s - mean) / std if std else s * 0
    anomalies = pd.DataFrame({
        "month": s.index,
        "revenue": s.values,
        "z_score": z.values,
    })
    anomalies["flag"] = np.where(
        anomalies["z_score"].abs() >= 2,
        np.where(anomalies["z_score"] > 0, "高 (🔺)", "低 (🔻)"),
        "",
    )
    anomalies_out = anomalies.copy()
    anomalies_out["month"] = anomalies_out["month"].dt.strftime("%Y-%m")
    res.csv_paths.append(write_csv(anomalies_out, out_dir, "revenue_anomalies.csv"))
    top_anom = anomalies_out[anomalies_out["flag"] != ""].sort_values("z_score", key=lambda s: s.abs(), ascending=False)
    res.tables_html["異常月份（|z| ≥ 2）"] = df_to_html(top_anom, max_rows=20)
    res.kpis["異常月份數"] = f"{len(top_anom):,}"

    # YoY 同比
    yoy = s.pct_change(12).dropna()
    if not yoy.empty:
        fig3, ax3 = plt.subplots(figsize=(12, 3.5))
        colors = np.where(yoy.values >= 0, "seagreen", "indianred")
        ax3.bar(yoy.index, yoy.values * 100, color=colors, alpha=0.7, width=20)
        ax3.axhline(0, color="black", linewidth=0.5)
        ax3.set_title("YoY 同比成長（%）")
        ax3.set_ylabel("成長率 (%)")
        month_axis(ax3, yoy.index)
        res.images_b64["yoy"] = fig_to_base64(fig3)

    res.notes.append("預測模型：線性趨勢 × 季節性係數 + 3 月移動平均，各取 50% 權重。僅供參考。")
    res.notes.append("異常偵測：|z-score| ≥ 2 的月份標記為異常高／低點。")
    return res
