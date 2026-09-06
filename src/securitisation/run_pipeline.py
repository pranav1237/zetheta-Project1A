"""End-to-end run: load real data -> ECL -> waterfall -> stress -> investor pack.

    python -m src.securitisation.run_pipeline

Writes every artifact to artifacts/securitisation/ so the Power BI model
(powerbi/data_model.md) has fresh CSVs to import.
"""
from __future__ import annotations
from pathlib import Path
import json

from .data_loader import load_loan_pool
from .ecl import calculate_ecl, portfolio_summary
from .waterfall import build_tranches, run_waterfall, credit_enhancement
from .stress_testing import run_scenarios
from .investor_reporting import write_investor_pack

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "securitisation"


def main():
    ART.mkdir(parents=True, exist_ok=True)

    pool = load_loan_pool()

    ecl = calculate_ecl(pool)
    ecl.to_csv(ART / "loan_level_ecl.csv", index=False)

    tranches = build_tranches(float(pool["OriginalLoanAmount"].sum()))
    tranches = credit_enhancement(tranches)
    tranches.to_csv(ART / "tranche_structure.csv", index=False)

    wf = run_waterfall()
    wf.to_csv(ART / "waterfall_monthly.csv", index=False)

    stress = run_scenarios(pool)
    stress.to_csv(ART / "stress_results.csv", index=False)

    write_investor_pack(ART / "investor_pack")

    summary = portfolio_summary(pool)
    (ART / "portfolio_summary.json").write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print("\nStress scenarios:\n", stress.to_string(index=False))
    print(f"\nArtifacts written to {ART}")


if __name__ == "__main__":
    main()
