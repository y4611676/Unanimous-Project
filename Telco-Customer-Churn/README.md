# How Much Revenue Are You Losing to Customers Who Quietly Leave?

An analysis of a telecom company's customer base that found **26.5% churn costing $139,000 per month in recurring revenue** — and identified three specific, fixable causes.

## This analysis is for you if:

- You run a subscription business and you're losing customers faster than you're replacing them, but you don't know *which* customers or *why*
- Your sales team focuses on new signups while the back door stays wide open
- You've tried generic retention offers and they didn't move the needle

---

## What We Found (And What to Do About It)

This was real data from 7,043 telecom customers. The patterns show up in almost every subscription business: internet, software, media, gyms, B2B services.

### Finding 1: Contract type is the single biggest churn driver

- **Month-to-month contracts: 42.7% churn**
- Two-year contracts: 3% churn
- That's a **15× difference** from one product decision

**What to do:** Offer a 10–15% discount to move month-to-month customers onto annual plans. The math almost always works: a 15% discount beats losing the customer entirely. Most operators resist this because it "feels like giving money away" — but your churn rate is already giving money away, silently.

### Finding 2: Electronic check users churn at 45%

This payment method was churning nearly double the others. Why? Electronic check customers tend to be the most price-sensitive and the least locked-in — they never set up auto-pay, so every bill is a chance to leave.

**What to do:** Offer a one-time credit ($5–$10) to anyone who switches to auto-pay. The retention lift pays it back within a quarter.

### Finding 3: The first 3 months are the danger zone

Churned customers had an average tenure of 18 months. Retained customers averaged 37. But drill in and the pattern is sharper: **most of the churn happens in the first 90 days.** If a customer survives the first quarter, they're likely to stay for years.

**What to do:** Automated outreach on Day 7, Day 30, and Day 90. Not a sales pitch — a check-in. "How's it going? Anything we can help with?" This single workflow typically recovers 3–5% of at-risk new customers.

---

## What You Get

A customer-by-customer risk score plus three specific, prioritized actions:

| Output | Decision It Supports |
|--------|---------------------|
| Churn rate by segment (contract, payment, service, tenure) | Where to focus retention budget first |
| Revenue impact per segment | Which problem is worth fixing vs. accepting |
| High-value customer Pareto | Who to protect at all costs |
| First-90-days risk profile | How to redesign onboarding |
| Three ranked recommendations | What to ship next quarter |

Full report: [`Telco_Churn_Analysis.pdf`](./Telco_Churn_Analysis.pdf)

---

## Want the Same Analysis on Your Data?

If you run any kind of recurring-revenue business — telecom, SaaS, subscription box, gym, streaming, professional services — this analysis maps directly onto your data.

**What we need from you:**
- Your customer records, subscription history, and churn events (whatever format you've got)
- A 30-minute call to understand your product and pricing model

**What you get back:**
- A ranked list of churn causes specific to *your* business (not a generic benchmark)
- Revenue impact attached to each cause — so you can prioritize what to fix
- Three concrete retention experiments to run, with expected lift estimates

Reach out through the portfolio main page.

---

## For Technical Readers

Standalone analysis project using the **IBM Telco Customer Churn** public dataset (7,043 customers, available on Kaggle).

### Project Structure

```
.
├── src/telco_churn/
│   ├── __init__.py
│   ├── cleaning.py          # CSV cleaning (shared with notebook)
│   ├── features.py          # Feature engineering (tenure buckets, add-on count)
│   ├── model.py             # sklearn Pipeline: LR / RF / GB benchmark + persist
│   └── evaluate.py          # ROC / PR / feature importance / threshold sweep
├── notebooks/
│   ├── telco_churn_analysis.ipynb    # Exploratory — why do customers churn?
│   └── 02_modeling.ipynb             # Predictive — can we forecast churn?
├── app.py                   # Streamlit churn-risk scoring demo
├── artifacts/               # Persisted model (created by model.py)
├── requirements.txt
└── README.md
```

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

### Three ways to use this repo

```bash
# 1. Exploratory analysis
jupyter notebook notebooks/telco_churn_analysis.ipynb

# 2. Modeling walkthrough (benchmarks LR / RF / GB, picks winner, saves model)
jupyter notebook notebooks/02_modeling.ipynb
# or from the CLI:
python -m telco_churn.model Telco-Customer-Churn.csv

# 3. Interactive churn-risk demo
streamlit run app.py
```

### Modeling approach

Three sklearn pipelines benchmarked with 5-fold stratified CV on ROC AUC:

| Model | Why it's here |
|-------|--------------|
| Logistic Regression | Interpretable baseline. Coefficients readable by business stakeholders. |
| Random Forest | Captures non-linear interactions (e.g. tenure × contract type) cheaply. |
| Gradient Boosting | Usually wins by a small margin; what the Streamlit app ships with. |

Features are standardised (numerics) and one-hot encoded (categoricals) through a single `ColumnTransformer`. Engineered features add tenure buckets, charges-per-month-of-tenure, and an add-on count. See `src/telco_churn/evaluate.py` for ROC, PR, confusion matrix, feature importance, and threshold sweep helpers — the threshold sweep in particular lets you pick an operating point that matches the business cost of a false positive (wasted retention offer) vs. false negative (missed churner).

### Analysis Focus

| Topic | Description |
|-------|-------------|
| Churn rate by segment | Contract type, payment method, internet service, tenure |
| Monthly revenue loss | Translate churn into actual revenue impact |
| High-value customer analysis | Identify the segments most worth investing in for retention |
| New customer danger zone | Identify highest-risk tenure months to help customer service prioritize |
| Business recommendations | Three immediately actionable directions |

### Reusable Pipeline

The same dataset can also be processed by the generic ETL framework in
[`../pipeline_template/`](../pipeline_template/) — see
[`examples/telco_churn/config.yaml`](../pipeline_template/examples/telco_churn/config.yaml)
for a YAML-only run that produces churn-rate breakdowns and a high-value
customer Pareto report.

### License

Code released under the [MIT License](LICENSE).
