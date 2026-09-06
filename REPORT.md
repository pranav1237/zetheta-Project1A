# Zetheta WorkBridge Project Report
## Project 1A: Data Analyst Securitisation

### 1. Problem statement

An auto-loan originator/servicer needs to (a) provision correctly under
IFRS 9 for expected credit losses, (b) understand whether the note structure
backing a securitised pool has enough credit enhancement to survive a
downturn, and (c) report both of these clearly to investors and internal
risk management, ideally through a Power BI dashboard a non-technical
stakeholder can navigate.

This project builds that full chain -- ECL, waterfall, stress testing,
investor reporting, dashboard model -- against four real datasets supplied
for the assignment, rather than any one piece in isolation.

### 2. Business framing

The project is framed around three questions a real securitisation
surveillance function asks every reporting period:

1. **Is the booked provision enough?** (`model_vs_booked_delta` in
   `portfolio_summary.json` -- on this pool, the model finds the current
   `ECL_Provision` field materially under-provisions relative to a
   lifetime-PD-based recalculation, concentrated in Stage 2/3.)
2. **Does the structure survive a downturn?** (`stress_testing.py` re-runs
   the waterfall with net losses scaled 1.5x-2.3x and reports whether the
   Class C subordinate tranche is wiped out.)
3. **Where is risk concentrated?** (`investor_reporting.py`'s state/servicer
   breakdowns.)

### 3. Industry context

IFRS 9 requires a probability-weighted expected credit loss recognised on a
12-month basis (Stage 1) or lifetime basis (Stage 2/3, once a significant
increase in credit risk has occurred) -- see
`docs/securitisation/ifrs9_ecl.md` for exactly how that's implemented here.
For an India-oriented auto-loan book, RBI's SMA (Special Mention Account)
classification framework is also relevant to how delinquency is reported and
escalated internally, which is why `RBI_SMA_Class` is carried through the DPD
snapshot data and surfaced as its own DAX measure
(`RBI SMA-2 Exposure`) rather than only reported as raw days-past-due.

### 4. Dataset

Four files, described in `data/README.md` and loaded via
`src/securitisation/data_loader.py`: a 500-loan static snapshot with 58
fields (balances, delinquency, IFRS 9 staging, PD/LGD/EAD/ECL, borrower and
vehicle attributes), a ~6,000-row monthly DPD-bucket transition panel, a
12-month pool-level performance history (collections, losses, CPR, excess
spread), and a 15-vintage x up-to-45-months-on-book cumulative loss-curve
panel.

### 5. Methodology

#### 5.1 IFRS 9 ECL

See `docs/securitisation/ifrs9_ecl.md`. In summary: Stage 1 uses the pool's
own 12-month `PD_Estimate`; Stage 2/3 uses a lifetime PD built by compounding
a pool-average, seasoning-indexed hazard curve (derived from
`static_pool_vintage_data.csv`) forward across each loan's own remaining
term, scaled by that loan's own idiosyncratic risk level. Three scenarios
(base/downside/severe) are probability-weighted, per IFRS 9's requirement to
avoid a single most-likely estimate.

#### 5.2 Waterfall

See `docs/securitisation/waterfall_methodology.md`. A sequential-pay Class
A(84%)/B(10%)/C(6%) structure, sized off the pool's own original balance, run
month-by-month against the pool's actual collections, net losses and
prepayments. Losses are allocated junior-to-senior (the core credit-
enhancement mechanic); interest and then principal are paid strictly in
priority order each period.

#### 5.3 Stress testing

See `docs/securitisation/stress_testing.md`. Three scenarios shock PD, LGD,
net losses up and CPR down simultaneously (deliberately -- both directions
follow from the same underlying downturn assumption, documented explicitly
to avoid the common modelling error of moving them independently).

#### 5.4 Investor reporting

See `docs/securitisation/investor_reporting.md`. Five reconciling tables
(stage, state, servicer, monthly trend, vintage curve), all built from the
same underlying `calculate_ecl()` output so there is a single source of truth
for exposure and ECL across every report -- checked automatically by
`tests/test_securitisation.py::test_investor_reports_reconcile_to_portfolio_exposure`.

#### 5.5 Power BI / DAX

See `powerbi/data_model.md`. A star schema (loan-level, snapshot-level,
pool-level, tranche-level fact tables at their correct grain, plus a
disconnected scenario dimension) is what makes the DAX in
`powerbi/dax_measures.dax` (roll-rate transition matrices, `RANKX`-based
scorecards, `ALLEXCEPT` vintage-curve lookups, a `SWITCH`-driven what-if
scenario selector) meaningful rather than a spreadsheet formula relabelled.

#### 5.6 Gamified risk arena

`risk_arena/index.html` is a self-contained, browser-based simulator: the
user adjusts tranche sizing, reserve fund, and stressed PD/LGD/CPR via
sliders (or picks a historical-crisis-style preset) and sees a live
resilience score, subordination level, implied loss-coverage multiple, and
whether the equity tranche survives -- turning the structural trade-off
(more protection vs. less junior yield) into something tangible rather than
a static table.

### 6. Validation

9 automated tests (`tests/test_securitisation.py`) check: schema loading,
ECL non-negativity and stage-sensitivity, portfolio reconciliation, hazard
-curve sanity, waterfall balance non-negativity, credit-enhancement ordering,
monotonic stress-scenario ECL, and investor-report reconciliation. All pass,
alongside the 6 pre-existing tests from the unrelated prior project.

### 7. Limitations (see also each methodology doc's own limitations section)

- No discounting of expected shortfalls (undiscounted ECL).
- Macro scenario shocks are documented judgment multipliers, not derived from
  an econometric model.
- Waterfall omits reserve-fund mechanics, trigger breaches, servicing fees,
  and clean-up calls.
- 12 months of dynamic pool history is a short observation window for
  calibrating stress severity.
- This is a project-level analytical exercise, not a production or
  regulator-reviewed model.

### 8. Governance

See `GOVERNANCE.md` for the repository-hygiene checklist required before
transferring ownership to Zetheta, and
`docs/securitisation/build_plan.md` for explicit scope boundaries.
