# Model Card — Retail Credit Risk Prototype

## Model

Primary model: logistic regression with one-hot encoding, median/mode imputation, numeric standardisation, and class weighting.

Challenger: random forest.

## Intended use

Research and portfolio-project demonstration of:

- credit-risk classification;
- cost-sensitive decision thresholds;
- probability scoring;
- model governance concepts.

## Not intended for

- production underwriting;
- automated adverse-action decisions;
- regulatory capital calculations;
- individual credit decisions;
- use outside a validated institutional risk-management framework.

## Target

`bad = 1` means the UCI target indicates bad credit risk.

## Validation

The pipeline uses a stratified 80/20 train/test split with fixed random seed 42. This is deliberately simple and should be replaced by out-of-time validation and repeated resampling for production work.

## Known limitations

1. Only 1,000 historical observations.
2. Historical German credit context; not representative of Indian retail borrowers.
3. Target is a credit-risk label, not a modern regulatory default definition.
4. No LGD/EAD data are available.
5. No reject inference.
6. No economic cycle coverage.
7. No documented production sampling frame.
8. Some attributes may act as proxies for sensitive characteristics.
9. Model performance is expected to be unstable under population shift.

## Fairness

The pipeline should be extended to evaluate performance and error rates across relevant segments. Segment diagnostics are not proof of legal fairness. Any production deployment requires legal, compliance and model-risk review appropriate to the jurisdiction.

## Explainability

The logistic model is selected as the primary model because its structure is comparatively auditable. A production scorecard would additionally document variable transformations, binning, monotonicity where required, reason codes, stability and approval governance.
