# -*- coding: utf-8 -*-
"""
【步驟 4】Streamlit 互動儀表板：營收、RFM／無交易客戶、滯銷品。

安裝：pip install streamlit pandas plotly
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

SALE_CSV = _CSV_DIR / "sale.csv"
RFM_CSV = _ANALYSIS / "rfm_all_customers_with_sales.csv"
INACTIVE_CSV = _ANALYSIS / "customers_no_trade_in_last_year.csv"
STALE_CSV = _ANALYSIS / "products_stale_over_one_year.csv"


def _inject_font_css() -> None:
    st.markdown(
        """
<style>
html, body, [class*="css"] {
  font-family: "Microsoft JhengHei", "Microsoft YaHei", sans-serif !important;
}
</style>
""",
        unsafe_allow_html=True,
    )


@st.cache_data
def load_sale() -> pd.DataFrame:
    df = pd.read_csv(SALE_CSV, encoding=ENCODING)
    df["sdate"] = pd.to_datetime(df["sdate"], errors="coerce")
    df["tot"] = pd.to_numeric(df["tot"], errors="coerce").fillna(0.0)
    return df.dropna(subset=["sdate"])


@st.cache_data
def load_rfm() -> pd.DataFrame:
    return pd.read_csv(RFM_CSV, encoding=ENCODING)


@st.cache_data
def load_inactive_full() -> pd.DataFrame:
    return pd.read_csv(INACTIVE_CSV, encoding=ENCODING)


@st.cache_data
def load_stale() -> pd.DataFrame:
    return pd.read_csv(STALE_CSV, encoding=ENCODING)


def main() -> None:
    st.set_page_config(page_title="商業儀表板", layout="wide")
    _inject_font_css()

    missing = [p for p in (SALE_CSV, RFM_CSV, INACTIVE_CSV, STALE_CSV) if not p.is_file()]
    if missing:
        st.error("找不到下列檔案，請先執行分析或檢查路徑：\n" + "\n".join(str(p) for p in missing))
        st.stop()

    sale = load_sale()
    rfm_raw = load_rfm()
    inactive_full = load_inactive_full()
    stale_raw = load_stale()

    dmin = sale["sdate"].min().date()
    dmax = sale["sdate"].max().date()

    with st.sidebar:
        st.header("日期篩選")
        st.caption("主要影響「營收概覽」之銷貨區間；RFM／滯銷為分析匯出之快照。")
        dr = st.date_input(
            "銷貨日期範圍",
            value=(dmin, dmax),
            min_value=dmin,
            max_value=dmax,
        )

    if isinstance(dr, tuple) and len(dr) == 2:
        start = pd.Timestamp(dr[0])
        end = pd.Timestamp(dr[1]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    else:
        start = pd.Timestamp(dr)
        end = pd.Timestamp(dr) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

    tab1, tab2, tab3 = st.tabs(["營收概覽", "客戶分析", "滯銷品清單"])

    # --- Tab 1 ---
    with tab1:
        sub = sale.loc[(sale["sdate"] >= start) & (sale["sdate"] <= end)].copy()
        sub["month"] = sub["sdate"].dt.to_period("M").dt.to_timestamp()
        monthly = sub.groupby("month", as_index=False)["tot"].sum()
        st.subheader("按月彙總營收（tot）")
        st.caption(f"區間內銷貨筆數：{len(sub):,}；合計 tot：{sub['tot'].sum():,.0f}")
        if monthly.empty:
            st.warning("此日期範圍內無資料。")
        else:
            fig = px.line(
                monthly,
                x="month",
                y="tot",
                markers=True,
                labels={"month": "月份", "tot": "營收合計"},
            )
            fig.update_traces(line=dict(width=2))
            fig.update_layout(hovermode="x unified", font=dict(family="Microsoft JhengHei"))
            st.plotly_chart(fig, use_container_width=True)

    # --- Tab 2 ---
    with tab2:
        rfm = rfm_raw.copy()
        rfm["cusno"] = rfm["cusno"].astype(str).str.strip()
        if "cusnm" in rfm.columns:
            rfm["cusnm"] = rfm["cusnm"].astype(str)
        inactive_set = set(
            inactive_full["cusno"].astype(str).str.strip().unique()
        )
        rfm["_inactive"] = rfm["cusno"].isin(inactive_set)

        q = st.text_input("搜尋客戶名稱（含部分字即可）", "")
        show = rfm
        if q.strip():
            show = rfm[rfm["cusnm"].str.contains(q.strip(), case=False, na=False)]

        show_idx = show.reset_index(drop=True)
        flags = show_idx["_inactive"].tolist()

        display_df = show_idx.drop(columns=["_inactive"])
        styler = display_df.style.apply(
            lambda row: [
                "background-color: #ffcccc; color: #660000"
                if flags[int(row.name)]
                else ""
                for _ in row
            ],
            axis=1,
        )

        st.subheader("RFM（有銷貨紀錄）")
        st.caption("紅底列：列於「最近一年無交易」名單之客戶（含仍出現在 RFM 者）。")
        st.dataframe(styler, use_container_width=True, height=480)

        rfm_cus = set(rfm["cusno"].unique())
        only_in_list = inactive_full[
            ~inactive_full["cusno"].astype(str).str.strip().isin(rfm_cus)
        ].copy()
        if not only_in_list.empty:
            with st.expander(f"僅在無交易名單、無 RFM 筆數之客戶（{len(only_in_list)} 人）"):
                cols = [c for c in only_in_list.columns if c in ("cusno", "cusnm", "last_purchase")]
                st.dataframe(only_in_list[cols], use_container_width=True)

    # --- Tab 3 ---
    with tab3:
        stale = stale_raw.copy()
        for c in ("lastin", "lastout", "last_activity"):
            if c in stale.columns:
                stale[c] = pd.to_datetime(stale[c], errors="coerce")
        stale["qty"] = pd.to_numeric(stale["qty"], errors="coerce")

        order = st.selectbox("庫存 qty 排序", ["由大到小", "由小到大"], index=0)
        asc = order == "由小到大"
        stale_sorted = stale.sort_values("qty", ascending=asc, na_position="last")

        show_cols = [
            c
            for c in (
                "prdno",
                "prdnm",
                "qty",
                "lastin",
                "lastout",
                "last_activity",
                "pcost",
                "isstock",
            )
            if c in stale_sorted.columns
        ]
        st.subheader("超過一年無進出之商品（分析快照）")
        st.caption("依 qty 排序；「最後進出」以 last_activity（max(lastin,lastout)）為準。")
        st.dataframe(
            stale_sorted[show_cols],
            use_container_width=True,
            height=520,
        )


if __name__ == "__main__":
    main()
