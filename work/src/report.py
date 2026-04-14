# -*- coding: utf-8 -*-
"""HTML 報告產生器：把所有 AnalysisResult 組成一份 self-contained 的 report.html。

特色：
- 圖表以 base64 data URI 內嵌，雙擊 HTML 即可離線瀏覽
- KPI 卡片區塊 + 章節導覽列
- 淺色風格，中文字型
"""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from .analyses import AnalysisResult

STYLE = """
body { font-family: "Microsoft JhengHei", "Microsoft YaHei", "Noto Sans CJK TC", sans-serif;
       margin: 0; padding: 0; background: #f6f7f9; color: #222; }
header { background: #1f3a5f; color: white; padding: 20px 32px; }
header h1 { margin: 0; font-size: 26px; }
header p { margin: 6px 0 0; opacity: 0.85; font-size: 14px; }
nav { background: #2b4e7f; padding: 10px 32px; position: sticky; top: 0; z-index: 10;
      box-shadow: 0 2px 6px rgba(0,0,0,0.15); }
nav a { color: #e4ecf5; text-decoration: none; margin-right: 18px; font-size: 14px; font-weight: 500; }
nav a:hover { color: #ffd36e; }
main { padding: 24px 32px 60px; max-width: 1280px; margin: 0 auto; }
section { background: white; border-radius: 8px; padding: 24px 28px; margin-bottom: 28px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
section h2 { margin-top: 0; color: #1f3a5f; border-left: 5px solid #1f3a5f; padding-left: 12px; }
h3 { color: #2b4e7f; margin-top: 28px; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 14px; margin: 16px 0 8px; }
.kpi-card { background: linear-gradient(135deg, #f0f5fc 0%, #d9e5f4 100%);
            border-left: 4px solid #2b4e7f; padding: 14px 16px; border-radius: 6px; }
.kpi-card .label { font-size: 12px; color: #555; }
.kpi-card .value { font-size: 22px; font-weight: 700; color: #1f3a5f; margin-top: 4px; }
img.chart { max-width: 100%; height: auto; border: 1px solid #e4e8ee; border-radius: 4px;
            margin: 12px 0; }
table.data { border-collapse: collapse; font-size: 13px; width: 100%; margin: 8px 0 16px; }
table.data th { background: #eef2f7; text-align: left; padding: 8px 10px;
                border-bottom: 2px solid #cfd8e3; }
table.data td { padding: 6px 10px; border-bottom: 1px solid #eef2f7; }
table.data tr:hover { background: #fafbfd; }
.notes { background: #fff8e1; border-left: 4px solid #e6b517; padding: 10px 14px;
         font-size: 13px; color: #5a4b10; border-radius: 4px; margin-top: 12px; }
.notes ul { margin: 6px 0; padding-left: 20px; }
.empty { color: #999; font-style: italic; }
.more { font-size: 12px; color: #888; margin: -6px 0 10px; }
.meta { color: #666; font-size: 13px; }
.toc-pill { display: inline-block; background: #eef2f7; padding: 3px 10px; border-radius: 12px;
            font-size: 12px; color: #444; margin: 2px 4px 2px 0; }
"""


def _kpi_html(kpis: dict[str, str]) -> str:
    if not kpis:
        return ""
    cards = "".join(
        f'<div class="kpi-card"><div class="label">{escape(k)}</div>'
        f'<div class="value">{escape(str(v))}</div></div>'
        for k, v in kpis.items()
    )
    return f'<div class="kpi-grid">{cards}</div>'


def _section_html(r: AnalysisResult) -> str:
    parts = [f'<section id="{escape(r.section_id)}">',
             f'<h2>{escape(r.title)}</h2>']
    parts.append(_kpi_html(r.kpis))

    for name, b64 in r.images_b64.items():
        parts.append(f'<img class="chart" src="{b64}" alt="{escape(name)}"/>')

    for name, tbl in r.tables_html.items():
        parts.append(f'<h3>{escape(name)}</h3>')
        parts.append(tbl)

    if r.csv_paths:
        links = "".join(
            f'<a class="toc-pill" href="{escape(p.name)}">⬇ {escape(p.name)}</a>'
            for p in r.csv_paths
        )
        parts.append(f'<p><strong>下載明細：</strong> {links}</p>')

    if r.notes:
        lis = "".join(f"<li>{escape(n)}</li>" for n in r.notes)
        parts.append(f'<div class="notes"><strong>方法說明</strong><ul>{lis}</ul></div>')

    parts.append("</section>")
    return "\n".join(parts)


def build_report(results: list[AnalysisResult], out_dir: Path, title: str = "商業分析綜合報告") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 總 KPI 牆（彙整各章節關鍵卡片）
    headline: dict[str, str] = {}
    for r in results:
        # 每章節最多挑 2 張放到 header
        for k, v in list(r.kpis.items())[:2]:
            headline[f"{r.title[:4]}｜{k}"] = v

    nav = " ".join(
        f'<a href="#{escape(r.section_id)}">{escape(r.title)}</a>' for r in results
    )

    body = "\n".join(_section_html(r) for r in results)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>{escape(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<header>
  <h1>{escape(title)}</h1>
  <p class="meta">產生時間：{escape(now)}　｜　共 {len(results)} 個分析章節</p>
</header>
<nav>{nav}</nav>
<main>
<section id="overview">
  <h2>總覽</h2>
  <p class="meta">下表彙整各章節最關鍵的 2 個指標，完整 KPI 請見各章節。</p>
  {_kpi_html(headline)}
</section>
{body}
</main>
</body>
</html>
"""
    path = out_dir / "report.html"
    path.write_text(html, encoding="utf-8")
    return path
