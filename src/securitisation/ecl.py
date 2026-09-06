"""IFRS 9 expected-credit-loss engine for the auto-loan pool.

Methodology
-----------
Stage 1 (12-month ECL):     ECL = EAD x PD_12m x LGD
Stage 2 / 3 (lifetime ECL): ECL = EAD x PD_lifetime x LGD

PD_lifetime is NOT a flat multiplier on PD_12m. It is built from the pool's own
observed marginal-loss (hazard) curve in ``static_pool_vintage_data.csv``: we
average ``MarginalLossRate`` by ``MonthsOnBook`` across all 15 vintages to get a
pool-level seasoning hazard curve, then survival-multiply the hazard forward
from a loan's current seasoning to its remaining term to obtain a lifetime
default probability. This is calibrated to the pool's own historical
performance rather than an assumed multiplier -- which is the core IFRS 9
requirement (a "significant increase in credit risk" moves a loan from a
12-month to a lifetime ECL basis; see docs/securitisation/ifrs9_ecl.md).

Multi-scenario (base / downside / severe) probability weighting is layered on
top of that lifetime/12-month PD split, following IFRS 9's requirement to use
a probability-weighted, not most-likely, outcome.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from .data_loader import load_loan_pool, load_static_pool_vintage

SCENARIO_WEIGHTS = {"base": 0.55, "downside": 0.30, "severe": 0.15}
SCENARIO_PD_SHOCK = {"base": 1.00, "downside": 1.45, "severe": 2.20}
SCENARIO_LGD_SHOCK = {"base": 1.00, "downside": 1.12, "severe": 1.30}


def build_hazard_curve(vintage: pd.DataFrame | None = None):
    """Average marginal loss (hazard) rate by seasoning month, across vintages."""
    vintage = vintage if vintage is not None else load_static_pool_vintage()
    curve = vintage.groupby("MonthsOnBook")["MarginalLossRate"].mean().sort_index()
    tail = curve.iloc[-6:].mean() if len(curve) >= 6 else curve.mean()
    return curve, float(tail if tail == tail else 0.0)  # guard NaN


def lifetime_pd(
    months_on_book: pd.Series,
    remaining_term: pd.Series,
    pd_12m: pd.Series,
    curve: pd.Series,
    tail: float,
) -> pd.Series:
    """Survival-adjusted cumulative default probability over the remaining life.

    The pool-average hazard curve gives the *shape* of how risk evolves with
    seasoning, but a loan already in arrears (Stage 2/3, high PD_Estimate) is
    materially riskier than the pool average at that same seasoning point.
    We therefore rescale the forward hazard path by each loan's own
    idiosyncratic risk (its 12-month PD relative to the pool's average
    monthly hazard at its current seasoning), then compound survival forward
    -- so a defaulted loan's lifetime PD reflects its own elevated risk, not
    just the average pool curve.
    """
    max_month = int(curve.index.max())

    def _pool_hazard(m: int) -> float:
        return curve.loc[m] if m in curve.index and m <= max_month else tail

    def _one(seasoning: int, remaining: int, own_pd_12m: float) -> float:
        remaining = max(int(remaining), 1)
        pool_monthly_hazard_now = max(_pool_hazard(int(seasoning)), 1e-6)
        own_monthly_hazard_now = min(max(own_pd_12m, 0.0), 1.0) / 12
        relative_risk = min(max(own_monthly_hazard_now / pool_monthly_hazard_now, 0.05), 60.0)
        survival = 1.0
        for m in range(int(seasoning), int(seasoning) + remaining):
            hazard = min(_pool_hazard(m) * relative_risk, 0.98)
            survival *= (1 - hazard)
        return 1 - survival

    return pd.Series(
        [_one(s, r, p) for s, r, p in zip(months_on_book, remaining_term, pd_12m)],
        index=months_on_book.index,
    )


def calculate_ecl(df: pd.DataFrame | None = None, scenario_weights: dict | None = None) -> pd.DataFrame:
    """Loan-level, scenario-weighted IFRS 9 ECL using PD_Estimate/LGD_Estimate/EAD fields."""
    out = (df if df is not None else load_loan_pool()).copy()
    weights = scenario_weights or SCENARIO_WEIGHTS

    curve, tail = build_hazard_curve()
    out["PD_Lifetime"] = lifetime_pd(out["MonthsOnBook"], out["RemainingTerm"], out["PD_Estimate"], curve, tail)
    out["PD_ForECL_Base"] = np.where(out["IFRS9_Stage"].eq(1), out["PD_Estimate"], out["PD_Lifetime"])

    for scenario, weight in weights.items():
        pd_s = (out["PD_ForECL_Base"] * SCENARIO_PD_SHOCK[scenario]).clip(0, 1)
        lgd_s = (out["LGD_Estimate"] * SCENARIO_LGD_SHOCK[scenario]).clip(0, 1)
        out[f"ECL_{scenario}"] = out["EAD"] * pd_s * lgd_s

    out["ECL_Weighted"] = sum(weights[s] * out[f"ECL_{s}"] for s in weights)
    out["ECL_Rate"] = (out["ECL_Weighted"] / out["EAD"]).replace([np.inf, -np.inf], np.nan).fillna(0)
    out["ECL_Model_vs_Booked_Delta"] = out["ECL_Weighted"] - out["ECL_Provision"]
    return out


def portfolio_summary(df: pd.DataFrame | None = None) -> dict:
    ecl = calculate_ecl(df)
    by_stage = ecl.groupby("IFRS9_Stage")["ECL_Weighted"].sum()
    return {
        "exposure": float(ecl["EAD"].sum()),
        "weighted_ecl": float(ecl["ECL_Weighted"].sum()),
        "ecl_rate_pct": float(100 * ecl["ECL_Weighted"].sum() / ecl["EAD"].sum()),
        "booked_provision": float(ecl["ECL_Provision"].sum()),
        "model_vs_booked_delta": float(ecl["ECL_Weighted"].sum() - ecl["ECL_Provision"].sum()),
        "stage_1_ecl": float(by_stage.get(1, 0.0)),
        "stage_2_ecl": float(by_stage.get(2, 0.0)),
        "stage_3_ecl": float(by_stage.get(3, 0.0)),
        "loan_count": int(len(ecl)),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(portfolio_summary(), indent=2))
