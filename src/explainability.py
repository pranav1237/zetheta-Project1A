from pathlib import Path

import joblib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "german_credit.csv"
ART = ROOT / "artifacts"

MODEL_PATH = ART / "random_forest.joblib"


def load_data():
    df = pd.read_csv(DATA)

    df["bad"] = (
        df["target"] == 2
    ).astype(int)

    return df.drop(columns=["target"])


def get_feature_names(preprocessor):
    """
    Recover feature names after preprocessing,
    including one-hot encoded categorical variables.
    """
    return list(
        preprocessor.get_feature_names_out()
    )


def main():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Run `python src/pipeline.py` first."
        )

    df = load_data()

    X = df.drop(columns=["bad"])

    model = joblib.load(
        MODEL_PATH
    )

    preprocessor = model.named_steps["pre"]
    estimator = model.named_steps["model"]

    feature_names = get_feature_names(
        preprocessor
    )

    importances = estimator.feature_importances_

    if len(feature_names) != len(importances):
        raise ValueError(
            "Feature-name count does not match "
            "feature-importance count."
        )

    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    })

    importance_df = (
        importance_df
        .sort_values(
            "importance",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    importance_df["importance_pct"] = (
        importance_df["importance"] * 100
    )

    print("=" * 80)
    print("RANDOM FOREST FEATURE IMPORTANCE")
    print("=" * 80)

    print(
        importance_df
        .head(20)
        .round(4)
        .to_string(index=False)
    )

    importance_df.to_csv(
        ART / "random_forest_feature_importance.csv",
        index=False,
    )

    # --------------------------------------------------------------
    # Aggregate one-hot encoded variables back to original columns.
    # --------------------------------------------------------------

    aggregated = []

    for original_feature in X.columns:

        matching = [
            i
            for i, name in enumerate(feature_names)
            if (
                name.endswith(
                    f"__{original_feature}"
                )
                or
                name.startswith(
                    f"num__{original_feature}"
                )
                or
                name.startswith(
                    f"cat__{original_feature}_"
                )
            )
        ]

        if matching:
            total_importance = (
                importance_df.loc[
                    importance_df["feature"].isin(
                        [
                            feature_names[i]
                            for i in matching
                        ]
                    ),
                    "importance",
                ].sum()
            )

            aggregated.append({
                "feature": original_feature,
                "importance": total_importance,
            })

    aggregated_df = (
        pd.DataFrame(aggregated)
        .sort_values(
            "importance",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    aggregated_df["importance_pct"] = (
        aggregated_df["importance"] * 100
    )

    print()
    print("=" * 80)
    print("AGGREGATED ORIGINAL-FEATURE IMPORTANCE")
    print("=" * 80)

    print(
        aggregated_df
        .round(4)
        .to_string(index=False)
    )

    aggregated_df.to_csv(
        ART / "random_forest_aggregated_importance.csv",
        index=False,
    )


if __name__ == "__main__":
    main()