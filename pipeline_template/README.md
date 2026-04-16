# Pipeline Template — Generic ETL Engine

A config-driven four-stage ETL template:

```
clean  →  aggregate  →  analyze  →  anonymize  →  Excel report
```

**Motivation**: the four scripts under `work/` (`step1_clean.py` → `step4_anonymize.py`) are a complete, working pipeline — but file names, column names, and business logic are all hard-coded in Python. Swapping in a different dataset would require rewriting 60–70% of the code.

This template pulls everything each stage needs to *know* out into a YAML config. The Python code itself is no longer bound to any specific field name.

---

## Quick start

```bash
pip install -r ../requirements.txt        # needs pandas / numpy / pyyaml / openpyxl
cp config.example.yaml my_config.yaml     # copy and edit to match your columns
python run_pipeline.py my_config.yaml
```

Output lands under the `paths.out_dir` defined in your config, split into four subfolders:

```
out/
├── cleaned/       # stage 1 output (same filenames as raw CSVs, but cleaned)
├── aggregated/    # stage 2 output (one CSV per aggregation)
├── analyzed/      # stage 3 output (RFM, Pareto, Top-N)
└── anonymized/    # stage 4 output (mirrors cleaned/aggregated with masking applied)
```

---

## Running individual stages

```bash
python run_pipeline.py my_config.yaml --only clean,aggregate
python run_pipeline.py my_config.yaml --only analyze   # reads from cleaned/
```

`--src` and `--out` override the paths in the config from the CLI.

---

## Config schema — quick reference

| Section | Purpose | Required |
|---|---|---|
| `paths.raw_dir` / `paths.out_dir` | Input / output folders | One or the other, unless `--src`/`--out` is passed |
| `sources[]` | CSV files + per-column cleaning rules | Required for the `clean` stage |
| `aggregations[]` | Groupby definitions | Required for the `aggregate` stage |
| `analysis.rfm` / `analysis.pareto` / `analysis.top_n` | Analysis settings | Optional |
| `anonymization` | De-identification rules | Optional |

See [`config.example.yaml`](./config.example.yaml) for a fully-commented walkthrough.

---

## Real-world examples

The repo ships two example configs — **the same engine drives both**, only the YAML differs:

### `examples/sales_report/` — Business analytics report
A YAML description of every CSV, column, gross-margin calculation, RFM, Pareto, and de-identification rule that was hard-coded in `work/step1`–`step4`, plus a 7-sheet Excel export.

```bash
cd examples/sales_report
python ../../run_pipeline.py config.yaml --src /path/to/raw_csvs
```

### `examples/telco_churn/` — Telecom customer churn
The same engine run against the IBM Telco Customer Churn dataset, producing churn-rate segmentation (Contract / Payment / Internet), a high-value-customer 80/20 Pareto, and a top-50 at-risk spenders list — delivered as a formatted Excel workbook.

```bash
cd examples/telco_churn
# drop Telco-Customer-Churn.csv next to config.yaml, then:
python ../../run_pipeline.py config.yaml
```

The two schemas are entirely different (retail sales vs. telecom), yet the same pipeline code runs on both — which is the proof that the abstraction is genuinely generic.

---

## Design principles

1. **The code doesn't know what your columns are called** — every field name is injected via config. The engine only operates on abstractions like "how many columns", "what to group by", "which columns are monetary"
2. **Missing data doesn't crash the pipeline** — missing CSV, missing column, missing metric all generate a warning and are skipped, matching the `if not df.empty` defensive style in the original `work/step1`
3. **Stages run independently** — each stage reads the previous stage's CSVs, so you don't need to run the whole pipeline end-to-end
4. **De-identification is opt-in** — remove the `anonymization:` block from the config and the stage is skipped entirely

---

## Folder structure

```
pipeline_template/
├── README.md                  # this file
├── config.example.yaml        # blank-slate starter template
├── run_pipeline.py            # CLI entry point
├── pipeline/
│   ├── __init__.py
│   ├── io_utils.py            # load_csv / save_csv / log / resolve_folder
│   ├── cleaning.py            # run_cleaning — clean stage
│   ├── aggregation.py         # run_aggregation — aggregate stage
│   ├── analysis.py            # run_analysis — RFM / Pareto / Top-N
│   ├── anonymization.py       # anonymize_tables — de-identification
│   └── excel_writer.py        # optional formatted xlsx report
└── examples/
    ├── sales_report/
    │   └── config.yaml        # reproduces the full work/ scenario via config
    └── telco_churn/
        └── config.yaml        # same engine on IBM Telco Churn dataset
```

---

## Excel output

Adding an `output.excel` block to the config produces a fully formatted xlsx report (coloured headers, borders, frozen panes, auto-sized columns, currency / percent formatting):

```yaml
output:
  excel:
    enabled: true
    filename: report.xlsx
    source: aggregated
    sheets:
      - {from: monthly, title: Monthly Revenue, number_cols: [revenue]}
      - {from: rfm, stage: analyzed, title: RFM Scores}
      - {from: customer_agg, title: Customer Ranking, percent_cols: [share, cum_share]}
```

Each sheet's `from` points to a table produced by one of the pipeline stages. `stage` defaults to the top-level `source` but can be overridden per-sheet (e.g. analysis outputs live under `analyzed/`).

## Tests

```bash
cd pipeline_template
pip install pytest
pytest tests/ -v
```

Five test files, ~20 cases covering: cleaning, aggregation (including the YAML 1.1 `on:` → `True` quirk), RFM / Pareto / Top-N, de-identification determinism and cross-table consistency, and Excel output.

## Possible extensions

- Additional example configs under `examples/` (e.g. `examples/bike_share/`) to turn the repo into a multi-scenario template library
- Add charts (`BarChart` / `LineChart`) to the Excel output — `openpyxl.chart` is already available; hook them into `excel_writer.py`'s `_write_sheet`
- Swap `io_utils.load_csv` for a DuckDB-backed loader (already listed in `requirements.txt`) if data volume outgrows pandas — the interface stays the same
