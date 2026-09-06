# Power BI Data Model -- Securitisation Risk Dashboard

## Import sources

| Power BI table          | Source file                                                        | Grain                              |
|--------------------------|---------------------------------------------------------------------|-------------------------------------|
| `FactLoanPool`           | `artifacts/securitisation/loan_level_ecl.csv`                       | 1 row per loan (as of cutoff date)  |
| `FactDPDSnapshot`        | `data/securitisation/raw/dpd_snapshot_history.csv`                  | 1 row per loan per monthly snapshot |
| `FactMonthlyPerformance` | `data/securitisation/raw/dynamic_loss_monthly.csv`                  | 1 row per reporting month (pool)    |
| `FactVintage`            | `data/securitisation/raw/static_pool_vintage_data.csv`              | 1 row per vintage per month-on-book |
| `FactWaterfall`          | `artifacts/securitisation/waterfall_monthly.csv`                    | 1 row per reporting month (tranche) |
| `DimTranche`             | `artifacts/securitisation/tranche_structure.csv`                    | 1 row per note class                |
| `DimDate`                | Generated via `CALENDAR()` spanning min/max of all date columns     | 1 row per day                       |
| `DimScenario`            | Manually entered (or a Power BI What-If Parameter), 3 rows           | 1 row per stress scenario           |

Run `python -m src.securitisation.run_pipeline` first -- it regenerates every
`artifacts/securitisation/*.csv` file used above from the raw source data.

## Relationships (star schema)

```
                         DimDate (1) ----------- (*) FactMonthlyPerformance
                            |
                            | (1)
                            |
   DimTranche (1) --- (*) FactWaterfall (*) -----(1) DimDate
                            
   FactLoanPool (*) ------(1) DimDate      [OriginationDate, CutoffDate]
        |  (1)
        |
        (*) FactDPDSnapshot   [relationship on LoanID, snapshot date to DimDate]

   FactVintage (*) --------(1) DimDate     [VintageStartDate]

   DimScenario -- disconnected (no relationship); read only via SELECTEDVALUE()
                  in the "Scenario Weighted ECL" measure, so a single slicer
                  re-prices the whole book without touching any fact table.
```

Key relationship notes:

- `FactLoanPool[LoanID]` -> `FactDPDSnapshot[LoanID]` is **one-to-many**: each
  loan has ~12 monthly snapshot rows in the sample extract.
- `FactLoanPool[PoolID]` and `FactWaterfall` are linked only through the
  reporting date axis (`DimDate`) because the waterfall operates at pool
  level, not loan level -- this is what lets a single "Total EAD" measure
  filter correctly whether the report page is loan-level or tranche-level.
- `DimTranche[tranche]` is the relationship key into `FactWaterfall`'s
  per-tranche ending-balance columns; because those columns are unpivoted
  wide (`Class_A_Senior_ending_balance`, `Class_B_Mezzanine_ending_balance`, ...)
  in the CSV, use Power Query's **Unpivot Columns** on `FactWaterfall` first so
  `DimTranche` can relate to it on a single `Tranche` column -- otherwise the
  DAX measures in section 6 of `dax_measures.dax` should reference the wide
  columns directly (as written), which avoids the unpivot step but means
  `DimTranche` stays a lookup table for static attributes (coupon, initial
  balance, subordination) rather than a filtering dimension.

## Why a star schema (not one flat table)

The brief calls for "the most complex DAX expressions" -- that's only
meaningful once there's a real model to write them against. A single flattened
table collapses every `CALCULATE`/`ALLEXCEPT`/`RANKX` pattern in
`dax_measures.dax` into a trivial row filter. Splitting loan-level, snapshot-
level, pool-level and tranche-level data into separate fact tables at their
correct grain is what makes measures like `Roll Rate 30 to 60`, `Vintage
Cumulative Net Loss Rate`, and `Scenario Weighted ECL` non-trivial DAX rather
than a spreadsheet formula in disguise.

## Suggested report pages

1. **Portfolio Overview** -- EAD, Weighted ECL, ECL Rate, stage mix donut, WAC/WAL/WALTV cards.
2. **IFRS 9 Staging** -- stage migration, SICR migration count, model-vs-booked provision delta by state/servicer.
3. **Delinquency & Roll Rates** -- DPD bucket flow (Sankey), roll-rate matrix, RBI SMA-class exposure.
4. **Vintage Curves** -- cumulative net loss rate by vintage x months-on-book (line chart, one line per vintage).
5. **Waterfall & Credit Enhancement** -- tranche ending balances over time, credit enhancement %, wipeout flag.
6. **Stress Testing (What-If)** -- `DimScenario` slicer driving Scenario ECL Rate and Scenario ECL Uplift vs Base cards.
7. **Investor Report** -- exportable table visual bound directly to the `investor_pack/*.csv` outputs.
