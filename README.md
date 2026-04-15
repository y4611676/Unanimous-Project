# Unanimous-Project

商業數據分析作品集——從具體案例到可重用的 ETL 框架。

## 內容

### 🔧 Framework

**[`pipeline_template/`](./pipeline_template/)** — 設定驅動（YAML）的 4 階段 ETL 模板：
`clean → aggregate → analyze → anonymize → Excel 報表`。
附 21 個 pytest 與兩個實際情境的 config（銷售、電信流失）。

### 📊 Case Studies

| Project | Domain | Stack | Key Finding |
|---|---|---|---|
| [Safe Haven Index](./Safe_Haven_Index/) | 地緣政治 / 國際 | Python, Streamlit, Plotly, World Bank API | **互動式儀表板**：六項指標加權排名 61 國，Top 5 = Australia/Canada/NZ/Norway/Ireland；權重可拉動即時換算 |
| [Telco Customer Churn](./Telco-Customer-Churn/) | 電信 | Python, Pandas, Seaborn | **$139K/月營收流失**；月租客戶流失率 42.7%（高於年約 15 倍），電子支票用戶流失 45% |
| [Bike Share](./Bike_Share/) | 共享經濟 | Python, DuckDB, Matplotlib | **Casual 騎乘時長是會員 2 倍**、僅 Casual 用 docked 車；夏季 5–7 PM 是轉會員黃金窗口 |
| [Fitabase](./Fitabase/) | 健康科技 | R, tidyverse, ggplot2 | **81% 日常時間靜態久坐**、平均睡眠僅 6.9 hrs，5–7 PM 是推播黃金時段 |
| [商業分析報表](./work/) | 零售批發 | Python, Pandas, openpyxl | **28% 客戶貢獻 65% 銷售**、20 項虧損品項拖累利潤、64% 商品零庫存 |

## Framework × Case Studies

`work/` 原本是一條手寫的銷售 ETL，所有檔名、欄位、業務邏輯都寫死在程式碼裡。
把共同模式萃取出來後，變成 `pipeline_template/`——
同一條引擎靠更換 YAML 就能套用到 Telco Churn 資料集，證明**抽象層是可用的**。

## Tech Stack

Python · R · SQL · Pandas · Seaborn · DuckDB · tidyverse · ggplot2 · Jupyter · openpyxl · pytest · Streamlit · Plotly · World Bank API

## Setup

```bash
pip install -r requirements.txt
# Framework 詳細用法見 pipeline_template/README.md
```
