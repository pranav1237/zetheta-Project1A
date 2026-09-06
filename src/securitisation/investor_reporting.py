"""Investor reporting pack: the summary tables an ABS investor/rating-agency
surveillance analyst would expect in a monthly servicer report.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

from .data_loader import load_loan_pool, load_dynamic_monthly, load_static_pool_vintage
from .ecl import calculate_ecl


def stage_summary(pool: pd.DataFrame | None = None) -> pd.DataFrame:
    ecl = calculate_ecl(pool)
    g = ecl.groupby("IFRS9_Stage").agg(
        loan_count=("LoanID", "count"),
        exposure=("EAD", "sum"),
        weighted_ecl=("ECL_Weighted", "sum"),
        avg_pd_pct=("PD_Estimate", lambda s: 100 * s.mean()),
        avg_ltv_current_pct=("LTV_Current", lambda s: 100 * s.mean()),
    ).reset_index()
    g["ecl_rate_pct"] = 100 * g["weighted_ecl"] / g["exposure"]
    return g


def state_summary(pool: pd.DataFrame | None = None) -> pd.DataFrame:
    ecl = calculate_ecl(pool)
    g = ecl.groupby("State").agg(
        loan_count=("LoanID", "count"),
        exposure=("EAD", "sum"),
        weighted_ecl=("ECL_Weighted", "sum"),
        dpd30_plus_pct=("DelinquencyDays", lambda s: 100 * (s >= 30).mean()),
    ).reset_index().sort_values("exposure", ascending=False)
    return g


def servicer_summary(pool: pd.DataFrame | None = None) -> pd.DataFrame:
    ecl = calculate_ecl(pool)
    g = ecl.groupby("ServicerName").agg(
        loan_count=("LoanID", "count"),
        exposure=("EAD", "sum"),
        dpd30_plus_pct=("DelinquencyDays", lambda s: 100 * (s >= 30).mean()),
        dpd90_plus_pct=("DelinquencyDays", lambda s: 100 * (s >= 90).mean()),
    ).reset_index().sort_values("exposure", ascending=False)
    return g


def collateral_performance_trend() -> pd.DataFrame:
    """Monthly trend table -- CPR, collection efficiency, default/loss rates."""
    monthly = load_dynamic_monthly()
    cols = ["ReportingDate", "EOP_Balance", "CollectionEfficiency",
            "MonthlyDefaultRate", "MonthlyNetLossRate", "SMM", "CPR_Annualised", "ExcessSpread_Monthly"]
    return monthly[cols].copy()


def vintage_curve_table() -> pd.DataFrame:
    vintage = load_static_pool_vintage()
    return vintage.pivot_table(index="MonthsOnBook", columns="VintageID",
                                values="CumulativeNetLossRate", aggfunc="mean")


def write_investor_pack(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    stage_summary().to_csv(out_dir / "stage_summary.csv", index=False)
    state_summary().to_csv(out_dir / "state_summary.csv", index=False)
    servicer_summary().to_csv(out_dir / "servicer_summary.csv", index=False)
    collateral_performance_trend().to_csv(out_dir / "collateral_performance_trend.csv", index=False)
    vintage_curve_table().to_csv(out_dir / "vintage_cumulative_loss_curve.csv")


if __name__ == "__main__":
    print(stage_summary().to_string(index=False))
