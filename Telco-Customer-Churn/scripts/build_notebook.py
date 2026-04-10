# -*- coding: utf-8 -*-
"""產生 notebooks/telco_churn_analysis.ipynb（無輸出、可重現）。"""
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
        """# Telco 客戶流失：端到端資料科學專案（教學版）

本筆記本對應專案目錄：

```
專案根目錄/
├── data/raw/Telco-Customer-Churn.csv   # 原始資料
├── src/telco_churn/cleaning.py         # 可重用的清理函式
├── notebooks/本檔.ipynb
├── requirements.txt
└── README.md
```

**商業問題**：哪些客戶較可能解約（Churn）？名單可用於留客預算與客服優先序（離線建模示範，非上線管線）。

## 流程總覽

| 階段 | 說明 |
|------|------|
| 讀取 | 自 `data/raw` 載入 CSV |
| 清理 | 模組化函式 `clean_telco_churn` |
| EDA | 結構、目標分佈、視覺化、分組流失率 |
| 前處理 | One-Hot、train/test 分層切分 |
| 建模 | 邏輯迴歸、隨機森林、HistGradientBoosting |
| 評估 | ROC-AUC、classification_report |

> **📌 本節目的**：對齊「可重現的專案結構」與問題陳述。  
> **為什麼**：GitHub／教學專案需要讓讀者知道檔案從哪來、程式從哪跑，避免只見 notebook 不見資料與模組。"""
    )
)

cells.append(
    md(
        """## 0. 環境與資料路徑

從專案根目錄或 `notebooks/` 啟動 kernel 皆可：下列程式會向上尋找含 `data/raw` 的專案根目錄，並把 `src` 加入 `sys.path` 以匯入清理模組。"""
    )
)

cells.append(
    code(
        """import sys
from pathlib import Path

import numpy as np
import pandas as pd

# 專案根目錄（含 data/raw 與 src）
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

print("專案根目錄:", ROOT)
print("資料檔:", CSV_PATH, CSV_PATH.exists())"""
    )
)

cells.append(
    md(
        """> **📌 本格目的**：可攜帶的路徑解析與匯入專案模組。  
> **為什麼**：教學 repo 常見「在 notebooks 裡跑就找不到 `src`」；固定搜尋根目錄可減少這類錯誤。"""
    )
)

cells.append(
    md(
        """## 1. 讀取原始資料

使用 `pandas.read_csv`；若遇編碼問題可改 `encoding='utf-8-sig'` 等。"""
    )
)

cells.append(
    code(
        """df = pd.read_csv(CSV_PATH)
print("形狀:", df.shape)
df.head()"""
    )
)

cells.append(
    md(
        """> **📌 本格目的**：載入與 README 同一來源的檔案。  
> **為什麼**：後續指標必須能對檔名與列數追溯；也是資料契約的第一步。"""
    )
)

cells.append(
    md(
        """## 2. 數據清理

規則實作於 `src/telco_churn/cleaning.py`（與本筆記本共用）。重點：欄名與字串 strip、主鍵去重、`TotalCharges` 數值化與填補、合法類別與數值範圍。"""
    )
)

cells.append(
    code(
        """df = clean_telco_churn(df)

print("\\n清理後缺失（應無或已處理）:")
miss = df.isna().sum()
print(miss[miss > 0] if miss.sum() else "無剩餘缺失")"""
    )
)

cells.append(
    md(
        """> **📌 本格目的**：讓每位客戶一列、型別正確。  
> **為什麼**：重複 ID 會扭曲流失率；`TotalCharges` 字串會讓模型無法使用；新戶缺總帳需符合營運解釋（年資 0）。"""
    )
)

cells.append(
    md(
        """## 3. 探索性分析（EDA）

在已清理的 `df` 上檢視型別、描述統計、目標比例與月費與 Churn 的關係。"""
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
print("\\nChurn 比例:")
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
        """> **📌 本格目的**：確認不平衡與月費分佈差異。  
> **為什麼**：類別比例影響指標解讀；圖形有助形成可驗證的假說。"""
    )
)

cells.append(
    md(
        """### 3.1 商業洞察：分組流失率

將資料翻成營運語言（合約、付款、方案、年資）；若與後續模型特徵方向一致，較易取得跨部門信任。**相關不等於因果**。"""
    )
)

cells.append(
    code(
        """def churn_rate_by(col: str) -> pd.Series:
    return df.groupby(col)["Churn"].apply(lambda s: (s == "Yes").mean()).sort_values(ascending=False)

print("整體流失率:", f"{(df['Churn'] == 'Yes').mean():.1%}")
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
print("\\n高累計(P75+)且月租 — 流失率:", f"{(df.loc[hq_m2m, 'Churn'] == 'Yes').mean():.1%}", "n=", int(hq_m2m.sum()))"""
    )
)

cells.append(
    md(
        """> **📌 本格目的**：對齊常見電信業敘事（月租、電子支票、Fiber、年資）。  
> **為什麼**：模型需能向業務交代「為何這份名單」；分組率是最直覺的對照。"""
    )
)

cells.append(
    md(
        """## 4. 前處理（特徵矩陣）

排除 `customerID`；`Churn` 轉 0/1；類別 One-Hot；**分層切分**維持流失比例。"""
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
        """> **📌 本格目的**：得到模型可讀矩陣與可報告的 hold-out。  
> **為什麼**：ID 不應當特徵；`stratify` 避免測試集類別比例漂移。"""
    )
)

cells.append(
    md(
        """## 5. 建模與評估

比較三種分類器；報告 **ROC-AUC** 與 **classification_report**（閾值預設 0.5，實務可依促銷成本調整）。"""
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
        """> **📌 本格目的**：離線比較泛化排序／分類能力。  
> **為什麼**：訓練集分數會樂觀；AUC 利於名單排序；精確／召回對應打擾與漏接權衡。"""
    )
)

cells.append(
    md(
        """## 6. 本專案刻意未涵蓋（之後可學）

- **時間切分**：若有觀測日期，應以時間驗證避免洩漏。  
- **交叉驗證／調參**：更穩的效能估計。  
- **部署與監控**：批次推論、資料漂移。  
- **因果／Uplift**：若要估「促銷是否真留住客」，需實驗設計而非僅離線 AUC。

---

## 7. 小結

1. 資料放在 `data/raw`，清理邏輯在 `src/telco_churn/cleaning.py`。  
2. EDA + 分組流失率形成商業假說，建模結果應與之一致方向。  
3. 上 GitHub 時請一併提交 `requirements.txt` 並在 README 寫清 Python 版本與執行方式。

> **📌 本節目的**：誠實標出教學專案邊界，方便未來加寬。  
> **為什麼**：作品集價值常來自「你知道還缺什麼」，而非宣稱已做完所有事。"""
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
