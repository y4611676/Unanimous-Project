# -*- coding: utf-8 -*-
"""
【步驟 2 · 選用】將匯出之 CSV 做去識別：客戶／廠商代碼改匿名編號、姓名與聯絡方式改占位、
內嵌之電話／Email／台灣常見車牌格式以正則替換。

不覆寫原始檔；預設寫入「原資料夾名_anonymized」。

  python anonymize_csvs.py
  python anonymize_csvs.py --in-dir db1_backup_20260414_csv --out-dir my_safe_csv
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

try:
    import pipeline_config as pc

    _DEFAULT_IN = pc.CSV_DIR
    _DEFAULT_OUT = pc.BASE / f"{pc.CSV_DIR.name}_anonymized"
except ImportError:
    _p = Path(__file__).resolve().parent
    _DEFAULT_IN = _p / "db1_backup_20260414_csv"
    _DEFAULT_OUT = _p / "db1_backup_20260414_csv_anonymized"

ENCODINGS = ("utf-8-sig", "utf-8", "big5", "cp950")

# 整欄改為占位（欄名不分大小寫比對）
FULL_MASK_COLUMNS = frozenset(
    {
        "cusnm",
        "cusab",
        "boss",
        "atent",
        "clatent",
        "latent",
        "tel1",
        "tel2",
        "fax",
        "mobil",
        "adrs1",
        "adrs2",
        "adrs3",
        "title",
        "note1",
        "email",
        "web",
        "paynote",
        "birthday",
        "area",
        "unifm",
        "transsubid",
        "tag",
        "s_lab",
        "facnm",
        "facab",
        "anote",
        "memo1",
        "memo",
        "cnew",
        "reno",
        "reindex",
        "busnm",
        "sex",
        "blood",
        "id",
        "wid",
        "lamoney",
        "photo",
        "indate",
        "outdate",
        "dmoney",
        "minprice",
        "tax1",
        "lin_k",
        "cardno",
        "timea",
        "repno",
    }
)


def read_csv(path: Path) -> pd.DataFrame:
    last: Exception | None = None
    for enc in ENCODINGS:
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError as e:
            last = e
            continue
    if last:
        raise last
    raise OSError(path)


def _add_ids(series: pd.Series, bucket: set[str]) -> None:
    for v in series.astype(str).str.strip():
        if v and v.lower() != "nan":
            bucket.add(v)


def build_maps(csv_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    cus_ids: set[str] = set()
    fac_ids: set[str] = set()
    cus_cols = ("cusno", "wcusno", "zcusno")

    for path in sorted(csv_dir.glob("*.csv")):
        try:
            df = read_csv(path)
        except Exception:
            continue
        for col in cus_cols:
            if col in df.columns:
                _add_ids(df[col], cus_ids)
        if "facno" in df.columns:
            _add_ids(df["facno"], fac_ids)

    cus_sorted = sorted(cus_ids)
    fac_sorted = sorted(fac_ids)
    cus_map = {k: f"CUS_{i:05d}" for i, k in enumerate(cus_sorted, start=1)}
    fac_map = {k: f"FAC_{i:05d}" for i, k in enumerate(fac_sorted, start=1)}
    return cus_map, fac_map


# 內嵌敏感資訊（跨欄位掃描）
_RE_EMAIL = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
)
_RE_PHONE = re.compile(
    r"(?:\+886[-\s]?|0)(?:\d{1,3}[-\s]?)?\d{6,10}\b|"
    r"09\d{8}\b|"
    r"\(\d{2,4}\)\s*\d{6,8}\b",
)
# 台灣常見車牌／類車牌英數組合（保守：避免過度誤殺，採較明確型）
_RE_PLATE = re.compile(
    r"(?:"
    r"[A-Z]{3}[-\s]?\d{4}"  # ABC-1234
    r"|\d{4}[-\s]?[A-Z]{2,3}"  # 1234-AB
    r"|[A-Z]{2,3}\d{4}"
    r"|\d{3,4}[A-Z]{2,3}"
    r")",
    re.IGNORECASE,
)
_RE_LONG_DIGIT = re.compile(r"\b\d{8,14}\b")  # 統編、長數字條


def scrub_embedded(text: str) -> str:
    if not text or not str(text).strip():
        return text
    s = str(text)
    s = _RE_EMAIL.sub("[EMAIL]", s)
    s = _RE_PHONE.sub("[電話]", s)
    s = _RE_PLATE.sub("[車牌]", s)
    s = _RE_LONG_DIGIT.sub("[編號]", s)
    return s


def mask_full_value(_: object) -> str:
    return "[已隱蔽]"


# 僅含單號／料號等，避免長數字 regex 誤傷
SKIP_EMBEDDED_SCRUB = frozenset(
    {
        "salno",
        "purno",
        "casno",
        "prdno",
        "prdno2",
        "stockno",
        "bomno",
        "setday",
        "busno",
        "dusno",
        "reno",
        "repno",
        "cardno",
    }
)


def anonymize_dataframe(
    df: pd.DataFrame,
    cus_map: dict[str, str],
    fac_map: dict[str, str],
) -> pd.DataFrame:
    out = df.copy()

    cus_like = {"cusno", "wcusno", "zcusno"}

    for col in out.columns:
        key = col.strip().lower()
        if key in cus_like:
            out[col] = out[col].apply(
                lambda x: (
                    cus_map.get(str(x).strip(), x)
                    if pd.notna(x) and str(x).strip().lower() != "nan"
                    else x
                )
            )
        elif key == "facno":
            out[col] = out[col].apply(
                lambda x: (
                    fac_map.get(str(x).strip(), x)
                    if pd.notna(x) and str(x).strip().lower() != "nan"
                    else x
                )
            )
        elif key in FULL_MASK_COLUMNS or col in FULL_MASK_COLUMNS:

            def _mask_cell(x: object) -> object:
                if pd.isna(x):
                    return x
                if isinstance(x, (int, float)) and not isinstance(x, bool):
                    return mask_full_value(x)
                s = str(x).strip()
                if not s or s.lower() == "nan":
                    return x
                return mask_full_value(x)

            out[col] = out[col].apply(_mask_cell)
        elif key not in SKIP_EMBEDDED_SCRUB and (
            out[col].dtype == object or str(out[col].dtype) == "string"
        ):
            out[col] = out[col].apply(
                lambda x: scrub_embedded(x) if isinstance(x, str) else x
            )

    # 其餘文字欄再掃一次內嵌敏感詞（含未列名之 note 等）
    for col in out.columns:
        key = col.strip().lower()
        if key in cus_like or key == "facno" or key in SKIP_EMBEDDED_SCRUB:
            continue
        if out[col].dtype == object or str(out[col].dtype) == "string":
            out[col] = out[col].apply(
                lambda x: scrub_embedded(x) if isinstance(x, str) else x
            )

    return out


def run(in_dir: Path, out_dir: Path) -> int:
    in_dir = in_dir.resolve()
    out_dir = out_dir.resolve()
    if not in_dir.is_dir():
        print(f"找不到輸入目錄：{in_dir}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)

    print("掃描 cusno / facno 並建立對照…")
    cus_map, fac_map = build_maps(in_dir)
    print(f"  客戶代碼 {len(cus_map)} 筆、廠商代碼 {len(fac_map)} 筆")

    files = sorted(in_dir.glob("*.csv"))
    for i, path in enumerate(files, 1):
        try:
            df = read_csv(path)
        except Exception as e:
            print(f"略過 {path.name}：{e}", file=sys.stderr)
            continue
        anon = anonymize_dataframe(df, cus_map, fac_map)
        dest = out_dir / path.name
        anon.to_csv(dest, index=False, encoding="utf-8-sig")
        if i % 50 == 0 or i == len(files):
            print(f"  已處理 {i}/{len(files)}…")

    print(f"完成：{len(files)} 個檔案 → {out_dir}")
    print("請改用匿名資料夾做分析／分享；原始檔請勿上傳公開環境。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CSV 去識別（客戶／聯絡／車牌等）")
    parser.add_argument("--in-dir", type=Path, default=_DEFAULT_IN, help="來源 CSV 目錄")
    parser.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT, help="輸出目錄")
    args = parser.parse_args()
    return run(args.in_dir, args.out_dir)


if __name__ == "__main__":
    sys.exit(main())
