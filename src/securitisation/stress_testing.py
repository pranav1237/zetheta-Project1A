"""Scenario stress testing applied to the real loan pool and waterfall.

Three macro scenarios are defined as PD / LGD / prepayment (CPR) shocks. These
are illustrative, project-level assumptions (not a regulatory model) but are
directionally consistent with how auto-loan ABS shocks are typically framed:
a downturn raises defaults and severity while suppressing voluntary prepayment
(borrowers who might have refinanced can no longer do so), which is why CPR
moves down, not up, in the adverse scenarios. See
docs/securitisation/stress_testing.md.
"""
from __future__ import annotations
import pandas as pd

from .data_loader import load_loan_pool, load_dynamic_monthly
from .ecl import calculate_ecl, SCENARIO_WEIGHTS
from .waterfall import build_tranches, run_waterfall, credit_enhancement

SCENARIOS = pd.DataFrame([
    {"scenario": "Base",             "pd_multiplier": 1.00, "lgd_multiplier": 1.00, "loss_multiplier": 1.00, "cpr_multiplier": 1.00},
    {"scenario": "Moderate stress",  "pd_multiplier": 1.50, "lgd_multiplier": 1.15, "loss_multiplier": 1.50, "cpr_multiplier": 0.80},
    {"scenario": "Severe stress",    "pd_multiplier": 2.30, "lgd_multiplier": 1.35, "loss_multiplier": 2.30, "cpr_multiplier": 0.60},
])


def stress_ecl(pool: pd.DataFrame, scenario: dict) -> dict:
    stressed = pool.copy()
    stressed["PD_Estimate"] = (stressed["PD_Estimate"] * scenario["pd_multiplier"]).clip(0, 1)
    stressed["LGD_Estimate"] = (stressed["LGD_Estimate"] * scenario["lgd_multiplier"]).clip(0, 1)
    ecl = calculate_ecl(stressed)
    return {
        "scenario": scenario["scenario"],
        "weighted_ecl": float(ecl["ECL_Weighted"].sum()),
        "ecl_rate_pct": float(100 * ecl["ECL_Weighted"].sum() / ecl["EAD"].sum()),
    }


def stress_waterfall(scenario: dict) -> dict:
    """Re-runs the note waterfall with monthly net losses scaled by the scenario,
    and reports whether the subordinate (equity) tranche is wiped out."""
    monthly = load_dynamic_monthly().copy()
    monthly["NetLoss_ThisMonth"] = monthly["NetLoss_ThisMonth"] * scenario["loss_multiplier"]
    monthly["Prepayments_ThisMonth"] = monthly["Prepayments_ThisMonth"] * scenario["cpr_multiplier"]
    wf = run_waterfall(monthly)
    last = wf.iloc[-1]
    return {
        "scenario": scenario["scenario"],
        "class_c_subordinate_ending_balance": float(last["Class_C_Subordinate_ending_balance"]),
        "class_c_wiped_out": bool(last["Class_C_Subordinate_ending_balance"] <= 1.0),
        "class_a_senior_ending_balance": float(last["Class_A_Senior_ending_balance"]),
    }


def run_scenarios(pool: pd.DataFrame | None = None) -> pd.DataFrame:
    pool = pool if pool is not None else load_loan_pool()
    rows = []
    for scenario in SCENARIOS.to_dict("records"):
        ecl_result = stress_ecl(pool, scenario)
        wf_result = stress_waterfall(scenario)
        rows.append({**ecl_result, **{k: v for k, v in wf_result.items() if k != "scenario"}})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print(run_scenarios().to_string(index=False))
