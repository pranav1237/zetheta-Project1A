# Model Card: Auto-Loan Securitisation ECL, Waterfall & Stress Model

## Overview

| | |
|---|---|
| Model type | Rules-based analytical model (survival-curve ECL + deterministic cashflow waterfall), not a fitted ML model |
| Intended use | Project 1A coursework/portfolio exercise: securitisation risk analytics, Power BI dashboarding, investor reporting |
| Out of scope | Production provisioning, regulatory IFRS 9 filing, real transaction structuring, credit decisioning |
| Owner | Project author (see repository) |
| Data | `data/securitisation/raw/*.csv` -- four project-supplied datasets, no real customer PII |

## What the model does

1. **ECL (`src/securitisation/ecl.py`):** loan-level, stage-sensitive,
   3-scenario probability-weighted IFRS 9-style expected credit loss. Stage
   2/3 lifetime PD is derived from a pool-average hazard curve
   (`static_pool_vintage_data.csv`) scaled by each loan's own risk level, not
   a flat multiplier.
2. **Waterfall (`src/securitisation/waterfall.py`):** sequential-pay Class
   A/B/C cashflow allocation against the pool's actual monthly collections,
   net losses, and prepayments.
3. **Stress testing (`src/securitisation/stress_testing.py`):** three
   macro scenarios (base/moderate/severe) applied to both the ECL and the
   waterfall.
4. **Investor reporting (`src/securitisation/investor_reporting.py`):** five
   reconciling summary tables by stage, state, servicer, monthly trend, and
   vintage.

## Inputs

The four raw CSVs described in `data/README.md` and `README.md`. No external
data, no PII, no personally identifying fields beyond a synthetic `LoanID`.

## Key assumptions (all documented in `docs/securitisation/`)

- Capital structure (84/10/6 Class A/B/C) is a project-level structuring
  assumption sized off this pool's original balance, not a real transaction.
- Scenario PD/LGD/loss/CPR multipliers (`docs/securitisation/
  stress_testing.md`) are judgment-based, not derived from a macro model.
- Lifetime PD uses a survival-curve approach calibrated to this pool's own
  vintage data (see `docs/securitisation/ifrs9_ecl.md`), not an
  institution-approved SICR/lifetime-PD methodology.
- No discounting of expected cash shortfalls (undiscounted ECL).

## Validation performed

9 automated tests in `tests/test_securitisation.py`: schema checks, ECL
non-negativity and stage-monotonicity, portfolio-level reconciliation,
hazard-curve sanity check, waterfall balance non-negativity, credit
-enhancement ordering down the capital stack, monotonic stress-scenario ECL,
and investor-report-to-portfolio exposure reconciliation. All pass.

## Known limitations

See each doc's own "Limitations" section
(`docs/securitisation/ifrs9_ecl.md`, `waterfall_methodology.md`,
`stress_testing.md`, `investor_reporting.md`). In summary: no macro-model
-driven scenarios, no discounting, no reserve/trigger mechanics in the
waterfall, and only 12 months of dynamic pool history to calibrate stress
severity against.

## Explicit non-claims

This model is **not** represented as: a regulator-approved IFRS 9
implementation, a real transaction's legal waterfall, a production credit
decisioning system, or a reconstruction of any specific historical
transaction. It is an educational/portfolio analytics exercise.
