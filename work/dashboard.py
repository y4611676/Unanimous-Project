# -*- coding: utf-8 -*-
"""【步驟 4】Streamlit 互動儀表板（綜合版）。

依賴於 analyze_business.py 已先產出 analysis_output/*.csv。
若缺檔會顯示提示但不中斷，讓其他分頁仍可使用。

執行：streamlit run dashboard.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ENCODING = "utf-8-sig"

try:
    import pipeline_config as pc

    _BASE = pc.BASE
    _CSV_DIR = pc.CSV_DIR
    _ANALYSIS = pc.ANALYSIS_OUTPUT
except ImportError:
    _BASE = Path(__file__).resolve().parent
    _CSV_DIR = _BASE / "db1_backup_20260414_csv"
    _ANALYSIS = _BASE / "analysis_output"


# --- 統一 font CSS ---
def _inject_font_css() -> None:
    st.markdown(
        """
<style>
html, body, [class*="css"] {
  font-family: "Microsoft JhengHei", "Microsoft YaHei", "Noto Sans CJK TC", sans-serif !important;
}
.kpi-row { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px; }
</style>
""",
        unsafe_allow_html=True,
    )


@st.cache_data
def _load(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding=ENCODING)
    except Exception:
        return pd.DataFrame()


# 個別 loader（cache_data 要求函式簽名穩定）
@st.cache_data
def load_sale() -> pd.DataFrame:
    p = _CSV_DIR / "sale.csv"
    if not p.is_file():
        return pd.DataFrame()
    for enc in ("big5", "cp950", "utf-8-sig", "utf-8"):
        try:
            df = pd.read_csv(p, encoding=enc)
            df["sdate"] = pd.to_datetime(df["sdate"], errors="coerce")
            df["tot"] = pd.to_numeric(df["tot"], errors="coerce").fillna(0.0)
            return df.dropna(subset=["sdate"])
        except UnicodeDecodeError:
            continue
    return pd.DataFrame()


def _info_card(label: str, value: str) -> None:
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#f0f5fc,#d9e5f4);"
        f"border-left:4px solid #2b4e7f;padding:12px 14px;border-radius:6px;'>"
        f"<div style='font-size:12px;color:#555'>{label}</div>"
        f"<div style='font-size:22px;font-weight:700;color:#1f3a5f'>{value}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _df_or_empty(df: pd.DataFrame, msg: str = "（尚未產生；請先執行 analyze_business.py）") -> bool:
    if df.empty:
        st.info(msg)
        return True
    return False


def main() -> None:
    st.set_page_config(page_title="商業儀表板", layout="wide")
    _inject_font_css()
    st.title("商業分析儀表板")
    st.caption(f"資料目錄：`{_CSV_DIR.name}` ｜ 分析輸出：`{_ANALYSIS.name}`")

    # 全域載入
    sale = load_sale()
    monthly_margin = _load(_ANALYSIS / "monthly_margin.csv")
    abc = _load(_ANALYSIS / "abc_analysis.csv")
    stale = _load(_ANALYSIS / "products_stale_over_one_year.csv")
    safety = _load(_ANALYSIS / "safety_stock_breach.csv")
    oos = _load(_ANALYSIS / "out_of_stock_with_recent_sales.csv")
    class_turnover = _load(_ANALYSIS / "class_turnover.csv")
    rfm = _load(_ANALYSIS / "rfm_scored.csv")
    seg = _load(_ANALYSIS / "rfm_segment_summary.csv")
    inactive = _load(_ANALYSIS / "customers_no_trade_in_last_year.csv")
    new_vs_repeat = _load(_ANALYSIS / "new_vs_repeat.csv")
    area = _load(_ANALYSIS / "area_revenue.csv")
    prod_margin = _load(_ANALYSIS / "product_margin.csv")
    neg_margin = _load(_ANALYSIS / "product_negative_margin.csv")
    cust_margin = _load(_ANALYSIS / "customer_margin.csv")
    basket = _load(_ANALYSIS / "basket_pairs.csv")
    supplier = _load(_ANALYSIS / "supplier_ranking.csv")
    overstock = _load(_ANALYSIS / "overstocked.csv")
    under = _load(_ANALYSIS / "underreplenished.csv")
    ar_aging = _load(_ANALYSIS / "ar_aging.csv")
    bad_debt = _load(_ANALYSIS / "bad_debt_risk.csv")
    cashflow = _load(_ANALYSIS / "monthly_cashflow.csv")
    salesrep = _load(_ANALYSIS / "salesrep_ranking.csv")
    salesrep_mix = _load(_ANALYSIS / "salesrep_customer_mix.csv")
    anomalies = _load(_ANALYSIS / "revenue_anomalies.csv")

    # 側欄：日期篩選（只影響營收與毛利的區間檢視）
    if not sale.empty:
        dmin, dmax = sale["sdate"].min().date(), sale["sdate"].max().date()
        with st.sidebar:
            st.header("日期篩選")
            st.caption("主要影響『營收 / 毛利區間檢視』分頁")
            dr = st.date_input("日期範圍", value=(dmin, dmax), min_value=dmin, max_value=dmax)
            if isinstance(dr, tuple) and len(dr) == 2:
                start = pd.Timestamp(dr[0])
                end = pd.Timestamp(dr[1]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
            else:
                start = end = pd.Timestamp(dr)
    else:
        start = end = None

    tabs = st.tabs([
        "📊 總覽",
        "💰 營收與毛利",
        "📦 商品與庫存",
        "👥 客戶分析",
        "🛒 購物籃",
        "🏭 供應商",
        "💵 現金流 / AR",
        "🧑‍💼 業務員",
        "🔮 預測",
    ])

    # ========== 總覽 ==========
    with tabs[0]:
        c = st.columns(4)
        def _kpi(col, label, value):
            with col: _info_card(label, value)
        total_rev = f"{sale['tot'].sum():,.0f}" if not sale.empty else "-"
        _kpi(c[0], "累計營收", total_rev)
        if not monthly_margin.empty:
            _kpi(c[1], "累計毛利", f"{monthly_margin['margin'].sum():,.0f}")
            rev_sum = monthly_margin["revenue"].sum()
            _kpi(c[2], "整體毛利率", f"{(monthly_margin['margin'].sum()/rev_sum*100):.1f}%" if rev_sum else "-")
        if not stale.empty:
            _kpi(c[3], "呆料金額", f"{stale['dead_value'].sum():,.0f}")
        st.markdown("---")
        st.subheader("章節捷徑")
        st.markdown(
            "- **營收與毛利**：月趨勢、毛利率、區間檢視\n"
            "- **商品與庫存**：ABC、呆料、週轉、安全庫存、疑似缺貨\n"
            "- **客戶分析**：RFM 分群、Pareto、地區、新客 vs 回頭客\n"
            "- **購物籃**：商品對關聯度\n"
            "- **供應商**：採購集中度、進多賣少\n"
            "- **現金流 / AR**：帳齡、壞帳名單、月現金流\n"
            "- **業務員**：業績、毛利、客戶集中度\n"
            "- **預測**：下月營收、異常月份"
        )

    # ========== 營收與毛利 ==========
    with tabs[1]:
        st.subheader("月營收與毛利")
        if not monthly_margin.empty:
            mm = monthly_margin.copy()
            mm["month"] = pd.to_datetime(mm["month"])
            fig = px.bar(mm, x="month", y=["revenue", "margin"], barmode="group",
                         labels={"value": "金額", "month": "月份", "variable": "指標"},
                         title="月營收 vs 毛利")
            st.plotly_chart(fig, use_container_width=True)
            fig2 = px.line(mm, x="month", y="margin_rate", markers=True,
                           labels={"margin_rate": "毛利率", "month": "月份"},
                           title="月毛利率")
            fig2.update_yaxes(tickformat=".1%")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            _df_or_empty(monthly_margin)

        st.subheader("區間銷貨")
        if not sale.empty and start is not None:
            sub = sale[(sale["sdate"] >= start) & (sale["sdate"] <= end)].copy()
            sub["month"] = sub["sdate"].dt.to_period("M").dt.to_timestamp()
            mbl = sub.groupby("month", as_index=False)["tot"].sum()
            st.caption(f"區間筆數：{len(sub):,}；合計：{sub['tot'].sum():,.0f}")
            if not mbl.empty:
                st.plotly_chart(px.line(mbl, x="month", y="tot", markers=True), use_container_width=True)

        st.subheader("毛利 Top 20 商品")
        if not _df_or_empty(prod_margin):
            st.dataframe(prod_margin.head(20), use_container_width=True, hide_index=True)
        st.subheader("負毛利商品")
        if not _df_or_empty(neg_margin, "目前沒有負毛利商品。"):
            st.dataframe(neg_margin, use_container_width=True, hide_index=True)
        st.subheader("毛利 Top 20 客戶")
        if not _df_or_empty(cust_margin):
            st.dataframe(cust_margin.head(20), use_container_width=True, hide_index=True)

    # ========== 商品與庫存 ==========
    with tabs[2]:
        st.subheader("ABC 分析（Pareto）")
        if not _df_or_empty(abc):
            a = abc.copy().reset_index(drop=True)
            a["rank"] = a.index + 1
            fig = px.bar(a.head(300), x="rank", y="revenue", color="abc_class",
                         category_orders={"abc_class": ["A", "B", "C"]},
                         title="商品營收 Pareto（前 300）")
            st.plotly_chart(fig, use_container_width=True)
            counts = a["abc_class"].value_counts().reindex(["A", "B", "C"]).fillna(0).astype(int)
            c = st.columns(3)
            for col, k in zip(c, ["A", "B", "C"]):
                with col:
                    _info_card(f"{k} 類品項數", f"{int(counts.get(k, 0)):,}")
            st.dataframe(a, use_container_width=True, hide_index=True, height=380)

        st.subheader("呆料清單（依金額）")
        if not _df_or_empty(stale):
            c = st.columns(2)
            _info_card("呆料金額合計", f"{stale['dead_value'].sum():,.0f}")
            _info_card("呆料品項數", f"{len(stale):,}")
            st.dataframe(stale, use_container_width=True, hide_index=True, height=380)

        st.subheader("分類庫存週轉率")
        if not _df_or_empty(class_turnover):
            st.dataframe(class_turnover, use_container_width=True, hide_index=True)

        st.subheader("安全庫存告警")
        if not _df_or_empty(safety, "目前沒有安全庫存破線品項。"):
            st.dataframe(safety, use_container_width=True, hide_index=True)

        st.subheader("疑似缺貨（isstock=Y 但 qty=0 且近一年有銷）")
        if not _df_or_empty(oos, "目前沒有偵測到疑似缺貨。"):
            st.dataframe(oos, use_container_width=True, hide_index=True)

    # ========== 客戶分析 ==========
    with tabs[3]:
        st.subheader("RFM 分群摘要")
        if not _df_or_empty(seg):
            fig = px.bar(seg, x="segment", y="revenue", color="segment",
                         title="各 RFM 分群的營收貢獻")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(seg, use_container_width=True, hide_index=True)

        st.subheader("RFM 明細（搜尋客戶名稱）")
        if not _df_or_empty(rfm):
            q = st.text_input("搜尋客戶名稱（含部分字即可）", "")
            show = rfm
            if q.strip() and "cusnm" in rfm.columns:
                show = rfm[rfm["cusnm"].astype(str).str.contains(q.strip(), case=False, na=False)]
            show = show.reset_index(drop=True).copy()
            inactive_set = set(inactive["cusno"].astype(str).str.strip()) if not inactive.empty else set()
            show["_inactive"] = show["cusno"].astype(str).str.strip().isin(inactive_set)
            flags = show["_inactive"].tolist()
            display_df = show.drop(columns=["_inactive"])
            styler = display_df.style.apply(
                lambda row: ["background-color: #ffe2e2" if flags[int(row.name)] else "" for _ in row],
                axis=1,
            )
            st.dataframe(styler, use_container_width=True, height=480)
            st.caption("紅底 = 近一年無交易")

        st.subheader("新客 vs 回頭客 月營收")
        if not _df_or_empty(new_vs_repeat):
            nvr = new_vs_repeat.copy()
            nvr["month"] = pd.to_datetime(nvr["month"])
            fig2 = px.area(nvr, x="month", y=["new_rev", "repeat_rev"],
                           labels={"value": "營收", "variable": "類型"})
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("地區營收")
        if not _df_or_empty(area, "沒有地區（area）資料。"):
            st.plotly_chart(px.bar(area.head(20), x="area", y="revenue"), use_container_width=True)
            st.dataframe(area, use_container_width=True, hide_index=True)

    # ========== 購物籃 ==========
    with tabs[4]:
        st.subheader("關聯度最高商品對（lift 排序）")
        if not _df_or_empty(basket):
            min_lift = st.slider("最低 lift", 1.0, 10.0, 1.5, 0.5)
            min_count = st.slider("最低共現次數", 1, 50, 3, 1)
            f = basket[(basket["lift"] >= min_lift) & (basket["co_occur"] >= min_count)]
            st.caption(f"符合條件：{len(f):,} 對")
            st.dataframe(f, use_container_width=True, hide_index=True, height=520)

    # ========== 供應商 ==========
    with tabs[5]:
        st.subheader("供應商採購排行")
        if not _df_or_empty(supplier):
            fig = px.bar(supplier.head(20), x="facno", y="purchase",
                         hover_data=["facnm"] if "facnm" in supplier.columns else None,
                         title="Top 20 供應商採購金額")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(supplier, use_container_width=True, hide_index=True, height=400)

        st.subheader("進多賣少")
        if not _df_or_empty(overstock, "沒有進多賣少的品項。"):
            st.dataframe(overstock, use_container_width=True, hide_index=True)

        st.subheader("賣多沒補")
        if not _df_or_empty(under, "沒有賣多沒補的品項。"):
            st.dataframe(under, use_container_width=True, hide_index=True)

    # ========== 現金流 / AR ==========
    with tabs[6]:
        st.subheader("應收帳齡分布")
        if not _df_or_empty(ar_aging):
            st.plotly_chart(px.bar(ar_aging, x="帳齡", y="未收金額"), use_container_width=True)
            st.dataframe(ar_aging, use_container_width=True, hide_index=True)

        st.subheader("壞帳風險名單")
        if not _df_or_empty(bad_debt):
            st.caption(f"共 {len(bad_debt):,} 位客戶；未收合計 {bad_debt['outstanding'].sum():,.0f}")
            st.dataframe(bad_debt, use_container_width=True, hide_index=True, height=420)

        st.subheader("月現金流（收 − 付）")
        if not _df_or_empty(cashflow):
            cf = cashflow.copy()
            cf["month"] = pd.to_datetime(cf["month"])
            fig = px.bar(cf, x="month", y=["in", "out"], barmode="group",
                         labels={"value": "金額", "variable": "類型"})
            st.plotly_chart(fig, use_container_width=True)
            st.plotly_chart(px.line(cf, x="month", y="net", markers=True,
                                    title="淨現金流"), use_container_width=True)

    # ========== 業務員 ==========
    with tabs[7]:
        st.subheader("業務員業績")
        if not _df_or_empty(salesrep):
            fig = px.bar(salesrep.head(15), x="busno", y=["revenue", "margin"], barmode="group")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(salesrep, use_container_width=True, hide_index=True)
        st.subheader("客戶集中度（單一客戶佔業務員營收比例）")
        if not _df_or_empty(salesrep_mix):
            st.dataframe(salesrep_mix, use_container_width=True, hide_index=True)

    # ========== 預測 ==========
    with tabs[8]:
        st.subheader("異常月份（|z| ≥ 2）")
        if not _df_or_empty(anomalies):
            a = anomalies.copy()
            a["month"] = pd.to_datetime(a["month"])
            fig = px.line(a, x="month", y="revenue", markers=True)
            flagged = a[a["flag"].fillna("") != ""]
            if not flagged.empty:
                fig.add_scatter(x=flagged["month"], y=flagged["revenue"], mode="markers",
                                marker=dict(size=14, color="red"), name="異常")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(flagged, use_container_width=True, hide_index=True)
        st.info("詳細預測圖表與季節性，請見 `analysis_output/report.html` 的「預測」章節。")


if __name__ == "__main__":
    main()
