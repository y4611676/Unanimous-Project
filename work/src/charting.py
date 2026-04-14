# -*- coding: utf-8 -*-
"""圖表輔助：統一字型、輸出 PNG 與轉為 base64 供 HTML 內嵌。"""
from __future__ import annotations

import base64
import io
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 中文字型（Windows / 常見 Linux fallback）
plt.rcParams["font.sans-serif"] = [
    "Microsoft JhengHei",
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK TC",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def save_fig(fig: plt.Figure, out_dir: Path, name: str, dpi: int = 150) -> Path:
    """儲存 PNG 到 out_dir。回傳路徑。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_to_base64(fig: plt.Figure, dpi: int = 150) -> str:
    """把圖表轉成 base64 data URI（HTML 內嵌，不必管外部檔）。"""
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def month_axis(ax, dates, max_ticks: int = 24) -> None:
    """月份 x 軸通用格式。"""
    n = len(dates)
    step = max(1, n // max_ticks) if n > max_ticks else 1
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=step))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
