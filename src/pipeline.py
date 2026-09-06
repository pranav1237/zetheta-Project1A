from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    roc_auc_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "german_credit.csv"
ART = ROOT / "artifacts"
ART.mkdir(exist_ok=True)

RANDOM_STATE = 42

# UCI German Credit asymmetric cost matrix:
# False positive (good classified as bad) = 1
# False negative (bad classified as good) = 5
FALSE_NEGATIVE_COST = 5
FALSE_POSITIVE_COST = 1


def load_data():
    if not DATA.exists():
        raise FileNotFoundError(
            "Run `python src/download_data.py` first."
        )

    df = pd.read_csv(DATA)

    if "target" not in df:
        raise ValueError("Target column missing.")

    # UCI: 1 = good, 2 = bad.
    # Convert to bad=1 because probability of default / bad credit
    # is the event of interest.
    df["bad"] = (df["target"] == 2).astype(int)

    return df.drop(columns=["target"])


def cost_at_threshold(
    y,
    p,
    threshold,
    false_negative_cost=FALSE_NEGATIVE_COST,
    false_positive_cost=FALSE_POSITIVE_COST,
):
    pred_bad = (p >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y,
        pred_bad,
        labels=[0, 1],
    ).ravel()

    cost = (
        false_negative_cost * fn
        + false_positive_cost * fp
    )

    return {
        "threshold": float(threshold),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "cost": int(cost),
    }


def metrics(y, p, threshold=0.5):
    d = cost_at_threshold(y, p, threshold)

    pred = (p >= threshold).astype(int)

    d.update({
        "roc_auc": float(
            roc_auc_score(y, p)
        ),
        "pr_auc": float(
            average_precision_score(y, p)
        ),
        "brier": float(
            brier_score_loss(y, p)
        ),
        "precision_bad": float(
            precision_score(
                y,
                pred,
                zero_division=0,
            )
        ),
        "recall_bad": float(
            recall_score(
                y,
                pred,
                zero_division=0,
            )
        ),
    })

    return d


def build_preprocessor(X):
    categorical = X.select_dtypes(
        include=["object", "str", "category", "bool"]
    ).columns.tolist()

    numeric = [
        c for c in X.columns
        if c not in categorical
    ]

    cat_pipe = Pipeline([
        (
            "impute",
            SimpleImputer(strategy="most_frequent"),
        ),
        (
            "onehot",
            OneHotEncoder(handle_unknown="ignore"),
        ),
    ])

    num_pipe = Pipeline([
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
        ("cat", cat_pipe, categorical),
        ("num", num_pipe, numeric),
    ])


def find_cost_optimal_threshold(y, p):
    """
    Select the operating threshold using ONLY the validation set.

    The test set is deliberately not used here.
    """
    grid = np.linspace(0.05, 0.95, 181)

    costs = [
        cost_at_threshold(y, p, threshold)["cost"]
        for threshold in grid
    ]

    best_idx = int(np.argmin(costs))

    return float(grid[best_idx])


def main():
    df = load_data()

    X = df.drop(columns=["bad"])
    y = df["bad"]

    # ------------------------------------------------------------------
    # Three-way split:
    #
    # Train      -> model fitting
    # Validation -> threshold selection
    # Test       -> final unbiased evaluation
    #
    # 60% / 20% / 20%
    # ------------------------------------------------------------------

    X_train, X_temp, y_train, y_temp = train_test_split(
        X,
        y,
        test_size=0.40,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    X_validation, X_test, y_validation, y_test = train_test_split(
        X_temp,
        y_temp,
        test_size=0.50,
        stratify=y_temp,
        random_state=RANDOM_STATE,
    )

    # ------------------------------------------------------------------
    # Model definitions
    # ------------------------------------------------------------------

    logistic = Pipeline([
        (
            "pre",
            build_preprocessor(X_train),
        ),
        (
            "model",
            LogisticRegression(
                max_iter=3000,
                class_weight="balanced",
            ),
        ),
    ])

    forest = Pipeline([
        (
            "pre",
            build_preprocessor(X_train),
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
    ])

    models = {
        "logistic": logistic,
        "random_forest": forest,
    }

    results = {}

    for name, model in models.items():

        # --------------------------------------------------------------
        # 1. Fit ONLY on training data
        # --------------------------------------------------------------
        model.fit(X_train, y_train)

        # --------------------------------------------------------------
        # 2. Validation predictions
        # --------------------------------------------------------------
        p_validation = model.predict_proba(
            X_validation
        )[:, 1]

        validation_default = metrics(
            y_validation,
            p_validation,
            threshold=0.5,
        )

        # Select threshold ONLY on validation data.
        validation_threshold = find_cost_optimal_threshold(
            y_validation,
            p_validation,
        )

        validation_optimal = metrics(
            y_validation,
            p_validation,
            threshold=validation_threshold,
        )

        # --------------------------------------------------------------
        # 3. Final test predictions
        # --------------------------------------------------------------
        p_test = model.predict_proba(
            X_test
        )[:, 1]

        test_default = metrics(
            y_test,
            p_test,
            threshold=0.5,
        )

        # Evaluate the validation-selected threshold on the untouched
        # test set.
        test_at_selected_threshold = metrics(
            y_test,
            p_test,
            threshold=validation_threshold,
        )

        results[name] = {
            "validation": {
                "threshold": 0.5,
                **validation_default,
                "cost_optimal_threshold": validation_threshold,
                "cost_optimal": validation_optimal,
            },
            "test": {
                "threshold": 0.5,
                **test_default,
                "selected_threshold": validation_threshold,
                "selected_threshold_metrics":
                    test_at_selected_threshold,
            },
        }

        # --------------------------------------------------------------
        # Save fitted model
        # --------------------------------------------------------------
        joblib.dump(
            model,
            ART / f"{name}.joblib",
        )

        # --------------------------------------------------------------
        # Save final test predictions
        # --------------------------------------------------------------
        pd.DataFrame({
            "actual_bad": y_test.to_numpy(),
            "predicted_pd": p_test,
            "predicted_bad_at_0_5": (
                p_test >= 0.5
            ).astype(int),
            "predicted_bad_at_selected_threshold": (
                p_test >= validation_threshold
            ).astype(int),
        }).to_csv(
            ART / f"{name}_predictions.csv",
            index=False,
        )

    # ------------------------------------------------------------------
    # Save complete metrics
    # ------------------------------------------------------------------

    (ART / "metrics.json").write_text(
        json.dumps(
            results,
            indent=2,
        )
    )

    (ART / "run_metadata.json").write_text(
        json.dumps(
            {
                "random_state": RANDOM_STATE,
                "train_size": 0.60,
                "validation_size": 0.20,
                "test_size": 0.20,
                "target_definition": (
                    "bad credit = 1; good credit = 0"
                ),
                "cost_matrix": {
                    "false_positive_good_as_bad": 1,
                    "false_negative_bad_as_good": 5,
                },
                "threshold_selection": (
                    "Validation-set cost minimization"
                ),
                "test_set_usage": (
                    "Final evaluation only"
                ),
            },
            indent=2,
        )
    )

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()