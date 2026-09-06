from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from data_dictionary import ATTRIBUTE_DESCRIPTIONS, CATEGORY_MAPPINGS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "german_credit.csv"
ART = ROOT / "artifacts"
ART.mkdir(exist_ok=True)


def load_data():
    df = pd.read_csv(DATA)

    # UCI: 1 = good, 2 = bad
    df["bad"] = (df["target"] == 2).astype(int)

    return df


def categorical_risk_table(df, column):
    result = (
        df.groupby(column)["bad"]
        .agg(
            borrowers="size",
            bad_count="sum",
            bad_rate="mean",
        )
        .sort_values("bad_rate", ascending=False)
    )

    result["bad_rate"] = result["bad_rate"] * 100
    return result


def numeric_summary(df):
    numeric = [
        "Attribute2",   # duration
        "Attribute5",   # credit amount
        "Attribute8",   # installment rate
        "Attribute11",  # residence
        "Attribute13",  # age
        "Attribute16",  # existing credits
        "Attribute18",  # dependants
    ]

    return (
        df.groupby("bad")[numeric]
        .agg(["mean", "median", "std"])
        .round(2)
    )


def main():
    df = load_data()

    print("=" * 70)
    print("DATASET PROFILE")
    print("=" * 70)
    print(f"Rows: {len(df):,}")
    print(f"Predictors: {df.shape[1] - 2}")
    print(f"Missing values: {df.isna().sum().sum():,}")

    print("\nTARGET DISTRIBUTION")
    print(df["bad"].value_counts().rename(index={
        0: "Good",
        1: "Bad"
    }))

    print("\nTARGET RATE")
    print(
        (df["bad"].value_counts(normalize=True)
         .rename(index={0: "Good", 1: "Bad"}) * 100)
        .round(2)
    )

    categorical_columns = [
        "Attribute1",
        "Attribute3",
        "Attribute4",
        "Attribute6",
        "Attribute7",
        "Attribute9",
        "Attribute10",
        "Attribute12",
        "Attribute14",
        "Attribute15",
        "Attribute17",
        "Attribute19",
        "Attribute20",
    ]

    for column in categorical_columns:
        table = categorical_risk_table(df, column)

        table = table.reset_index()

        table["category"] = table[column].map(
            CATEGORY_MAPPINGS.get(column, {})
        )

        table["attribute"] = ATTRIBUTE_DESCRIPTIONS[column]

        table = table[
            [
                "attribute",
                column,
                "category",
                "borrowers",
                "bad_count",
                "bad_rate",
            ]
        ]

        print("\n" + "=" * 70)
        print(f"RISK BY {ATTRIBUTE_DESCRIPTIONS[column]}")
        print("=" * 70)
        print(table.round(2).to_string(index=False))

        table.to_csv(
            ART / f"risk_by_{column}.csv",
            index=False
        )
    plt.title("Credit Amount by Credit-Risk Outcome")
    plt.suptitle("")
    plt.xlabel("Bad Credit (0 = Good, 1 = Bad)")
    plt.ylabel("Credit Amount")

    plt.tight_layout()
    plt.savefig(
        ART / "credit_amount_by_risk.png",
        dpi=200
    )
    plt.close()

    # Duration distribution
    plt.figure(figsize=(8, 5))

    df.boxplot(
        column="Attribute2",
        by="bad"
    )

    plt.title("Loan Duration by Credit-Risk Outcome")
    plt.suptitle("")
    plt.xlabel("Bad Credit (0 = Good, 1 = Bad)")
    plt.ylabel("Duration (months)")

    plt.tight_layout()
    plt.savefig(
        ART / "duration_by_risk.png",
        dpi=200
    )
    plt.close()

    print("\nEDA completed successfully.")
    print(f"Outputs written to: {ART}")


if __name__ == "__main__":
    main()
