# 商業分析報表 ETL（手寫版）

針對特定零售批發業者的商業分析報表，從原始 CSV 一路走到去識別化 Excel 報表。

## 流程

```
step1_clean.py  →  step2_aggregate.py  →  step3_analyze.py  →  step4_anonymize.py
   清理               聚合                    Excel 報表             去識別化
```

每一步讀前一步的輸出，依序執行：

```bash
python step1_clean.py /path/to/raw_csvs
python step2_aggregate.py /path/to/raw_csvs/cleaned
python step3_analyze.py /path/to/raw_csvs/aggregated
python step4_anonymize.py /path/to/raw_csvs/aggregated
```

## 涵蓋資料

9 個 CSV：`sale`、`sales1`、`purc`、`purcs1`、`cust`、`fact`、`prod`、`stockqty`、`rereces/repays`。

## 產出

- `cleaned/` — 清理後的乾淨 CSV
- `aggregated/` — 月度、客戶、產品、供應商、庫存、應收應付的聚合表
- `商業分析報表_完整版.xlsx` — 完整格式化 Excel 報表
- `商業分析報表_去識別化版.xlsx` — 客戶/品項/廠商遮罩、金額縮放、日期平移後的版本

## 與 `pipeline_template/` 的關係

這份程式是 **領域特定的手寫 ETL**——檔名、欄位、業務邏輯（毛利、RFM、Pareto）全寫死在程式碼裡，要套用到別的資料集得改 60-70% 的程式。

從這條管線萃取出來的通用版本在 [`../pipeline_template/`](../pipeline_template/)，
其中 [`examples/sales_report/config.yaml`](../pipeline_template/examples/sales_report/config.yaml) 用 YAML 設定重現了完全相同的流程，無須改任何程式碼。

兩者並存的用意：

| 看 `work/` 學到 | 看 `pipeline_template/` 學到 |
|---|---|
| 一條完整商業 ETL 長什麼樣、解什麼問題 | 怎麼把硬編碼的程式抽象成可重用框架 |
