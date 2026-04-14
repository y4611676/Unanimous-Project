# -*- coding: utf-8 -*-
"""D. 購物籃 / 交叉銷售：共現商品對 + 簡易關聯指標（support, confidence, lift）。

為了避免引入 mlxtend 依賴，直接枚舉明細中的商品對。
限制：只計「同一張銷貨單內」出現在一起的 Top 商品，僅對前 N 熱銷品計算以控制計算量。
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path
from collections import Counter

import pandas as pd

from ..loaders import DataBundle
from . import AnalysisResult, df_to_html, write_csv


TOP_N_PRODUCTS = 150   # 只看最熱銷的前 N 項，控制組合爆量


def run(data: DataBundle, out_dir: Path) -> AnalysisResult:
    res = AnalysisResult(section_id="basket", title="D. 購物籃 / 交叉銷售")
    s1 = data.sales1.copy()
    if s1.empty:
        res.notes.append("無銷貨明細。")
        return res

    # 熱銷 Top N
    freq = s1.groupby("prdno", as_index=False).agg(
        n=("prdno", "count"),
    ).sort_values("n", ascending=False)
    top = set(freq.head(TOP_N_PRODUCTS)["prdno"])
    s1_top = s1[s1["prdno"].isin(top)]

    # 每張單的商品集合
    baskets = s1_top.groupby("salno")["prdno"].apply(lambda s: sorted(set(s)))
    baskets = baskets[baskets.map(len) >= 2]  # 只留有兩項以上的單

    total_orders = len(baskets)
    if total_orders < 10:
        res.notes.append(f"兩項以上的銷貨單太少（{total_orders}），購物籃分析不具代表性。")
        return res

    # 單品支持度（出現於幾張單）
    single_count: Counter = Counter()
    for items in baskets:
        for x in items:
            single_count[x] += 1

    # 商品對共現
    pair_count: Counter = Counter()
    for items in baskets:
        for a, b in combinations(items, 2):
            pair_count[(a, b)] += 1

    # 商品名對照
    name_map = data.prod.set_index("prdno")["prdnm"].to_dict() if not data.prod.empty else {}

    rows = []
    for (a, b), cnt in pair_count.items():
        support = cnt / total_orders
        conf_a_b = cnt / single_count[a] if single_count[a] else 0
        conf_b_a = cnt / single_count[b] if single_count[b] else 0
        lift = support / ((single_count[a] / total_orders) * (single_count[b] / total_orders)) if single_count[a] and single_count[b] else 0
        rows.append({
            "A": a,
            "A_name": name_map.get(a, ""),
            "B": b,
            "B_name": name_map.get(b, ""),
            "co_occur": cnt,
            "support": support,
            "conf_A→B": conf_a_b,
            "conf_B→A": conf_b_a,
            "lift": lift,
        })
    pairs = pd.DataFrame(rows)
    if pairs.empty:
        res.notes.append("找不到任何商品對。")
        return res

    # 篩選：共現至少 3 次、lift >= 1.5 以過濾雜訊
    sig = pairs[(pairs["co_occur"] >= 3) & (pairs["lift"] >= 1.5)].sort_values(
        ["lift", "co_occur"], ascending=[False, False]
    )

    res.csv_paths.append(write_csv(sig, out_dir, "basket_pairs.csv"))
    res.tables_html["關聯度最高 Top 20 商品對"] = df_to_html(sig.head(20), max_rows=20)
    res.kpis["有效商品對數"] = f"{len(sig):,}"
    res.kpis["納入分析的單據數"] = f"{total_orders:,}"
    res.kpis["分析商品範圍"] = f"Top {TOP_N_PRODUCTS} 熱銷"

    res.notes.append(f"僅對 Top {TOP_N_PRODUCTS} 熱銷品做配對；限定共現 ≥3 次且 lift ≥ 1.5。")
    res.notes.append("lift > 1 代表「A 與 B 同買」高於機率獨立的預期；愈高愈值得搭售。")
    return res
