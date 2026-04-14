# Pipeline Template — 通用化 ETL 管線

一套設定驅動（config-driven）的四階段 ETL 模板：

```
clean  →  aggregate  →  analyze  →  anonymize
```

**動機**：倉庫內 `work/` 下的四支程式（`step1_clean.py` → `step4_anonymize.py`）是一條完整可用的管線，但檔名、欄位、業務邏輯全寫死在程式碼裡，換一份資料就得改 60-70% 的程式碼。

這個模板把每一階段需要「知道的事情」全部抽到一個 YAML config，程式碼本身完全不綁定任何欄位名。

---

## 快速開始

```bash
pip install -r ../requirements.txt        # 需要 pandas / numpy / pyyaml / openpyxl
cp config.example.yaml my_config.yaml     # 複製並改成你的欄位
python run_pipeline.py my_config.yaml
```

輸出會進到 `my_config.yaml` 的 `paths.out_dir` 裡，分成四個子資料夾：

```
out/
├── cleaned/       # step 1 輸出（與原始 CSV 同名，已清洗）
├── aggregated/    # step 2 輸出（每個 aggregation 一個 CSV）
├── analyzed/      # step 3 輸出（RFM、Pareto、Top-N）
└── anonymized/    # step 4 輸出（與 cleaned/aggregated 對應，但已去識別化）
```

---

## 只跑部分階段

```bash
python run_pipeline.py my_config.yaml --only clean,aggregate
python run_pipeline.py my_config.yaml --only analyze   # 從 cleaned/ 讀取
```

`--src` 和 `--out` 可以在 CLI 覆蓋 config 裡的路徑。

---

## Config Schema 速查

| 區塊 | 目的 | 必填 |
|---|---|---|
| `paths.raw_dir` / `paths.out_dir` | 資料夾位置 | 其一，否則用 CLI `--src/--out` |
| `sources[]` | 要清洗的 CSV + 欄位規則 | clean 階段必填 |
| `aggregations[]` | groupby 定義 | aggregate 階段必填 |
| `analysis.rfm` / `analysis.pareto` / `analysis.top_n` | 分析設定 | 可選 |
| `anonymization` | 去識別化設定 | 可選 |

詳細欄位請看 [`config.example.yaml`](./config.example.yaml) 的註解。

---

## 實際案例

這個 repo 附了兩個實際情境的 config，**兩個都用同一套引擎**，只靠 YAML 不同就能跑出不同領域的報表：

### `examples/sales_report/` — 商業分析報表
用 YAML 描述原本 `work/step1`~`step4` 裡寫死的全部 9 個 CSV、30+ 欄位、毛利計算、RFM、Pareto、去識別化規則，外加 Excel 輸出（7 張工作表）。

```bash
cd examples/sales_report
python ../../run_pipeline.py config.yaml --src /path/to/raw_csvs
```

### `examples/telco_churn/` — 電信客戶流失分析
用同一套引擎跑 IBM Telco Customer Churn 資料集，產生流失率分段（Contract / Payment / Internet）、高價值客戶 80/20、風險客戶 Top 50 的完整 Excel 報表。

```bash
cd examples/telco_churn
# 把 Telco-Customer-Churn.csv 放在同資料夾後
python ../../run_pipeline.py config.yaml
```

這兩個 schema 完全不同（銷售 vs 電信），但跑的是同一條 pipeline 程式碼——這就是「通用化」的證明。

---

## 設計原則

1. **程式不知道你的欄位叫什麼**：所有欄位名透過 config 注入，程式碼只操作「有幾欄」「怎麼 group」「哪些是金額」這類抽象概念
2. **缺資料不崩潰**：missing CSV、missing column、missing metric 都會 warn 後略過，和 `work/step1` 原本的 `if not df.empty` 防禦一致
3. **階段可獨立執行**：每階段讀前階段的 CSV，不需要一次跑完整條管線
4. **去識別化是可選的**：不要的話整段 `anonymization:` 拿掉就不會跑

---

## 目錄結構

```
pipeline_template/
├── README.md                  # 你正在看的這份
├── config.example.yaml        # 空白起步範本
├── run_pipeline.py            # 進入點
├── pipeline/
│   ├── __init__.py
│   ├── io_utils.py            # load_csv / save_csv / log / resolve_folder
│   ├── cleaning.py            # run_cleaning  — clean 階段
│   ├── aggregation.py         # run_aggregation — aggregate 階段
│   ├── analysis.py            # run_analysis — RFM / Pareto / Top-N
│   └── anonymization.py       # anonymize_tables — 去識別化
└── examples/
    └── sales_report/
        └── config.yaml        # 重現 work/ 情境的完整 config
```

---

## Excel 輸出

Config 裡加一段 `output.excel` 就會產出格式化的 xlsx 報表（表頭配色、邊框、凍結列、欄寬自動調整、金額/百分比格式化）：

```yaml
output:
  excel:
    enabled: true
    filename: report.xlsx
    source: aggregated
    sheets:
      - {from: monthly, title: 月度營收, number_cols: [revenue]}
      - {from: rfm, stage: analyzed, title: RFM 分數}
      - {from: customer_agg, title: 客戶排行, percent_cols: [share, cum_share]}
```

每張工作表的 `from` 指向某個階段產出的表名；`stage` 預設用 `source`，也可以逐表覆蓋（例如分析結果在 `analyzed/`）。

## 測試

```bash
cd pipeline_template
pip install pytest
pytest tests/ -v
```

附了 5 支測試檔共約 20 個 case，涵蓋：清洗、聚合（含 YAML `on:` → `True` 的 quirk）、RFM/Pareto/Top-N、去識別化的確定性與跨表一致性、Excel 輸出。

## 延伸方向

- 其他情境的 config 可加到 `examples/`（如 `examples/bike_share/`），把整個 repo 變成「多情境模板庫」
- Excel 輸出若要加圖表（`BarChart` / `LineChart`），`openpyxl.chart` 已經可用，在 `excel_writer.py` 的 `_write_sheet` 後綴加幾行即可
- 若資料量大到 pandas 吃不動，`io_utils.load_csv` 可改用 `duckdb`（requirements.txt 已含）並維持同樣介面
