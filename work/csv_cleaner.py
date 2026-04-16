"""
通用 CSV 清理工具 — 由設定檔驅動
用法: python cleaner.py <config.yaml>

支援模組（在 config.yaml 中按需開啟）:
  drop_duplicates   — 移除重複列
  drop_columns      — 刪除指定欄位
  rename            — 重新命名欄位
  clean_quotes      — 移除欄位值前後多餘的引號
  replace_with_nan  — 把特定文字值替換為空值
  extract_number    — 從含單位字串中抽出數字（e.g. "90 mph" → 90）
  parse_money       — 把金額字串轉成百萬美元浮點數
"""

import re
import sys
import pandas as pd
import yaml


# ── 模組實作 ─────────────────────────────────────────────────────────────────

def module_drop_duplicates(df, cfg):
    if cfg:
        before = len(df)
        df = df.drop_duplicates()
        print(f"     drop_duplicates: 移除 {before - len(df)} 列重複資料")
    return df


def module_drop_columns(df, cfg):
    targets = [c for c in cfg if c in df.columns]
    df = df.drop(columns=targets, errors="ignore")
    print(f"     drop_columns: 刪除 {targets}")
    return df


def module_rename(df, cfg):
    # pandas 讀取無標題第一欄時，欄位名稱為 "Unnamed: 0"；config 可用 "" 或 "Unnamed: 0"
    mapping = {}
    for old, new in cfg.items():
        if old == "" and "Unnamed: 0" in df.columns:
            mapping["Unnamed: 0"] = new
        elif old in df.columns:
            mapping[old] = new
    df = df.rename(columns=mapping)
    print(f"     rename: {mapping}")
    return df


def module_clean_quotes(df, cfg):
    for item in cfg:
        col = item["column"]
        if col not in df.columns:
            continue
        df[col] = df[col].apply(
            lambda x: re.sub(r'^["\']+(.*?)["\'"]+$', r'\1', str(x).strip())
            if not pd.isna(x) else x
        )
        print(f"     clean_quotes: {col}")
    return df


def module_replace_with_nan(df, cfg):
    for col, values in cfg.items():
        if col not in df.columns:
            continue
        str_values = [str(v) for v in values]
        df[col] = df[col].apply(
            lambda x: float("nan") if (not pd.isna(x) and str(x).strip() in str_values) else x
        )
        print(f"     replace_with_nan: {col} ← {values}")
    return df


def module_extract_number(df, cfg):
    for item in cfg:
        col = item["column"]
        if col not in df.columns:
            continue
        pattern = item.get("pattern", r"([\d]+)")

        def extract(val):
            if pd.isna(val):
                return val
            s = str(val).replace(",", "")   # 移除千分位逗號
            m = re.search(pattern, s)
            if m:
                try:
                    return float(m.group(1))
                except (ValueError, IndexError):
                    return float("nan")
            return float("nan")

        df[col] = df[col].apply(extract)
        print(f"     extract_number: {col}（pattern={pattern}）")
    return df


def _parse_single_money(val) -> float:
    """把各種金額字串轉成「百萬美元」浮點數，無法解析回傳 NaN。"""
    if pd.isna(val):
        return float("nan")
    s = str(val).strip()
    # 移除 > ~ ≈ 等前綴
    s = re.sub(r"^[>~≈\s]+", "", s)
    # 移除 $ 符號（包括 $$）
    s = s.lstrip("$").strip()
    # 匹配「數字 [單位]」
    m = re.match(r"^([\d,\.]+)\s*(billion|million|thousand)?", s, re.IGNORECASE)
    if not m:
        return float("nan")
    amount = float(m.group(1).replace(",", ""))
    unit = (m.group(2) or "").lower()
    if unit == "billion":
        return round(amount * 1000, 4)
    elif unit == "million":
        return amount
    elif unit == "thousand":
        return round(amount / 1000, 6)
    else:
        # 純數字，假設是美元，轉成百萬
        return round(amount / 1_000_000, 6)


def module_parse_money(df, cfg):
    for item in cfg:
        col = item["column"]
        if col not in df.columns:
            continue
        df[col] = df[col].apply(_parse_single_money)
        print(f"     parse_money: {col}（單位：百萬美元）")
    return df


# ── 模組執行順序與對應函式 ────────────────────────────────────────────────────

MODULE_ORDER = [
    "drop_duplicates",
    "drop_columns",
    "rename",
    "clean_quotes",
    "replace_with_nan",
    "extract_number",
    "parse_money",
]

MODULE_MAP = {
    "drop_duplicates":  module_drop_duplicates,
    "drop_columns":     module_drop_columns,
    "rename":           module_rename,
    "clean_quotes":     module_clean_quotes,
    "replace_with_nan": module_replace_with_nan,
    "extract_number":   module_extract_number,
    "parse_money":      module_parse_money,
}


# ── 主流程 ────────────────────────────────────────────────────────────────────

def run(config_path: str):
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    input_path  = cfg["input"]
    output_path = cfg.get("output", input_path.replace(".csv", "_clean.csv"))

    df = pd.read_csv(input_path)
    print(f"\n讀入：{input_path}  （{len(df)} 列 × {len(df.columns)} 欄）")
    print(f"欄位：{list(df.columns)}\n")

    for module_name in MODULE_ORDER:
        if module_name not in cfg:
            continue
        fn = MODULE_MAP[module_name]
        df = fn(df, cfg[module_name])

    df.to_csv(output_path, index=False)
    print(f"\n[OK] 輸出：{output_path}  （{len(df)} 列 × {len(df.columns)} 欄）")
    print(f"欄位：{list(df.columns)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python cleaner.py <config.yaml>")
        sys.exit(1)
    run(sys.argv[1])
