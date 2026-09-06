from pathlib import Path
import json

import numpy as np
import pandas as pd

from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

from pipeline import build_preprocessor, load_data, RANDOM_STATE
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
ART.mkdir(exist_ok=True)


def build_models(X):
    return {
        "logistic": Pipeline([
            ("pre", build_preprocessor(X)),
            (
                "model",
                LogisticRegression(
                    max_iter=3000,
                    class_weight="balanced"
                ),
            ),
        ]),
        "random_forest": Pipeline([
            ("pre", build_preprocessor(X)),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=500,
                    min_samples_leaf=8,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]),
    }


def main():
    df = load_data()

    X = df.drop(columns=["bad"])
    y = df["bad"]

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    results = []

    for name, model in build_models(X).items():
        probabilities = cross_val_predict(
            model,
            X,
            y,
            cv=cv,
            method="predict_proba",
        )[:, 1]

        brier = brier_score_loss(y, probabilities)

        fraction_of_positives, mean_predicted_value = calibration_curve(
            y,
            probabilities,
            n_bins=10,
            strategy="quantile",
        )

        calibration_table = pd.DataFrame({
            "mean_predicted_probability": mean_predicted_value,
            "observed_bad_rate": fraction_of_positives,
        })

        calibration_table["absolute_gap"] = (
            calibration_table["mean_predicted_probability"]
            - calibration_table["observed_bad_rate"]
        ).abs()

        calibration_table.to_csv(
            ART / f"{name}_calibration.csv",
            index=False,
        )

        results.append({
            "model": name,
            "brier_score": float(brier),
            "mean_absolute_calibration_gap": float(
                calibration_table["absolute_gap"].mean()
            ),
        })

    results_df = pd.DataFrame(results)

    print("=" * 80)
    print("PROBABILITY CALIBRATION ANALYSIS")
    print("=" * 80)
    print(results_df.to_string(index=False))

    results_df.to_json(
        ART / "calibration_summary.json",
        orient="records",
        indent=2,
    )


if __name__ == "__main__":
    main()