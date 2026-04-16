# -*- coding: utf-8 -*-
"""Generate notebooks/telco_churn_analysis.ipynb (no outputs, reproducible)."""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks" / "telco_churn_analysis.ipynb"


def S(text: str) -> list:
    if not text.endswith("\n"):
        text += "\n"
    return text.splitlines(keepends=True)


def md(s: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": S(s), "id": uuid.uuid4().hex[:8]}


def code(s: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": S(s),
        "id": uuid.uuid4().hex[:8],
    }


cells = []

cells.append(
    md(
        """# Telco Customer Churn: End-to-End Data Science Project (Tutorial)

This notebook corresponds to the following project layout:

```
project_root/
├── data/raw/Telco-Customer-Churn.csv   # raw data
├── src/telco_churn/cleaning.py         # reusable cleaning function
├── notebooks/this_notebook.ipynb
├── requirements.txt
└── README.md
```

**Business question**: which customers are most likely to churn? The resulting list can drive retention-budget allocation and customer-service prioritisation. (This is an offline modelling demonstration, not a production pipeline.)

## Workflow overview

| Stage | Description |
|---|---|
| Load | Read the CSV from `data/raw` |
| Clean | Modular function `clean_telco_churn` |
| EDA | Shape, target distribution, charts, group-level churn rates |
| Preprocess | One-hot encoding, stratified train/test split |
| Model | Logistic Regression, Random Forest, HistGradientBoosting |
| Evaluate | ROC-AUC, classification_report |

> **📌 Purpose of this section**: align the reader on a reproducible project structure and the problem statement.
> **Why**: a GitHub / tutorial project needs readers to see where files come from and where the code runs — otherwise the notebook exists in a vacuum without data or modules."""
    )
)

cells.append(
    md(
        """## 0. Environment and data paths

You can start the kernel from either the project root or from `notebooks/` — the code below walks up the directory tree to find the folder containing `data/raw`, and adds `src` to `sys.path` so the cleaning module can be imported."""
    )
)

cells.append(
    code(
        """import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Locate the project root (the one containing data/raw and src)
ROOT = Path.cwd().resolve()
for _ in range(6):
    if (ROOT / "data" / "raw" / "Telco-Customer-Churn.csv").exists():
        break
    ROOT = ROOT.parent

SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from telco_churn.cleaning import clean_telco_churn

CSV_PATH = ROOT / "data" / "raw" / "Telco-Customer-Churn.csv"
RANDOM_STATE = 42

print("project root:", ROOT)
print("data file:", CSV_PATH, CSV_PATH.exists())"""
    )
)

cells.append(
    md(
        """> **📌 Purpose**: portable path resolution and module import.
> **Why**: a common tutorial-repo failure mode is "running inside notebooks/ can't find src"; a fixed root search avoids that class of bug."""
    )
)

cells.append(
    md(
        """## 1. Load the raw data

Use `pandas.read_csv`; switch to `encoding='utf-8-sig'` (or similar) if you hit encoding issues."""
    )
)

cells.append(
    code(
        """df = pd.read_csv(CSV_PATH)
print("shape:", df.shape)
df.head()"""
    )
)

cells.append(
    md(
        """> **📌 Purpose**: load the exact file referenced in the README.
> **Why**: downstream metrics need to trace back to a filename and row count — this is the first step of the data contract."""
    )
)

cells.append(
    md(
        """## 2. Data cleaning

Rules live in `src/telco_churn/cleaning.py` (shared with this notebook). Highlights: strip column names and string values, de-duplicate on the primary key, coerce `TotalCharges` to numeric and impute, enforce valid categorical + numeric ranges."""
    )
)

cells.append(
    code(
        """df = clean_telco_churn(df)

print("\\nremaining missing values after cleaning (should be none or handled):")
miss = df.isna().sum()
print(miss[miss > 0] if miss.sum() else "no remaining missing values")"""
    )
)

cells.append(
    md(
        """> **📌 Purpose**: one row per customer with correct dtypes.
> **Why**: duplicate IDs skew churn rate; string-typed `TotalCharges` prevents the model from using it; missing totals for brand-new customers need to make operational sense (tenure = 0)."""
    )
)

cells.append(
    md(
        """## 3. Exploratory analysis (EDA)

On the cleaned `df`, inspect dtypes, descriptive statistics, the target proportion, and the relationship between monthly charges and Churn."""
    )
)

cells.append(
    code(
        """df.info()
df.describe(include="all")"""
    )
)

cells.append(
    code(
        """print("TotalCharges dtype:", df["TotalCharges"].dtype)
print("\\nChurn distribution:")
print(df["Churn"].value_counts(normalize=True))"""
    )
)

cells.append(
    code(
        """import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
df["Churn"].value_counts().plot(kind="bar", ax=axes[0], title="Churn count")
df.boxplot(column="MonthlyCharges", by="Churn", ax=axes[1])
plt.suptitle("")
axes[1].set_title("MonthlyCharges vs Churn")
plt.tight_layout()
plt.show()"""
    )
)

cells.append(
    md(
        """> **📌 Purpose**: confirm class imbalance and monthly-charge distribution differences.
> **Why**: class balance shifts how you read the metrics; plots help form testable hypotheses."""
    )
)

cells.append(
    md(
        """### 3.1 Business insight: group-level churn rates

Translate the data into operations language (contract, payment, plan, tenure). When these group-level patterns align with later model feature directions, cross-functional trust in the model is easier to earn. **Correlation is not causation.**"""
    )
)

cells.append(
    code(
        """def churn_rate_by(col: str) -> pd.Series:
    return df.groupby(col)["Churn"].apply(lambda s: (s == "Yes").mean()).sort_values(ascending=False)

print("overall churn rate:", f"{(df['Churn'] == 'Yes').mean():.1%}")
print("\\nContract:")
print(churn_rate_by("Contract"))
print("\\nPaymentMethod:")
print(churn_rate_by("PaymentMethod"))
print("\\nInternetService:")
print(churn_rate_by("InternetService"))

df["_tb"] = pd.cut(
    df["tenure"],
    bins=[-1, 0, 12, 24, 60, 1000],
    labels=["0", "1-12", "13-24", "25-60", ">60"],
)
print("\\nTenure bin:")
print(df.groupby("_tb", observed=True)["Churn"].apply(lambda s: (s == "Yes").mean()))
df.drop(columns=["_tb"], inplace=True)

p75 = df["TotalCharges"].quantile(0.75)
hq_m2m = (df["Contract"] == "Month-to-month") & (df["TotalCharges"] >= p75)
print("\\nhigh-spend (P75+) month-to-month churn rate:",
      f"{(df.loc[hq_m2m, 'Churn'] == 'Yes').mean():.1%}",
      "n=", int(hq_m2m.sum()))"""
    )
)

cells.append(
    md(
        """> **📌 Purpose**: align with the common telecom narrative (month-to-month, electronic check, fiber, tenure).
> **Why**: the model needs to explain to the business *why* this particular list — group-level rates are the most intuitive reference."""
    )
)

cells.append(
    md(
        """## 4. Preprocessing (feature matrix)

Drop `customerID`; convert `Churn` to 0/1; one-hot encode categorical features; use **stratified** splits to preserve the churn ratio."""
    )
)

cells.append(
    code(
        """from sklearn.model_selection import train_test_split

X = df.drop(columns=["customerID", "Churn"])
y = (df["Churn"] == "Yes").astype(int)
X = pd.get_dummies(X, drop_first=True)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)
X_train.shape, X_test.shape, y.mean()"""
    )
)

cells.append(
    md(
        """> **📌 Purpose**: obtain a model-ready matrix and a reportable hold-out set.
> **Why**: IDs shouldn't be features; `stratify` prevents the test split from drifting in class ratio."""
    )
)

cells.append(
    md(
        """## 5. Modelling and evaluation

Compare three classifiers; report **ROC-AUC** and **classification_report** (threshold defaults to 0.5 — in practice it can be tuned to the promotion cost)."""
    )
)

cells.append(
    code(
        """from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score

models = {
    "LogisticRegression": LogisticRegression(max_iter=2000, random_state=RANDOM_STATE),
    "RandomForest": RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1),
    "HistGradientBoosting": HistGradientBoostingClassifier(random_state=RANDOM_STATE),
}

for name, model in models.items():
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    auc = roc_auc_score(y_test, proba)
    print(f"=== {name} ===")
    print(f"ROC-AUC: {auc:.4f}")
    print(classification_report(y_test, pred, digits=4))"""
    )
)

cells.append(
    md(
        """> **📌 Purpose**: compare offline generalisation / ranking capability.
> **Why**: training scores are optimistic; AUC is useful for list prioritisation; precision / recall maps to the over-contact vs. missed-contact trade-off."""
    )
)

cells.append(
    md(
        """## 6. Deliberately out of scope (good to add later)

- **Time-based splits**: if observation dates are available, validate on time to avoid leakage.
- **Cross-validation / hyperparameter tuning**: more stable performance estimates.
- **Deployment and monitoring**: batch inference, data drift tracking.
- **Causal inference / Uplift modelling**: to estimate "did the promotion *actually* retain the customer", you need experimental design, not just offline AUC.

---

## 7. Summary

1. Data sits in `data/raw`; cleaning logic lives in `src/telco_churn/cleaning.py`.
2. EDA + group churn rates form the business hypothesis; the model's results should move in the same direction.
3. When publishing to GitHub, include `requirements.txt` and document the Python version + how to run in the README.

> **📌 Purpose**: honestly demarcate the boundaries of a tutorial project so it can be extended later.
> **Why**: portfolio value often comes from knowing *what's missing* — not claiming to have done it all."""
    )
)

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB.parent.mkdir(parents=True, exist_ok=True)
with open(NB, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("Wrote", NB, "cells=", len(cells))
