from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "german_credit.csv"
ART = ROOT / "artifacts"

MODEL_PATH = ART / "random_forest.joblib"


RANDOM_STATE = 42


def load_data():

    df = pd.read_csv(DATA)

    df["bad"] = (
        df["target"] == 2
    ).astype(int)

    return df.drop(columns=["target"])


def main():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Run `python src/pipeline.py` first."
        )

    df = load_data()

    X = df.drop(columns=["bad"])
    y = df["bad"]

    # Recreate the same stratified split used by pipeline.py.
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    model = joblib.load(MODEL_PATH)

    baseline_probability = (
        model.predict_proba(X_test)[:, 1]
    )

    baseline_auc = roc_auc_score(
        y_test,
        baseline_probability,
    )

    print("=" * 80)
    print("PERMUTATION IMPORTANCE")
    print("=" * 80)

    print(
        f"Baseline ROC-AUC: {baseline_auc:.4f}"
    )

    result = permutation_importance(
        model,
        X_test,
        y_test,
        scoring="roc_auc",
        n_repeats=20,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    importance_df = pd.DataFrame({
        "feature": X_test.columns,
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std,
    })

    importance_df["importance_pct"] = (
        importance_df["importance_mean"] * 100
    )

    importance_df = (
        importance_df
        .sort_values(
            "importance_mean",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    print()
    print(
        importance_df
        .round(4)
        .to_string(index=False)
    )

    importance_df.to_csv(
        ART / "permutation_importance.csv",
        index=False,
    )


if __name__ == "__main__":
    main()