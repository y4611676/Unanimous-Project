# Telco 客戶流失 — 資料科學教學專案

以 **IBM Telco Customer Churn** 公開資料為例，示範一條可放進 GitHub 的迷你專案：**讀取資料 → 清理 → EDA → 特徵工程 → 分類模型 → 評估**。程式碼以繁體中文註解與筆記本說明為主，適合自學與履歷作品集。

## 專案結構

```
.
├── data/raw/                    # 原始 CSV（請保留檔名便於重現）
│   └── Telco-Customer-Churn.csv
├── src/telco_churn/             # 可重用的清理邏輯
│   ├── __init__.py
│   └── cleaning.py
├── notebooks/
│   └── telco_churn_analysis.ipynb
├── scripts/
│   └── build_notebook.py      # 可選：從腳本重新產生 notebook
├── requirements.txt
├── LICENSE
└── README.md
```

## 環境需求

- Python **3.10+**（建議 3.11）
- 依賴見 `requirements.txt`

## 安裝與執行

於專案根目錄：

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
jupyter notebook notebooks/telco_churn_analysis.ipynb
```

執行筆記本時，kernel 的工作目錄建議為**專案根目錄**或 **`notebooks/`**；筆記本內會自動尋找含 `data/raw` 的根目錄並將 `src` 加入路徑。

若要以模組方式測試清理函式：

```bash
set PYTHONPATH=src            # Windows cmd
# export PYTHONPATH=src       # Unix
python -c "from telco_churn.cleaning import clean_telco_churn; ..."
```

## 資料來源

本專案使用常見的 **Telco Customer Churn** 資料集（客戶方案、在網月數、是否流失等）。若你自 Kaggle 或其他來源下載，請置於 `data/raw/Telco-Customer-Churn.csv` 或自行修改筆記本中的檔名／路徑。

## 授權

專案程式碼與文件以 [MIT License](LICENSE) 釋出。資料集之權利依原發布單位為準。

## 作者說明

此 repo 定位為**教學與作品集**：未包含上線管線、即時監控與 A/B 測試；筆記本第 6 節列出可延伸方向。
