from pathlib import Path
import pandas as pd
from ucimlrepo import fetch_ucirepo

OUT = Path(__file__).resolve().parents[1] / "data" / "german_credit.csv"

def main():
    dataset = fetch_ucirepo(id=144)
    X = dataset.data.features.copy()
    y = dataset.data.targets.copy()
    target = y.columns[0]
    df = X.copy()
    df["target"] = y[target].astype(int)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df):,} rows to {OUT}")

if __name__ == "__main__":
    main()
