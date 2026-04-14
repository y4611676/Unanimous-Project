"""Generic 4-stage ETL pipeline runner driven entirely by a YAML config.

Usage::

    python run_pipeline.py path/to/config.yaml
    python run_pipeline.py path/to/config.yaml --only clean,aggregate
    python run_pipeline.py path/to/config.yaml --src /data/raw --out /data/out

Stages: clean → aggregate → analyze → anonymize. Each stage can be skipped
by listing only the stages you want in ``--only``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    print(
        "pyyaml is required. Install with:\n"
        "    pip install pyyaml\n"
        "(or: pip install -r ../requirements.txt from the repo root).",
        file=sys.stderr,
    )
    raise

# Allow running as a script: ``python run_pipeline.py`` from this folder.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.cleaning import run_cleaning  # noqa: E402
from pipeline.aggregation import run_aggregation  # noqa: E402
from pipeline.analysis import run_analysis  # noqa: E402
from pipeline.anonymization import anonymize_tables  # noqa: E402
from pipeline.io_utils import log  # noqa: E402


VALID_STAGES = ("clean", "aggregate", "analyze", "anonymize")


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("config", type=Path, help="Path to YAML config")
    p.add_argument("--src", type=Path, help="Override sources.raw_dir from config")
    p.add_argument("--out", type=Path, help="Override output root from config")
    p.add_argument(
        "--only",
        default=",".join(VALID_STAGES),
        help=f"Comma-separated stages to run (default: all). Choices: {VALID_STAGES}",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = load_config(args.config)
    config_dir = args.config.resolve().parent

    stages = [s.strip() for s in args.only.split(",") if s.strip()]
    for s in stages:
        if s not in VALID_STAGES:
            print(f"Unknown stage: {s}. Valid: {VALID_STAGES}", file=sys.stderr)
            return 2

    paths_cfg = cfg.get("paths", {})

    def resolve(p: str | Path | None) -> Path:
        if p is None:
            return config_dir
        p = Path(p)
        return p if p.is_absolute() else (config_dir / p).resolve()

    raw_dir = args.src or resolve(paths_cfg.get("raw_dir"))
    out_root = args.out or resolve(paths_cfg.get("out_dir", "output"))

    cleaned_dir = out_root / "cleaned"
    aggregated_dir = out_root / "aggregated"
    analyzed_dir = out_root / "analyzed"
    anonymized_dir = out_root / "anonymized"

    log(f"config: {args.config}", level="step")
    log(f"raw:    {raw_dir}")
    log(f"out:    {out_root}")
    log(f"stages: {stages}\n" + "=" * 50)

    cleaned: dict = {}
    aggregated: dict = {}

    if "clean" in stages:
        log("\n[1/4] cleaning", level="step")
        cleaned = run_cleaning(cfg, str(raw_dir), str(cleaned_dir))
    else:
        # Allow resuming from already-cleaned CSVs on disk.
        from pipeline.io_utils import load_csv
        for s in cfg.get("sources", []):
            cleaned[s["name"]] = load_csv(cleaned_dir, s["file"])

    if "aggregate" in stages:
        log("\n[2/4] aggregating", level="step")
        aggregated = run_aggregation(cfg, cleaned, str(aggregated_dir))

    # Both cleaned and aggregated tables are addressable by analysis/anonymization.
    tables = {**cleaned, **aggregated}

    analyzed: dict = {}
    if "analyze" in stages:
        log("\n[3/4] analyzing", level="step")
        analyzed = run_analysis(cfg, tables, str(analyzed_dir))
        tables.update(analyzed)

    if "anonymize" in stages:
        log("\n[4/4] anonymizing", level="step")
        anonymize_tables(cfg, tables, str(anonymized_dir))

    log("\n" + "=" * 50)
    log(f"done. output at: {out_root}", level="ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
