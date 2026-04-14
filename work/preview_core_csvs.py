"""
【選用】讀取核心商業分析用 CSV，印出欄位、筆數與前兩筆預覽。

預設從與本腳本同目錄下的 db1_backup_20260414_csv 讀取（可依 --dir 覆寫）。
編碼會依序嘗試 utf-8-sig / utf-8 / big5 / cp950，以相容本工具匯出與傳統 Big5 檔案。

使用：pip install pandas
       python preview_core_csvs.py
       python preview_core_csvs.py --dir "D:\\work\\db1_backup_20260414_csv"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

DEFAULT_FILES = [
    "cust.csv",
    "fact.csv",
    "prod.csv",
    "stock.csv",
    "sale.csv",
    "purc.csv",
    "cash.csv",
]

# 匯出為 UTF-8-BOM 時優先；舊檔或 Excel 另存常為 Big5
ENCODINGS_TO_TRY = ("utf-8-sig", "utf-8", "big5", "cp950")


def read_csv_flexible(path: Path) -> pd.DataFrame:
    last_err: Exception | None = None
    for enc in ENCODINGS_TO_TRY:
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    raise OSError(f"無法讀取：{path}")


def _configure_stdout_utf8() -> None:
    """盡量讓 Windows 終端機正確顯示中文（需終端本身支援 UTF-8，例如 chcp 65001）。"""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


def main() -> int:
    _configure_stdout_utf8()
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="預覽核心 CSV 欄位與筆數")
    parser.add_argument(
        "--dir",
        type=Path,
        default=script_dir / "db1_backup_20260414_csv",
        help="CSV 所在資料夾（預設：與腳本同層的 db1_backup_20260414_csv）",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=DEFAULT_FILES,
        help="要檢視的檔名（預設為七個核心表）",
    )
    args = parser.parse_args()
    csv_dir: Path = args.dir.resolve()

    if not csv_dir.is_dir():
        print(f"找不到資料夾：{csv_dir}", file=sys.stderr)
        return 1

    for name in args.files:
        path = csv_dir / name
        print(f"=== {name} ===")
        if not path.is_file():
            print(f"  略過：檔案不存在 — {path}\n")
            continue
        try:
            df = read_csv_flexible(path)
            print(df.columns.tolist())
            print(f"筆數：{len(df)}")
            print(df.head(2))
        except Exception as e:  # noqa: BLE001 — 預覽腳本需印出任何失敗原因
            print(f"讀取失敗：{e}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
