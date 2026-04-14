# -*- coding: utf-8 -*-
"""
【選用】一次性刪除低價值 CSV（p/s 數字表、before、報表快照、空 BOM）。
會處理 `pipeline_config.CSV_DIR` 與對應 `*_anonymized` 目錄（若存在）。可重跑。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import pipeline_config as pc

    DIRS = [pc.CSV_DIR, pc.BASE / f"{pc.CSV_DIR.name}_anonymized"]
except ImportError:
    _b = Path(__file__).resolve().parent
    DIRS = [_b / "db1_backup_20260414_csv", _b / "db1_backup_20260414_csv_anonymized"]

RE_P = re.compile(r"^p\d+\.csv$", re.I)
RE_S = re.compile(r"^s\d+\.csv$", re.I)
EXACT = {
    "salebefore.csv",
    "purcbefore.csv",
    "bom1.csv",
    "bom2.csv",
    "report1.csv",
    "report2.csv",
    "report3.csv",
    "report4.csv",
    "report5.csv",
    "rep_t1.csv",
    "rep_t2.csv",
    "rep_t3.csv",
    "rep_t4.csv",
}


def main() -> int:
    n = 0
    for base in DIRS:
        base = base.resolve()
        if not base.is_dir():
            print(f"略過（無此目錄）：{base}")
            continue
        for f in base.glob("*.csv"):
            name = f.name
            low = name.lower()
            if low in EXACT or RE_P.match(name) or RE_S.match(name):
                f.unlink()
                n += 1
                print(f"已刪：{f}")
    print(f"完成，共刪除 {n} 個檔案。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
