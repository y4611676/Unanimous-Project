# Unanimous-Project

Data analysis portfolio — concrete case studies, a reusable ETL framework, and an interactive dashboard.

## Contents

### 🔧 Framework

**[`pipeline_template/`](./pipeline_template/)** — YAML-configured 4-stage ETL template:
`clean → aggregate → analyze → anonymize → Excel report`.
Ships with 21 pytest cases and two real-world example configs (sales, telco churn).

### 📊 Case Studies

| Project | Domain | Stack | Key Finding |
|---|---|---|---|
| [Safe Haven Index](./Safe_Haven_Index/) | Geopolitics / International | Python, Streamlit, Plotly, World Bank API | **Interactive dashboard** ranking 61 countries on six weighted indicators; equal-weight Top 5 = Australia / Canada / NZ / Norway / Ireland, sliders re-rank live |
| [Telco Customer Churn](./Telco-Customer-Churn/) | Telecom | Python, Pandas, Seaborn | **$139K/month revenue at risk**; month-to-month customers churn at 42.7% (15× vs. two-year contracts), electronic check users churn at 45% |
| [Bike Share](./Bike_Share/) | Shared economy | Python, DuckDB, Matplotlib | **Casual riders average 2× ride duration** of members; only casuals use docked bikes; summer 5–7 PM is the prime conversion window |
| [Fitabase](./Fitabase/) | Health tech | R, tidyverse, ggplot2 | **81% of the average day is sedentary**, avg sleep only 6.9 hrs, 5–7 PM is the peak push-notification window |
| [Business Analytics Report](./work/) | Retail / wholesale | Python, Pandas, openpyxl, scikit-learn | **28% of customers drive 65% of sales**, 20 loss-making SKUs, 64% of items are out-of-stock; ships as two six-step pipelines ([quarterly](./work/quarterly_analysis/) / [annual](./work/annual_analysis/)) producing four Excel reports each |

## Framework × Case Studies

This repo tells a single engineering story in three moves:

1. **Build it by hand** — `work/` started as a hand-written sales ETL against real ERP CSVs. File names, column names, and business logic were all hard-coded in Python. It grew into two six-step pipelines (`quarterly_analysis/`, `annual_analysis/`) producing four Excel reports: main analysis, de-identified version, advanced analytics (forecast / cohort / churn / basket / anomaly), and a one-page executive summary.
2. **Extract the abstraction** — pulling the common patterns out of `work/`'s first four steps produced `pipeline_template/`: a YAML-driven engine that doesn't know what your columns are called.
3. **Prove it generalises** — the same engine drives the Telco Churn dataset by swapping only the YAML config. Two completely different schemas (retail sales vs. telecom), same Python code.

## Tech Stack

Python · R · SQL · Pandas · Seaborn · DuckDB · tidyverse · ggplot2 · Jupyter · openpyxl · pytest · Streamlit · Plotly · World Bank API

## Setup

```bash
pip install -r requirements.txt
# Framework details: pipeline_template/README.md
```