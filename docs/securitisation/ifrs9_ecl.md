# IFRS 9 Expected Credit Loss Methodology

This module implements a loan-level, three-scenario, stage-sensitive ECL
engine (`src/securitisation/ecl.py`) driven entirely by the real pool in
`data/securitisation/raw/auto_loan_securitisation_data.csv` and the vintage
loss curve in `static_pool_vintage_data.csv`. It is a project-level,
illustrative implementation of the standard's mechanics -- not an
institution-approved regulatory model.

## 1. Staging

The source data already carries an `IFRS9_Stage` field (1/2/3) per loan,
consistent with the standard's three-bucket approach:

- **Stage 1** -- no significant increase in credit risk (SICR) since
  origination. ECL is measured on a **12-month** basis.
- **Stage 2** -- SICR has occurred (in this book, typically loans that have
  rolled to 30+ DPD, per `DPD_Bucket`). ECL is measured on a **lifetime** basis.
- **Stage 3** -- credit-impaired / defaulted. ECL is also **lifetime**, applied
  to a loan already in default.

In addition to the DPD-based staging already in the data, `ecl.py` computes a
`SICR Migration Count` proxy off CIBIL score deterioration (origination vs.
current score, 50+ point fall) -- IFRS 9 requires SICR assessment to look
beyond pure delinquency, and a credit-bureau-score deterioration trigger is a
common real-world overlay alongside DPD.

## 2. Twelve-month vs. lifetime PD

Stage 1 uses the pool's own `PD_Estimate` field directly (a 12-month PD).

Stage 2/3 lifetime PD is **not** a flat multiplier on the 12-month PD (that
was the approach in the previous version of this module, and it is a common
shortcut but not defensible under audit: it implicitly assumes every loan's
lifetime risk scales by the same constant regardless of how much life is left
or how the pool's own hazard actually evolves with seasoning).

Instead, `build_hazard_curve()` derives a **pool-specific monthly hazard
curve** by averaging `MarginalLossRate` across all 15 vintages in
`static_pool_vintage_data.csv`, indexed by `MonthsOnBook`. `lifetime_pd()`
then:

1. Takes each loan's own idiosyncratic risk level (`PD_Estimate`, which
   already reflects its actual delinquency/credit deterioration) relative to
   the pool-average hazard at that loan's current seasoning, to get a
   loan-specific **relative risk multiplier**.
2. Compounds that scaled hazard forward, month by month, across the loan's
   *actual* remaining term (`RemainingTerm`), producing a genuine
   survival-based cumulative lifetime default probability rather than an
   assumed constant.

This means a loan seasoned 40 months with 8 months left carries a materially
different lifetime PD than an identical-risk loan seasoned 2 months with 70
months left -- which a flat multiplier cannot represent.

## 3. Multi-scenario probability weighting

IFRS 9 requires a **probability-weighted** outcome across at least a base and
one or more downside scenarios, not a single most-likely estimate.
`SCENARIO_WEIGHTS = {base: 0.55, downside: 0.30, severe: 0.15}` in `ecl.py`
sets the weights; `SCENARIO_PD_SHOCK` / `SCENARIO_LGD_SHOCK` apply
scenario-specific multipliers to PD and LGD before computing `ECL_weighted`
as the probability-weighted sum. These weights and shock factors are
project-level assumptions -- documented and easy to change in one place --
not calibrated to any institution's approved economic scenarios.

## 4. What the model tells you that the booked provision doesn't

`ECL_Model_vs_Booked_Delta` (loan-level) and `model_vs_booked_delta`
(portfolio-level, in `portfolio_summary()`) compare the model's output
against the `ECL_Provision` value already present in the source data. Running
the pipeline on this pool shows the model produces a materially **higher**
provision than what's currently booked, concentrated in Stage 2/3 -- exactly
the kind of finding an investor-reporting or model-validation exercise exists
to surface. See `artifacts/securitisation/investor_pack/stage_summary.csv`
after running the pipeline.

## 5. Limitations (stated deliberately, not hidden)

- No discounting of expected cash shortfalls to a discounted ECL (IFRS 9
  technically requires ECL to be the present value of expected shortfalls).
- No explicit forward-looking macroeconomic model (unemployment, interest
  rate, used-vehicle price index) driving the scenario shocks -- shocks are
  judgment-based multipliers, documented as such.
- SICR/staging is taken from the source data rather than independently
  re-derived from a full transition-matrix model (though the CIBIL-based
  proxy in section 1 offers a partial independent check).
- This is a project exercise on illustrative data, not a production or
  regulator-reviewed model.
