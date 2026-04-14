# -*- coding: utf-8 -*-
"""集中載入所有核心 CSV，並做基本型別轉換。

取出後統一放進 dict[str, DataFrame]，下游分析模組用 `data["sale"]` 取用。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .io_utils import read_csv_enc, strip_id


@dataclass
class DataBundle:
    """所有核心表格與它們的衍生欄位。"""

    sale: pd.DataFrame          # 銷貨單頭
    sales1: pd.DataFrame        # 銷貨明細（毛利分析主要來源）
    purc: pd.DataFrame          # 進貨單頭
    purcs1: pd.DataFrame        # 進貨明細
    cash: pd.DataFrame          # 現金銷貨單頭
    cashs1: pd.DataFrame        # 現金銷貨明細
    cust: pd.DataFrame          # 客戶主檔
    prod: pd.DataFrame          # 商品主檔
    fact: pd.DataFrame          # 廠商主檔
    classes: pd.DataFrame       # 商品分類
    stockqty: pd.DataFrame      # 分倉庫存
    rerece: pd.DataFrame        # 收款單頭
    rereces: pd.DataFrame       # 收款明細
    repay: pd.DataFrame         # 付款單頭
    repays: pd.DataFrame        # 付款明細
    ref_date: pd.Timestamp      # 參考截止日（sale 最大日）

    def as_dict(self) -> dict[str, pd.DataFrame]:
        return {
            "sale": self.sale,
            "sales1": self.sales1,
            "purc": self.purc,
            "purcs1": self.purcs1,
            "cash": self.cash,
            "cashs1": self.cashs1,
            "cust": self.cust,
            "prod": self.prod,
            "fact": self.fact,
            "class": self.classes,
            "stockqty": self.stockqty,
            "rerece": self.rerece,
            "rereces": self.rereces,
            "repay": self.repay,
            "repays": self.repays,
        }


def _to_dt(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _to_num(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _read(csv_dir: Path, name: str) -> pd.DataFrame:
    path = csv_dir / f"{name}.csv"
    if not path.is_file():
        return pd.DataFrame()
    df = read_csv_enc(path)
    # pandas 可能把 BOM 留在第一欄欄名
    df.columns = [c.lstrip("\ufeff").strip() for c in df.columns]
    return df


def load_all(csv_dir: Path) -> DataBundle:
    """載入並標準化所有核心表格。缺表回傳空 DataFrame，不中斷。"""
    sale = _read(csv_dir, "sale")
    sales1 = _read(csv_dir, "sales1")
    purc = _read(csv_dir, "purc")
    purcs1 = _read(csv_dir, "purcs1")
    cash = _read(csv_dir, "cash")
    cashs1 = _read(csv_dir, "cashs1")
    cust = _read(csv_dir, "cust")
    prod = _read(csv_dir, "prod")
    fact = _read(csv_dir, "fact")
    classes = _read(csv_dir, "class")
    stockqty = _read(csv_dir, "stockqty")
    rerece = _read(csv_dir, "rerece")
    rereces = _read(csv_dir, "rereces")
    repay = _read(csv_dir, "repay")
    repays = _read(csv_dir, "repays")

    # 日期
    _to_dt(sale, "sdate")
    _to_dt(purc, "pdate")
    _to_dt(cash, "cdate")
    _to_dt(prod, "lastin")
    _to_dt(prod, "lastout")
    _to_dt(rerece, "rdate")
    _to_dt(repay, "rdate")

    # 數字
    _to_num(sale, ["tot", "ttot", "tprice", "smoney", "price", "apcost"])
    _to_num(sales1, ["prqty", "price", "pcost", "indexs"])
    _to_num(purc, ["tot", "ttot", "smoney", "Tprice", "price"])
    _to_num(purcs1, ["prqty", "price", "indexs"])
    _to_num(cash, ["tot", "tot1", "apcost", "rtax", "mtax", "tot2", "smoney"])
    _to_num(cashs1, ["prqty", "price", "pcost", "price2"])
    _to_num(prod, ["qty", "price", "pcost", "safeqty"])
    _to_num(cust, ["settle", "cusamt", "sday", "pday"])
    _to_num(stockqty, ["qty"])
    _to_num(rereces, ["rlamt3", "rlamt4", "rdisc"])
    _to_num(repays, ["rlamt3", "rlamt4", "rdisc"])

    # ID 欄位去除尾隨空白
    for df, col in (
        (sale, "cusno"), (sale, "busno"), (sale, "salno"), (sale, "stockno"),
        (sales1, "salno"), (sales1, "prdno"),
        (purc, "facno"), (purc, "purno"), (purc, "stockno"),
        (purcs1, "purno"), (purcs1, "prdno"),
        (cash, "casno"), (cash, "cusno"), (cash, "busno"),
        (cashs1, "casno"), (cashs1, "prdno"),
        (cust, "cusno"), (cust, "busno"), (cust, "area"), (cust, "kind"),
        (prod, "prdno"), (prod, "classno"),
        (fact, "facno"), (fact, "area"),
        (classes, "classno"),
        (stockqty, "stockno"), (stockqty, "prdno"),
        (rerece, "cusno"), (rerece, "relno"),
        (rereces, "relno"),
        (repay, "facno"), (repay, "relno"),
        (repays, "relno"),
    ):
        if col in df.columns:
            df[col] = strip_id(df[col])

    ref_date = sale["sdate"].max() if "sdate" in sale.columns and not sale.empty else pd.Timestamp.today()

    return DataBundle(
        sale=sale, sales1=sales1, purc=purc, purcs1=purcs1,
        cash=cash, cashs1=cashs1, cust=cust, prod=prod, fact=fact,
        classes=classes, stockqty=stockqty,
        rerece=rerece, rereces=rereces, repay=repay, repays=repays,
        ref_date=ref_date,
    )
