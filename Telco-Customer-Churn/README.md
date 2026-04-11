# Telco Customer Churn — Business Analysis

Using the **IBM Telco Customer Churn** public dataset to analyze customer churn behavior from a business perspective and provide actionable retention recommendations.

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
├── data/raw/
│   └── Telco-Customer-Churn.csv
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

## Key Findings

- Month-to-month contract customers churn at **6x the rate** of two-year contract customers
- Electronic check payment has the highest churn rate; automatic payment has the lowest
- New customers are at highest risk in the **first 3 months**
- Fiber optic customers churn at a higher rate than DSL — worth further investigation

## Data Source

IBM Telco Customer Churn public dataset (available on Kaggle)

## License

Code released under the [MIT License](LICENSE).
