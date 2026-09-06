from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import confusion_matrix


ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "german_credit.csv"
ART = ROOT / "artifacts"

MODEL_PATH = ART / "random_forest.joblib"
PREDICTIONS_PATH = ART / "random_forest_predictions.csv"


# These values will be validated against the model results.
DEFAULT_APPROVAL_THRESHOLD = 0.50

# Risk bands are intentionally simple and transparent.
LOW_RISK_MAX = 0.20
MEDIUM_RISK_MAX = 0.40


def load_data():

    df = pd.read_csv(DATA)

    df["bad"] = (
        df["target"] == 2
    ).astype(int)

    return df


def assign_risk_band(pd_value):

    if pd_value < LOW_RISK_MAX:
        return "Low"

    if pd_value < MEDIUM_RISK_MAX:
        return "Medium"

    return "High"


def recommended_action(risk_band):

    actions = {
        "Low": "Standard underwriting",
        "Medium": "Manual review / additional verification",
        "High": "Enhanced review or decline",
    }

    return actions[risk_band]


def main():

    if not PREDICTIONS_PATH.exists():
        raise FileNotFoundError(
            "Run `python src/pipeline.py` first."
        )

    predictions = pd.read_csv(
        PREDICTIONS_PATH
    )

    predictions["risk_band"] = (
        predictions["predicted_pd"]
        .apply(assign_risk_band)
    )

    predictions["recommended_action"] = (
        predictions["risk_band"]
        .apply(recommended_action)
    )

    summary = (
        predictions
        .groupby("risk_band")
        .agg(
            borrowers=("actual_bad", "size"),
            bad_count=("actual_bad", "sum"),
            average_pd=("predicted_pd", "mean"),
        )
        .reset_index()
    )

    summary["bad_rate"] = (
        summary["bad_count"]
        / summary["borrowers"]
    )

    summary["bad_rate_pct"] = (
        summary["bad_rate"] * 100
    ).round(2)

    summary["average_pd_pct"] = (
        summary["average_pd"] * 100
    ).round(2)

    summary["recommended_action"] = (
        summary["risk_band"]
        .apply(recommended_action)
    )

    summary = summary[
        [
            "risk_band",
            "borrowers",
            "bad_count",
            "bad_rate_pct",
            "average_pd_pct",
            "recommended_action",
        ]
    ]

    print("=" * 80)
    print("CREDIT RISK SEGMENTATION")
    print("=" * 80)

    print(
        summary.to_string(
            index=False
        )
    )

    predictions.to_csv(
        ART / "risk_segmented_predictions.csv",
        index=False,
    )

    summary.to_csv(
        ART / "risk_segment_summary.csv",
        index=False,
    )

    metadata = {
        "model": "random_forest",
        "risk_band_definition": {
            "low": f"PD < {LOW_RISK_MAX}",
            "medium": (
                f"{LOW_RISK_MAX} <= PD < "
                f"{MEDIUM_RISK_MAX}"
            ),
            "high": f"PD >= {MEDIUM_RISK_MAX}",
        },
        "actions": {
            "low": "Standard underwriting",
            "medium": (
                "Manual review / additional verification"
            ),
            "high": (
                "Enhanced review or decline"
            ),
        },
    }

    (
        ART / "risk_segmentation_metadata.json"
    ).write_text(
        json.dumps(
            metadata,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()