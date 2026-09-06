# Zetheta WorkBridge — Retail Credit Risk Decisioning & Early-Warning Prototype

**Project type:** BFSI / Retail Lending / Credit Risk Analytics  
**Primary objective:** Build an auditable prototype that estimates probability of credit deterioration from applicant-level information and converts the model into a cost-sensitive underwriting decision.

## Executive summary

This project treats credit scoring as a **decision system**, not merely a classification exercise.

The prototype:

1. Downloads the public UCI Statlog German Credit dataset.
2. Validates the data and preserves a reproducible preprocessing pipeline.
3. Trains an interpretable logistic-regression scorecard baseline and a nonlinear random-forest challenger.
4. Evaluates discrimination (ROC-AUC / PR-AUC), probability quality (Brier score), and business cost using the dataset's published asymmetric error-cost matrix.
5. Selects an operating threshold using expected decision cost rather than defaulting to 0.50.
6. Produces a model card, feature importance, segment-level monitoring tables, and a JSON score for an applicant.
7. Includes controls for leakage, reproducibility, model governance, and fairness review.

**Important limitation:** the UCI dataset is historical and small (1,000 observations). It is suitable for demonstrating methodology, not for deploying a production lending model.

## Why this is BFSI-relevant

The Basel Framework explicitly uses risk components such as probability of default (PD), loss given default (LGD), exposure at default (EAD), and maturity in internal-ratings-based credit-risk approaches. This project focuses on the PD/decisioning layer and does not claim to estimate regulatory capital.

The UCI dataset itself supplies a cost matrix in which classifying a bad credit as good is five times as costly as classifying a good credit as bad. The project therefore makes the threshold-selection problem explicit.

## Data source

UCI Machine Learning Repository, **Statlog (German Credit Data)**:
https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data

The dataset has 1,000 observations and 20 predictive attributes. The target is binary: good vs bad credit risk. UCI states that the dataset is licensed under CC BY 4.0.

The code downloads the dataset through `ucimlrepo`; raw data are deliberately not committed to this repository.

## Architecture

```text
Public UCI data
      |
      v
Data acquisition + validation
      |
      v
Train/test split (stratified)
      |
      +-----------------------+
      |                       |
      v                       v
Logistic baseline       Random Forest challenger
      |                       |
      +-----------+-----------+
                  v
        Metrics + cost analysis
                  |
                  v
        Threshold optimization
                  |
                  v
        Model card + monitoring
                  |
                  v
          JSON scoring API
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python src/pipeline.py
python src/score_applicant.py --input examples/applicant.json
```

Outputs are written to `artifacts/`.

## Suggested 15-day execution plan

| Day | Workstream | Output |
|---|---|---|
| 1 | Business framing + BFSI research | Problem statement |
| 2 | Data acquisition + data dictionary | Data validation |
| 3 | EDA | Risk-driver hypotheses |
| 4 | Baseline scorecard | Logistic model |
| 5 | Challenger model | Random forest |
| 6 | Validation design | Robust metrics |
| 7 | Cost-sensitive thresholding | Decision policy |
| 8 | Calibration | Probability-quality analysis |
| 9 | Explainability | Feature / segment analysis |
| 10 | Fairness review | Segment diagnostics |
| 11 | Stress tests | Sensitivity analysis |
| 12 | API / operationalization | Scoring endpoint |
| 13 | Governance | Model card + controls |
| 14 | Documentation | Final report |
| 15 | QA / packaging | Submission repository |

## Governance requirements before production

Do **not** use this prototype to approve/decline real borrowers. A production system would additionally require:

- institution-specific definition of default;
- representative, current data;
- reject-inference treatment where relevant;
- out-of-time validation;
- calibration and stability monitoring;
- policy / affordability rules independent of the ML model;
- explainability and adverse-action processes applicable to the jurisdiction;
- privacy, security, access controls and retention rules;
- independent model validation;
- documented overrides and human escalation;
- drift / PSI monitoring;
- challenger governance and rollback procedures.

## References

- UCI Statlog German Credit Data: https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data
- Basel Framework, CRE32 — risk components: https://www.bis.org/baselframework/chapter/CRE/32.htm
- RBI Master Direction — Credit Information Reporting Directions, 2025: https://www.rbi.org.in/
