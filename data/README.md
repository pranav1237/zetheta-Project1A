# Data

## Securitisation project (Project 1A -- current)

Raw data **is committed** under `data/securitisation/raw/` (four small,
project-supplied CSVs, no real customer PII):

- `auto_loan_securitisation_data.csv`
- `dpd_snapshot_history.csv`
- `dynamic_loss_monthly.csv`
- `static_pool_vintage_data.csv`

Run the pipeline to regenerate every derived artifact from these files:

```bash
python -m src.securitisation.run_pipeline
```

Outputs are written to `artifacts/securitisation/` (not committed --
regenerate them any time by re-running the command above).

## Retail credit-scoring project (prior, unrelated -- see docs/retail-credit-scoring/)

That project's raw data is deliberately **not** committed. Run:

```bash
python src/download_data.py
```

which retrieves the Statlog German Credit Data from the UCI Machine Learning
Repository (dataset 144) via `ucimlrepo`.
