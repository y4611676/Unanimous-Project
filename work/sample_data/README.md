# Sample Data

Minimal mock CSVs for running the work/ pipeline end-to-end.

## Usage

```bash
python step1_clean.py sample_data
python step2_aggregate.py sample_data/cleaned
python step3_analyze.py sample_data/aggregated
python step4_anonymize.py sample_data/aggregated
```

## Files

| File | Description |
|------|-------------|
| sale.csv | Sales master (2 orders) |
| sales1.csv | Sales detail lines |
| purc.csv | Purchase master (2 orders) |
| purcs1.csv | Purchase detail lines |
| cust.csv | Customer master |
| fact.csv | Supplier master |
| prod.csv | Product master |
| stockqty.csv | Current stock quantities |
