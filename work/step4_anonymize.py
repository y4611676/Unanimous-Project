"""
步驟四：去識別化報表
- 讀取 aggregated/ 聚合資料
- 對識別欄位做一致性遮罩
- 對金額做等比例縮放（保留趨勢比例，但無法對應真實規模）
- 對日期做一致性平移（保留相對時序，但無法對應真實起始時間）
- 輸出去識別化的 Excel 報表（不修改原始資料）

遮罩規則：
  cusno / cusnm  →  CUST-001 / 客戶A
  prdno / prdnm  →  PROD-001 / 品項A
  facno / facnm  →  SUPP-001 / 廠商A
  金額欄位       →  乘以隨機縮放係數（每次執行固定，由 ANON_SEED 控制）
  日期欄位       →  整體平移隨機月數（同 ANON_SEED）
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from dateutil.relativedelta import relativedelta
import importlib.util

# ══════════════════════════════════════════════════════════
# 去識別化參數（改 ANON_SEED 可得到不同的縮放/平移結果）
# ══════════════════════════════════════════════════════════
ANON_SEED = 20240101   # 整數即可，任意更改

_rng = np.random.default_rng(ANON_SEED)

# 金額縮放係數：保證偏離至少 40%（避免落在 0.9～1.1 之間）
# 一半機率縮小到 0.15～0.55；一半機率放大到 1.5～2.8
_side = int(_rng.integers(0, 2))
MONEY_SCALE = round(
    float(_rng.uniform(0.15, 0.55)) if _side == 0
    else float(_rng.uniform(1.5, 2.8)),
    6
)

# 日期平移：保證偏移 24～72 個月（2～6 年），方向隨機
_dir = 1 if int(_rng.integers(0, 2)) == 0 else -1
DATE_SHIFT_M = _dir * int(_rng.integers(24, 73))

# ── 哪些欄要縮放金額 ──────────────────────────────────────
MONEY_COLS = {
    "monthly":   ["銷售額","採購額","毛利","差額","銷售額_明細","成本"],
    "cust_agg":  ["銷售額","平均客單價"],
    "prod_agg":  ["銷售額","成本","毛利"],
    "fact_agg":  ["採購額","平均採購單價"],
    "stock_agg": ["庫存價值","price","pcost"],
}

# ── 哪些欄要平移日期 ──────────────────────────────────────
DATE_COLS = {
    "cust_agg":  ["最早交易","最近交易"],
    "fact_agg":  ["最早採購","最近採購"],
}


# ══════════════════════════════════════════════════════════
# 動態載入 step3 的報表函式
# ══════════════════════════════════════════════════════════
def _import_step3():
    spec = importlib.util.spec_from_file_location(
        "step3_analyze",
        Path(__file__).parent / "step3_analyze.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ══════════════════════════════════════════════════════════
# 遮罩工具
# ══════════════════════════════════════════════════════════

def _idx_to_letters(i):
    return chr(65 + i) if i < 26 else chr(65 + i // 26 - 1) + chr(65 + i % 26)


def _make_id_map(series, prefix):
    """原始 ID → XXXX-001 對照表（以字串為鍵）"""
    vals = [str(v).strip() for v in series.dropna().unique() if str(v).strip() not in ("", "nan")]
    return {v: f"{prefix}-{str(i+1).zfill(3)}" for i, v in enumerate(vals)}


def _make_nm_map(id_series, nm_series, label):
    """
    根據 id 欄的順序建立 名稱→遮罩名稱 對照表。
    相同 id 順序的名稱統一遮罩為「標籤A / 標籤B…」。
    """
    vals = [str(v).strip() for v in id_series.dropna().unique() if str(v).strip() not in ("", "nan")]
    nm_map = {}
    for i, orig_id in enumerate(vals):
        mask = id_series.astype(str).str.strip() == orig_id
        names = nm_series[mask].dropna().unique()
        for nm in names:
            nm_str = str(nm).strip()
            if nm_str and nm_str != "nan":
                nm_map[nm_str] = f"{label}{_idx_to_letters(i)}"
    return nm_map


def _apply(df, col_maps):
    """將 col_maps（欄名→對照dict）套用到 df 複本，型別不同時強制轉字串比對。"""
    df = df.copy()
    for col, mapping in col_maps.items():
        if col not in df.columns:
            continue
        df[col] = df[col].apply(
            lambda x: mapping.get(str(x).strip(), x)
            if pd.notna(x) and str(x).strip() not in ("", "nan")
            else x
        )
    return df


def build_id_maps(cust_agg, prod_agg, fact_agg):
    """建立所有識別欄位的遮罩對照表，回傳 col_maps dict。"""
    col_maps = {}

    if not cust_agg.empty and "cusno" in cust_agg.columns:
        col_maps["cusno"] = _make_id_map(cust_agg["cusno"], "CUST")
        if "cusnm" in cust_agg.columns:
            col_maps["cusnm"] = _make_nm_map(cust_agg["cusno"], cust_agg["cusnm"], "客戶")

    if not prod_agg.empty and "prdno" in prod_agg.columns:
        col_maps["prdno"] = _make_id_map(prod_agg["prdno"], "PROD")
        if "prdnm" in prod_agg.columns:
            col_maps["prdnm"] = _make_nm_map(prod_agg["prdno"], prod_agg["prdnm"], "品項")

    if not fact_agg.empty and "facno" in fact_agg.columns:
        col_maps["facno"] = _make_id_map(fact_agg["facno"], "SUPP")
        if "facnm" in fact_agg.columns:
            col_maps["facnm"] = _make_nm_map(fact_agg["facno"], fact_agg["facnm"], "廠商")

    return col_maps


# ══════════════════════════════════════════════════════════
# 金額縮放
# ══════════════════════════════════════════════════════════

def scale_money(df, df_key):
    df = df.copy()
    for col in MONEY_COLS.get(df_key, []):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0) * MONEY_SCALE
    return df


# ══════════════════════════════════════════════════════════
# 日期平移
# ══════════════════════════════════════════════════════════

def _shift_ym_str(ym_str):
    """
    將 "2019-06" 或 "2019Q2" 這類字串平移 DATE_SHIFT_M 個月。
    無法解析則原樣回傳。
    """
    s = str(ym_str).strip()
    try:
        # 處理 2019-06 格式
        if len(s) == 7 and s[4] == "-":
            dt = pd.to_datetime(s + "-01") + relativedelta(months=DATE_SHIFT_M)
            return dt.strftime("%Y-%m")
        # 處理 2019Q2 格式
        if len(s) == 6 and s[4] == "Q":
            base_month = (int(s[5]) - 1) * 3 + 1
            dt = pd.to_datetime(f"{s[:4]}-{base_month:02d}-01") + relativedelta(months=DATE_SHIFT_M)
            new_q = (dt.month - 1) // 3 + 1
            return f"{dt.year}Q{new_q}"
    except Exception:
        pass
    return ym_str


def _shift_date_col(series):
    """平移一欄日期（字串或 datetime 皆可）。"""
    result = pd.to_datetime(series, errors="coerce")
    shifted = result.apply(
        lambda d: d + relativedelta(months=DATE_SHIFT_M) if pd.notna(d) else d
    )
    return shifted.dt.strftime("%Y-%m-%d").where(shifted.notna(), other="")


def shift_dates(df, df_key):
    df = df.copy()
    for col in DATE_COLS.get(df_key, []):
        if col in df.columns:
            df[col] = _shift_date_col(df[col])
    # monthly 的 ym / yq 欄特別處理
    if df_key == "monthly":
        for col in ["ym", "yq"]:
            if col in df.columns:
                df[col] = df[col].apply(_shift_ym_str)
    return df


# ══════════════════════════════════════════════════════════
# 對照表頁籤
# ══════════════════════════════════════════════════════════

def _add_mapping_sheet(wb, col_maps, cust_agg, prod_agg, fact_agg):
    from openpyxl.styles import Font, PatternFill, Alignment
    ws = wb.create_sheet("🔑 對照表（機密）")
    ws.sheet_view.showGridLines = False

    ws.merge_cells("A1:E1")
    c = ws["A1"]
    c.value = (
        "去識別化對照表（僅限內部使用）｜"
        f"金額縮放係數：{MONEY_SCALE:.4f}　"
        f"日期平移：{DATE_SHIFT_M:+d} 個月　"
        f"Seed：{ANON_SEED}"
    )
    c.font  = Font(name="Arial", bold=True, size=11, color="FFFFFF")
    c.fill  = PatternFill("solid", fgColor="C00000")
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 26

    row = 3
    sections = [
        ("客戶對照", "cusno", "cusnm", cust_agg),
        ("產品對照", "prdno", "prdnm", prod_agg),
        ("供應商對照","facno", "facnm", fact_agg),
    ]

    for section_title, id_key, nm_key, ref_df in sections:
        if id_key not in col_maps:
            continue
        ws.cell(row=row, column=1, value=section_title).font = Font(bold=True, size=11)
        row += 1
        for ci, h in enumerate(["原始編號","遮罩編號","原始名稱","遮罩名稱"], 1):
            ws.cell(row=row, column=ci, value=h).font = Font(bold=True)
        row += 1

        id_map = col_maps[id_key]
        nm_map = col_maps.get(nm_key, {})
        nm_rev = {v: k for k, v in nm_map.items()}

        for orig_id, anon_id in id_map.items():
            idx = list(id_map.keys()).index(orig_id)
            anon_nm = f"{'客戶' if id_key=='cusno' else '品項' if id_key=='prdno' else '廠商'}{_idx_to_letters(idx)}"
            orig_nm = nm_rev.get(anon_nm, "")
            ws.cell(row=row, column=1, value=orig_id)
            ws.cell(row=row, column=2, value=anon_id)
            ws.cell(row=row, column=3, value=orig_nm)
            ws.cell(row=row, column=4, value=anon_nm if orig_nm else "")
            row += 1
        row += 2

    for col_letter, w in [("A",18),("B",14),("C",30),("D",14)]:
        ws.column_dimensions[col_letter].width = w


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main():
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = input("請輸入 aggregated 資料夾路徑（step2 輸出的那個）：\n> ").strip()

    src = Path(folder)
    if not src.exists():
        print(f"❌ 找不到資料夾：{folder}")
        input("按 Enter 結束..."); return

    out_path = src.parent / "商業分析報表_去識別化版.xlsx"
    print(f"\n📂 來源：{src}")
    print(f"📊 輸出：{out_path}\n{'='*50}")
    print(f"🔑 Seed={ANON_SEED}  金額縮放={MONEY_SCALE:.4f}  日期平移={DATE_SHIFT_M:+d}個月")

    # ── 載入 step3 報表模組 ───────────────────────────────
    print("\n🔧 載入報表模組（step3_analyze.py）...")
    try:
        s3 = _import_step3()
    except Exception as e:
        print(f"❌ 無法載入 step3_analyze.py：{e}")
        input("按 Enter 結束..."); return

    # ── 讀取聚合資料 ──────────────────────────────────────
    def load(fname):
        p = src / fname
        if not p.exists(): return pd.DataFrame()
        return pd.read_csv(p, encoding="utf-8-sig")

    monthly   = load("monthly.csv")
    cust_agg  = load("cust_agg.csv")
    prod_agg  = load("prod_agg.csv")
    fact_agg  = load("fact_agg.csv")
    stock_agg = load("stock_agg.csv")

    # 數值欄位轉型
    for df, cols in [
        (monthly,  ["銷售額","採購額","毛利","毛利率","差額","銷售額_明細"]),
        (cust_agg, ["銷售額","訂單數","平均客單價","交易月數"]),
        (prod_agg, ["銷售額","成本","毛利","毛利率","銷售數量"]),
        (stock_agg,["qty","safeqty","庫存價值"]),
    ]:
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # ── 建立識別碼對照表 ──────────────────────────────────
    print("\n🔒 建立識別碼遮罩...")
    col_maps = build_id_maps(cust_agg, prod_agg, fact_agg)
    print(f"   客戶：{len(col_maps.get('cusno', {}))} 筆")
    print(f"   產品：{len(col_maps.get('prdno', {}))} 筆")
    print(f"   供應商：{len(col_maps.get('facno', {}))} 筆")

    # ── 套用遮罩 ──────────────────────────────────────────
    print("🔒 套用編號遮罩...")
    anon_cust  = _apply(cust_agg,  col_maps)
    anon_prod  = _apply(prod_agg,  col_maps)
    anon_fact  = _apply(fact_agg,  col_maps)
    anon_stock = _apply(stock_agg, col_maps)

    # ── 金額縮放 ──────────────────────────────────────────
    print("💰 縮放金額欄位...")
    anon_monthly  = scale_money(monthly,   "monthly")
    anon_cust     = scale_money(anon_cust, "cust_agg")
    anon_prod     = scale_money(anon_prod, "prod_agg")
    anon_fact     = scale_money(anon_fact, "fact_agg")
    anon_stock    = scale_money(anon_stock,"stock_agg")

    # ── 日期平移 ──────────────────────────────────────────
    print("📅 平移日期欄位...")
    anon_monthly = shift_dates(anon_monthly, "monthly")
    anon_cust    = shift_dates(anon_cust,    "cust_agg")
    anon_fact    = shift_dates(anon_fact,    "fact_agg")

    # ── RFM 分析 ──────────────────────────────────────────
    print("🔍 RFM 分析...")
    rfm_df = s3.rfm_analysis(anon_cust)

    # ── 產生報表 ──────────────────────────────────────────
    print("📊 建立報表...")
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)

    s3.sheet_charts(wb, anon_monthly, anon_cust, anon_prod)
    s3.sheet_summary(wb, anon_monthly, anon_cust, anon_prod, anon_stock)
    s3.sheet_rfm(wb, rfm_df)
    s3.sheet_pareto(wb, anon_prod, anon_cust)
    s3.sheet_gross_margin(wb, anon_prod)
    s3.sheet_inventory_alert(wb, anon_stock)
    _add_mapping_sheet(wb, col_maps, cust_agg, prod_agg, fact_agg)

    wb.save(out_path)
    print(f"\n✅ 去識別化報表完成：{out_path}")
    print("\n📋 包含頁籤：")
    for ws in wb.worksheets:
        print(f"   {ws.title}")
    print("\n⚠️  對外分享前，請先刪除「🔑 對照表（機密）」頁籤！")
    input("\n按 Enter 結束...")


if __name__ == "__main__":
    main()
