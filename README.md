# Zetheta WorkBridge -- Project 1A: Data Analyst Securitisation

**Project type:** BFSI / Structured Credit / Securitisation Analytics
**Primary objective:** Build an auditable, real-data-driven securitisation
risk assessment platform: IFRS 9 ECL modelling, a note-tranche cashflow
waterfall, multi-scenario stress testing, investor reporting, a Power BI
semantic model with complex DAX, and a gamified risk-arena simulator
analysing real securitisation crises through a data-analytics lens.

> This repository also contains an earlier, unrelated Zetheta project
> (retail credit-risk decisioning on the UCI German Credit dataset), now
> relocated to `docs/retail-credit-scoring/` so it doesn't get confused with
> this submission. **If you are grading/reviewing Project 1A specifically,
> everything relevant is under `src/securitisation/`, `powerbi/`,
> `risk_arena/`, and `docs/securitisation/`.**

## Executive summary

This project treats a securitised auto-loan pool as a full analytics
pipeline, not a single model: real loan-level data goes in, and IFRS 9 ECL,
tranche cashflows, stress results, and investor-facing reports come out --
all reconciled to the same underlying exposure figure end to end.

The pipeline:

1. Loads four real source datasets: a 500-loan static snapshot, a ~6,000-row
   monthly DPD-bucket panel, a 12-month pool-level performance history, and a
   15-vintage cumulative loss-curve panel.
2. Computes loan-level IFRS 9 ECL using a **vintage-curve-derived lifetime PD
   term structure** for Stage 2/3 (not a flat multiplier), probability
   -weighted across base/downside/severe scenarios.
3. Runs a sequential-pay Class A/B/C waterfall against the pool's **actual**
   monthly collections, net losses and prepayments.
4. Stress-tests both the ECL and the waterfall across three scenarios, and
   reports whether the subordinate tranche survives each one.
5. Produces a five-table investor reporting pack (stage, state, servicer,
   monthly trend, vintage curve), all reconciling to the same total exposure.
6. Ships a Power BI star-schema design and a DAX measure library covering
   time intelligence, roll-rate transition matrices, `RANKX`/`ALLEXCEPT`
   patterns, and a disconnected what-if scenario table.
7. Ships an interactive, browser-based gamified risk-arena simulator with
   real-crisis presets (2008-GFC-style, COVID-19-style).

**Important limitation:** every number in this repository is a project-level
analytical exercise on data supplied for this assignment. It is not a
production model, not a regulator-reviewed IFRS 9 implementation, and not a
reconstruction of any specific real transaction's legal terms -- this is
stated explicitly (not buried) in every methodology doc under
`docs/securitisation/`.

## Data source

Four CSVs supplied for this project, committed under
`data/securitisation/raw/` (small, non-PII, project-supplied synthetic-but-
realistic data -- see `data/README.md`):

| File | Rows | Grain |
|---|---|---|
| `auto_loan_securitisation_data.csv` | 500 | 1 row per loan |
| `dpd_snapshot_history.csv` | ~6,000 | 1 row per loan per monthly snapshot |
| `dynamic_loss_monthly.csv` | 12 | 1 row per reporting month (pool level) |
| `static_pool_vintage_data.csv` | 376 | 1 row per vintage per month-on-book |

## Architecture

```text
Real project data (4 CSVs)
      |
      v
data_loader.py  (typed, parsed loaders -- everything downstream reads these)
      |
      +--------------------+--------------------+
      v                    v                     v
   ecl.py              waterfall.py        investor_reporting.py
   (lifetime PD from   (sequential-pay      (stage / state / servicer /
    vintage hazard      Class A/B/C on       trend / vintage-curve
    curve, 3-scenario    real monthly         summary tables)
    weighting)           collections)
      |                    |                     |
      +--------------------+---------------------+
                           v
                   stress_testing.py
              (ECL + waterfall re-run under
               3 macro scenarios)
                           |
                           v
                    run_pipeline.py
           (writes every artifact to artifacts/securitisation/)
                           |
                           v
        powerbi/ (star schema + DAX)  +  risk_arena/index.html
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.securitisation.run_pipeline
```

This writes every CSV/JSON artifact to `artifacts/securitisation/`, including
the exact files the Power BI model imports (see `powerbi/data_model.md`).

Run the test suite:

```bash
pytest tests/test_securitisation.py -v
```

Open the risk arena simulator directly in a browser (no server needed):

```
risk_arena/index.html
```

Build the Power BI report:

1. Run the pipeline above so `artifacts/securitisation/*.csv` exist.
2. In Power BI Desktop, **Get Data > Text/CSV** for each file listed in
   `powerbi/data_model.md`, and set up the relationships described there.
3. Paste the measures in `powerbi/dax_measures.dax` into a new blank query /
   modelling tab, one at a time (or via Tabular Editor's "Advanced Scripting"
   if available), using `New Measure` for each `Name := Expression` pair.

## Repository map

```text
src/securitisation/          Data loading, ECL, waterfall, stress testing, investor reporting, pipeline
data/securitisation/raw/     The four source CSVs supplied for this project
artifacts/securitisation/    Generated outputs (created by run_pipeline.py)
powerbi/                     Star-schema design (data_model.md) + DAX measures (dax_measures.dax)
risk_arena/index.html        Interactive gamified risk-structuring simulator
docs/securitisation/         Methodology docs: ECL, waterfall, stress testing, investor reporting, crisis case studies, build plan
tests/test_securitisation.py 9 tests validating the pipeline against the real data
docs/retail-credit-scoring/  The unrelated prior project (README/REPORT/MODEL_CARD/policy docs), kept for its own record
```

## Suggested 15-day execution plan

| Day | Workstream | Output |
|---|---|---|
| 1 | Read the four datasets; map fields to IFRS 9 / ABS concepts | Data dictionary notes |
| 2 | Build `data_loader.py`; validate schema and joins | Clean loaders |
| 3-4 | Build the ECL engine (12m PD, lifetime PD from vintage curve, scenario weighting) | `ecl.py` + tests |
| 5 | Size the Class A/B/C capital structure | `waterfall.py::build_tranches` |
| 6-7 | Build the sequential-pay waterfall against real monthly data | `waterfall.py` + tests |
| 8 | Build the 3-scenario stress framework (ECL + waterfall) | `stress_testing.py` |
| 9 | Build the investor reporting pack | `investor_reporting.py` |
| 10 | Wire the end-to-end pipeline | `run_pipeline.py` |
| 11-12 | Design the Power BI star schema and write the DAX library | `powerbi/` |
| 13 | Build the interactive risk-arena simulator | `risk_arena/index.html` |
| 14 | Write the crisis case-study analysis and methodology docs | `docs/securitisation/` |
| 15 | Tests, README/REPORT, packaging, QA pass | This submission |

## Governance requirements before production use

See `docs/securitisation/build_plan.md` for scope boundaries, and
`GOVERNANCE.md` for the repository-hygiene checklist required before
transferring ownership to Zetheta.
