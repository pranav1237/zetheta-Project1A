# Credit Risk Decision Policy

## 1. Purpose

This policy defines how the credit-risk model should be interpreted and used as a decision-support tool for credit underwriting.

The model estimates the probability that an applicant represents a bad-credit outcome. It is intended to support underwriting decisions, not replace human review or institutional credit policy.

---

## 2. Target Definition

The original UCI German Credit dataset defines:

- `1` = good credit
- `2` = bad credit

For modelling, the target is transformed to:

- `0` = good
- `1` = bad

Therefore, the model probability represents an estimated probability of bad credit, subject to the limitations of the dataset and model calibration.

---

## 3. Candidate Models

Two candidate models were evaluated:

1. Logistic Regression
2. Random Forest

Both models use preprocessing appropriate for mixed categorical and numerical variables.

---

## 4. Model Selection

Five-fold stratified cross-validation produced the following results:

| Model | ROC-AUC Mean | PR-AUC Mean | Brier Mean |
|---|---:|---:|---:|
| Logistic Regression | 0.7855 | 0.6102 | 0.1884 |
| Random Forest | 0.7899 | 0.6318 | 0.1894 |

Random Forest provides a modest advantage in discrimination, particularly on PR-AUC.

The difference is not large enough to claim that Random Forest is universally superior. Therefore, model selection should consider discrimination, cost, stability, interpretability, calibration, and operational requirements.

For this project, Random Forest is treated as the candidate champion model.

---

## 5. Cost-Sensitive Decisioning

The project assumes an asymmetric cost structure:

- False positive: classifying a good borrower as bad = cost 1
- False negative: classifying a bad borrower as good = cost 5

This reflects the greater assumed business consequence of approving a borrower who subsequently represents bad credit compared with unnecessarily rejecting a good borrower.

The cost function is:

`Cost = 5 × FN + 1 × FP`

A threshold of 0.50 is therefore not automatically optimal.

Cross-validation produced:

| Model | Cost @ 0.50 | Mean Optimized Cost | Mean Optimal Threshold |
|---|---:|---:|---:|
| Logistic Regression | 123.4 | 98.6 | 0.277 |
| Random Forest | 131.0 | 95.6 | 0.366 |

The optimal threshold varies substantially between folds. This indicates that the threshold should not be considered a universally fixed property of the model.

In production, the threshold should be selected using an independent validation period and the institution's actual economic cost assumptions.

---

## 6. Risk Segmentation

The project produces three operational risk bands:

### Low Risk

Recommended action:

**Standard underwriting**

The modelled risk is relatively low and no additional intervention is indicated solely by the model.

### Medium Risk

Recommended action:

**Manual review / additional verification**

Applications in this band warrant additional information or human assessment.

### High Risk

Recommended action:

**Enhanced review or decline**

These applications represent materially higher estimated risk and require enhanced underwriting scrutiny.

Risk bands should be calibrated against institutional approval rates, expected loss, policy constraints, and regulatory requirements before production use.

---

## 7. Explainability

Feature analysis identified `Attribute1` as the most influential predictor.

Permutation importance produced:

| Feature | Mean Importance |
|---|---:|
| Attribute1 | 0.1334 |
| Attribute3 | 0.0126 |
| Attribute2 | 0.0123 |
| Attribute4 | 0.0100 |
| Attribute5 | 0.0085 |

Attribute1 also shows substantial bad-rate separation in exploratory analysis.

Feature importance should be interpreted as evidence of predictive association rather than causation.

---

## 8. Underwriting Controls

The model should not be the sole basis for an irreversible credit decision.

A production implementation should include:

- model input validation;
- missing-value handling;
- out-of-range detection;
- monitoring for data drift;
- monitoring for prediction drift;
- threshold performance monitoring;
- periodic calibration assessment;
- human review for borderline cases;
- documented override procedures;
- periodic model validation.

---

## 9. Limitations

The analysis is subject to important limitations:

1. The dataset contains only 1,000 observations.
2. The dataset is historical and may not represent a modern lending population.
3. No external validation dataset was used.
4. No temporal validation was performed.
5. The assumed cost matrix is illustrative rather than institution-specific.
6. Thresholds are sensitive to sample composition and economic assumptions.
7. Feature importance does not establish causality.
8. The analysis does not establish regulatory approval for production credit decisioning.
9. Calibration requires further assessment before interpreting predicted probabilities as production-grade PD estimates.
10. Fairness and protected-group impact analysis should be conducted before deployment where applicable.

---

## 10. Production Recommendation

The model should initially be deployed, if at all, as a decision-support or pilot model rather than an autonomous approval/decline mechanism.

Before production use, the institution should independently validate:

- predictive performance;
- calibration;
- stability;
- population representativeness;
- economic cost assumptions;
- fairness;
- regulatory compliance;
- operational integration.

The threshold should be selected using production-relevant validation data rather than copied directly from this project.


---

## 11. Calibration Interpretation

The five-fold out-of-fold calibration analysis produced:

| Model | Brier Score | Mean Absolute Calibration Gap |
|---|---:|---:|
| Logistic Regression | 0.1884 | 0.1327 |
| Random Forest | 0.1894 | 0.1465 |

Lower values indicate better probability quality.

Logistic Regression produced slightly better calibration metrics, while Random Forest produced slightly stronger discrimination metrics in cross-validation.

Accordingly, the project does not treat Random Forest as unconditionally superior.

Random Forest is preferred when ranking/discrimination is the primary objective, while Logistic Regression remains a credible alternative where probability quality, transparency, and simpler model structure are prioritized.

The calibration analysis is based on the available historical dataset and should not be interpreted as evidence that either model produces production-grade probability of default estimates.

---

## 12. Risk-Band Sample Size

The current risk segmentation produced:

| Risk Band | Borrowers | Observed Bad Rate | Average Model PD |
|---|---:|---:|---:|
| Low | 15 | 0.00% | 15.69% |
| Medium | 69 | 13.04% | 31.40% |
| High | 116 | 43.97% | 57.37% |

The ordering of observed risk is directionally consistent with the model's risk ranking.

However, the Low-risk segment contains only 15 observations. Its observed 0% bad rate should therefore not be interpreted as evidence that the true population default rate is zero.

Risk-band boundaries should be recalibrated using a substantially larger and representative validation population before production deployment.