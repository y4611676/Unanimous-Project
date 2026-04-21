# Unanimous Project

Business analytics portfolio with a reusable ETL pipeline framework and multiple case studies.

## Project Structure

- `work/` — Hand-written 6-step ETL pipeline for retail/wholesale ERP data, split into two cadence variants (`quarterly_analysis/`, `annual_analysis/`) sharing step1–step5; step6 differs per cadence (QoQ vs YoY executive summary)
- `pipeline_template/` — Generalized config-driven (YAML) ETL framework with tests
- `Safe_Haven_Index/` — Geopolitical risk dashboard (Streamlit)
- `Telco-Customer-Churn/` — Telecom churn analysis
- `Bike_Share/` — Bike sharing patterns (DuckDB)
- `Fitabase/` — Health/wellness analytics (R)

## Development

### Dependencies

```bash
pip install -r requirements.txt
```

### Running Tests

```bash
# Pipeline template tests
pytest pipeline_template/tests/ -v
```

### Work Pipeline

`work/` ships two cadence variants that share step1–step5 and differ only at step6:

- `work/quarterly_analysis/pipeline/` — QoQ executive summary at step6
- `work/annual_analysis/pipeline/` — YoY executive summary at step6

Each variant runs in 6 sequential steps (step5 and step6 are optional):

```bash
cd work/quarterly_analysis/pipeline   # or work/annual_analysis/pipeline

python step1_clean.py                 # Clean raw CSVs (prompts for folder path)
python step2_aggregate.py             # Build aggregate tables
python step3_analyze.py               # Main report (RFM, Pareto, GP, inventory)
python step4_anonymize.py             # De-identified version of main report
python step5_advanced.py              # Advanced analytics (optional)
python step6_executive_summary.py     # One-page executive summary (optional)
```

### Advanced Analytics (step5)

`step5_advanced.py` produces a second Excel report with 6 analyses:

| Sheet | Analysis | Business Question |
|-------|----------|-------------------|
| Sales Forecast | EWMA + seasonal projection (next 3 months) | What's next? |
| Seasonality | Additive decomposition (trend + seasonal + residual) | Is this dip seasonal or real? |
| Cohort Analysis | Retention matrix by first-purchase month | Are we keeping customers? |
| Churn Risk | Logistic regression on RFM features | Who's about to leave? |
| Market Basket | Product pair lift analysis | What should we bundle? |
| Anomaly Detection | IQR-based outlier flagging on sale lines | What looks wrong? |

All analyses degrade gracefully on insufficient data (return empty results, don't crash).
Dependencies: pandas, numpy, openpyxl, scikit-learn (already in requirements.txt).

### Column Naming Convention

All pipeline steps use English column names:

| Column | Description |
|--------|-------------|
| sales | Sales amount |
| purchases | Purchase amount |
| gross_profit | Gross profit |
| cost | Cost |
| gp_rate | Gross profit rate |
| balance | Sales minus purchases |
| order_count | Number of orders |
| avg_order_value | Average order value |
| stock_status | Inventory status (Normal/Low Stock/Zero Stock) |
| stock_value | Inventory value |
| first_transaction / last_transaction | Customer transaction date range |
| first_purchase / last_purchase | Supplier purchase date range |

### Code Style

- Python 3.10+
- Use English for all column names, comments, docstrings, and UI text
- ID columns keep original short names: cusno, cusnm, prdno, prdnm, facno, facnm
