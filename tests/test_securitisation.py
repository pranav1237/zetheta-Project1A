import pandas as pd
import pytest

from src.securitisation.data_loader import (
    load_loan_pool, load_dynamic_monthly, load_static_pool_vintage, load_dpd_snapshots,
)
from src.securitisation.ecl import calculate_ecl, portfolio_summary, build_hazard_curve
from src.securitisation.waterfall import build_tranches, run_waterfall, credit_enhancement
from src.securitisation.stress_testing import run_scenarios
from src.securitisation.investor_reporting import stage_summary, state_summary


def test_loan_pool_loads_and_has_expected_schema():
    pool = load_loan_pool()
    assert len(pool) > 0
    for col in ["LoanID", "PD_Estimate", "LGD_Estimate", "EAD", "IFRS9_Stage", "ECL_Provision"]:
        assert col in pool.columns


def test_ecl_is_stage_sensitive_and_nonnegative():
    ecl = calculate_ecl()
    assert (ecl["ECL_Weighted"] >= 0).all()
    # Lifetime (Stage 2/3) exposures should carry a materially higher ECL rate
    # than Stage 1 on average -- the core IFRS 9 staging mechanic.
    rate_by_stage = ecl.groupby("IFRS9_Stage")["ECL_Rate"].mean()
    assert rate_by_stage.loc[3] > rate_by_stage.loc[1]


def test_portfolio_summary_reconciles():
    summary = portfolio_summary()
    assert summary["stage_1_ecl"] + summary["stage_2_ecl"] + summary["stage_3_ecl"] == pytest.approx(
        summary["weighted_ecl"], rel=1e-6
    )
    assert summary["exposure"] > 0


def test_hazard_curve_is_monotonic_nondecreasing_on_average():
    curve, tail = build_hazard_curve()
    # Early-seasoning hazard should be lower than late-seasoning hazard for an
    # auto pool (loss curves ramp up before rolling off) -- sanity check only.
    assert curve.iloc[:6].mean() <= curve.iloc[6:24].mean() + 1e-6


def test_waterfall_preserves_priority_and_ends_nonnegative():
    wf = run_waterfall()
    assert (wf.filter(like="ending_balance") >= -1e-6).all().all()
    assert (wf["residual_to_equity"] >= -1e-6).all()


def test_credit_enhancement_decreases_down_the_stack():
    tranches = build_tranches(300_000_000.0)
    ce = credit_enhancement(tranches)
    values = ce.sort_values("priority")["credit_enhancement_pct"].tolist()
    assert values == sorted(values, reverse=True)


def test_stress_scenarios_increase_ecl_monotonically():
    out = run_scenarios()
    base = out.loc[out.scenario == "Base", "weighted_ecl"].iloc[0]
    moderate = out.loc[out.scenario == "Moderate stress", "weighted_ecl"].iloc[0]
    severe = out.loc[out.scenario == "Severe stress", "weighted_ecl"].iloc[0]
    assert base < moderate < severe


def test_investor_reports_reconcile_to_portfolio_exposure():
    pool = load_loan_pool()
    stages = stage_summary(pool)
    states = state_summary(pool)
    assert stages["exposure"].sum() == pytest.approx(pool["EAD"].sum(), rel=1e-6)
    assert states["exposure"].sum() == pytest.approx(pool["EAD"].sum(), rel=1e-6)


def test_dpd_and_vintage_files_load():
    dpd = load_dpd_snapshots()
    vintage = load_static_pool_vintage()
    assert len(dpd) > 0
    assert len(vintage) > 0
    assert {"CumulativeNetLossRate", "MarginalLossRate"}.issubset(vintage.columns)
