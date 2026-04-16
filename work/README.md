# Where Is Your Profit Actually Coming From?

A complete analysis of a retail/wholesale business that answered three questions the owner didn't have reliable answers to: **which customers drive revenue, which products drag profit down, and where is inventory bleeding money.**

## This analysis is for you if:

- You feel like a handful of customers keep the lights on, but you can't name them — and you have no plan if one of them leaves
- You know some products are "good" and some are "bad," but every time you look at the data it's a spreadsheet you don't trust
- Your warehouse is full of stuff that isn't selling, and stuff that *is* selling keeps running out

---

## What We Found (And What They Did About It)

Below are the actual numbers from this client's data. Absolute dollar amounts have been scaled for privacy, but **the proportions are real.**

### Finding 1: 28% of customers drive 65% of sales

The 197 "high-value new customers" bring in almost two-thirds of revenue. Another 347 are sliding toward churn and account for 30% of sales.

**Decision enabled:** The owner handed the at-risk list to their sales lead the same week. One-on-one outreach before a customer disappears is cheap. Reacquiring them after they've left is expensive — or impossible.

### Finding 2: 20 SKUs are actively losing money on every sale

1,677 products have healthy margins (>30%) and account for 89% of revenue. But 20 products are selling *below cost* — every order of these is a loss.

**Decision enabled:** Discontinue or reprice the 20 loss-makers. There is no reason to sell something below cost unless you're using it to pull in other orders. Confirm that, or stop.

### Finding 3: 64% of inventory is out of stock

Of 3,224 SKUs, 2,066 are at zero inventory. Another 428 are below safety stock. Only 22.5% are at healthy levels. This isn't a supply-chain hiccup — it's a planning problem.

**Decision enabled:** Auto-replenishment alerts on the fast-moving items. The owner was losing sales on bestsellers while sitting on slow movers. One afternoon of reorder-point configuration closed the biggest leak.

---

## What You Get

A single Excel file with everything the owner needs to act on, broken into sheets:

| Sheet | What It Shows | Decision It Supports |
|-------|---------------|---------------------|
| Business Summary | Total revenue, profit, margin at a glance | Is the quarter on track? |
| Customer Ranking | Who are your top customers, and who's about to leave | Where should sales focus this week? |
| Customer Segments (RFM) | Customers grouped by value and risk | Which customers to protect, win back, or upsell |
| Product 80/20 | Which products drive most revenue | Don't promote a product unless you know where it sits here |
| Gross Margin Analysis | Profit per product, sorted | Discontinue the losers, push the winners |
| Inventory Alert | What's out of stock, what's dead weight | Reorder / clearance decisions |
| Key Charts | One-page visual summary for meetings | Board decks, monthly reviews |

**Plus an optional second report** covering forecasting, customer churn risk, product-pairing analysis, seasonal patterns, and order-level anomaly detection — when you're ready to go beyond the basics.

---

## Want the Same Analysis on Your Data?

If you have sales records, customer records, and inventory data in almost any format — we can produce this report for your business.

**What we need from you:**
- Your transaction data (CSV, Excel, database export — we'll figure it out)
- One conversation to understand your business context
- A few days' turnaround

**What you get back:**
- A de-identified version first (we see patterns, not your actual customer names) — for the initial review
- The full, named report once you're comfortable
- A plain-English explanation of every finding, and a prioritized list of what to act on first

Reach out through the portfolio main page.

---

## For Technical Readers

This folder contains a **hand-written, domain-specific ETL pipeline** built for one real client. A generalized, config-driven version lives at [`../pipeline_template/`](../pipeline_template/).

### Pipeline

```
step1_clean.py  →  step2_aggregate.py  →  step3_analyze.py  →  step4_anonymize.py
   Clean             Aggregate             Excel report          De-identify
                                                  ↓
                                          step5_advanced.py (optional)
                                          Forecast / Churn / Basket / etc.
```

Run sequentially:

```bash
python step1_clean.py /path/to/raw_csvs
python step2_aggregate.py /path/to/raw_csvs/cleaned
python step3_analyze.py /path/to/raw_csvs/aggregated
python step4_anonymize.py /path/to/raw_csvs/aggregated
python step5_advanced.py /path/to/raw_csvs/aggregated   # optional
```

Sample data lives in `sample_data/` — the full pipeline runs on it without any setup.

### Data covered

Nine CSVs: `sale`, `sales1`, `purc`, `purcs1`, `cust`, `fact`, `prod`, `stockqty`, `rereces`/`repays`.

### Outputs

- `cleaned/` — cleaned CSVs (deduplicated, type-corrected, date-parsed)
- `aggregated/` — monthly / customer / product / supplier / inventory / AR-AP roll-ups
- `business_analysis_report.xlsx` — the basic report (step3)
- `business_analysis_deidentified.xlsx` — masked names, scaled money, shifted dates (step4)
- `advanced_analysis_report.xlsx` — forecasting, churn, basket, etc. (step5)

### Tests

```bash
pytest work/tests/ -v
```

20 smoke tests covering all 5 steps and every analysis function. All gracefully degrade on insufficient data rather than crashing.

### Relationship to `pipeline_template/`

These scripts have file names, column names, and business logic hard-coded. Adapting to a different client typically requires rewriting 60–70% of the code.

The generic version in [`../pipeline_template/`](../pipeline_template/) — specifically [`examples/sales_report/config.yaml`](../pipeline_template/examples/sales_report/config.yaml) — reproduces this entire pipeline using YAML only, no code changes.

Both exist because each teaches a different lesson:

| Reading `work/` teaches you | Reading `pipeline_template/` teaches you |
|---|---|
| What a complete real-world business ETL looks like and which problems it solves | How to extract the generic pattern from a hard-coded pipeline into a reusable framework |
