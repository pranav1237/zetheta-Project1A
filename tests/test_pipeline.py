import numpy as np
from src.pipeline import cost_at_threshold

def test_cost_matrix_penalizes_false_negative_more():
    y = np.array([1, 1, 0, 0])
    p = np.array([0.1, 0.9, 0.1, 0.9])
    # threshold .5 => one FN and one FP => 5 + 1
    result = cost_at_threshold(y, p, .5)
    assert result["fn"] == 1
    assert result["fp"] == 1
    assert result["cost"] == 6
