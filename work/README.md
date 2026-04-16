# Business Analytics Report — Hand-Written ETL

End-to-end pipeline for a specific retail/wholesale business, from raw CSVs to a de-identified Excel report.

## Key Findings

(Numbers from [`Business Analytics Report_Deidentified Version.xlsx`](./Business%20Analytics%20Report_Deidentified%20Version.xlsx); absolute monetary amounts have been scaled for anonymisation, but the proportions and structural findings are preserved.)

- **Extreme customer concentration**: 197 "high-value new customers" (28% of all customers) drive **65.4% of total sales**; another 347 "at-risk" customers account for 30% of sales and urgently need retention
- **Bimodal margins**: 1,677 high-margin SKUs (>30% gross margin) deliver **89.3% of revenue**, but 20 loss-making SKUs (<0% margin) are still actively dragging profit down
- **Severe inventory health imbalance**: of 3,224 SKUs, **64.1% are out of stock, 13.3% are below safety stock**, only 22.5% are at healthy levels — replenishment pacing and forecasting are clearly broken
- **Recommendations**: (1) hand the at-risk customer list to sales for 1:1 outreach; (2) immediately discontinue or re-price the 20 loss-making SKUs; (3) set up auto-replenishment alerts for out-of-stock best-sellers

## Pipeline

```
step1_clean.py  →  step2_aggregate.py  →  step3_analyze.py  →  step4_anonymize.py
   Clean             Aggregate             Excel report          De-identify
```

Each stage reads the previous stage's output and runs sequentially:

```bash
python step1_clean.py /path/to/raw_csvs
python step2_aggregate.py /path/to/raw_csvs/cleaned
python step3_analyze.py /path/to/raw_csvs/aggregated
python step4_anonymize.py /path/to/raw_csvs/aggregated
```

## Data covered

Nine CSVs: `sale`, `sales1`, `purc`, `purcs1`, `cust`, `fact`, `prod`, `stockqty`, `rereces`/`repays`.

## Outputs

- `cleaned/` — cleaned CSVs (deduplicated, type-corrected, date-parsed)
- `aggregated/` — monthly / customer / product / supplier / inventory / AR-AP roll-ups
- `Business Analytics Report_Full Version.xlsx` — fully formatted Excel report
- `Business Analytics Report_Deidentified Version.xlsx` — customer / product / supplier identifiers masked, monetary amounts scaled, dates shifted

> The scripts print status messages and report column names in Chinese because
> they were built for a Chinese-speaking business analyst. The output Excel
> sheets are likewise Chinese. This is intentional — it's the real tool that
> serves the real stakeholder.

## Relationship to `pipeline_template/`

These scripts are a **domain-specific, hand-written ETL** — file names, column names, and business logic (gross margin, RFM, Pareto) are all hard-coded in Python. Adapting them to a different dataset would require rewriting 60–70% of the code.

The generic version extracted from this pipeline lives at [`../pipeline_template/`](../pipeline_template/). In particular, [`examples/sales_report/config.yaml`](../pipeline_template/examples/sales_report/config.yaml) reproduces the exact same flow using YAML only — no code changes required.

Why both exist:

| Reading `work/` teaches you | Reading `pipeline_template/` teaches you |
|---|---|
| What a complete real-world business ETL looks like and which problems it solves | How to extract the generic pattern from a hard-coded pipeline into a reusable framework |
