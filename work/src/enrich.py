# -*- coding: utf-8 -*-
"""將 sales1（銷貨明細）補上日期、客戶、商品分類等欄位；並計算毛利。

毛利定義：
    line_revenue = price * prqty
    line_cost    = pcost * prqty
    line_margin  = line_revenue - line_cost
    margin_rate  = line_margin / line_revenue（營收為 0 時回 NaN）
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .loaders import DataBundle


def enrich_sales_lines(data: DataBundle) -> pd.DataFrame:
    """回傳銷貨明細 + 日期 + 客戶 + 商品資訊 + 毛利欄位。"""
    s1 = data.sales1.copy()
    if s1.empty:
        return s1

    # sales1 本身沒有日期與客戶，從 sale 帶入
    head = data.sale[["salno", "sdate", "cusno", "busno"]].drop_duplicates("salno")
    s1 = s1.merge(head, on="salno", how="left")

    # 商品分類（optional）
    if not data.prod.empty and "classno" in data.prod.columns:
        s1 = s1.merge(
            data.prod[["prdno", "classno"]].drop_duplicates("prdno"),
            on="prdno",
            how="left",
        )

    # 客戶區域／類型（optional）
    if not data.cust.empty:
        cust_cols = [c for c in ("cusno", "cusnm", "area", "kind", "settle") if c in data.cust.columns]
        s1 = s1.merge(data.cust[cust_cols].drop_duplicates("cusno"), on="cusno", how="left")

    # 分類名稱
    if not data.classes.empty and "classno" in s1.columns:
        s1 = s1.merge(
            data.classes[["classno", "classnm"]].drop_duplicates("classno"),
            on="classno",
            how="left",
        )

    s1["prqty"] = pd.to_numeric(s1["prqty"], errors="coerce").fillna(0.0)
    s1["price"] = pd.to_numeric(s1["price"], errors="coerce").fillna(0.0)
    s1["pcost"] = pd.to_numeric(s1["pcost"], errors="coerce").fillna(0.0)

    s1["line_revenue"] = s1["price"] * s1["prqty"]
    s1["line_cost"] = s1["pcost"] * s1["prqty"]
    s1["line_margin"] = s1["line_revenue"] - s1["line_cost"]
    # 避免除以 0
    s1["margin_rate"] = np.where(
        s1["line_revenue"] != 0,
        s1["line_margin"] / s1["line_revenue"],
        np.nan,
    )
    s1["month"] = pd.to_datetime(s1["sdate"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    return s1


def enrich_purchase_lines(data: DataBundle) -> pd.DataFrame:
    """進貨明細 + 日期 + 廠商 + 商品分類（供應商分析用）。"""
    p1 = data.purcs1.copy()
    if p1.empty:
        return p1

    head = data.purc[["purno", "pdate", "facno"]].drop_duplicates("purno")
    p1 = p1.merge(head, on="purno", how="left")

    if not data.prod.empty:
        p1 = p1.merge(
            data.prod[["prdno", "classno"]].drop_duplicates("prdno"),
            on="prdno",
            how="left",
        )
    if not data.fact.empty:
        cols = [c for c in ("facno", "facnm", "area") if c in data.fact.columns]
        p1 = p1.merge(data.fact[cols].drop_duplicates("facno"), on="facno", how="left")

    p1["prqty"] = pd.to_numeric(p1["prqty"], errors="coerce").fillna(0.0)
    p1["price"] = pd.to_numeric(p1["price"], errors="coerce").fillna(0.0)
    p1["line_cost"] = p1["price"] * p1["prqty"]
    p1["month"] = pd.to_datetime(p1["pdate"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    return p1
