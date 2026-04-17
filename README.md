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
| [Business Analytics Report](./work/) | Retail / wholesale | Python, Pandas, openpyxl | **28% of customers drive 65% of sales**, 20 loss-making SKUs, 64% of items are out-of-stock |

## Framework × Case Studies

`work/` started as a hand-written sales ETL with file names, column names, and business logic all hard-coded in Python.
Extracting the common patterns produced `pipeline_template/` —
the same engine drives the Telco Churn dataset by swapping only the YAML config, proving the abstraction layer actually works.

## Tech Stack

Python · R · SQL · Pandas · Seaborn · DuckDB · tidyverse · ggplot2 · Jupyter · openpyxl · pytest · Streamlit · Plotly · World Bank API

## Setup

```bash
pip install -r requirements.txt
# Framework details: pipeline_template/README.md
```

## Contact

Available for hire on:

- **[Fiverr](https://www.fiverr.com/s/1qygL2p)**