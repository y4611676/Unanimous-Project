# -*- coding: utf-8 -*-
"""
【步驟 1+3 一鍵】從 .mdb 匯出 CSV → 商業分析 → 產生 HTML 報告（內嵌圖表）。

  python run_pipeline.py              # 匯出 + 分析（預設）
  python run_pipeline.py --analyze-only   # 只分析（CSV 已存在）
  python run_pipeline.py --export-only    # 只匯出
  python run_pipeline.py --open           # 結束後用預設瀏覽器開啟報告

路徑請改 pipeline_config.py。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path

import pipeline_config as pc


def run_export() -> None:
    export_py = pc.BASE / "export_mdb_to_csv.py"
    cmd = [
        sys.executable,
        str(export_py),
        "--mdb",
        str(pc.MDB_PATH),
        "--out",
        str(pc.CSV_DIR),
    ]
    print("執行：", " ".join(cmd))
    subprocess.run(cmd, check=True)


def run_analyze() -> None:
    analyze_py = pc.BASE / "analyze_business.py"
    cmd = [
        sys.executable,
        str(analyze_py),
        "--csv-dir",
        str(pc.CSV_DIR),
        "--out-dir",
        str(pc.ANALYSIS_OUTPUT),
    ]
    print("執行：", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="MDB → CSV → 分析報告")
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="只執行 MDB 匯出 CSV",
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="只執行分析（不匯出）",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="完成後用瀏覽器開啟 analysis_output/report.html",
    )
    args = parser.parse_args()

    if args.export_only and args.analyze_only:
        print("請勿同時指定 --export-only 與 --analyze-only", file=sys.stderr)
        return 1

    try:
        if args.export_only:
            run_export()
        elif args.analyze_only:
            run_analyze()
        else:
            if not pc.MDB_PATH.is_file():
                print(
                    f"找不到 MDB：{pc.MDB_PATH}\n改 pipeline_config.py 或改檔名後再試。"
                    f"\n若已有 CSV，可改用：python run_pipeline.py --analyze-only",
                    file=sys.stderr,
                )
                return 1
            run_export()
            run_analyze()
    except subprocess.CalledProcessError as e:
        return e.returncode or 1

    report = pc.ANALYSIS_OUTPUT / "report.html"
    if report.is_file() and args.open:
        webbrowser.open(report.as_uri())
    elif args.open and not report.is_file():
        print(f"找不到報告：{report}", file=sys.stderr)

    print("完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
