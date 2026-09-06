# Investor Reporting

`src/securitisation/investor_reporting.py` produces the summary tables an ABS
investor or trustee/servicer surveillance report would carry, all computed
from the real loan pool and monthly performance data (not synthetic figures).

## Tables produced (`write_investor_pack()`)

| File | Content |
|---|---|
| `stage_summary.csv` | Loan count, exposure, weighted ECL, ECL rate, average PD/LTV by IFRS9 stage |
| `state_summary.csv` | Exposure, weighted ECL, 30+ DPD rate by state -- geographic concentration risk |
| `servicer_summary.csv` | Exposure and 30+/90+ DPD rate by servicer -- servicer performance/concentration risk |
| `collateral_performance_trend.csv` | Monthly EOP balance, collection efficiency, default rate, net loss rate, SMM, CPR, excess spread |
| `vintage_cumulative_loss_curve.csv` | Cumulative net loss rate by vintage x months-on-book, pivoted for a Power BI line chart |

## Why these five tables specifically

A real ABS investor report typically has three audiences with different
questions:

1. **The trustee/rating agency** wants stage/geography/servicer concentration
   -- is risk building up in one bucket that could threaten a trigger.
2. **The portfolio manager** wants the monthly performance trend -- is
   collection efficiency, CPR, or the default rate moving in a direction that
   changes the reinvestment or prepayment assumption.
3. **The structurer/rating analyst** wants the vintage curve -- is this
   specific pool tracking better or worse than prior vintages at the same
   seasoning, which is the standard early-warning signal in ABS surveillance.

## Reconciliation

Every table is built by grouping the *same* loan-level ECL output used
everywhere else in the pipeline (`calculate_ecl()`), so `stage_summary.csv`'s
`exposure` column always sums to the same total EAD as `state_summary.csv`
and the portfolio-level `portfolio_summary.json` -- there is a single source
of truth for exposure and ECL across every report, which is exactly what a
real trustee report is expected to demonstrate under audit (`tests/
test_securitisation.py::test_investor_reports_reconcile_to_portfolio_exposure`
checks this automatically).

## Production extensions

- Tranche-level cash distribution statements (amounts actually paid to each
  noteholder that period, not just ending balances).
- Trigger test results (delinquency trigger, cumulative loss trigger) with
  pass/fail status and consequence (e.g., sequential-pay lock-in).
- A PDF/Excel-formatted version matching a specific trustee's report template.
