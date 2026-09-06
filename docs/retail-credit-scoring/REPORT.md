# Zetheta WorkBridge Project Report
## Retail Credit Risk Decisioning & Early-Warning Prototype

### 1. Problem statement

Retail lenders need to distinguish applicants with materially different credit-risk profiles while balancing two competing errors: rejecting a borrower who would perform well and approving a borrower who is likely to become problematic.

The project objective is to build a reproducible proof-of-concept for estimating probability of bad credit risk and converting that probability into a business operating threshold.

### 2. Business framing

The project is deliberately framed around a **decision policy** rather than model accuracy alone.

For the UCI dataset, the published cost matrix assigns a cost of 5 when a genuinely bad credit is classified as good, versus 1 when a genuinely good credit is classified as bad. That asymmetry is economically intuitive: approving a risky borrower can be more costly than referring a good borrower for additional review.

Therefore:

`Expected decision cost = 5 × false negatives + 1 × false positives`

The pipeline searches candidate thresholds and reports the cost-minimising threshold on the held-out test sample.

### 3. Industry context

Basel's credit-risk framework describes probability of default (PD), loss given default (LGD), exposure at default (EAD), and maturity as risk components in IRB approaches. This prototype addresses only the PD/decisioning concept and should not be interpreted as a regulatory capital model.

For an India-oriented implementation, credit-information governance must also be considered. RBI's Credit Information Reporting Directions establish requirements around reporting and dissemination of credit information and apply to relevant regulated entities and credit information companies.

### 4. Dataset

The UCI Statlog German Credit dataset contains 1,000 observations and 20 predictive attributes. Variables cover checking-account status, loan duration, credit history, purpose, credit amount, savings, employment, installment rate, personal status, guarantors, residence, property, age, other payment plans, housing, existing credits, job, dependants, telephone and foreign-worker status.

The dataset is public and licensed CC BY 4.0 according to UCI.

### 5. Methodology

#### 5.1 Data quality

The pipeline verifies:

- target presence;
- target coding;
- categorical/numeric schema;
- missing-value handling inside the model pipeline;
- reproducibility through fixed random seed.

Raw data are not committed to the repository.

#### 5.2 Baseline

The baseline is logistic regression because credit-risk systems benefit from transparency, stable coefficients, and straightforward reason-code generation.

#### 5.3 Challenger

A random forest is included to test whether nonlinear interactions materially improve discrimination.

#### 5.4 Validation

A stratified 80/20 holdout is used for the initial demonstration. This is not sufficient for production validation. A production-grade extension should use repeated cross-validation plus an out-of-time sample.

#### 5.5 Metrics

The pipeline reports:

- ROC-AUC;
- PR-AUC;
- Brier score;
- precision and recall for bad-risk classification;
- confusion matrix;
- business cost under the published asymmetric matrix;
- threshold that minimises test-set cost.

### 6. How to reproduce

```bash
python src/download_data.py
python src/pipeline.py
python src/score_applicant.py --input examples/applicant.json
```

### 7. Interpretation framework

A model should not be judged by a single metric.

- **ROC-AUC:** ranking ability across thresholds.
- **PR-AUC:** useful when the event class is relatively less frequent.
- **Brier score:** probability-quality signal.
- **Recall for bad risk:** how many risky cases are captured.
- **Business cost:** whether the operating point aligns with the stated economics.

The most important analytical question is not "Which model has the highest AUC?" but "Which operating point gives an acceptable trade-off between risk capture, customer friction, and expected loss?"

### 8. Fairness and responsible lending

Credit models can amplify historical patterns. A production assessment should compare approval/decline rates, false-positive rates, false-negative rates and calibration across legally relevant segments.

The presence of a `foreign_worker` variable makes the dataset particularly useful for demonstrating why model governance must inspect potential proxy or protected-attribute effects. This is an analytical audit flag, not a conclusion that the variable is unlawful to use in every jurisdiction.

### 9. Production architecture proposal

```text
Application
   |
   v
Identity + consent + data-quality checks
   |
   v
Credit bureau / internal banking data
   |
   v
Feature store + policy engine
   |
   +----> PD model
   |
   +----> Affordability / eligibility rules
   |
   v
Decision orchestration
   |
   +----> Approve
   +----> Refer to human
   +----> Decline
   |
   v
Audit log + monitoring
```

The model should not be the sole decision-maker. Policy rules, affordability checks, fraud controls and human escalation should remain separate control layers.

### 10. Monitoring proposal

At minimum, monitor monthly:

| Control | Example trigger |
|---|---|
| Population Stability Index | Investigate material feature drift |
| Bad-rate by score band | Compare observed vs expected |
| Calibration | Recalibration review if material |
| Missingness | Alert on new missing-data patterns |
| Segment error rates | Investigate material divergence |
| Approval rate | Compare with policy baseline |
| Override rate | Review unusual manual behaviour |
| Data freshness | Alert on stale bureau/internal feeds |

Exact thresholds should be set by the institution's model-risk function rather than copied from a generic template.

### 11. Key limitations

This is a methodology demonstration, not a deployable lending model. The dataset is old, small and not representative of current Indian retail-credit populations. It lacks the longitudinal information needed for true early-warning modelling and lacks LGD/EAD data needed for expected-loss estimation.

### 12. Deliverables

- reproducible data acquisition;
- preprocessing and modelling pipeline;
- interpretable baseline;
- nonlinear challenger;
- cost-sensitive threshold analysis;
- applicant scoring script;
- FastAPI prototype;
- tests;
- model card;
- project report;
- governance notes.

### 13. Original contribution

The main project contribution is to combine three layers that are often treated separately in classroom ML projects:

1. **BFSI decision economics** — asymmetric loss and operating threshold;
2. **model-risk governance** — validation, limitations, fairness and monitoring;
3. **operationalisation** — reproducible pipeline plus scoring API.

This makes the deliverable closer to a small credit-risk product prototype than a standalone classification notebook.
