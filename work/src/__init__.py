# -*- coding: utf-8 -*-
"""work.src — 商業分析模組。

設計原則：
- 每個 analyses/*.py 暴露一個 run(data, out_dir) -> AnalysisResult
- 共用 loaders / enrich / charting，避免重複程式碼
- HTML 報告由 report.py 收集所有 AnalysisResult 組裝
"""
