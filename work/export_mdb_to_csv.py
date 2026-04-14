"""
【步驟 1】將 Microsoft Access .mdb 內所有使用者資料表匯出為 CSV，寫入與 .mdb 同層的子資料夾。

需求：已安裝 Python、pyodbc，以及 Windows 上的 Access ODBC 驅動
（Office/Access 或 Microsoft Access Database Engine Redistributable）。

使用前請關閉正在開啟該 .mdb 的 Access，以免鎖檔 (.ldb)。
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import pyodbc


def _try_connect(mdb_path: Path) -> pyodbc.Connection:
    drivers = [
        "Microsoft Access Driver (*.mdb, *.accdb)",
        "Microsoft Access Driver (*.mdb)",
    ]
    available = {d.upper() for d in pyodbc.drivers()}
    last_err: Exception | None = None
    for drv in drivers:
        if drv.upper() not in available:
            continue
        conn_str = f"DRIVER={{{drv}}};DBQ={mdb_path.resolve()};"
        try:
            return pyodbc.connect(conn_str)
        except Exception as e:  # noqa: BLE001 — 嘗試下一個驅動
            last_err = e
    msg = (
        "無法連線到 .mdb。請確認已安裝 Microsoft Access Database Engine 或 Office/Access，"
        "且 Python 位元（32/64）與驅動一致。\n"
        f"已安裝的 ODBC 驅動：{pyodbc.drivers()}"
    )
    if last_err:
        raise RuntimeError(msg) from last_err
    raise RuntimeError(msg)


def _safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip() or "table"


def _list_user_tables(cur: pyodbc.Cursor) -> list[str]:
    # 使用 ODBC SQLTables，避免依賴 MSysObjects 讀取權限（部分 .mdb 會拒絕）
    names: list[str] = []
    for row in cur.tables(tableType="TABLE"):
        name = row.table_name
        if name.startswith("MSys") or name.startswith("~"):
            continue
        names.append(name)
    return sorted(names)


def export_mdb_to_csv(mdb_path: Path, out_dir: Path) -> int:
    mdb_path = mdb_path.resolve()
    if not mdb_path.is_file():
        print(f"找不到檔案：{mdb_path}", file=sys.stderr)
        return 1

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = _try_connect(mdb_path)
    try:
        cur = conn.cursor()
        tables = _list_user_tables(cur)
        if not tables:
            print("未找到可匯出的使用者資料表。", file=sys.stderr)
            return 1

        for table in tables:
            safe = _safe_filename(table)
            csv_path = out_dir / f"{safe}.csv"
            cur.execute(f"SELECT * FROM [{table.replace(']', ']]')}]")
            columns = [c[0] for c in cur.description]
            with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in cur.fetchall():
                    writer.writerow(row)
            print(f"OK  {table} -> {csv_path.name}")

    finally:
        conn.close()

    print(f"完成：共 {len(tables)} 個 CSV，目錄：{out_dir}")
    return 0


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    try:
        import pipeline_config as pc  # noqa: PLC0415 — 可選，統一路徑

        default_mdb = pc.MDB_PATH
    except ImportError:
        default_mdb = script_dir / "db1_backup_20260414.mdb"

    parser = argparse.ArgumentParser(description="將 .mdb 各資料表匯出為 CSV（子資料夾）。")
    parser.add_argument(
        "--mdb",
        type=Path,
        default=default_mdb,
        help=f".mdb 路徑（預設：{default_mdb.name} 與本腳本同目錄）",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="輸出資料夾（預設：與 .mdb 同層，名稱為「檔名_csv」）",
    )
    args = parser.parse_args()

    mdb = args.mdb
    if args.out is not None:
        out_dir = args.out
    else:
        out_dir = mdb.parent / f"{mdb.stem}_csv"

    return export_mdb_to_csv(mdb, out_dir)


if __name__ == "__main__":
    sys.exit(main())
