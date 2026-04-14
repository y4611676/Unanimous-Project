# -*- coding: utf-8 -*-
"""【步驟 3】商業分析綜合版（A–H）。

流程：載入所有 CSV → 逐章節分析 → 產生 CSV / PNG / report.html。
報告為 self-contained HTML（圖表內嵌），雙擊即可在瀏覽器開啟。

相容舊呼叫：保留原本 main() 行為（產出 report.html、同資料夾 CSV）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允許以腳本或 `python -m work.analyze_business` 執行
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from src.loaders import load_all
from src.analyses import AnalysisResult
from src.analyses import revenue as m_revenue
from src.analyses import profit as m_profit
from src.analyses import inventory as m_inventory
from src.analyses import customer as m_customer
from src.analyses import basket as m_basket
from src.analyses import supplier as m_supplier
from src.analyses import cashflow as m_cashflow
from src.analyses import salesrep as m_salesrep
from src.analyses import forecast as m_forecast
from src.report import build_report


def _default_paths() -> tuple[Path, Path]:
    try:
        import pipeline_config as pc  # noqa: PLC0415

        return pc.CSV_DIR, pc.ANALYSIS_OUTPUT
    except ImportError:
        p = Path(__file__).resolve().parent
        return p / "db1_backup_20260414_csv", p / "analysis_output"


MODULES = [
    ("營收", m_revenue),
    ("毛利", m_profit),
    ("庫存", m_inventory),
    ("客戶", m_customer),
    ("購物籃", m_basket),
    ("供應商", m_supplier),
    ("現金流", m_cashflow),
    ("業務員", m_salesrep),
    ("預測", m_forecast),
]


def main() -> int:
    csv_def, out_def = _default_paths()
    parser = argparse.ArgumentParser(description="商業分析綜合版（A–H）")
    parser.add_argument("--csv-dir", type=Path, default=csv_def,
                        help=f"CSV 目錄（預設：{csv_def.name}）")
    parser.add_argument("--out-dir", type=Path, default=out_def,
                        help="圖表、CSV、HTML 報告輸出目錄")
    parser.add_argument("--only", nargs="*", default=None,
                        help="只跑指定章節 key（如 profit inventory customer）")
    parser.add_argument("--no-html", action="store_true", help="不產生 report.html")
    args = parser.parse_args()

    csv_dir: Path = args.csv_dir.resolve()
    out_dir: Path = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not csv_dir.is_dir():
        print(f"找不到 CSV 目錄：{csv_dir}", file=sys.stderr)
        return 1

    print(f"[載入] {csv_dir}")
    data = load_all(csv_dir)
    print(f"[載入] 完成。參考截止日：{data.ref_date}")

    results: list[AnalysisResult] = []
    for label, mod in MODULES:
        mod_key = mod.__name__.rsplit(".", 1)[-1]
        if args.only and mod_key not in args.only:
            continue
        print(f"[{label}] 執行 {mod_key}.run() …")
        try:
            r = mod.run(data, out_dir)
            results.append(r)
            print(f"       KPI: {r.kpis}")
        except Exception as e:  # noqa: BLE001
            print(f"       !! 失敗：{type(e).__name__}: {e}", file=sys.stderr)

    if not args.no_html and results:
        rep = build_report(results, out_dir)
        print(f"[報告] {rep}")

    print("全部完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
