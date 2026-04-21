"""
Step 2: Data Aggregation
- Read cleaned/ data from step1
- Join master and detail tables
- Build aggregated analysis tables
- Output to aggregated/ folder
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
        folder = input("Enter path to cleaned folder (step1 output):\n> ").strip()

    src = Path(folder)
    out = src.parent / "aggregated"
    out.mkdir(exist_ok=True)
    print(f"\nSource: {src}")
    print(f"Output: {out}\n{'='*50}")

    # Read base data
    sale    = load(src, "sale.csv")
    sales1  = load(src, "sales1.csv")
    purc    = load(src, "purc.csv")
    purcs1  = load(src, "purcs1.csv")
    cust    = load(src, "cust.csv")
    fact    = load(src, "fact.csv")
    prod    = load(src, "prod.csv")
    stockqty= load(src, "stockqty.csv")

    # ── Derive time-period columns for grouping ────────
    # ym = year-month ("2023-06") for monthly aggregation
    # yq = year-quarter ("2023Q2") for quarterly roll-ups
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

    # ── 1. Join sale master + detail ─────────────────
    # Answers: what was sold, to whom, at what margin? (header + line items + names)
    print("\n[1/7] Joining sale details...")
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
        print("   Warning: missing sale or sales1")

    # ── 2. Monthly revenue aggregation ──────────────
    # Answers: how is the business trending month-over-month? (revenue, cost, profit, cash flow)
    print("\n[2/7] Monthly revenue aggregation...")
    if not sale.empty and "ym" in sale.columns:
        monthly_sale = sale.groupby("ym").agg(
            sales_count=("salno","count"),
            sales=("tot","sum"),
        ).reset_index()

        # sales_detail comes from line-item rev (qty*price), while sales comes from
        # the header tot field — they can differ due to discounts/tax adjustments on the header.
        # We need both: header totals for cash flow, line-item totals for margin analysis.
        if not sales1.empty and "rev" in sales1.columns and not sale_full.empty and "ym" in sale_full.columns:
            monthly_margin = sale_full.groupby("ym").agg(
                sales_detail=("rev","sum"),
                cost=("cost","sum"),
                gross_profit=("gross","sum"),
            ).reset_index()
            monthly_sale = monthly_sale.merge(monthly_margin, on="ym", how="left")
            monthly_sale["gp_rate"] = monthly_sale["gross_profit"] / monthly_sale["sales_detail"].replace(0, np.nan)

        if not purc.empty and "ym" in purc.columns:
            monthly_purc = purc.groupby("ym").agg(purchases=("tot","sum")).reset_index()
            monthly_sale = monthly_sale.merge(monthly_purc, on="ym", how="outer").sort_values("ym")
            monthly_sale["balance"] = monthly_sale["sales"].fillna(0) - monthly_sale["purchases"].fillna(0)

        monthly_sale.to_csv(out / "monthly.csv", index=False, encoding="utf-8-sig")
        print(f"   monthly.csv: {len(monthly_sale)} months")

    # ── 3. Customer aggregation ─────────────────────
    # Answers: who are the most valuable customers? (lifetime value, frequency, tenure)
    print("\n[3/7] Customer aggregation...")
    if not sale.empty and "cusno" in sale.columns:
        cust_agg = sale.groupby("cusno").agg(
            order_count=("salno","count"),
            sales=("tot","sum"),
            first_transaction=("sdate","min"),
            last_transaction=("sdate","max"),
        ).reset_index()
        cust_agg["transaction_months"] = ((cust_agg["last_transaction"] - cust_agg["first_transaction"]) / np.timedelta64(30,"D")).round(1)
        cust_agg["avg_order_value"] = cust_agg["sales"] / cust_agg["order_count"]
        if not cust.empty:
            cust_agg = cust_agg.merge(cust[["cusno","cusnm"]].drop_duplicates("cusno"), on="cusno", how="left")
        # share + cumulative_share: Pareto-ready output so step3 can immediately
        # identify which customers make up the top 80% of revenue
        total = cust_agg["sales"].sum()
        cust_agg["share"] = cust_agg["sales"] / total
        cust_agg["cumulative_share"] = cust_agg.sort_values("sales", ascending=False)["share"].cumsum().values
        cust_agg = cust_agg.sort_values("sales", ascending=False)
        cust_agg.to_csv(out / "cust_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   cust_agg.csv: {len(cust_agg)} customers")

    # ── 4. Product aggregation ─────────────────────
    # Answers: which products drive revenue and margin? (sales, cost, GP per SKU)
    print("\n[4/7] Product aggregation...")
    if not sales1.empty and "prdno" in sales1.columns:
        prod_agg = sales1.groupby("prdno").agg(
            sales_qty=("prqty","sum"),
            sales=("rev","sum"),
            cost=("cost","sum"),
            gross_profit=("gross","sum"),
            transaction_count=("salno","count"),
        ).reset_index()
        prod_agg["gp_rate"] = prod_agg["gross_profit"] / prod_agg["sales"].replace(0, np.nan)
        if not prod.empty:
            prod_sub = prod[["prdno"] + [c for c in ["prdnm","classno","safeqty"] if c in prod.columns]].drop_duplicates("prdno")
            prod_agg = prod_agg.merge(prod_sub, on="prdno", how="left")
        prod_agg = prod_agg.sort_values("sales", ascending=False)
        prod_agg.to_csv(out / "prod_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   prod_agg.csv: {len(prod_agg)} products")

    # ── 5. Supplier aggregation ────────────────────
    # Answers: which suppliers do we depend on most? (spend concentration, frequency)
    print("\n[5/7] Supplier aggregation...")
    if not purc.empty and "facno" in purc.columns:
        fact_agg = purc.groupby("facno").agg(
            purchase_count=("purno","count"),
            purchases=("tot","sum"),
            first_purchase=("pdate","min"),
            last_purchase=("pdate","max"),
        ).reset_index()
        fact_agg["avg_purchase_price"] = fact_agg["purchases"] / fact_agg["purchase_count"]
        if not fact.empty:
            fact_agg = fact_agg.merge(fact[["facno","facnm"]].drop_duplicates("facno"), on="facno", how="left")
        fact_agg = fact_agg.sort_values("purchases", ascending=False)
        fact_agg.to_csv(out / "fact_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   fact_agg.csv: {len(fact_agg)} suppliers")

    # ── 6. Inventory aggregation ────────────────────
    # Answers: what needs restocking? (current qty vs threshold, stock value at risk)
    print("\n[6/7] Inventory aggregation...")
    if not stockqty.empty:
        stock_agg = stockqty.copy()
        if not prod.empty:
            prod_sub = prod[["prdno"] + [c for c in ["prdnm","price","pcost","safeqty","lastin","lastout"] if c in prod.columns]].drop_duplicates("prdno")
            stock_agg = stock_agg.merge(prod_sub, on="prdno", how="left")
        # Threshold logic: qty<=0 is out-of-stock (urgent), qty<=LOW is dangerously
        # low and needs reorder, everything else is normal. LOW=1 is conservative;
        # ideally this would use each product's safeqty instead.
        LOW = 1  # Low stock threshold
        stock_agg["stock_status"] = stock_agg["qty"].apply(
            lambda q: "零庫存" if q <= 0 else ("低庫存" if q <= LOW else "正常"))
        if "price" in stock_agg.columns:
            stock_agg["stock_value"] = pd.to_numeric(stock_agg["qty"], errors="coerce") * pd.to_numeric(stock_agg["price"], errors="coerce")
        stock_agg = stock_agg.sort_values("qty")
        stock_agg.to_csv(out / "stock_agg.csv", index=False, encoding="utf-8-sig")
        print(f"   stock_agg.csv: {len(stock_agg)} items")

    # ── 7. AR/AP aggregation ────────────────────────
    # Answers: what is outstanding? (receivables = money owed to us, payables = money we owe)
    print("\n[7/7] AR/AP aggregation...")
    for src_file, out_file, label in [
        ("rereces.csv", "ar_agg.csv", "AR"),
        ("repays.csv",  "ap_agg.csv", "AP"),
    ]:
        df = load(src, src_file)
        if not df.empty:
            df.to_csv(out / out_file, index=False, encoding="utf-8-sig")
            print(f"   {out_file} ({label}): {len(df)} rows")

    print(f"\n{'='*50}")
    print(f"Aggregation complete. Output saved to: {out}")
    print(f"   Next step: python step3_analyze.py \"{out}\"")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
