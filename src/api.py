from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
MODEL = joblib.load(ROOT / "artifacts" / "logistic.joblib")

app = FastAPI(title="Zetheta Credit Risk Prototype", version="0.1.0")

class Applicant(BaseModel):
    # Flexible fields are intentionally accepted because the UCI schema contains
    # mixed categorical and numeric attributes.
    model_config = {"extra": "allow"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/score")
def score(applicant: Applicant):
    X = pd.DataFrame([applicant.model_dump()])
    p = float(MODEL.predict_proba(X)[0, 1])
    return {
        "probability_of_bad_credit": p,
        "risk_band": "LOW_RISK" if p < .20 else ("MEDIUM_RISK" if p < .40 else "HIGH_RISK"),
        "production_use": False
    }
