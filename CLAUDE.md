# Unanimous Project

Business analytics portfolio with a reusable ETL pipeline framework and multiple case studies.

## Project Structure

- `work/` — Hand-written 4-step ETL pipeline (clean → aggregate → analyze → anonymize) for retail/wholesale data
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

# Work pipeline smoke tests
pytest work/tests/ -v
```

### Work Pipeline

The `work/` pipeline runs in 5 sequential steps (step5 is optional):

```bash
cd work
python step1_clean.py <csv_folder>                  # Clean raw CSVs
python step2_aggregate.py <csv_folder>/cleaned      # Build aggregate tables
python step3_analyze.py <csv_folder>/aggregated     # Basic report (RFM, Pareto, GP, inventory)
python step4_anonymize.py <csv_folder>/aggregated   # De-identified version of basic report
python step5_advanced.py <csv_folder>/aggregated    # Advanced analytics (optional)
```

Sample data is available in `work/sample_data/` for testing.

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
