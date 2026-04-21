# 季度分析工具 (Quarterly Analysis)

每季結束後，將 ERP 原始 CSV 餵入管線，自動產出三份 Excel 報表供管理層決策。

---

## 專案結構

```
quarterly_analysis/
├── README.md
└── pipeline/
    ├── step1_clean.py          資料清洗
    ├── step2_aggregate.py      資料彙總
    ├── step3_analyze.py        主分析報表
    ├── step4_anonymize.py      去識別報表（對外/簡報用）
    ├── step5_advanced.py       進階分析
    └── step6_executive_summary.py  季度經營摘要（給老闆）
```

---

## 快速開始

### 環境安裝（第一次使用）
```bash
pip install -r requirements.txt
```
> `requirements.txt` 位於本目錄的上層（`d:\work\`）。

### 執行流程（依序執行）

```bash
cd quarterly_analysis/pipeline

# Step 1：清洗原始 CSV
python step1_clean.py
# 輸入：原始 CSV 所在資料夾（例如 d:\work\data\db1_backup_20260414_csv）
# 輸出：同資料夾下的 cleaned\ 子目錄

# Step 2：彙總
python step2_aggregate.py
# 輸入：cleaned\ 資料夾路徑
# 輸出：同上層的 aggregated\ 子目錄

# Step 3：產出主分析 Excel
python step3_analyze.py
# 輸入：aggregated\ 資料夾路徑
# 輸出：business_analysis_report.xlsx

# Step 4：去識別版本（視需要）
python step4_anonymize.py
# 輸出：business_analysis_deidentified.xlsx

# Step 5：進階分析（季節性、同期群、預測、流失風險…）
python step5_advanced.py
# 輸出：advanced_analysis_report.xlsx

# Step 6：季度經營摘要（一頁給老闆看）
python step6_executive_summary.py
# 輸出：quarterly_executive_summary.xlsx
```

---

## 輸出 Excel 說明

| 檔案 | 工作表 | 適合對象 |
|------|--------|---------|
| `business_analysis_report.xlsx` | 重要圖表、業務摘要、客戶RFM分析、帕累托分析、毛利分析、庫存警示 | 業務主管、財務 |
| `advanced_analysis_report.xlsx` | 銷售預測、季節性分析、同期群分析、流失風險、購物籃分析、異常偵測 | 分析師、PM |
| `quarterly_executive_summary.xlsx` | 季度經營摘要（單頁） | 總經理、老闆 |
| `business_analysis_deidentified.xlsx` | 同 step3，數字已縮放、ID 已遮罩 | 外部顧問、簡報 |

---

## 輸入 CSV 欄位說明

管線需要以下 CSV 檔案（置於同一個資料夾）：

| 檔案 | 必要欄位 | 說明 |
|------|----------|------|
| `sale.csv` | `salno`, `sdate`, `cusno`, `tot` | 銷售單表頭 |
| `sales1.csv` | `salno`, `prdno`, `prqty`, `price`, `pcost` | 銷售單明細 |
| `purc.csv` | `purno`, `pdate`, `facno`, `tot` | 進貨單表頭 |
| `purcs1.csv` | `purno`, `prdno`, `prqty`, `price` | 進貨單明細 |
| `cust.csv` | `cusno`, `cusnm` | 客戶主檔 |
| `fact.csv` | `facno`, `facnm` | 廠商主檔 |
| `prod.csv` | `prdno`, `prdnm`, `price`, `pcost`, `safeqty` | 產品主檔 |
| `stockqty.csv` | `prdno`, `qty` | 現有庫存 |
| `rereces.csv` | `rlamt3`, `rlamt4` | 應收帳款（選填） |
| `repays.csv` | `rlamt3`, `rlamt4` | 應付帳款（選填） |

---

## 與 annual_analysis 的差異

| 面向 | quarterly_analysis | annual_analysis |
|------|-------------------|-----------------|
| 資料視窗 | 單季（約3個月） | 全年（約12個月） |
| Step 6 主指標 | 本季營收 + QoQ（季增率） | 本年度營收 + YoY（年增率） |
| Step 6 額外內容 | — | 各季分佈長條 |
| Step 6 決策欄 | 以「下季規劃」結尾 | 以「明年規劃」結尾 |
| 輸出檔名 | `quarterly_executive_summary.xlsx` | `annual_executive_summary.xlsx` |

兩者共用相同的 Step 1–5 邏輯；差異在於餵入的資料時間範圍。

---

## 注意事項

- Step 5 的銷售預測需要至少 **6 個月**月度資料才能運作；單季資料會自動略過預測。
- 每次執行前確認 `step1` 的輸入資料夾路徑正確。
- 建議每季建立獨立的工作資料夾，避免覆蓋前一季的輸出。
