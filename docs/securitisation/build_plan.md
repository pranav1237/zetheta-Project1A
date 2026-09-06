# Build Plan

## Implemented in this repository (real data, not synthetic)

- Data loaders for all four source files (`src/securitisation/data_loader.py`).
- Loan-level IFRS 9 ECL with a vintage-curve-derived lifetime PD term
  structure and 3-scenario probability weighting (`ecl.py`).
- Sequential-pay Class A/B/C waterfall driven by real monthly collections,
  net losses and prepayments (`waterfall.py`).
- Scenario stress testing across ECL *and* the cashflow waterfall
  (`stress_testing.py`).
- Investor reporting pack: stage/state/servicer summaries, monthly
  performance trend, vintage loss-curve pivot (`investor_reporting.py`).
- End-to-end orchestration writing every artifact to
  `artifacts/securitisation/` (`run_pipeline.py`).
- Power BI star-schema design and complex DAX measure library
  (`powerbi/data_model.md`, `powerbi/dax_measures.dax`).
- Interactive gamified risk-arena simulator (`risk_arena/index.html`).
- Crisis case-study analysis grounded in the metrics this repo actually
  computes (`docs/securitisation/crisis_case_studies.md`).
- 9 automated tests validating the pipeline against the real data
  (`tests/test_securitisation.py`), all passing alongside the pre-existing
  test suite.

## Suggested next extensions (documented, not built)

- Discounted ECL (present value of expected shortfalls) rather than
  undiscounted expected loss.
- Reserve-fund and trigger-breach mechanics in the waterfall.
- A macro-variable-driven stress scenario generator instead of judgment-based
  multipliers.
- A published `.pbix` file (this repo ships the model design + DAX text so it
  can be built in Power BI Desktop directly against the CSVs in
  `artifacts/securitisation/`; see `powerbi/data_model.md` for the exact
  import/relationship steps).

## Explicit scope statement

All ECL, stress, and waterfall outputs in this repository are a project-level
analytical exercise built on data supplied for Project 1A. They are not a
production model, not a regulator-reviewed IFRS 9 implementation, and not a
reconstruction of any specific real transaction's legal terms.
