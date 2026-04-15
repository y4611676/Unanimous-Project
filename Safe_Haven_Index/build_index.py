"""CLI entry point — compute all indicators, save a wide table + default ranking.

Usage::

    python build_index.py                # offline: use shipped snapshot
    python build_index.py --live         # hit World Bank API, cache to data/raw/
    python build_index.py --live --out custom.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.indicators import INDICATOR_FUNCS, INDICATOR_LABELS, build_all
from src.scoring import compute_index


ROOT = Path(__file__).resolve().parent


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true",
                   help="Fetch fresh data from World Bank API (default: use snapshot)")
    p.add_argument("--out", default=str(ROOT / "data" / "safe_haven_index.csv"),
                   help="Where to save the computed ranking")
    args = p.parse_args(argv)

    print("▶ computing indicators...")
    wide = build_all(live=args.live)
    print(f"  {len(wide)} countries, {len(INDICATOR_FUNCS)} indicators\n")

    print("▶ per-indicator coverage:")
    for col in INDICATOR_FUNCS:
        pct = wide[col].notna().mean() * 100 if col in wide else 0
        print(f"  {col:<26} {INDICATOR_LABELS[col]:<10} {pct:5.1f}%")

    ranked = compute_index(wide)  # default equal weights

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ranked.to_csv(out, index=False)
    print(f"\n✅ saved to {out}")

    print("\n=== Top 10 (equal weights) ===")
    print(
        ranked.head(10)[["rank", "country", "safe_haven_score"] + list(INDICATOR_FUNCS)]
        .to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
