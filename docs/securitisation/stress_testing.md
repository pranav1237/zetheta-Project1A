# Stress Testing Framework

`src/securitisation/stress_testing.py` applies three macro scenarios to
**both** the ECL engine and the waterfall, using the real pool and real
monthly performance data as the starting point in every case.

## Scenarios

| Scenario | PD multiplier | LGD multiplier | Net-loss multiplier | CPR multiplier | Rationale |
|---|---|---|---|---|---|
| Base | 1.00x | 1.00x | 1.00x | 1.00x | Pool's own observed/estimated performance |
| Moderate stress | 1.50x | 1.15x | 1.50x | 0.80x | A typical consumer-credit downturn: defaults rise, recovery values soften, and fewer borrowers can refinance/prepay |
| Severe stress | 2.30x | 1.35x | 2.30x | 0.60x | A correlated, systemic shock (see crisis_case_studies.md) -- defaults spike, collateral (vehicle resale) values fall sharply, and prepayment options largely disappear |

**Why CPR falls, not rises, in stress:** this is a common point of confusion.
In an auto-loan pool, voluntary prepayment mostly comes from refinancing or
selling the vehicle to buy a new one -- both of which require the borrower to
be creditworthy and have access to credit. In a downturn, that channel
narrows, so involuntary defaults rise *and* voluntary prepayment falls
simultaneously. Modelling both moving the same direction (e.g., both "up" in
stress) is a common but incorrect simplification that this framework
deliberately avoids.

## Two outputs per scenario

`run_scenarios()` reports, per scenario:

1. **ECL impact** (`weighted_ecl`, `ecl_rate_pct`) -- how much more provisioning
   the book would need under that scenario, using the same lifetime-PD
   methodology as the base ECL engine (see `ifrs9_ecl.md`), just with shocked
   PD/LGD inputs.
2. **Structural impact** (`class_c_subordinate_ending_balance`,
   `class_c_wiped_out`, `class_a_senior_ending_balance`) -- what happens to
   noteholders if the *cashflow* waterfall (not just the accounting ECL) sees
   those same loss levels. This is the question a rating agency or investor
   actually cares about: does credit enhancement survive the scenario.

## Reading the current results

On this pool, ECL roughly triples from Base to Severe stress (see
`artifacts/securitisation/stress_results.csv` after running the pipeline),
while the waterfall shows the Class C subordinate tranche is **not** wiped
out even under the severe scenario at current pool seasoning -- i.e., the
84/10/6 structure documented in `waterfall_methodology.md` has meaningful,
quantifiable headroom against the scenarios modelled here. Use the
`risk_arena/index.html` simulator to explore where that headroom actually
runs out (lower the Class A size or raise stressed PD/LGD further).

## Limitations

- Shocks are judgment-based multipliers on the pool's own current PD/LGD/loss
  figures, not derived from a macro-econometric model (unemployment, used
  -vehicle price index, interest rates).
- Only 12 months of dynamic pool history are available in this dataset, so
  the "moderate"/"severe" multipliers are illustrative severity assumptions,
  not calibrated to this pool's own historical stress episode (it hasn't had
  one in the observation window).
- A production stress-testing framework would additionally run reverse
  stress tests (solve for the loss level at which each tranche breaks) and
  correlate stress severity to explicit macro variables.
