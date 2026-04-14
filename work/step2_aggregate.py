"""
步驟二：數據聚合
- 讀取 cleaned/ 的乾淨資料
- 合併主檔與明細
- 建立分析用的聚合表
- 輸出到 aggregated/ 資料夾
"""

import os, sys
import pandas as pd
import numpy as np
from pathlib import Path

def load(folder, fname):
    p = Path(folder) / fname
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, encoding="utf-8-sig", parse_dates=True)

def main():
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = input("請輸入 cleaned 資料夾路徑（step1 輸出的那個）：\n> ").strip()

    src = Path(folder)
    out = src.parent / "aggregated"
    out.mkdir(exist_ok=True)
    print(f"\n📂 來源：{src}")
    print(f"📁 輸出：{out}\n{'='*50}")

    # 讀取基礎資料
    sale    = load(src, "sale.csv")
    sales1  = load(src, "sales1.csv")
    purc    = load(src, "purc.csv")
    purcs1  = load(src, "purcs1.csv")
    cust    = load(src, "cust.csv")
    fact    = load(src, "fact.csv")
    prod    = load(src, "prod.csv")
    stockqty= load(src, "stockqty.csv")

    # 日期欄位
    if not sale.empty and "sdate" in sale.columns:
        sale["sdate"] = pd.to_datetime(sale["sdate"], errors="coerce")
        sale["year"]  = sale["sdate"].dt.year
        sale["month"] = sale["sdate"].dt.month
        sale["ym"]    = sale["sdate"].dt.to_period("M").astype(str)
        sale["yq"]    = sale["sdate"].dt.to_period("Q").astype(str)

    if not purc.empty and "pdate" in purc.columns:
        purc["pdate"] = pd.to_datetime(purc["pdate"], errors="coerce")
        purc["year"]  = purc["pdate"].dt.year
        purc["month"] = purc["pdate"].dt.month
        purc["ym"]    = purc["pdate"].dt.to_period("M").astype(str)

    # ── 1. 銷售主檔 + 明細合併 ────────────────────────
    print("\n[1/7] 銷售明細合併...")
    if not sale.empty and not sales1.empty:
        sale_cols = ["salno","sdate","year","month","ym","yq","cusno","busno","stockno","tot","apcost"]
        sale_sub  = sale[[c for c in sale_cols if c in sale.columns]]
        sale_full = sales1.merge(sale_sub, on="salno", how="left")
        if not cust.empty:
            sale_full = sale_full.merge(cust[["cusno","cusnm"]].drop_duplicates("cusno"),
                                        on="cusno", how="left")
        if not prod.empty:
            prod_sub = prod[["prdno"] + [c for c in ["prdnm","classno"] if c in prod.columns]].drop_duplicates("prdno")
            sale_full = sale_full.merge(prod_sub, on="prdno", how="left", suffixes=("","_prod"))
        sale_full.to_csv(out / "sale_full.csv", index=False, encoding="utf-8-sig")
        print(f"   sale_full.csv：{len(sale_full)} 筆")
    else:
        sale_full = pd.DataFrame()
        print("   ⚠️  缺少 sale 或 sales1")

    # ── 2. 月營收聚合 ─────────────────────────────────
    print("\n[2/7] 月營收聚合...")
    if not sale.empty and "ym" in sale.columns:
        monthly_sale = sale.groupby("ym").agg(
            銷售單數=("salno","count"),
            銷售額=("tot","sum"),
        ).reset_index()

        if not sales1.empty and "rev" in sales1.columns and not sale_full.empty and "ym" in sale_full.columns:
            monthly_margin = sale_full.groupby("ym").agg(
                銷售額_明細=("rev","sum"),
                成本=("cost","sum"),
                毛利=("gross","sum"),
            ).reset_index()
            monthly_sale = monthly_sale.merge(monthly_margin, on="ym", how="left")
            monthly_sale["毛利率"] = monthly_sale["毛利"] / monthly_sale["銷售額_明細"].replace(0, np.nan)

        if not purc.empty and "ym" in purc.columns:
            monthly_purc = purc.groupby("ym").agg(採購額=("tot","sum")).reset_index()
            monthly_sale = monthly_sale.merge(monthly_purc, on="ym", how="outer").sort_values("ym")
            monthly_sale["差額"] = monthly_sale["銷售額"].fillna(0) - monthly_sale["採購額"].fillna(0)

        monthly_sale.to_csv(out / "monthly.csv", index=False, encoding="utf-8-sig")
        print(f"   monthly.csv：{len(monthly_sale)} 個月")

    # ── 3. 客戶聚合 ───────────────────────────────────
    print("\n[3/7] 客戶聚合...")
    if not sale.empty and "cusno" in sale.columns:
        cust_agg = sale.groupby("cusno").agg(
            訂單數=("salno","count"),
            銷售額=("tot","sum"),
            最早交易=("sdate","min"),
            最近交易=("sdate","max"),
        ).reset_index()
        cust_agg["交易月數"] = ((cust_agg["最近交易"] - cust_agg["最早交易"]) / np.timedelta64(30,"D")).round(1)
        cust_agg["平均客單價"] = cust_agg["銷售額"] / cust_agg["訂單數"]
        if not cust.empty:
            cust_agg = cust_agg.merge(cust[["cusno","cusnm"]].drop_duplicates("cusno"), on="cusno", how="left")
        total = cust_agg["銷售額"].sum()
        cust_agg["佔比"] = cust_agg["銷售額"] / total
        cust_agg["累計佔比"] = cust_agg.sort_values("銷售額", ascending=False)["佔比"].cumsum().values
        cust_agg = cust_agg.sort_values("銷售額", ascending=False)
        cust_agg.to_csv(out / "cust_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   cust_agg.csv：{len(cust_agg)} 個客戶")

    # ── 4. 產品聚合 ───────────────────────────────────
    print("\n[4/7] 產品聚合...")
    if not sales1.empty and "prdno" in sales1.columns:
        prod_agg = sales1.groupby("prdno").agg(
            銷售數量=("prqty","sum"),
            銷售額=("rev","sum"),
            成本=("cost","sum"),
            毛利=("gross","sum"),
            交易次數=("salno","count"),
        ).reset_index()
        prod_agg["毛利率"] = prod_agg["毛利"] / prod_agg["銷售額"].replace(0, np.nan)
        if not prod.empty:
            prod_sub = prod[["prdno"] + [c for c in ["prdnm","classno","safeqty"] if c in prod.columns]].drop_duplicates("prdno")
            prod_agg = prod_agg.merge(prod_sub, on="prdno", how="left")
        prod_agg = prod_agg.sort_values("銷售額", ascending=False)
        prod_agg.to_csv(out / "prod_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   prod_agg.csv：{len(prod_agg)} 個產品")

    # ── 5. 供應商聚合 ─────────────────────────────────
    print("\n[5/7] 供應商聚合...")
    if not purc.empty and "facno" in purc.columns:
        fact_agg = purc.groupby("facno").agg(
            採購單數=("purno","count"),
            採購額=("tot","sum"),
            最早採購=("pdate","min"),
            最近採購=("pdate","max"),
        ).reset_index()
        fact_agg["平均採購單價"] = fact_agg["採購額"] / fact_agg["採購單數"]
        if not fact.empty:
            fact_agg = fact_agg.merge(fact[["facno","facnm"]].drop_duplicates("facno"), on="facno", how="left")
        fact_agg = fact_agg.sort_values("採購額", ascending=False)
        fact_agg.to_csv(out / "fact_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   fact_agg.csv：{len(fact_agg)} 個供應商")

    # ── 6. 庫存聚合 ───────────────────────────────────
    print("\n[6/7] 庫存聚合...")
    if not stockqty.empty:
        stock_agg = stockqty.copy()
        if not prod.empty:
            prod_sub = prod[["prdno"] + [c for c in ["prdnm","price","pcost","safeqty","lastin","lastout"] if c in prod.columns]].drop_duplicates("prdno")
            stock_agg = stock_agg.merge(prod_sub, on="prdno", how="left")
        LOW = 1  # 低庫存閾值，可自行調整
        stock_agg["庫存狀態"] = stock_agg["qty"].apply(
            lambda q: "❌ 零庫存" if q <= 0 else ("⚠️ 低庫存" if q <= LOW else "✅ 正常"))
        if "price" in stock_agg.columns:
            stock_agg["庫存價值"] = pd.to_numeric(stock_agg["qty"], errors="coerce") * pd.to_numeric(stock_agg["price"], errors="coerce")
        stock_agg = stock_agg.sort_values("qty")
        stock_agg.to_csv(out / "stock_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   stock_agg.csv：{len(stock_agg)} 個品項")

    # ── 7. 應收應付聚合 ───────────────────────────────
    print("\n[7/7] 應收應付聚合...")
    for src_file, out_file, label in [
        ("rereces.csv", "ar_agg.csv", "應收"),
        ("repays.csv",  "ap_agg.csv", "應付"),
    ]:
        df = load(src, src_file)
        if not df.empty:
            df.to_csv(out / out_file, index=False, encoding="utf-8-sig")
            print(f"   {out_file}（{label}）：{len(df)} 筆")

    print(f"\n{'='*50}")
    print(f"✅ 聚合完成！分析用資料已儲存到：{out}")
    print(f"   接下來執行：python step3_analyze.py \"{out}\"")
    input("\n按 Enter 結束...")

if __name__ == "__main__":
    main()
