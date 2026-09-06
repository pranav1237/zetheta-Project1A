import numpy as np
import pandas as pd
import pytest

from src.monitoring import (
    data_quality_report,
    population_stability_index,
    prediction_monitoring,
    psi_interpretation,
)


def test_psi_identical_distributions_is_zero():
    distribution = np.array([10, 20, 30, 40])

    psi = population_stability_index(
        distribution,
        distribution,
    )

    assert psi == pytest.approx(0.0)


def test_psi_rejects_different_lengths():
    with pytest.raises(ValueError):
        population_stability_index(
            np.array([10, 20]),
            np.array([10, 20, 30]),
        )


def test_psi_interpretation():
    assert psi_interpretation(0.05) == "stable"
    assert psi_interpretation(0.15) == "moderate_change"
    assert psi_interpretation(0.30) == "significant_change"


def test_data_quality_report():
    df = pd.DataFrame({
        "Attribute1": ["A11", "A12"],
        "target": [1, 2],
    })

    report = data_quality_report(df)

    assert report["rows"] == 2
    assert report["columns"] == 2
    assert report["missing_values"] == 0
    assert report["duplicate_rows"] == 0
    assert report["schema_valid"] is False


def test_prediction_monitoring():
    predictions = pd.DataFrame({
        "actual_bad": [0, 1, 0, 1],
        "predicted_pd": [0.10, 0.80, 0.20, 0.70],
    })

    result = prediction_monitoring(predictions)

    assert result["observations"] == 4
    assert result["average_pd"] == pytest.approx(0.45)
    assert result["observed_bad_rate"] == pytest.approx(0.50)
    assert 0 <= result["brier_score"] <= 1
    assert 0 <= result["roc_auc"] <= 1
    assert 0 <= result["pr_auc"] <= 1