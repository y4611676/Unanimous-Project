"""
Step 1: Data cleaning
- Load all key CSVs
- Strip whitespace, unify encoding
- Normalise date formats
- Handle missing values and outliers
- Write cleaned CSVs to the cleaned/ folder
"""

import os, sys
import pandas as pd
import numpy as np
from pathlib import Path

def load(folder, fname):
    p = Path(folder) / fname
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, encoding="utf-8-sig", on_bad_lines="skip")
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
    return df

def clean_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

def clean_date(df, col):
    if col not in df.columns:
        return df
    df[col] = pd.to_datetime(df[col].astype(str).str[:10], errors="coerce")
    return df

def report(name, df_before, df_after, issues):
    print(f"\n[{name}]")
    print(f"  rows in: {len(df_before)}  rows out: {len(df_after)}")
    for msg in issues:
        print(f"  ⚠️  {msg}")

def main():
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = input("Enter your CSV folder path:\n> ").strip()

    out = Path(folder) / "cleaned"
    out.mkdir(exist_ok=True)
    print(f"\n📂 source: {folder}")
    print(f"📁 output: {out}\n{'='*50}")

    # ── sale.csv ──────────────────────────────────────
    df = load(folder, "sale.csv")
    issues = []
    if not df.empty:
        before = len(df)
        df = clean_date(df, "sdate")
        df = clean_numeric(df, ["tot","ttot","price","apcost","smoney","tprice"])
        null_dates = df["sdate"].isna().sum()
        if null_dates: issues.append(f"{null_dates} invalid dates (kept as NaT)")
        neg = (df["tot"] < 0).sum()
        if neg: issues.append(f"tot: {neg} negative value(s)")
        dup = df.duplicated(subset=["salno"]).sum()
        if dup: issues.append(f"{dup} duplicate salno (keeping first)")
        df = df.drop_duplicates(subset=["salno"], keep="first")
        report("sale.csv", pd.DataFrame(index=range(before)), df, issues)
        df.to_csv(out / "sale.csv", index=False, encoding="utf-8-sig")

    # ── sales1.csv ────────────────────────────────────
    df = load(folder, "sales1.csv")
    issues = []
    if not df.empty:
        before = len(df)
        df = clean_numeric(df, ["prqty","price","pcost","indexs","rept2index"])
        df["rev"] = df["price"] * df["prqty"]
        df["cost"] = df["pcost"] * df["prqty"]
        df["gross"] = df["rev"] - df["cost"]
        neg_margin = (df["gross"] < 0).sum()
        if neg_margin: issues.append(f"{neg_margin} rows with negative gross margin (price < cost)")
        zero_price = (df["price"] == 0).sum()
        if zero_price: issues.append(f"rows with price = 0: {zero_price}")
        report("sales1.csv", pd.DataFrame(index=range(before)), df, issues)
        df.to_csv(out / "sales1.csv", index=False, encoding="utf-8-sig")

    # ── purc.csv ──────────────────────────────────────
    df = load(folder, "purc.csv")
    issues = []
    if not df.empty:
        before = len(df)
        df = clean_date(df, "pdate")
        df = clean_numeric(df, ["tot","ttot","price","smoney","Tprice"])
        dup = df.duplicated(subset=["purno"]).sum()
        if dup: issues.append(f"{dup} duplicate purno")
        df = df.drop_duplicates(subset=["purno"], keep="first")
        report("purc.csv", pd.DataFrame(index=range(before)), df, issues)
        df.to_csv(out / "purc.csv", index=False, encoding="utf-8-sig")

    # ── purcs1.csv ────────────────────────────────────
    df = load(folder, "purcs1.csv")
    issues = []
    if not df.empty:
        df = clean_numeric(df, ["prqty","price","indexs","rept4index"])
        df["purc_amt"] = df["price"] * df["prqty"]
        report("purcs1.csv", df, df, issues)
        df.to_csv(out / "purcs1.csv", index=False, encoding="utf-8-sig")

    # ── cust.csv ──────────────────────────────────────
    df = load(folder, "cust.csv")
    issues = []
    if not df.empty:
        before = len(df)
        dup = df.duplicated(subset=["cusno"]).sum()
        if dup: issues.append(f"{dup} duplicate cusno")
        df = df.drop_duplicates(subset=["cusno"], keep="first")
        missing_name = df["cusnm"].isna().sum() if "cusnm" in df.columns else 0
        if missing_name: issues.append(f"{missing_name} customers with missing name")
        report("cust.csv", pd.DataFrame(index=range(before)), df, issues)
        df.to_csv(out / "cust.csv", index=False, encoding="utf-8-sig")

    # ── fact.csv ──────────────────────────────────────
    df = load(folder, "fact.csv")
    issues = []
    if not df.empty:
        df = df.drop_duplicates(subset=["facno"], keep="first")
        report("fact.csv", df, df, issues)
        df.to_csv(out / "fact.csv", index=False, encoding="utf-8-sig")

    # ── prod.csv ──────────────────────────────────────
    df = load(folder, "prod.csv")
    issues = []
    if not df.empty:
        before = len(df)
        df = clean_numeric(df, ["price","price3","price4","qty","pcost","safeqty"])
        dup = df.duplicated(subset=["prdno"]).sum()
        if dup: issues.append(f"{dup} duplicate prdno")
        df = df.drop_duplicates(subset=["prdno"], keep="first")
        no_price = (df["price"] == 0).sum()
        if no_price: issues.append(f"{no_price} products with price = 0")
        report("prod.csv", pd.DataFrame(index=range(before)), df, issues)
        df.to_csv(out / "prod.csv", index=False, encoding="utf-8-sig")

    # ── stockqty.csv ──────────────────────────────────
    df = load(folder, "stockqty.csv")
    if not df.empty:
        df = clean_numeric(df, ["qty"])
        neg = (df["qty"] < 0).sum()
        issues = [f"{neg} rows with negative inventory"] if neg else []
        report("stockqty.csv", df, df, issues)
        df.to_csv(out / "stockqty.csv", index=False, encoding="utf-8-sig")

    # ── rereces / repays ──────────────────────────────
    for fname in ["rereces.csv", "repays.csv", "repay.csv", "rerece.csv"]:
        df = load(folder, fname)
        if not df.empty:
            for c in ["rlamt3","rlamt4","rdisc"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
            df.to_csv(out / fname, index=False, encoding="utf-8-sig")
            print(f"\n[{fname}] {len(df)} rows cleaned")

    print(f"\n{'='*50}")
    print(f"✅ Cleaning complete. Cleaned data saved to: {out}")
    print(f"   Next: python step2_aggregate.py \"{out}\"")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
