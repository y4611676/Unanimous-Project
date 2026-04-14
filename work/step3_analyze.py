"""
步驟三：數據分析 → Excel 報表
- 讀取 aggregated/ 的聚合資料
- 進行 RFM、帕累托、趨勢、庫存預警等分析
- 輸出完整 Excel 報表
"""

import os, sys
import pandas as pd
import numpy as np
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, Reference

# ── 顏色 ──────────────────────────────────────────────────
DARK_BLUE  = "1F3864"
MED_BLUE   = "2E75B6"
LIGHT_BLUE = "BDD7EE"
GREEN      = "375623"
GREEN_SOFT = "70AD47"
RED        = "C00000"
ORANGE     = "ED7D31"
GRAY       = "F2F2F2"
WHITE      = "FFFFFF"
BLACK      = "000000"

# ── 樣式工具 ──────────────────────────────────────────────

def hdr(ws, row, col, val, bg=DARK_BLUE, fg=WHITE, bold=True, sz=10):
    c = ws.cell(row=row, column=col, value=val)
    c.font = Font(name="Arial", bold=bold, color=fg, size=sz)
    c.fill = PatternFill("solid", fgColor=bg)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    return c

def cel(ws, row, col, val, fmt=None, bold=False, fg=BLACK, bg=None, align="right"):
    c = ws.cell(row=row, column=col, value=val)
    c.font = Font(name="Arial", bold=bold, color=fg, size=10)
    c.alignment = Alignment(horizontal=align, vertical="center")
    if fmt: c.number_format = fmt
    if bg: c.fill = PatternFill("solid", fgColor=bg)
    return c

def border(ws, r1, r2, c1, c2):
    thin = Side(style="thin", color="BFBFBF")
    for row in ws.iter_rows(min_row=r1, max_row=r2, min_col=c1, max_col=c2):
        for c in row:
            c.border = Border(left=thin, right=thin, top=thin, bottom=thin)

def title(ws, row, col, text, span, bg=MED_BLUE, sz=11):
    c = ws.cell(row=row, column=col, value=text)
    c.font = Font(name="Arial", bold=True, color=WHITE, size=sz)
    c.fill = PatternFill("solid", fgColor=bg)
    c.alignment = Alignment(horizontal="left", vertical="center")
    if span > 1:
        ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col+span-1)
    ws.row_dimensions[row].height = 22

def page_title(ws, text, cols):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=cols)
    c = ws["A1"]
    c.value = text
    c.font = Font(name="Arial", bold=True, size=14, color=WHITE)
    c.fill = PatternFill("solid", fgColor=DARK_BLUE)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36
    ws.sheet_view.showGridLines = False

def load(folder, fname):
    p = Path(folder) / fname
    if not p.exists(): return pd.DataFrame()
    return pd.read_csv(p, encoding="utf-8-sig")

def widths(ws, d):
    for col, w in d.items():
        ws.column_dimensions[col].width = w

# ══════════════════════════════════════════════════════════
# 分析函式
# ══════════════════════════════════════════════════════════

def rfm_analysis(cust_agg):
    """RFM 客戶分群"""
    if cust_agg.empty: return pd.DataFrame()
    df = cust_agg.copy()
    df["最近交易"] = pd.to_datetime(df["最近交易"], errors="coerce")
    ref_date = df["最近交易"].max()
    df["R_days"] = (ref_date - df["最近交易"]).dt.days
    df["F"] = df["訂單數"]
    df["M"] = df["銷售額"]

    for col, label in [("R_days","R_score"),("F","F_score"),("M","M_score")]:
        try:
            df[label] = pd.qcut(df[col], q=4, labels=[4,3,2,1] if col=="R_days" else [1,2,3,4], duplicates="drop")
        except:
            df[label] = 2
    df["RFM_score"] = df["R_score"].astype(str) + df["F_score"].astype(str) + df["M_score"].astype(str)

    def segment(row):
        r,f,m = int(str(row["R_score"])), int(str(row["F_score"])), int(str(row["M_score"]))
        if r >= 3 and f >= 3 and m >= 3: return "💎 高價值客戶"
        if r >= 3 and f >= 3:            return "🌟 忠實客戶"
        if r <= 2 and f >= 3:            return "😴 沉睡客戶"
        if r >= 3 and m >= 3:            return "💰 高消費新客"
        if r <= 2 and f <= 2:            return "⚠️  流失風險"
        return "📊 一般客戶"

    df["客戶分群"] = df.apply(segment, axis=1)
    return df

def pareto_analysis(df, value_col, name_col):
    """帕累托 80/20 分析"""
    df = df.sort_values(value_col, ascending=False).copy()
    total = df[value_col].sum()
    df["佔比"] = df[value_col] / total
    df["累計佔比"] = df["佔比"].cumsum()
    df["帕累托"] = df["累計佔比"].apply(lambda x: "前80%" if x <= 0.8 else "後20%")
    return df

# ══════════════════════════════════════════════════════════
# 報表頁面
# ══════════════════════════════════════════════════════════

def sheet_summary(wb, monthly, cust_agg, prod_agg, stock_agg):
    ws = wb.create_sheet("📊 經營總覽")
    page_title(ws, "經營總覽 Business Summary", 8)

    monthly = monthly.fillna(0)
    total_sale = monthly["銷售額"].sum() if "銷售額" in monthly.columns else 0
    total_purc = monthly["採購額"].sum() if "採購額" in monthly.columns else 0
    total_gp   = monthly["毛利"].sum()   if "毛利"   in monthly.columns else 0
    gp_rate    = total_gp / total_sale   if total_sale else 0
    cust_cnt   = len(cust_agg)
    prod_cnt   = len(prod_agg)

    kpis = [
        ("總銷售額",  total_sale, "#,##0",  MED_BLUE),
        ("總採購額",  total_purc, "#,##0",  DARK_BLUE),
        ("總毛利",    total_gp,   "#,##0",  GREEN if total_gp >= 0 else RED),
        ("平均毛利率",gp_rate,    "0.0%",   GREEN_SOFT),
        ("活躍客戶數",cust_cnt,   "#,##0",  ORANGE),
        ("銷售品項數",prod_cnt,   "#,##0",  "7030A0"),
    ]

    for i, (label, value, fmt, color) in enumerate(kpis):
        col = (i % 3) * 3 + 1
        row = 3 if i < 3 else 7
        ws.merge_cells(start_row=row,   start_column=col, end_row=row,   end_column=col+1)
        ws.merge_cells(start_row=row+1, start_column=col, end_row=row+2, end_column=col+1)
        lc = ws.cell(row=row,   column=col, value=label)
        lc.font  = Font(name="Arial", size=10, color=WHITE)
        lc.fill  = PatternFill("solid", fgColor=color)
        lc.alignment = Alignment(horizontal="center", vertical="center")
        vc = ws.cell(row=row+1, column=col, value=value)
        vc.font  = Font(name="Arial", bold=True, size=16, color=color)
        vc.fill  = PatternFill("solid", fgColor="F7F7F7")
        vc.alignment = Alignment(horizontal="center", vertical="center")
        vc.number_format = fmt
        ws.row_dimensions[row+1].height = 34

    # 月度趨勢小表
    row = 11
    title(ws, row, 1, "月度趨勢摘要", 7)
    row += 1
    for ci, h in enumerate(["年月","銷售額","採購額","毛利","毛利率","差額","累計銷售"], 1):
        hdr(ws, row, ci, h, bg=MED_BLUE)
    row += 1
    cum = 0
    for i, r in monthly.sort_values("ym").iterrows():
        cum += r.get("銷售額", 0)
        bg = GRAY if i % 2 == 0 else WHITE
        cel(ws, row, 1, r.get("ym",""),        align="center", bg=bg)
        cel(ws, row, 2, r.get("銷售額",0),     "#,##0", bg=bg)
        cel(ws, row, 3, r.get("採購額",0),     "#,##0", bg=bg)
        gp = r.get("毛利",0)
        cel(ws, row, 4, gp,                    "#,##0", fg=(GREEN if gp>=0 else RED), bg=bg)
        mr = r.get("毛利率", np.nan)
        cel(ws, row, 5, mr if pd.notna(mr) else 0, "0.0%", bg=bg)
        cel(ws, row, 6, r.get("差額",0),       "#,##0", bg=bg)
        cel(ws, row, 7, cum,                   "#,##0", bg=bg)
        row += 1
    border(ws, 12, row-1, 1, 7)

    widths(ws, {get_column_letter(i): 14 for i in range(1, 9)})


def sheet_rfm(wb, rfm_df):
    ws = wb.create_sheet("👥 客戶RFM分群")
    page_title(ws, "客戶 RFM 分群分析", 9)
    if rfm_df.empty:
        ws["A2"] = "資料不足"; return

    # 分群統計
    grp_sum = rfm_df.groupby("客戶分群").agg(
        客戶數=("cusno","count"),
        總銷售額=("銷售額","sum"),
        平均銷售額=("銷售額","mean"),
    ).reset_index().sort_values("總銷售額", ascending=False)

    title(ws, 2, 1, "各分群統計", 5)
    for ci, h in enumerate(["分群","客戶數","總銷售額","平均銷售額","佔比"], 1):
        hdr(ws, 3, ci, h)
    total = grp_sum["總銷售額"].sum()
    for i, r in grp_sum.reset_index(drop=True).iterrows():
        row = i + 4
        bg = GRAY if i % 2 == 0 else WHITE
        cel(ws, row, 1, r["客戶分群"],           align="left",   bg=bg)
        cel(ws, row, 2, r["客戶數"],             "#,##0",        bg=bg)
        cel(ws, row, 3, r["總銷售額"],           "#,##0",        bg=bg)
        cel(ws, row, 4, r["平均銷售額"],         "#,##0",        bg=bg)
        cel(ws, row, 5, r["總銷售額"]/total,     "0.0%",         bg=bg)
    border(ws, 3, 3+len(grp_sum), 1, 5)

    # 明細
    row = 4 + len(grp_sum) + 2
    title(ws, row, 1, "客戶明細（依銷售額排序）", 9)
    row += 1
    show_cols = ["cusno","cusnm","客戶分群","訂單數","銷售額","平均客單價","R_days","RFM_score"]
    show_cols = [c for c in show_cols if c in rfm_df.columns]
    hdrs_map  = {"cusno":"客戶編號","cusnm":"客戶名稱","R_days":"距今天數"}
    for ci, c in enumerate(show_cols, 1):
        hdr(ws, row, ci, hdrs_map.get(c, c))
    row += 1
    for i, r in rfm_df.sort_values("銷售額", ascending=False).reset_index(drop=True).iterrows():
        bg = GRAY if i % 2 == 0 else WHITE
        for ci, c in enumerate(show_cols, 1):
            v = r.get(c,"")
            fmt = "#,##0" if c in ["銷售額","訂單數","平均客單價","R_days"] else None
            cel(ws, row, ci, v, fmt=fmt, bg=bg, align="left" if c in ["cusno","cusnm","客戶分群","RFM_score"] else "right")
        row += 1
    border(ws, 4+len(grp_sum)+3, row-1, 1, len(show_cols))

    widths(ws, {"A":14,"B":22,"C":16,"D":10,"E":14,"F":14,"G":10,"H":12,"I":12})


def sheet_pareto(wb, prod_agg, cust_agg):
    ws = wb.create_sheet("📐 帕累托分析")
    page_title(ws, "帕累托 80/20 分析", 8)

    # 產品帕累托
    title(ws, 2, 1, "產品銷售帕累托（前80%貢獻的產品）", 8)
    if not prod_agg.empty:
        prd = pareto_analysis(prod_agg.copy(), "銷售額", "prdno")
        hdrs_p = ["排名","產品編號","產品名稱","銷售額","毛利率","佔比","累計佔比","帕累托"]
        for ci, h in enumerate(hdrs_p, 1):
            hdr(ws, 3, ci, h)
        for i, r in prd.reset_index(drop=True).iterrows():
            row = i + 4
            is_top = r["帕累托"] == "前80%"
            bg = "EBF3E8" if is_top else GRAY if i%2==0 else WHITE
            mr = r.get("毛利率", np.nan)
            cel(ws, row, 1, i+1,                       align="center", bg=bg)
            cel(ws, row, 2, r.get("prdno",""),         align="center", bg=bg)
            cel(ws, row, 3, r.get("prdnm",""),         align="left",   bg=bg)
            cel(ws, row, 4, r["銷售額"],               "#,##0",        bg=bg)
            cel(ws, row, 5, mr if pd.notna(mr) else 0,"0.0%",         bg=bg)
            cel(ws, row, 6, r["佔比"],                 "0.0%",         bg=bg)
            cel(ws, row, 7, r["累計佔比"],             "0.0%",         bg=bg)
            cel(ws, row, 8, r["帕累托"],               align="center", bg=bg)
        border(ws, 3, 3+len(prd), 1, 8)
        prd_end = 3 + len(prd) + 2
    else:
        prd_end = 5

    # 客戶帕累托
    title(ws, prd_end, 1, "客戶銷售帕累托", 8)
    if not cust_agg.empty:
        cst = pareto_analysis(cust_agg.copy(), "銷售額", "cusno")
        for ci, h in enumerate(["排名","客戶編號","客戶名稱","銷售額","佔比","累計佔比","帕累托"], 1):
            hdr(ws, prd_end+1, ci, h)
        for i, r in cst.reset_index(drop=True).iterrows():
            row = prd_end + 2 + i
            is_top = r["帕累托"] == "前80%"
            bg = "EBF3E8" if is_top else GRAY if i%2==0 else WHITE
            cel(ws, row, 1, i+1,                      align="center", bg=bg)
            cel(ws, row, 2, r.get("cusno",""),         align="center", bg=bg)
            cel(ws, row, 3, r.get("cusnm",""),         align="left",   bg=bg)
            cel(ws, row, 4, r["銷售額"],               "#,##0",        bg=bg)
            cel(ws, row, 5, r["佔比"],                 "0.0%",         bg=bg)
            cel(ws, row, 6, r["累計佔比"],             "0.0%",         bg=bg)
            cel(ws, row, 7, r["帕累托"],               align="center", bg=bg)
        border(ws, prd_end+1, prd_end+1+len(cst), 1, 7)

    widths(ws, {"A":8,"B":16,"C":26,"D":14,"E":10,"F":10,"G":10,"H":10})


def sheet_inventory_alert(wb, stock_agg):
    ws = wb.create_sheet("🚨 庫存預警")
    page_title(ws, "庫存預警分析", 8)
    if stock_agg.empty:
        ws["A2"] = "資料不足"; return

    # 分類統計
    if "庫存狀態" in stock_agg.columns:
        stat = stock_agg["庫存狀態"].value_counts().reset_index()
        stat.columns = ["狀態","品項數"]
        title(ws, 2, 1, "庫存狀態統計", 3)
        for ci, h in enumerate(["狀態","品項數","百分比"], 1):
            hdr(ws, 3, ci, h)
        total = stat["品項數"].sum()
        for i, r in stat.iterrows():
            row = i + 4
            cel(ws, row, 1, r["狀態"],         align="left")
            cel(ws, row, 2, r["品項數"],        "#,##0")
            cel(ws, row, 3, r["品項數"]/total,  "0.0%")
        border(ws, 3, 3+len(stat), 1, 3)

    # 明細
    row_start = 5 + (len(stock_agg["庫存狀態"].unique()) if "庫存狀態" in stock_agg.columns else 0)
    title(ws, row_start, 1, "庫存明細（低庫存優先）", 8)
    show_cols = [c for c in ["prdno","prdnm","qty","safeqty","庫存狀態","庫存價值","lastin","lastout"] if c in stock_agg.columns]
    hdrs_map  = {"prdno":"產品編號","prdnm":"產品名稱","qty":"現有庫存",
                 "safeqty":"安全庫存","lastin":"最後進貨","lastout":"最後出貨"}
    for ci, c in enumerate(show_cols, 1):
        hdr(ws, row_start+1, ci, hdrs_map.get(c, c))
    for i, r in stock_agg.reset_index(drop=True).iterrows():
        row = row_start + 2 + i
        state = r.get("庫存狀態","")
        bg = "FFCCCC" if "低庫存" in str(state) or "零庫存" in str(state) else (GRAY if i%2==0 else WHITE)
        for ci, c in enumerate(show_cols, 1):
            v = r.get(c,"")
            fmt = "#,##0" if c in ["qty","safeqty","庫存價值"] else None
            cel(ws, row, ci, v, fmt=fmt, bg=bg, align="left" if c in ["prdno","prdnm","庫存狀態"] else "right")
    border(ws, row_start+1, row_start+1+len(stock_agg), 1, len(show_cols))

    widths(ws, {"A":16,"B":28,"C":12,"D":12,"E":14,"F":14,"G":14,"H":14})


def sheet_gross_margin(wb, prod_agg):
    ws = wb.create_sheet("💰 毛利分析")
    page_title(ws, "產品毛利深度分析", 8)
    if prod_agg.empty:
        ws["A2"] = "資料不足"; return

    df = prod_agg.copy()
    df["毛利率"] = pd.to_numeric(df["毛利率"], errors="coerce").fillna(0)

    # 毛利率分布
    bins = [-np.inf, 0, 0.1, 0.2, 0.3, np.inf]
    labels = ["虧損(<0%)", "低(0-10%)", "中(10-20%)", "良(20-30%)", "優(>30%)"]
    df["毛利分級"] = pd.cut(df["毛利率"], bins=bins, labels=labels)
    dist = df.groupby("毛利分級", observed=True).agg(品項數=("prdno","count"), 銷售額=("銷售額","sum")).reset_index()

    title(ws, 2, 1, "毛利率分布", 4)
    for ci, h in enumerate(["毛利分級","品項數","銷售額佔比","建議"], 1):
        hdr(ws, 3, ci, h)
    total_sale = df["銷售額"].sum()
    suggestions = {
        "虧損(<0%)": "🔴 立即檢討定價或停售",
        "低(0-10%)":  "🟠 考慮提價或降低成本",
        "中(10-20%)": "🟡 持續監控",
        "良(20-30%)": "🟢 維持現狀",
        "優(>30%)":   "💎 重點推廣",
    }
    for i, r in dist.iterrows():
        row = i + 4
        bg = GRAY if i % 2 == 0 else WHITE
        cel(ws, row, 1, str(r["毛利分級"]),                    align="left",   bg=bg)
        cel(ws, row, 2, r["品項數"],                           "#,##0",        bg=bg)
        cel(ws, row, 3, r["銷售額"]/total_sale if total_sale else 0, "0.0%", bg=bg)
        cel(ws, row, 4, suggestions.get(str(r["毛利分級"]),""), align="left",  bg=bg)
    border(ws, 3, 3+len(dist), 1, 4)

    # 高/低毛利產品明細
    row = 5 + len(dist) + 1
    for label, subset in [("🔴 低毛利產品（<10%，需關注）", df[df["毛利率"] < 0.1].sort_values("銷售額", ascending=False).head(20)),
                          ("💎 高毛利產品（>30%，重點推廣）", df[df["毛利率"] > 0.3].sort_values("銷售額", ascending=False).head(20))]:
        title(ws, row, 1, label, 6)
        row += 1
        for ci, h in enumerate(["產品編號","產品名稱","銷售額","成本","毛利","毛利率"], 1):
            hdr(ws, row, ci, h)
        row += 1
        for i, r in subset.reset_index(drop=True).iterrows():
            bg = GRAY if i % 2 == 0 else WHITE
            cel(ws, row, 1, r.get("prdno",""),    align="center", bg=bg)
            cel(ws, row, 2, r.get("prdnm",""),    align="left",   bg=bg)
            cel(ws, row, 3, r["銷售額"],          "#,##0",        bg=bg)
            cel(ws, row, 4, r["成本"],            "#,##0",        bg=bg)
            cel(ws, row, 5, r["毛利"],            "#,##0", fg=(GREEN if r["毛利"]>=0 else RED), bg=bg)
            cel(ws, row, 6, r["毛利率"],          "0.0%",  fg=(GREEN_SOFT if r["毛利率"]>=0.2 else RED), bg=bg)
            row += 1
        border(ws, row - len(subset) - 1, row-1, 1, 6)
        row += 2

    widths(ws, {"A":16,"B":28,"C":14,"D":14,"E":14,"F":12})



# ══════════════════════════════════════════════════════════
# 給公司看的三張重點圖
# ══════════════════════════════════════════════════════════

def sheet_charts(wb, monthly, cust_agg, prod_agg):
    """獨立一頁：月營收趨勢 + TOP客戶 + TOP產品，給公司簡報用"""
    from openpyxl.chart import BarChart, LineChart, Reference
    from openpyxl.chart.series import DataPoint
    from openpyxl.utils import get_column_letter

    ws = wb.create_sheet("📈 重點圖表")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:P1")
    c = ws["A1"]
    c.value = "銷售數據重點圖表"
    c.font = Font(name="Arial", bold=True, size=16, color=WHITE)
    c.fill = PatternFill("solid", fgColor=DARK_BLUE)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 40

    # ── 圖1：月營收趨勢折線圖 ─────────────────────────────
    # 把 monthly 資料寫到隱藏區（右側遠處）
    monthly_s = monthly.sort_values("ym").reset_index(drop=True) if not monthly.empty else pd.DataFrame()
    data_col_start = 20  # 從第20欄開始放資料，不影響畫面

    if not monthly_s.empty and "銷售額" in monthly_s.columns:
        # 寫標題
        ws.cell(row=2, column=data_col_start, value="年月")
        ws.cell(row=2, column=data_col_start+1, value="銷售額")
        ws.cell(row=2, column=data_col_start+2, value="採購額")
        for i, r in monthly_s.iterrows():
            ws.cell(row=i+3, column=data_col_start,   value=str(r.get("ym","")))
            ws.cell(row=i+3, column=data_col_start+1, value=float(r.get("銷售額",0)))
            ws.cell(row=i+3, column=data_col_start+2, value=float(r.get("採購額",0)))
        n = len(monthly_s)

        chart1 = LineChart()
        chart1.title = "月營收趨勢"
        chart1.style = 10
        chart1.height = 14
        chart1.width  = 26
        chart1.y_axis.title = "金額"
        chart1.x_axis.title = "年月"

        data_ref = Reference(ws, min_col=data_col_start+1, max_col=data_col_start+2,
                             min_row=2, max_row=2+n)
        chart1.add_data(data_ref, titles_from_data=True)
        cats = Reference(ws, min_col=data_col_start, min_row=3, max_row=2+n)
        chart1.set_categories(cats)

        # 線條顏色
        chart1.series[0].graphicalProperties.line.solidFill = "2E75B6"
        chart1.series[0].graphicalProperties.line.width = 20000
        if len(chart1.series) > 1:
            chart1.series[1].graphicalProperties.line.solidFill = "ED7D31"
            chart1.series[1].graphicalProperties.line.width = 20000

        ws.add_chart(chart1, "A3")

    # ── 圖2：TOP 10 客戶橫向長條圖 ───────────────────────
    top_cust = cust_agg.sort_values("銷售額", ascending=False).head(10).reset_index(drop=True) if not cust_agg.empty else pd.DataFrame()
    data_col2 = data_col_start + 5

    if not top_cust.empty:
        ws.cell(row=2, column=data_col2,   value="客戶")
        ws.cell(row=2, column=data_col2+1, value="銷售額")
        name_col = "cusnm" if "cusnm" in top_cust.columns else "cusno"
        for i, r in top_cust.iterrows():
            ws.cell(row=i+3, column=data_col2,   value=str(r.get(name_col, r.get("cusno","")))[:12])
            ws.cell(row=i+3, column=data_col2+1, value=float(r.get("銷售額",0)))
        n2 = len(top_cust)

        chart2 = BarChart()
        chart2.type   = "bar"   # 橫向
        chart2.style  = 10
        chart2.title  = "TOP 10 客戶銷售額"
        chart2.height = 14
        chart2.width  = 20
        chart2.y_axis.title = "客戶"
        chart2.x_axis.title = "銷售額"

        data_ref2 = Reference(ws, min_col=data_col2+1, max_col=data_col2+1,
                              min_row=2, max_row=2+n2)
        chart2.add_data(data_ref2, titles_from_data=True)
        cats2 = Reference(ws, min_col=data_col2, min_row=3, max_row=2+n2)
        chart2.set_categories(cats2)
        chart2.series[0].graphicalProperties.solidFill = "2E75B6"

        ws.add_chart(chart2, "A22")

    # ── 圖3：TOP 10 產品橫向長條圖 ───────────────────────
    top_prod = prod_agg.sort_values("銷售額", ascending=False).head(10).reset_index(drop=True) if not prod_agg.empty else pd.DataFrame()
    data_col3 = data_col_start + 8

    if not top_prod.empty:
        ws.cell(row=2, column=data_col3,   value="產品")
        ws.cell(row=2, column=data_col3+1, value="銷售額")
        name_col3 = "prdnm" if "prdnm" in top_prod.columns else "prdno"
        for i, r in top_prod.iterrows():
            ws.cell(row=i+3, column=data_col3,   value=str(r.get(name_col3, r.get("prdno","")))[:12])
            ws.cell(row=i+3, column=data_col3+1, value=float(r.get("銷售額",0)))
        n3 = len(top_prod)

        chart3 = BarChart()
        chart3.type   = "bar"
        chart3.style  = 10
        chart3.title  = "TOP 10 產品銷售額"
        chart3.height = 14
        chart3.width  = 20
        chart3.y_axis.title = "產品"
        chart3.x_axis.title = "銷售額"

        data_ref3 = Reference(ws, min_col=data_col3+1, max_col=data_col3+1,
                              min_row=2, max_row=2+n3)
        chart3.add_data(data_ref3, titles_from_data=True)
        cats3 = Reference(ws, min_col=data_col3, min_row=3, max_row=2+n3)
        chart3.set_categories(cats3)
        chart3.series[0].graphicalProperties.solidFill = "70AD47"

        ws.add_chart(chart3, "L22")

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

    out_path = src.parent / "商業分析報表_完整版.xlsx"
    print(f"\n📂 來源：{src}")
    print(f"📊 輸出：{out_path}\n{'='*50}")

    monthly   = load(src, "monthly.csv")
    cust_agg  = load(src, "cust_agg.csv")
    prod_agg  = load(src, "prod_agg.csv")
    fact_agg  = load(src, "fact_agg.csv")
    stock_agg = load(src, "stock_agg.csv")

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

    print("🔍 RFM 分析...")
    rfm_df = rfm_analysis(cust_agg)

    print("📊 建立報表...")
    wb = Workbook()
    wb.remove(wb.active)

    sheet_charts(wb, monthly, cust_agg, prod_agg)
    sheet_summary(wb, monthly, cust_agg, prod_agg, stock_agg)
    sheet_rfm(wb, rfm_df)
    sheet_pareto(wb, prod_agg, cust_agg)
    sheet_gross_margin(wb, prod_agg)
    sheet_inventory_alert(wb, stock_agg)

    wb.save(out_path)
    print(f"\n✅ 報表完成：{out_path}")
    print("\n📋 包含頁籤：")
    for name in [ws.title for ws in wb.worksheets]:
        print(f"   {name}")
    input("\n按 Enter 結束...")

if __name__ == "__main__":
    main()
