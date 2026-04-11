# Telco 客戶流失 — 商業分析專案

以 **IBM Telco Customer Churn** 公開資料為例，從商業角度分析客戶流失行為，提供可執行的留客建議。

## 分析重點

| 主題 | 說明 |
|------|------|
| 流失率分組 | 合約類型、付款方式、網路服務、在網時間 |
| 月費損失估算 | 把流失行為換算成實際收入損失 |
| 高價值客戶分析 | 找出最值得投入留客資源的族群 |
| 新客危險期 | 識別最高風險的在網月份，協助客服排優先序 |
| 商業建議 | 三個可立即執行的行動方向 |

## 專案結構

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

## 安裝與執行

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
jupyter notebook notebooks/telco_churn_analysis.ipynb
```

## 主要發現

- 月租型客戶流失率是兩年約客戶的 **6 倍以上**
- 電子支票付款流失率最高，自動扣款最低
- 新客戶**前 3 個月**是最高危險期
- Fiber 光纖客戶流失率高於 DSL，值得深入調查

## 資料來源

IBM Telco Customer Churn 公開資料集（常見於 Kaggle）

## 授權

程式碼以 [MIT License](LICENSE) 釋出。
