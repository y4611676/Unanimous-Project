"""
Step 2: Data aggregation
- Load the cleaned data from cleaned/
- Merge master tables with detail tables
- Build aggregation tables for analysis
- Write output to the aggregated/ folder
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
        folder = input("Enter the cleaned/ folder path (from step1):\n> ").strip()

    src = Path(folder)
    out = src.parent / "aggregated"
    out.mkdir(exist_ok=True)
    print(f"\n📂 source: {src}")
    print(f"📁 output: {out}\n{'='*50}")

    # Load base tables
    sale    = load(src, "sale.csv")
    sales1  = load(src, "sales1.csv")
    purc    = load(src, "purc.csv")
    purcs1  = load(src, "purcs1.csv")
    cust    = load(src, "cust.csv")
    fact    = load(src, "fact.csv")
    prod    = load(src, "prod.csv")
    stockqty= load(src, "stockqty.csv")

    # Derive date columns
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

    # ── 1. Sales master + detail merge ────────────────
    print("\n[1/7] merging sales master + detail...")
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
        print(f"   sale_full.csv: {len(sale_full)} rows")
    else:
        sale_full = pd.DataFrame()
        print("   ⚠️  missing sale or sales1")

    # ── 2. Monthly revenue ─────────────────────────────
    print("\n[2/7] monthly revenue aggregation...")
    if not sale.empty and "ym" in sale.columns:
        monthly_sale = sale.groupby("ym").agg(
            order_count=("salno","count"),
            sales=("tot","sum"),
        ).reset_index()

        if not sales1.empty and "rev" in sales1.columns and not sale_full.empty and "ym" in sale_full.columns:
            monthly_margin = sale_full.groupby("ym").agg(
                sales_detail=("rev","sum"),
                cost=("cost","sum"),
                gross_profit=("gross","sum"),
            ).reset_index()
            monthly_sale = monthly_sale.merge(monthly_margin, on="ym", how="left")
            monthly_sale["gross_margin"] = monthly_sale["gross_profit"] / monthly_sale["sales_detail"].replace(0, np.nan)

        if not purc.empty and "ym" in purc.columns:
            monthly_purc = purc.groupby("ym").agg(purchases=("tot","sum")).reset_index()
            monthly_sale = monthly_sale.merge(monthly_purc, on="ym", how="outer").sort_values("ym")
            monthly_sale["net"] = monthly_sale["sales"].fillna(0) - monthly_sale["purchases"].fillna(0)

        monthly_sale.to_csv(out / "monthly.csv", index=False, encoding="utf-8-sig")
        print(f"   monthly.csv: {len(monthly_sale)} month(s)")

    # ── 3. Customer aggregation ────────────────────────
    print("\n[3/7] customer aggregation...")
    if not sale.empty and "cusno" in sale.columns:
        cust_agg = sale.groupby("cusno").agg(
            orders=("salno","count"),
            sales=("tot","sum"),
            first_purchase=("sdate","min"),
            last_purchase=("sdate","max"),
        ).reset_index()
        cust_agg["tenure_months"] = ((cust_agg["last_purchase"] - cust_agg["first_purchase"]) / np.timedelta64(30,"D")).round(1)
        cust_agg["avg_order_value"] = cust_agg["sales"] / cust_agg["orders"]
        if not cust.empty:
            cust_agg = cust_agg.merge(cust[["cusno","cusnm"]].drop_duplicates("cusno"), on="cusno", how="left")
        total = cust_agg["sales"].sum()
        cust_agg["share"] = cust_agg["sales"] / total
        cust_agg["cum_share"] = cust_agg.sort_values("sales", ascending=False)["share"].cumsum().values
        cust_agg = cust_agg.sort_values("sales", ascending=False)
        cust_agg.to_csv(out / "cust_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   cust_agg.csv: {len(cust_agg)} customer(s)")

    # ── 4. Product aggregation ─────────────────────────
    print("\n[4/7] product aggregation...")
    if not sales1.empty and "prdno" in sales1.columns:
        prod_agg = sales1.groupby("prdno").agg(
            units_sold=("prqty","sum"),
            sales=("rev","sum"),
            cost=("cost","sum"),
            gross_profit=("gross","sum"),
            txn_count=("salno","count"),
        ).reset_index()
        prod_agg["gross_margin"] = prod_agg["gross_profit"] / prod_agg["sales"].replace(0, np.nan)
        if not prod.empty:
            prod_sub = prod[["prdno"] + [c for c in ["prdnm","classno","safeqty"] if c in prod.columns]].drop_duplicates("prdno")
            prod_agg = prod_agg.merge(prod_sub, on="prdno", how="left")
        prod_agg = prod_agg.sort_values("sales", ascending=False)
        prod_agg.to_csv(out / "prod_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   prod_agg.csv: {len(prod_agg)} product(s)")

    # ── 5. Supplier aggregation ────────────────────────
    print("\n[5/7] supplier aggregation...")
    if not purc.empty and "facno" in purc.columns:
        fact_agg = purc.groupby("facno").agg(
            po_count=("purno","count"),
            purchase_amt=("tot","sum"),
            first_po=("pdate","min"),
            last_po=("pdate","max"),
        ).reset_index()
        fact_agg["avg_po_value"] = fact_agg["purchase_amt"] / fact_agg["po_count"]
        if not fact.empty:
            fact_agg = fact_agg.merge(fact[["facno","facnm"]].drop_duplicates("facno"), on="facno", how="left")
        fact_agg = fact_agg.sort_values("purchase_amt", ascending=False)
        fact_agg.to_csv(out / "fact_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   fact_agg.csv: {len(fact_agg)} supplier(s)")

    # ── 6. Inventory aggregation ───────────────────────
    print("\n[6/7] inventory aggregation...")
    if not stockqty.empty:
        stock_agg = stockqty.copy()
        if not prod.empty:
            prod_sub = prod[["prdno"] + [c for c in ["prdnm","price","pcost","safeqty","lastin","lastout"] if c in prod.columns]].drop_duplicates("prdno")
            stock_agg = stock_agg.merge(prod_sub, on="prdno", how="left")
        LOW = 1  # low-stock threshold — tune as needed
        stock_agg["stock_status"] = stock_agg["qty"].apply(
            lambda q: "❌ out_of_stock" if q <= 0 else ("⚠️ low_stock" if q <= LOW else "✅ ok"))
        if "price" in stock_agg.columns:
            stock_agg["stock_value"] = pd.to_numeric(stock_agg["qty"], errors="coerce") * pd.to_numeric(stock_agg["price"], errors="coerce")
        stock_agg = stock_agg.sort_values("qty")
        stock_agg.to_csv(out / "stock_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   stock_agg.csv: {len(stock_agg)} item(s)")

    # ── 7. AR / AP aggregation ─────────────────────────
    print("\n[7/7] AR / AP aggregation...")
    for src_file, out_file, label in [
        ("rereces.csv", "ar_agg.csv", "AR"),
        ("repays.csv",  "ap_agg.csv", "AP"),
    ]:
        df = load(src, src_file)
        if not df.empty:
            df.to_csv(out / out_file, index=False, encoding="utf-8-sig")
            print(f"   {out_file} ({label}): {len(df)} rows")

    print(f"\n{'='*50}")
    print(f"✅ Aggregation complete. Data saved to: {out}")
    print(f"   Next: python step3_analyze.py \"{out}\"")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
