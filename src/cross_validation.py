from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "german_credit.csv"
ART = ROOT / "artifacts"

RANDOM_STATE = 42

FALSE_NEGATIVE_COST = 5
FALSE_POSITIVE_COST = 1


def load_data():
    df = pd.read_csv(DATA)

    # UCI:
    # 1 = good credit
    # 2 = bad credit
    df["bad"] = (df["target"] == 2).astype(int)

    return df.drop(columns=["target"])


def build_preprocessor(X):
    categorical = X.select_dtypes(
        include=["object", "str", "category", "bool"]
    ).columns.tolist()

    numeric = [
        c for c in X.columns
        if c not in categorical
    ]

    categorical_pipeline = Pipeline([
        (
            "impute",
            SimpleImputer(strategy="most_frequent"),
        ),
        (
            "onehot",
            OneHotEncoder(handle_unknown="ignore"),
        ),
    ])

    numeric_pipeline = Pipeline([
        (
            "impute",
            SimpleImputer(strategy="median"),
        ),
        (
            "scale",
            StandardScaler(),
        ),
    ])

    return ColumnTransformer([
        (
            "cat",
            categorical_pipeline,
            categorical,
        ),
        (
            "num",
            numeric_pipeline,
            numeric,
        ),
    ])


def calculate_cost(y, probabilities, threshold):
    predictions = (
        probabilities >= threshold
    ).astype(int)

    false_negative = (
        (y == 1) & (predictions == 0)
    ).sum()

    false_positive = (
        (y == 0) & (predictions == 1)
    ).sum()

    return (
        FALSE_NEGATIVE_COST * false_negative
        + FALSE_POSITIVE_COST * false_positive
    )


def find_optimal_threshold(y, probabilities):
    thresholds = np.linspace(
        0.05,
        0.95,
        181,
    )

    costs = [
        calculate_cost(
            y,
            probabilities,
            threshold,
        )
        for threshold in thresholds
    ]

    best_index = int(np.argmin(costs))

    return float(thresholds[best_index])


def main():

    df = load_data()

    X = df.drop(columns=["bad"])
    y = df["bad"]

    models = {
        "logistic": Pipeline([
            (
                "pre",
                build_preprocessor(X),
            ),
            (
                "model",
                LogisticRegression(
                    max_iter=3000,
                    class_weight="balanced",
                ),
            ),
        ]),

        "random_forest": Pipeline([
            (
                "pre",
                build_preprocessor(X),
            ),
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

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    all_results = []

    for model_name, model in models.items():

        fold_results = []

        for fold, (train_idx, val_idx) in enumerate(
            cv.split(X, y),
            start=1,
        ):

            X_train = X.iloc[train_idx]
            X_val = X.iloc[val_idx]

            y_train = y.iloc[train_idx]
            y_val = y.iloc[val_idx]

            model.fit(
                X_train,
                y_train,
            )

            probabilities = model.predict_proba(
                X_val
            )[:, 1]

            # ----------------------------------------------------------
            # Standard 0.50 operating threshold
            # ----------------------------------------------------------

            cost_050 = calculate_cost(
                y_val,
                probabilities,
                0.50,
            )

            # ----------------------------------------------------------
            # Fold-specific cost-optimal threshold
            # ----------------------------------------------------------

            optimal_threshold = find_optimal_threshold(
                y_val,
                probabilities,
            )

            optimal_cost = calculate_cost(
                y_val,
                probabilities,
                optimal_threshold,
            )

            fold_results.append({
                "model": model_name,
                "fold": fold,
                "roc_auc": roc_auc_score(
                    y_val,
                    probabilities,
                ),
                "pr_auc": average_precision_score(
                    y_val,
                    probabilities,
                ),
                "brier": brier_score_loss(
                    y_val,
                    probabilities,
                ),
                "cost_at_0_50": cost_050,
                "optimal_threshold": optimal_threshold,
                "optimal_cost": optimal_cost,
            })

        fold_df = pd.DataFrame(
            fold_results
        )

        print()
        print("=" * 80)
        print(model_name.upper())
        print("=" * 80)

        print(
            fold_df.round(4).to_string(
                index=False
            )
        )

        summary = {
            "model": model_name,

            "roc_auc_mean":
                fold_df["roc_auc"].mean(),

            "roc_auc_std":
                fold_df["roc_auc"].std(),

            "pr_auc_mean":
                fold_df["pr_auc"].mean(),

            "pr_auc_std":
                fold_df["pr_auc"].std(),

            "brier_mean":
                fold_df["brier"].mean(),

            "brier_std":
                fold_df["brier"].std(),

            "cost_at_0_50_mean":
                fold_df["cost_at_0_50"].mean(),

            "cost_at_0_50_std":
                fold_df["cost_at_0_50"].std(),

            "optimal_cost_mean":
                fold_df["optimal_cost"].mean(),

            "optimal_cost_std":
                fold_df["optimal_cost"].std(),

            "optimal_threshold_mean":
                fold_df["optimal_threshold"].mean(),

            "optimal_threshold_std":
                fold_df["optimal_threshold"].std(),
        }

        all_results.append(summary)

    results_df = pd.DataFrame(
        all_results
    )

    print()
    print("=" * 80)
    print("COST-SENSITIVE CROSS-VALIDATION SUMMARY")
    print("=" * 80)

    print(
        results_df.round(4).to_string(
            index=False
        )
    )

    ART.mkdir(
        exist_ok=True
    )

    results_df.to_csv(
        ART / "cross_validation_results.csv",
        index=False,
    )


if __name__ == "__main__":
    main()