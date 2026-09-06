# Model Governance & Monitoring Policy

## 1. Purpose

This document defines the governance, monitoring, validation, and escalation framework for the credit-risk model developed in this project.

The purpose is to ensure that model performance, data quality, probability quality, and operational behaviour remain observable after deployment.

---

## 2. Model Ownership

The model should have clearly assigned ownership across three responsibilities:

### Model Owner

Responsible for:

- business purpose;
- approved use cases;
- decision thresholds;
- economic assumptions;
- operational implementation.

### Model Development

Responsible for:

- source code;
- feature engineering;
- model training;
- performance analysis;
- documentation;
- reproducibility.

### Independent Validation

Responsible for challenging:

- methodology;
- assumptions;
- data quality;
- performance;
- calibration;
- stability;
- limitations;
- implementation controls.

Development and independent validation should be separated in a production environment.

---

## 3. Data Quality Monitoring

The monitoring implementation checks:

- row count;
- column count;
- missing values;
- duplicate records;
- expected columns;
- unexpected columns;
- target availability where labels exist.

A production implementation should additionally monitor:

- unexpected categorical values;
- numerical range violations;
- feature-level missingness;
- changes in data types;
- source-system failures;
- stale data;
- duplicate application identifiers.

A schema failure should prevent automated scoring until investigated.

---

## 4. Population Stability

Population Stability Index (PSI) can be used to compare a reference population with a later monitoring population.

Illustrative interpretation:

| PSI | Interpretation |
|---:|---|
| < 0.10 | Stable |
| 0.10–0.25 | Moderate change |
| ≥ 0.25 | Significant change |

These thresholds are monitoring conventions rather than universal regulatory limits.

The project produced a PSI demonstration of 0.0404 for `Attribute2`, classified as stable.

However, this value must not be interpreted as evidence of production stability because the comparison uses two portions of the same historical dataset rather than independent development and production populations.

---

## 5. Prediction Monitoring

The monitoring framework records:

- number of scored observations;
- average predicted PD;
- observed bad rate;
- ROC-AUC where labels are available;
- PR-AUC where labels are available;
- Brier score;
- risk-band distribution.

For the current test population, the Random Forest produced:

| Metric | Value |
|---|---:|
| Observations | 200 |
| Average predicted PD | 45.28% |
| Observed bad rate | 30.00% |
| ROC-AUC | 0.7746 |
| PR-AUC | 0.5815 |
| Brier score | 0.1941 |

The difference between average predicted PD and observed bad rate should be investigated through calibration analysis and population monitoring.

It should not automatically be interpreted as model failure because the dataset, sampling process, target definition, and prediction population all affect the relationship.

---

## 6. Performance Monitoring

When outcome labels become available, production monitoring should calculate:

- ROC-AUC;
- PR-AUC;
- Brier score;
- confusion matrix;
- precision;
- recall;
- false-positive count;
- false-negative count;
- business cost under the approved cost matrix.

Performance should be evaluated against an approved baseline rather than against an arbitrary universal threshold.

---

## 7. Threshold Monitoring

The project demonstrates that the economically optimal threshold differs from 0.50.

Cross-validation produced:

| Model | Mean Optimal Threshold | Mean Optimal Cost |
|---|---:|---:|
| Logistic Regression | 0.277 | 98.6 |
| Random Forest | 0.366 | 95.6 |

The threshold varies between folds.

Therefore, a production threshold should be approved using representative validation data and documented business costs.

A threshold should not be changed solely because a short-term sample produces a lower apparent cost.

---

## 8. Calibration Monitoring

The project produced the following five-fold calibration results:

| Model | Brier Score | Mean Absolute Calibration Gap |
|---|---:|---:|
| Logistic Regression | 0.1884 | 0.1327 |
| Random Forest | 0.1894 | 0.1465 |

Lower values indicate better probability quality.

Logistic Regression demonstrated slightly better calibration, while Random Forest demonstrated stronger discrimination.

This means model selection is a trade-off rather than a simple winner-takes-all comparison.

Before production use, probability calibration should be assessed on an independent validation population.

---

## 9. Monitoring Triggers

The following should trigger investigation:

### Data-quality trigger

Any of:

- schema mismatch;
- unexpected categories;
- unexplained missing-value increase;
- duplicate-record increase;
- invalid numerical values.

### Population trigger

PSI ≥ 0.10 should trigger investigation.

PSI ≥ 0.25 should trigger formal review and consideration of model redevelopment or recalibration.

### Performance trigger

Material deterioration from the approved baseline in:

- ROC-AUC;
- PR-AUC;
- Brier score;
- recall;
- precision;
- business cost.

### Calibration trigger

Persistent divergence between predicted probabilities and observed bad rates should trigger calibration investigation.

---

## 10. Model Risk Escalation

Monitoring results should be classified as:

### Green

No material deterioration.

Continue normal monitoring.

### Amber

Potential deterioration or moderate data/population change.

Actions may include:

- investigation;
- increased monitoring frequency;
- calibration review;
- threshold review.

### Red

Material deterioration, significant population shift, or data-quality failure.

Actions may include:

- suspend automated decisions;
- route applications to manual review;
- initiate model validation;
- recalibrate or redevelop the model.

---

## 11. Human Oversight

The model should be treated as decision support rather than an autonomous credit authority.

Borderline or high-risk applications may require:

- manual underwriting;
- additional verification;
- documentation of overrides;
- second-level approval.

Human overrides should be logged so that override rates and outcomes can be monitored.

---

## 12. Auditability

Every production model release should maintain:

- model version;
- training dataset version;
- feature definitions;
- preprocessing configuration;
- model parameters;
- validation results;
- approved threshold;
- approval date;
- model owner;
- validation evidence;
- deployment date.

The project repository should preserve reproducible source code and test evidence.

---

## 13. Limitations

This monitoring framework is a project-level implementation and is not a substitute for a production model-risk management framework.

In particular:

- the dataset is historical;
- the sample is relatively small;
- production population drift cannot be established from this dataset;
- the assumed cost matrix is illustrative;
- no independent temporal validation population is available;
- regulatory requirements depend on the actual institution and jurisdiction.

These limitations must be addressed before production deployment.

---

## 14. Recommended Monitoring Frequency

A production implementation should monitor:

| Monitoring Area | Suggested Frequency |
|---|---|
| Data quality | Every scoring batch |
| Schema validation | Every scoring batch |
| Population distribution | Monthly |
| Average predicted PD | Monthly |
| Risk-band distribution | Monthly |
| Model performance | Monthly/quarterly when outcomes mature |
| Calibration | Quarterly |
| Full model validation | At least annually or according to institutional policy |

Actual frequencies should be determined by materiality, portfolio volume, model usage, and institutional model-risk policy.

---

## 15. Governance Principle

The central governance principle is:

> A credit-risk model is not considered reliable merely because it performed well during development.

Reliability requires continuing evidence that:

1. inputs remain valid;
2. the population remains sufficiently comparable;
3. predictions remain useful;
4. probabilities remain appropriately calibrated;
5. economic decisions remain aligned with approved costs;
6. model limitations remain understood;
7. human oversight remains effective.