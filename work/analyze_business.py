# -*- coding: utf-8 -*-
"""
【步驟 3】商業分析：營收月趨勢、RFM／近一年未交易客戶、久未進出商品（依 prod 最後進出日）。
CSV 預設以 Big5 讀取；若失敗則嘗試 utf-8-sig（與 export_mdb_to_csv 匯出一致）。

輸出目錄：與腳本同層的 analysis_output/
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from html import escape
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

# 微軟正黑體（Windows）
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

ENCODINGS = ("big5", "cp950", "utf-8-sig", "utf-8")


def read_csv_enc(path: Path, **kwargs) -> pd.DataFrame:
    last: Exception | None = None
    for enc in ENCODINGS:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError as e:
            last = e
            continue
    if last:
        raise last
    raise OSError(f"無法讀取：{path}")


def strip_id(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


def _default_paths() -> tuple[Path, Path]:
    try:
        import pipeline_config as pc  # noqa: PLC0415

        return pc.CSV_DIR, pc.ANALYSIS_OUTPUT
    except ImportError:
        p = Path(__file__).resolve().parent
        return p / "db1_backup_20260414_csv", p / "analysis_output"


def write_report_html(out_dir: Path) -> Path:
    """產生可離線瀏覽的 HTML（內嵌圖表、連結同資料夾 CSV）。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    png_name = "monthly_revenue_trend.png"
    csv_files = [
        "rfm_all_customers_with_sales.csv",
        "customers_no_trade_in_last_year.csv",
        "products_stale_over_one_year.csv",
    ]
    lines = [
        "<!DOCTYPE html>",
        '<html lang="zh-Hant">',
        "<head>",
        '<meta charset="utf-8"/>',
        "<title>商業分析報告</title>",
        "<style>",
        'body { font-family: "Microsoft JhengHei", "Microsoft YaHei", sans-serif; margin: 24px; }',
        "h1 { color: #333; }",
        ".section { margin-bottom: 32px; }",
        "img { max-width: 100%; height: auto; border: 1px solid #ddd; }",
        "ul { line-height: 1.8; }",
        ".meta { color: #666; font-size: 14px; }",
        "a { color: #06c; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>商業分析報告</h1>",
        f'<p class="meta">產生時間：{escape(now)}</p>',
        '<div class="section">',
        "<h2>1. 營收趨勢（按月彙總 tot）</h2>",
        f'<p><img src="{escape(png_name)}" alt="月營收折線圖"/></p>',
        "</div>",
        '<div class="section">',
        "<h2>2. 結果 CSV（與本檔同資料夾）</h2>",
        "<ul>",
    ]
    for name in csv_files:
        lines.append(f'<li><a href="{escape(name)}">{escape(name)}</a></li>')
    lines.extend(
        [
            "</ul>",
            "<p>將此 HTML 與同資料夾內 PNG、CSV 一併複製即可離線檢視。</p>",
            "</div>",
            "</body>",
            "</html>",
        ]
    )
    html_path = out_dir / "report.html"
    html_path.write_text("\n".join(lines), encoding="utf-8")
    return html_path


def analysis_1_monthly_revenue(sale: pd.DataFrame, out_dir: Path) -> None:
    df = sale.copy()
    df["sdate"] = pd.to_datetime(df["sdate"], errors="coerce")
    df = df.dropna(subset=["sdate"])
    df["tot"] = pd.to_numeric(df["tot"], errors="coerce").fillna(0.0)

    monthly = (
        df.set_index("sdate")
        .groupby(pd.Grouper(freq="MS"))["tot"]
        .sum()
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(monthly.index, monthly.values, marker="o", linewidth=2, markersize=4)
    ax.set_title("銷貨營收趨勢（按月彙總 tot）")
    ax.set_xlabel("月份")
    ax.set_ylabel("營收（tot 合計）")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    n = len(monthly)
    step = max(1, n // 24) if n > 24 else 1
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=step))
    plt.xticks(rotation=45, ha="right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    png = out_dir / "monthly_revenue_trend.png"
    fig.savefig(png, dpi=150)
    plt.close(fig)
    print(f"[1] 已輸出：{png}")


def analysis_2_rfm_inactive(
    sale: pd.DataFrame, cust: pd.DataFrame, out_dir: Path
) -> None:
    s = sale.copy()
    s["sdate"] = pd.to_datetime(s["sdate"], errors="coerce")
    s["cusno"] = strip_id(s["cusno"])
    s["tot"] = pd.to_numeric(s["tot"], errors="coerce").fillna(0.0)
    s = s.dropna(subset=["sdate"])

    ref_date = s["sdate"].max()
    cutoff = ref_date - pd.Timedelta(days=365)

    # 有銷貨紀錄的客戶：RFM
    g = s.groupby("cusno", as_index=False).agg(
        last_purchase=("sdate", "max"),
        frequency=("salno", "count"),
        monetary=("tot", "sum"),
    )
    g["recency_days"] = (ref_date - g["last_purchase"]).dt.days

    c = cust.copy()
    c["cusno"] = strip_id(c["cusno"])

    g = g.merge(
        c[["cusno", "cusnm"]],
        on="cusno",
        how="left",
    )

    rfm_path = out_dir / "rfm_all_customers_with_sales.csv"
    g.sort_values("monetary", ascending=False).to_csv(
        rfm_path, index=False, encoding="utf-8-sig"
    )
    print(f"[2a] RFM（有銷貨者）已輸出：{rfm_path}")

    # 最近一年內「沒有」交易：最後購買日 < cutoff，或從未出現在 sale
    inactive_from_sales = g[g["last_purchase"] < cutoff].copy()

    had_sale_cus = set(g["cusno"].unique())
    never_bought = c[~c["cusno"].isin(had_sale_cus)][["cusno", "cusnm"]].copy()
    never_bought["last_purchase"] = pd.NaT
    never_bought["frequency"] = 0
    never_bought["monetary"] = 0.0
    never_bought["recency_days"] = pd.NA

    inactive = pd.concat(
        [
            inactive_from_sales,
            never_bought,
        ],
        ignore_index=True,
    )
    inactive.insert(0, "參考截止日期", ref_date.strftime("%Y-%m-%d"))
    inactive.insert(1, "一年未交易判定起算", cutoff.strftime("%Y-%m-%d"))

    inactive_path = out_dir / "customers_no_trade_in_last_year.csv"
    inactive.sort_values(["cusno"]).to_csv(
        inactive_path, index=False, encoding="utf-8-sig"
    )
    print(
        f"[2b] 最近一年無交易客戶（含從未交易）：{len(inactive)} 筆 → {inactive_path}"
    )


def analysis_3_stale_products(prod: pd.DataFrame, sale: pd.DataFrame, out_dir: Path) -> None:
    """最後進出日 = max(lastin, lastout)；若皆空則不列入「超過一年未進出」。"""
    ref_date = pd.to_datetime(sale["sdate"], errors="coerce").max()

    p = prod.copy()
    p["lastin"] = pd.to_datetime(p["lastin"], errors="coerce")
    p["lastout"] = pd.to_datetime(p["lastout"], errors="coerce")
    p["qty"] = pd.to_numeric(p["qty"], errors="coerce")

    last_act = pd.concat([p["lastin"], p["lastout"]], axis=1).max(axis=1)
    p["last_activity"] = last_act

    # 至少有一筆進出日期，且距參考日「超過」365 天無進出（嚴格 > 365 天）
    has_date = p["lastin"].notna() | p["lastout"].notna()
    idle = (ref_date - p["last_activity"]) > pd.Timedelta(days=365)
    stale = p[has_date & idle].copy()

    out_cols = [
        "prdno",
        "prdnm",
        "qty",
        "lastin",
        "lastout",
        "last_activity",
        "pcost",
        "isstock",
    ]
    out_cols = [c for c in out_cols if c in stale.columns]
    stale = stale[out_cols].sort_values("last_activity")

    stale.insert(0, "參考截止日期", ref_date.strftime("%Y-%m-%d"))
    stale.insert(
        1,
        "一年以上未進出判定",
        "最後進出日距今超過 365 天（max(lastin,lastout)）",
    )

    stale_path = out_dir / "products_stale_over_one_year.csv"
    stale.to_csv(stale_path, index=False, encoding="utf-8-sig")
    print(f"[3] 超過一年無進出商品：{len(stale)} 筆 → {stale_path}")


def main() -> int:
    csv_def, out_def = _default_paths()
    parser = argparse.ArgumentParser(description="sale／cust／prod 商業分析")
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=csv_def,
        help=f"CSV 目錄（預設：pipeline_config 或 {csv_def.name}）",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=out_def,
        help="圖表、CSV、HTML 報告輸出目錄",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="不產生 report.html",
    )
    args = parser.parse_args()
    csv_dir: Path = args.csv_dir.resolve()
    out_dir: Path = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    sale_path = csv_dir / "sale.csv"
    cust_path = csv_dir / "cust.csv"
    prod_path = csv_dir / "prod.csv"
    for p in (sale_path, cust_path, prod_path):
        if not p.is_file():
            print(f"找不到：{p}", file=sys.stderr)
            return 1

    sale = read_csv_enc(sale_path)
    cust = read_csv_enc(cust_path)
    prod = read_csv_enc(prod_path)

    if "salno" not in sale.columns:
        print("sale.csv 需含 salno 欄位", file=sys.stderr)
        return 1

    analysis_1_monthly_revenue(sale, out_dir)
    analysis_2_rfm_inactive(sale, cust, out_dir)
    analysis_3_stale_products(prod, sale, out_dir)

    if not args.no_html:
        rep = write_report_html(out_dir)
        print(f"[報告] 瀏覽器開啟：{rep}")

    print("全部完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
