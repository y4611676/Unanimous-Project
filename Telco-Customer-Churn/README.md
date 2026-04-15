# Telco Customer Churn — Business Analysis

Using the **IBM Telco Customer Churn** public dataset to analyze customer churn behavior from a business perspective and provide actionable retention recommendations.

## Key Findings

- **26.5% overall churn rate** — 1,869 customers lost, averaging **$139K/month** in recurring revenue
- **Month-to-month contracts churn at 42.7%** — 15× higher than two-year contracts (3%)
- **Electronic check users churn at 45%** — the highest of any payment method
- Churned customers averaged **18-month tenure vs. 37 months** for retained — first 3 months are the danger zone
- **Recommendation**: offer a 10–15% annual-plan discount to month-to-month customers + auto-pay credit to electronic-check users; trigger Day 7/30/90 outreach for new signups

See [`Telco_Churn_Analysis.pdf`](./Telco_Churn_Analysis.pdf) for the full report.

## Analysis Focus

| Topic | Description |
|-------|-------------|
| Churn rate by segment | Contract type, payment method, internet service, tenure |
| Monthly revenue loss | Translate churn into actual revenue impact |
| High-value customer analysis | Identify the segments most worth investing in for retention |
| New customer danger zone | Identify highest-risk tenure months to help customer service prioritize |
| Business recommendations | Three immediately actionable directions |

## Project Structure

```
.
├── src/telco_churn/
│   ├── __init__.py
│   └── cleaning.py
├── notebooks/
│   └── telco_churn_analysis.ipynb
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
jupyter notebook notebooks/telco_churn_analysis.ipynb
```

## Data Source

IBM Telco Customer Churn public dataset (available on Kaggle)

## Reusable Pipeline

The same dataset can also be processed by the generic ETL framework in
[`../pipeline_template/`](../pipeline_template/) — see
[`examples/telco_churn/config.yaml`](../pipeline_template/examples/telco_churn/config.yaml)
for a YAML-only run that produces churn-rate breakdowns and a high-value
customer Pareto report.

## License

Code released under the [MIT License](LICENSE).
