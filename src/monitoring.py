from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
DATA = ROOT / "data" / "german_credit.csv"


def population_stability_index(expected, actual, bins=10):
    """
    Calculate Population Stability Index (PSI).

    expected: reference distribution
    actual: monitoring/current distribution

    PSI = sum((actual_pct - expected_pct)
              * ln(actual_pct / expected_pct))
    """

    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)

    if expected.ndim != 1 or actual.ndim != 1:
        raise ValueError("PSI inputs must be one-dimensional.")

    if len(expected) != len(actual):
        raise ValueError("PSI inputs must have equal length.")

    if len(expected) == 0:
        raise ValueError("PSI inputs cannot be empty.")

    if np.any(expected < 0) or np.any(actual < 0):
        raise ValueError("PSI inputs cannot contain negative values.")

    expected_total = expected.sum()
    actual_total = actual.sum()

    if expected_total <= 0 or actual_total <= 0:
        raise ValueError("PSI distributions must have positive totals.")

    expected_pct = expected / expected_total
    actual_pct = actual / actual_total

    # Prevent division by zero.
    epsilon = 1e-6
    expected_pct = np.clip(expected_pct, epsilon, None)
    actual_pct = np.clip(actual_pct, epsilon, None)

    return float(
        np.sum(
            (actual_pct - expected_pct)
            * np.log(actual_pct / expected_pct)
        )
    )


def psi_interpretation(psi):
    if psi < 0.10:
        return "stable"
    if psi < 0.25:
        return "moderate_change"
    return "significant_change"


def data_quality_report(df):
    expected_columns = {
        "Attribute1",
        "Attribute2",
        "Attribute3",
        "Attribute4",
        "Attribute5",
        "Attribute6",
        "Attribute7",
        "Attribute8",
        "Attribute9",
        "Attribute10",
        "Attribute11",
        "Attribute12",
        "Attribute13",
        "Attribute14",
        "Attribute15",
        "Attribute16",
        "Attribute17",
        "Attribute18",
        "Attribute19",
        "Attribute20",
        "target",
    }

    actual_columns = set(df.columns)

    missing_columns = sorted(expected_columns - actual_columns)
    unexpected_columns = sorted(actual_columns - expected_columns)

    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_values": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "schema_valid": (
            not missing_columns
            and not unexpected_columns
        ),
    }


def target_monitoring(df):
    if "target" not in df.columns:
        return {
            "available": False,
            "reason": "target column unavailable",
        }

    target_counts = df["target"].value_counts().sort_index()
    target_distribution = (
        df["target"]
        .value_counts(normalize=True)
        .sort_index()
        .to_dict()
    )

    return {
        "available": True,
        "target_counts": {
            str(k): int(v)
            for k, v in target_counts.items()
        },
        "target_distribution": {
            str(k): float(v)
            for k, v in target_distribution.items()
        },
    }


def prediction_monitoring(predictions):
    required = {"actual_bad", "predicted_pd"}

    if not required.issubset(predictions.columns):
        raise ValueError(
            f"Prediction file must contain {required}."
        )

    y = predictions["actual_bad"].astype(int)
    p = predictions["predicted_pd"].astype(float)

    if len(y) == 0:
        raise ValueError("Prediction dataset is empty.")

    if ((p < 0) | (p > 1)).any():
        raise ValueError("Predicted probabilities must be between 0 and 1.")

    return {
        "observations": int(len(predictions)),
        "average_pd": float(p.mean()),
        "observed_bad_rate": float(y.mean()),
        "roc_auc": float(roc_auc_score(y, p)),
        "pr_auc": float(average_precision_score(y, p)),
        "brier_score": float(brier_score_loss(y, p)),
    }


def risk_band_distribution(predictions):
    p = predictions["predicted_pd"]

    bands = pd.cut(
        p,
        bins=[-np.inf, 0.20, 0.40, np.inf],
        labels=["Low", "Medium", "High"],
    )

    result = (
        pd.DataFrame({
            "risk_band": bands,
            "actual_bad": predictions["actual_bad"],
            "predicted_pd": predictions["predicted_pd"],
        })
        .groupby("risk_band", observed=False)
        .agg(
            borrowers=("actual_bad", "size"),
            bad_count=("actual_bad", "sum"),
            bad_rate=("actual_bad", "mean"),
            average_pd=("predicted_pd", "mean"),
        )
        .reset_index()
    )

    return result


def main():
    if not DATA.exists():
        raise FileNotFoundError(
            "Run `python src/download_data.py` first."
        )

    df = pd.read_csv(DATA)

    quality = data_quality_report(df)
    target = target_monitoring(df)

    prediction_file = ART / "random_forest_predictions.csv"

    if prediction_file.exists():
        predictions = pd.read_csv(prediction_file)

        prediction_metrics = prediction_monitoring(
            predictions
        )

        bands = risk_band_distribution(predictions)

        bands.to_csv(
            ART / "monitoring_risk_bands.csv",
            index=False,
        )
    else:
        prediction_metrics = {
            "available": False,
            "reason": "random forest predictions not found",
        }

    # Demonstration of PSI using two halves of the current sample.
    # This is NOT a production drift estimate.
    numeric = df["Attribute2"].astype(float)

    expected = numeric.iloc[:500].to_numpy()
    actual = numeric.iloc[500:].to_numpy()

    quantile_edges = np.quantile(
        expected,
        np.linspace(0, 1, 11),
    )

    quantile_edges[0] = -np.inf
    quantile_edges[-1] = np.inf

    expected_hist, _ = np.histogram(
        expected,
        bins=quantile_edges,
    )

    actual_hist, _ = np.histogram(
        actual,
        bins=quantile_edges,
    )

    psi = population_stability_index(
        expected_hist,
        actual_hist,
    )

    report = {
        "data_quality": quality,
        "target_monitoring": target,
        "prediction_monitoring": prediction_metrics,
        "psi_demo": {
            "feature": "Attribute2",
            "psi": psi,
            "interpretation": psi_interpretation(psi),
            "note": (
                "Demonstration only: the two samples come from "
                "the same historical dataset and are not independent "
                "production monitoring populations."
            ),
        },
    }

    (ART / "monitoring_report.json").write_text(
        json.dumps(report, indent=2)
    )

    print("=" * 80)
    print("MODEL MONITORING REPORT")
    print("=" * 80)

    print("\nDATA QUALITY")
    print(json.dumps(quality, indent=2))

    print("\nTARGET MONITORING")
    print(json.dumps(target, indent=2))

    print("\nPREDICTION MONITORING")
    print(json.dumps(prediction_metrics, indent=2))

    print("\nPSI DEMONSTRATION")
    print(f"Attribute2 PSI: {psi:.4f}")
    print(f"Interpretation: {psi_interpretation(psi)}")

    print("\nMonitoring artifacts written to:")
    print(ART)


if __name__ == "__main__":
    main()