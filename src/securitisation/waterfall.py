"""Sequential-pay (senior/mezz/subordinate) cashflow waterfall.

Driven month-by-month by the ACTUAL pool performance in
``dynamic_loss_monthly.csv`` (collections, net losses, prepayments, scheduled
amortisation) rather than a simulated cashflow. The capital structure below is
a representative structuring of the original pool balance implied by the
first month's BOP_Balance in that file -- documented assumptions, sized the
way an arranger would size a class A/B/C note for this collateral pool. See
docs/securitisation/waterfall_methodology.md.
"""
from __future__ import annotations
import pandas as pd

from .data_loader import load_dynamic_monthly

# Tranche sizing (% of original pool balance) and coupon, senior to junior.
DEFAULT_TRANCHES = pd.DataFrame([
    {"tranche": "Class_A_Senior", "priority": 1, "pct_of_pool": 0.84, "coupon_rate": 0.084},
    {"tranche": "Class_B_Mezzanine", "priority": 2, "pct_of_pool": 0.10, "coupon_rate": 0.108},
    {"tranche": "Class_C_Subordinate", "priority": 3, "pct_of_pool": 0.06, "coupon_rate": 0.145},
])


def build_tranches(original_pool_balance: float, structure: pd.DataFrame | None = None) -> pd.DataFrame:
    structure = (structure if structure is not None else DEFAULT_TRANCHES).copy()
    structure["initial_balance"] = structure["pct_of_pool"] * original_pool_balance
    total = structure["initial_balance"].sum()
    structure["subordination_balance"] = total - structure["initial_balance"].cumsum()
    return structure


def run_waterfall(monthly: pd.DataFrame | None = None, tranches: pd.DataFrame | None = None) -> pd.DataFrame:
    """Run the sequential-pay waterfall across every reporting month available."""
    monthly = (monthly if monthly is not None else load_dynamic_monthly()).sort_values("ReportingDate")
    original_pool_balance = float(monthly.iloc[0]["BOP_Balance"])
    tranches = tranches if tranches is not None else build_tranches(original_pool_balance)

    balances = dict(zip(tranches["tranche"], tranches["initial_balance"].astype(float)))
    rates = dict(zip(tranches["tranche"], tranches["coupon_rate"].astype(float)))
    priority = tranches.sort_values("priority")["tranche"].tolist()

    rows = []
    for _, period in monthly.iterrows():
        available = float(period["CollectionsTotal"])
        loss = float(period["NetLoss_ThisMonth"])
        # Losses (net of recoveries) are absorbed junior-to-senior, writing down
        # subordinate balance first -- the core credit-enhancement mechanic.
        for tranche in reversed(priority):
            absorbed = min(balances[tranche], loss)
            balances[tranche] -= absorbed
            loss -= absorbed
            if loss <= 1e-9:
                break

        allocation = {
            "period": period["ReportingDate"],
            "collections": available,
            "net_loss": float(period["NetLoss_ThisMonth"]),
            "prepayments": float(period["Prepayments_ThisMonth"]),
        }
        for tranche in priority:
            interest_due = balances[tranche] * rates[tranche] / 12
            interest_paid = min(available, interest_due)
            available -= interest_paid
            # Sequential pay: whatever cash remains after interest goes 100% to
            # principal on the senior-most tranche still outstanding.
            principal_paid = min(available, balances[tranche])
            available -= principal_paid
            balances[tranche] -= principal_paid
            allocation[f"{tranche}_interest_paid"] = interest_paid
            allocation[f"{tranche}_principal_paid"] = principal_paid
            allocation[f"{tranche}_ending_balance"] = balances[tranche]
        allocation["residual_to_equity"] = available
        rows.append(allocation)
    return pd.DataFrame(rows)


def credit_enhancement(tranches: pd.DataFrame) -> pd.DataFrame:
    total = tranches["initial_balance"].sum()
    out = tranches.copy()
    out["credit_enhancement_pct"] = out["subordination_balance"] / total
    return out


if __name__ == "__main__":
    wf = run_waterfall()
    pd.set_option("display.width", 200)
    print(wf[["period", "collections", "net_loss", "Class_A_Senior_ending_balance",
               "Class_B_Mezzanine_ending_balance", "Class_C_Subordinate_ending_balance",
               "residual_to_equity"]])
