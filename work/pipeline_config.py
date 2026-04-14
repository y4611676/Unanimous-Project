# -*- coding: utf-8 -*-
"""
【設定】一處設定：之後若檔名或資料夾慣例不變，只改這裡即可重複跑完整流程。

run_pipeline.py、export_mdb_to_csv.py、analyze_business.py 會讀取這些路徑。
"""

from pathlib import Path

BASE = Path(__file__).resolve().parent

# 備份檔（與 BASE 同目錄）
MDB_FILENAME = "db1_backup_20260414.mdb"
MDB_PATH = BASE / MDB_FILENAME

# 與 export_mdb_to_csv 預設一致：{mdb 主檔名}_csv
CSV_DIR = BASE / f"{MDB_PATH.stem}_csv"

# 分析圖表與 CSV 結果
ANALYSIS_OUTPUT = BASE / "analysis_output"
