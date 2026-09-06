import argparse, json
from pathlib import Path
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "artifacts" / "logistic.joblib"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    model = joblib.load(MODEL)
    applicant = json.loads(Path(args.input).read_text())
    X = pd.DataFrame([applicant])
    pd_bad = float(model.predict_proba(X)[0, 1])

    # This is a demonstration policy, not a production credit policy.
    if pd_bad < 0.20:
        band = "LOW_RISK"
    elif pd_bad < 0.40:
        band = "MEDIUM_RISK"
    else:
        band = "HIGH_RISK"

    print(json.dumps({
        "probability_of_bad_credit": round(pd_bad, 6),
        "risk_band": band,
        "note": "Prototype output only; not a lending decision."
    }, indent=2))

if __name__ == "__main__":
    main()
