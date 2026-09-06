"""Loaders for Zetheta's Project 1A auto-loan securitisation datasets.

These are the four source files supplied for the project:

- ``auto_loan_securitisation_data.csv``  loan-level static snapshot (1 row / loan)
- ``dpd_snapshot_history.csv``           monthly delinquency-bucket panel (1 row / loan / month)
- ``dynamic_loss_monthly.csv``           pool-level monthly performance (dynamic pool)
- ``static_pool_vintage_data.csv``       vintage curves (1 row / vintage / month-on-book)

Every downstream module (ecl, waterfall, stress_testing, investor_reporting) is
built to consume these directly -- nothing in this pipeline runs on synthetic data.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "securitisation" / "raw"

DATE_COLS_LOAN = ["OriginationDate", "CutoffDate", "MaturityDate", "LastPaymentDate"]


def load_loan_pool(path: Path = RAW / "auto_loan_securitisation_data.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=[c for c in DATE_COLS_LOAN], dayfirst=False)
    # Normalise a couple of frequently-used derived fields used across modules.
    df["IsStage2Plus"] = df["IFRS9_Stage"].ge(2)
    df["DPD_Bucket_Simplified"] = pd.cut(
        df["DelinquencyDays"],
        bins=[-1, 0, 29, 59, 89, 119, 10_000],
        labels=["Current", "1-29 DPD", "30-59 DPD", "60-89 DPD", "90-119 DPD", "120+ DPD"],
    )
    return df


def load_dpd_snapshots(path: Path = RAW / "dpd_snapshot_history.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["SnapshotDate", "LastPaymentDate"])
    return df


def load_dynamic_monthly(path: Path = RAW / "dynamic_loss_monthly.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["ReportingDate"]).sort_values("ReportingDate")
    return df


def load_static_pool_vintage(path: Path = RAW / "static_pool_vintage_data.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["VintageStartDate"]).sort_values(["VintageID", "MonthsOnBook"])
    return df


def load_all() -> dict[str, pd.DataFrame]:
    return {
        "loan_pool": load_loan_pool(),
        "dpd_snapshots": load_dpd_snapshots(),
        "dynamic_monthly": load_dynamic_monthly(),
        "static_vintage": load_static_pool_vintage(),
    }
