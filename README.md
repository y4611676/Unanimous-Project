# Unanimous-Project

商業數據分析作品集——從具體案例到可重用的 ETL 框架。

## 內容

### 🔧 Framework

**[`pipeline_template/`](./pipeline_template/)** — 設定驅動（YAML）的 4 階段 ETL 模板：
`clean → aggregate → analyze → anonymize → Excel 報表`。
附 21 個 pytest 與兩個實際情境的 config（銷售、電信流失）。

### 📊 Case Studies

| Project | Domain | Stack | Highlights |
|---|---|---|---|
| [Telco Customer Churn](./Telco-Customer-Churn/) | 電信 | Python, Pandas, Seaborn | 流失率分群、營收流失估算、留客建議 |
| [Bike Share](./Bike_Share/) | 共享經濟 | Python, DuckDB, Matplotlib | SQL、EDA、視覺化 |
| [Fitabase](./Fitabase/) | 健康科技 | R, tidyverse, ggplot2 | 清理、EDA、行為分析 |
| [商業分析報表](./work/) | 零售批發 | Python, Pandas, openpyxl | 銷售 / 採購 / 客戶 / 庫存 ETL + 去識別化 |

## Framework × Case Studies

`work/` 原本是一條手寫的銷售 ETL，所有檔名、欄位、業務邏輯都寫死在程式碼裡。
把共同模式萃取出來後，變成 `pipeline_template/`——
同一條引擎靠更換 YAML 就能套用到 Telco Churn 資料集，證明**抽象層是可用的**。

## Tech Stack

Python · R · SQL · Pandas · Seaborn · DuckDB · tidyverse · ggplot2 · Jupyter · openpyxl · pytest

## Setup

```bash
pip install -r requirements.txt
# Framework 詳細用法見 pipeline_template/README.md
```
