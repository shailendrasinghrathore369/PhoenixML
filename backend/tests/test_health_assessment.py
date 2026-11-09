import pytest
import math
from app.monitoring.health import (
    HealthAssessor,
    HealthScoreConfiguration,
    HealthStatus,
    HealthAssessmentResult
)

def test_all_metrics_available():
    assessor = HealthAssessor()
    # 0.90, 0.88, 0.85, 0.92
    # Normalized: 90, 88, 85, 92
    # weights: f1(0.4) = 36.8, prec(0.25) = 22, rec(0.25) = 21.25, acc(0.1) = 9
    # total = 36.8 + 22 + 21.25 + 9 = 89.05
    res = assessor.assess(accuracy=0.90, precision=0.88, recall=0.85, f1_score=0.92)
    assert res.health_status == HealthStatus.HEALTHY
    assert math.isclose(res.health_score, 89.05)
    assert res.normalized_metrics["f1_score"] == 92.0
    assert "accuracy" in res.available_metrics
    assert "precision" in res.available_metrics
    assert "recall" in res.available_metrics
    assert "f1_score" in res.available_metrics

def test_missing_f1():
    assessor = HealthAssessor()
    # f1 missing. Remaining weights sum = 0.60
    # precision = 0.25/0.60, recall = 0.25/0.60, accuracy = 0.10/0.60
    res = assessor.assess(accuracy=0.90, precision=0.88, recall=0.85, f1_score=None)
    assert "f1_score" not in res.available_metrics
    assert math.isclose(res.effective_weights["precision"], 0.25 / 0.60)
    assert math.isclose(res.effective_weights["recall"], 0.25 / 0.60)
    assert math.isclose(res.effective_weights["accuracy"], 0.10 / 0.60)
    # score = (88 * 0.4166) + (85 * 0.4166) + (90 * 0.1666) = 36.66 + 35.416 + 15 = 87.0833
    assert res.health_status == HealthStatus.HEALTHY
    assert math.isclose(res.health_score, (88 * (0.25/0.60)) + (85 * (0.25/0.60)) + (90 * (0.10/0.60)))

def test_missing_precision():
    assessor = HealthAssessor()
    res = assessor.assess(accuracy=0.90, precision=None, recall=0.85, f1_score=0.92)
    assert "precision" not in res.available_metrics
    assert math.isclose(res.effective_weights["f1_score"], 0.40 / 0.75)

def test_missing_recall():
    assessor = HealthAssessor()
    res = assessor.assess(accuracy=0.90, precision=0.88, recall=None, f1_score=0.92)
    assert "recall" not in res.available_metrics

def test_missing_accuracy():
    assessor = HealthAssessor()
    res = assessor.assess(accuracy=None, precision=0.88, recall=0.85, f1_score=0.92)
    assert "accuracy" not in res.available_metrics

def test_multiple_missing():
    assessor = HealthAssessor()
    res = assessor.assess(accuracy=None, precision=None, recall=0.85, f1_score=0.92)
    assert len(res.available_metrics) == 2
    assert "recall" in res.available_metrics
    assert "f1_score" in res.available_metrics
    assert math.isclose(res.effective_weights["recall"], 0.25 / 0.65)
    assert math.isclose(res.effective_weights["f1_score"], 0.40 / 0.65)

def test_all_missing():
    assessor = HealthAssessor()
    res = assessor.assess(accuracy=None, precision=None, recall=None, f1_score=None)
    assert res.health_score is None
    assert res.health_status == HealthStatus.INSUFFICIENT_DATA
    assert len(res.available_metrics) == 0

def test_boundaries():
    assessor = HealthAssessor()
    
    # EXACTLY 80 -> HEALTHY
    res = assessor.assess(accuracy=0.80, precision=0.80, recall=0.80, f1_score=0.80)
    assert res.health_score == 80.0
    assert res.health_status == HealthStatus.HEALTHY
    
    # 79.99 -> WARNING
    res = assessor.assess(accuracy=0.799, precision=0.799, recall=0.799, f1_score=0.799)
    assert res.health_status == HealthStatus.WARNING

    # EXACTLY 60 -> WARNING
    res = assessor.assess(accuracy=0.60, precision=0.60, recall=0.60, f1_score=0.60)
    assert res.health_score == 60.0
    assert res.health_status == HealthStatus.WARNING

    # 59.99 -> CRITICAL
    res = assessor.assess(accuracy=0.599, precision=0.599, recall=0.599, f1_score=0.599)
    assert res.health_status == HealthStatus.CRITICAL

    # 0 -> CRITICAL
    res = assessor.assess(accuracy=0.0, precision=0.0, recall=0.0, f1_score=0.0)
    assert res.health_score == 0.0
    assert res.health_status == HealthStatus.CRITICAL

def test_score_bounded():
    assessor = HealthAssessor()
    # Though logically bounded to 100 because inputs are [0,1], we test numerical safety limit
    res = assessor.assess(accuracy=1.1, precision=1.1, recall=1.1, f1_score=1.1)
    assert res.health_score == 100.0

def test_nan_infinity_handling():
    assessor = HealthAssessor()
    res = assessor.assess(accuracy=float('nan'), precision=float('inf'), recall=float('-inf'), f1_score=0.9)
    # all but f1 are treated as missing
    assert len(res.available_metrics) == 1
    assert "f1_score" in res.available_metrics
    assert res.effective_weights["f1_score"] == 1.0
    assert res.health_score == 90.0

def test_custom_weights_and_thresholds():
    config = HealthScoreConfiguration(
        f1_weight=0.1,
        precision_weight=0.1,
        recall_weight=0.1,
        accuracy_weight=0.7,
        healthy_threshold=90.0,
        warning_threshold=70.0
    )
    assessor = HealthAssessor(config)
    res = assessor.assess(accuracy=0.9, precision=0.5, recall=0.5, f1_score=0.5)
    # score = (90 * 0.7) + (50 * 0.3) = 63 + 15 = 78
    assert math.isclose(res.health_score, 78.0)
    # 78 is between 70 and 90 -> WARNING
    assert res.health_status == HealthStatus.WARNING

def test_invalid_configurations():
    with pytest.raises(ValueError):
        HealthScoreConfiguration(healthy_threshold=50.0, warning_threshold=60.0).validate_policy()
        
    with pytest.raises(ValueError):
        HealthScoreConfiguration(f1_weight=0, precision_weight=0, recall_weight=0, accuracy_weight=0).validate_policy()

def test_deterministic():
    assessor = HealthAssessor()
    res1 = assessor.assess(accuracy=0.90, precision=0.88, recall=0.85, f1_score=0.92)
    res2 = assessor.assess(accuracy=0.90, precision=0.88, recall=0.85, f1_score=0.92)
    assert res1.health_score == res2.health_score
    assert res1.health_status == res2.health_status

def test_effective_weights_sum_to_one():
    assessor = HealthAssessor()
    res = assessor.assess(accuracy=None, precision=0.88, recall=0.85, f1_score=0.92)
    total = sum(res.effective_weights.values())
    assert math.isclose(total, 1.0)
