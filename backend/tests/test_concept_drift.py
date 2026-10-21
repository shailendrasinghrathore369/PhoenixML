"""
Tests for Concept Drift Detection Foundation (Step 16).

Verifies window-based performance comparison, zero-division handling,
configurable degradation threshold, minimum sample sizing, architecture
independence, and deterministic output.
"""

import ast
import math
from datetime import datetime, timezone
from pathlib import Path
import pytest

from app.monitoring.concept_drift import (
    ConceptDriftAnalysis,
    ConceptDriftConfiguration,
    ConceptDriftDetector,
    ConceptDriftMetricResult,
    ConceptDriftStatus,
    LabeledWindow,
)


# 1. Identical reference/current windows
def test_identical_windows():
    detector = ConceptDriftDetector()
    y_t = [0, 1, 0, 1] * 10
    y_p = [0, 1, 0, 1] * 10

    ref = LabeledWindow(y_true=y_t, y_pred=y_p)
    cur = LabeledWindow(y_true=y_t, y_pred=y_p)

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.NO_DRIFT
    assert res.drift_detected is False
    assert len(res.drifted_metrics) == 0
    for m in res.metric_results:
        assert m.degraded is False
        assert m.absolute_change == 0.0


# 2. Degraded accuracy
def test_degraded_accuracy():
    detector = ConceptDriftDetector(ConceptDriftConfiguration(degradation_threshold=0.05))
    # Ref: 100% accuracy (20/20)
    ref = LabeledWindow(
        y_true=[0] * 10 + [1] * 10,
        y_pred=[0] * 10 + [1] * 10,
    )
    # Cur: 80% accuracy (drop of -0.20 > 0.05 threshold)
    cur = LabeledWindow(
        y_true=[0] * 10 + [1] * 10,
        y_pred=[0] * 8 + [1] * 2 + [1] * 8 + [0] * 2,
    )

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.DRIFTED
    assert "accuracy" in res.drifted_metrics
    acc_metric = next(m for m in res.metric_results if m.metric_name == "accuracy")
    assert acc_metric.degraded is True
    assert acc_metric.reference_value == 1.0
    assert acc_metric.current_value == 0.8
    assert math.isclose(acc_metric.absolute_change, -0.20)


# 3. Degraded precision
def test_degraded_precision():
    detector = ConceptDriftDetector(ConceptDriftConfiguration(degradation_threshold=0.05))
    # Ref: TP=5, FP=0 -> Precision = 1.0
    ref = LabeledWindow(
        y_true=[0] * 10 + [1] * 5,
        y_pred=[0] * 10 + [1] * 5,
    )
    # Cur: TP=5, FP=5 -> Precision = 5/10 = 0.5 (drop of -0.50)
    cur = LabeledWindow(
        y_true=[0] * 10 + [1] * 5,
        y_pred=[0] * 5 + [1] * 5 + [1] * 5,
    )

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.DRIFTED
    assert "precision" in res.drifted_metrics
    prec_metric = next(m for m in res.metric_results if m.metric_name == "precision")
    assert prec_metric.degraded is True
    assert prec_metric.reference_value == 1.0
    assert prec_metric.current_value == 0.5
    assert math.isclose(prec_metric.absolute_change, -0.50)


# 4. Degraded recall
def test_degraded_recall():
    detector = ConceptDriftDetector(ConceptDriftConfiguration(degradation_threshold=0.05))
    # Ref: TP=10, FN=0 -> Recall = 1.0
    ref = LabeledWindow(
        y_true=[1] * 10 + [0] * 10,
        y_pred=[1] * 10 + [0] * 10,
    )
    # Cur: TP=5, FN=5 -> Recall = 5/10 = 0.5 (drop of -0.50)
    cur = LabeledWindow(
        y_true=[1] * 10 + [0] * 10,
        y_pred=[1] * 5 + [0] * 5 + [0] * 10,
    )

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.DRIFTED
    assert "recall" in res.drifted_metrics
    rec_metric = next(m for m in res.metric_results if m.metric_name == "recall")
    assert rec_metric.degraded is True
    assert rec_metric.reference_value == 1.0
    assert rec_metric.current_value == 0.5
    assert math.isclose(rec_metric.absolute_change, -0.50)


# 5. Degraded F1
def test_degraded_f1():
    detector = ConceptDriftDetector(ConceptDriftConfiguration(degradation_threshold=0.05))
    ref = LabeledWindow(
        y_true=[0, 1] * 10,
        y_pred=[0, 1] * 10,
    )
    cur = LabeledWindow(
        y_true=[0, 1] * 10,
        y_pred=[1, 0] * 10,
    )

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.DRIFTED
    assert "f1_score" in res.drifted_metrics
    f1_metric = next(m for m in res.metric_results if m.metric_name == "f1_score")
    assert f1_metric.degraded is True
    assert f1_metric.reference_value == 1.0
    assert f1_metric.current_value == 0.0


# 6. Threshold boundary
def test_threshold_boundary():
    # Exactly -0.05 drop must trigger drift; -0.04 drop must not
    detector = ConceptDriftDetector(ConceptDriftConfiguration(degradation_threshold=0.05))

    ref = LabeledWindow(
        y_true=[1] * 20,
        y_pred=[1] * 20,
    )

    # 1 error out of 20 = 19/20 = 0.95 -> drop is exactly -0.05
    cur_boundary = LabeledWindow(
        y_true=[1] * 20,
        y_pred=[1] * 19 + [0],
    )
    res_boundary = detector.analyze(ref, cur_boundary)
    assert res_boundary.status == ConceptDriftStatus.DRIFTED
    assert "accuracy" in res_boundary.drifted_metrics

    # Now with 100 samples: 4 errors = 96/100 = 0.96 -> drop is -0.04 (< 0.05)
    ref_100 = LabeledWindow(
        y_true=[1] * 100,
        y_pred=[1] * 100,
    )
    cur_sub_boundary = LabeledWindow(
        y_true=[1] * 100,
        y_pred=[1] * 96 + [0] * 4,
    )
    res_sub_boundary = detector.analyze(ref_100, cur_sub_boundary)
    assert res_sub_boundary.status == ConceptDriftStatus.NO_DRIFT
    assert res_sub_boundary.drift_detected is False


# 7. Configurable degradation threshold
def test_configurable_degradation_threshold():
    # A 0.08 drop will trigger drift if threshold is 0.05, but not if threshold is 0.10
    detector_strict = ConceptDriftDetector(ConceptDriftConfiguration(degradation_threshold=0.05))
    detector_lenient = ConceptDriftDetector(ConceptDriftConfiguration(degradation_threshold=0.10))

    # Ref: 1.0 (50/50)
    ref = LabeledWindow(
        y_true=[1] * 50,
        y_pred=[1] * 50,
    )
    # Cur: 0.92 (46/50) -> drop is -0.08
    cur = LabeledWindow(
        y_true=[1] * 50,
        y_pred=[1] * 46 + [0] * 4,
    )

    res_strict = detector_strict.analyze(ref, cur)
    res_lenient = detector_lenient.analyze(ref, cur)

    assert res_strict.status == ConceptDriftStatus.DRIFTED
    assert res_lenient.status == ConceptDriftStatus.NO_DRIFT


# 8. Multiple metrics monitored and exposed
def test_multiple_metrics():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(y_true=[0, 1] * 10, y_pred=[0, 1] * 10)
    cur = LabeledWindow(y_true=[0, 1] * 10, y_pred=[0, 1] * 10)

    res = detector.analyze(ref, cur)
    metric_names = [m.metric_name for m in res.metric_results]
    assert metric_names == ["accuracy", "precision", "recall", "f1_score"]
    for m in res.metric_results:
        assert isinstance(m, ConceptDriftMetricResult)
        assert m.degradation_threshold == 0.05


# 9. Multiple degraded metrics
def test_multiple_degraded_metrics():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(y_true=[0, 1] * 10, y_pred=[0, 1] * 10)
    cur = LabeledWindow(y_true=[0, 1] * 10, y_pred=[1, 0] * 10)

    res = detector.analyze(ref, cur)
    assert len(res.drifted_metrics) >= 2
    assert "accuracy" in res.drifted_metrics
    assert "f1_score" in res.drifted_metrics


# 10. No degraded metrics (including metric improvements)
def test_no_degraded_metrics():
    detector = ConceptDriftDetector()
    # Ref has errors (0.80 accuracy)
    ref = LabeledWindow(
        y_true=[1] * 10,
        y_pred=[1] * 8 + [0] * 2,
    )
    # Cur has improved (1.00 accuracy)
    cur = LabeledWindow(
        y_true=[1] * 10,
        y_pred=[1] * 10,
    )

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.NO_DRIFT
    assert res.drift_detected is False
    assert len(res.drifted_metrics) == 0
    acc_metric = next(m for m in res.metric_results if m.metric_name == "accuracy")
    assert acc_metric.absolute_change == pytest.approx(0.20)
    assert acc_metric.degraded is False


# 11. Overall DRIFTED status
def test_overall_drifted_status():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(y_true=[0, 1] * 5, y_pred=[0, 1] * 5)
    cur = LabeledWindow(y_true=[0, 1] * 5, y_pred=[1, 0] * 5)

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.DRIFTED
    assert res.drift_detected is True


# 12. Overall NO_DRIFT status
def test_overall_no_drift_status():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(y_true=[0, 1] * 5, y_pred=[0, 1] * 5)
    cur = LabeledWindow(y_true=[0, 1] * 5, y_pred=[0, 1] * 5)

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.NO_DRIFT
    assert res.drift_detected is False


# 13. Insufficient reference samples
def test_insufficient_reference_samples():
    detector = ConceptDriftDetector(ConceptDriftConfiguration(minimum_samples=3))
    ref = LabeledWindow(y_true=[1, 0], y_pred=[1, 0])  # Only 2 samples
    cur = LabeledWindow(y_true=[1, 0, 1], y_pred=[1, 0, 1])

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.INSUFFICIENT_DATA
    assert res.drift_detected is None
    assert res.reference_sample_size == 2
    assert res.current_sample_size == 3


# 14. Insufficient current samples
def test_insufficient_current_samples():
    detector = ConceptDriftDetector(ConceptDriftConfiguration(minimum_samples=3))
    ref = LabeledWindow(y_true=[1, 0, 1], y_pred=[1, 0, 1])
    cur = LabeledWindow(y_true=[1], y_pred=[1])  # Only 1 sample

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.INSUFFICIENT_DATA
    assert res.drift_detected is None
    assert res.current_sample_size == 1


# 15. Empty y_true
def test_empty_y_true():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(y_true=[], y_pred=[])
    cur = LabeledWindow(y_true=[1, 0], y_pred=[1, 0])

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.INSUFFICIENT_DATA
    assert res.reference_sample_size == 0


# 16. Empty y_pred
def test_empty_y_pred():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(y_true=[1, 0], y_pred=[1, 0])
    cur = LabeledWindow(y_true=[], y_pred=[])

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.INSUFFICIENT_DATA
    assert res.current_sample_size == 0


# 17. Mismatched y_true/y_pred lengths
def test_mismatched_y_true_y_pred_lengths():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(y_true=[1, 0], y_pred=[1])
    cur = LabeledWindow(y_true=[1, 0], y_pred=[1, 0])

    with pytest.raises(ValueError, match="same length"):
        detector.analyze(ref, cur)


# 18. Invalid labels and predictions omitted
def test_invalid_labels_predictions():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(
        y_true=[1, 0, 999, "unknown", -5],
        y_pred=[1, 0, 1, 0, 1],
    )
    cur = LabeledWindow(
        y_true=[1, 0],
        y_pred=[1, 0],
    )

    res = detector.analyze(ref, cur)
    assert res.reference_sample_size == 2
    assert res.current_sample_size == 2
    assert res.status == ConceptDriftStatus.NO_DRIFT


# 19. None values handled safely
def test_none_values():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(
        y_true=[1, 0, None, 1],
        y_pred=[1, 0, 1, None],
    )
    cur = LabeledWindow(
        y_true=[1, 0],
        y_pred=[1, 0],
    )

    res = detector.analyze(ref, cur)
    assert res.reference_sample_size == 2
    assert res.current_sample_size == 2


# 20. NaN and invalid numeric handling
def test_nan_invalid_numeric_handling():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(
        y_true=[1, 0, float("nan"), float("inf"), float("-inf")],
        y_pred=[1, 0, 1, 0, 1],
    )
    cur = LabeledWindow(
        y_true=[1, 0],
        y_pred=[1, 0],
    )

    res = detector.analyze(ref, cur)
    assert res.reference_sample_size == 2
    assert res.current_sample_size == 2


# 21. Undefined metric handling (zero positive labels or predictions)
def test_undefined_metric_handling():
    detector = ConceptDriftDetector()
    # All negatives: TP=0, FP=0, FN=0 -> Precision and Recall are undefined (None)
    ref = LabeledWindow(y_true=[0, 0, 0], y_pred=[0, 0, 0])
    cur = LabeledWindow(y_true=[0, 0, 0], y_pred=[0, 0, 0])

    res = detector.analyze(ref, cur)
    metric_map = {m.metric_name: m for m in res.metric_results}

    assert metric_map["accuracy"].reference_value == 1.0
    assert metric_map["accuracy"].current_value == 1.0
    assert metric_map["precision"].reference_value is None
    assert metric_map["precision"].current_value is None
    assert metric_map["precision"].degraded is None
    assert metric_map["recall"].reference_value is None
    assert metric_map["f1_score"].reference_value is None
    assert res.status == ConceptDriftStatus.NO_DRIFT


# 22. Sample sizes exposed in output
def test_sample_sizes_exposed():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(y_true=[1, 0, 1, 0], y_pred=[1, 0, 1, 0])
    cur = LabeledWindow(y_true=[1, 0, 1], y_pred=[1, 0, 1])

    res = detector.analyze(ref, cur)
    assert res.reference_sample_size == 4
    assert res.current_sample_size == 3


# 23. Drifted metrics output
def test_drifted_metrics_output():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(
        y_true=[0, 0, 1, 1],
        y_pred=[0, 0, 1, 0],
    )
    cur = LabeledWindow(
        y_true=[0, 0, 1, 1],
        y_pred=[1, 1, 1, 0],
    )

    res = detector.analyze(ref, cur)
    assert isinstance(res.drifted_metrics, list)
    assert "precision" in res.drifted_metrics


# 24. Summary output
def test_summary_output():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(y_true=[0, 1] * 5, y_pred=[0, 1] * 5)
    cur = LabeledWindow(y_true=[0, 1] * 5, y_pred=[1, 0] * 5)

    res = detector.analyze(ref, cur)
    assert isinstance(res.summary, str)
    assert "Concept drift detected" in res.summary
    assert "accuracy" in res.summary

    # Insufficient data summary
    res_insuf = detector.analyze(
        LabeledWindow(y_true=[1], y_pred=[1]),
        LabeledWindow(y_true=[1], y_pred=[1]),
    )
    assert "Insufficient" in res_insuf.summary


# 25. Configuration validation
def test_configuration_validation():
    with pytest.raises(ValueError, match="strictly greater than 0"):
        ConceptDriftConfiguration(degradation_threshold=0)

    with pytest.raises(ValueError, match="strictly greater than 0"):
        ConceptDriftConfiguration(degradation_threshold=-0.05)

    with pytest.raises(ValueError, match="at least 2"):
        ConceptDriftConfiguration(minimum_samples=1)

    with pytest.raises(ValueError, match="distinct"):
        ConceptDriftConfiguration(positive_class=1, negative_class=1)


def _get_imports_from_file(filepath: Path) -> set:
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(filepath))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.lower())
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.lower())
            for alias in node.names:
                imports.add(alias.name.lower())
    return imports


# 26. Architecture independence from SQLAlchemy
def test_architecture_independence_sqlalchemy():
    module_path = Path(__file__).resolve().parent.parent / "app" / "monitoring" / "concept_drift.py"
    imported = _get_imports_from_file(module_path)

    assert not any("sqlalchemy" in name for name in imported)
    assert "session" not in imported
    assert "create_engine" not in imported


# 27. Architecture independence from FastAPI
def test_architecture_independence_fastapi():
    module_path = Path(__file__).resolve().parent.parent / "app" / "monitoring" / "concept_drift.py"
    imported = _get_imports_from_file(module_path)

    assert not any("fastapi" in name for name in imported)
    assert "depends" not in imported
    assert "apirouter" not in imported


# 28. Detector does not use MonitoringService
def test_detector_does_not_use_monitoring_service():
    module_path = Path(__file__).resolve().parent.parent / "app" / "monitoring" / "concept_drift.py"
    imported = _get_imports_from_file(module_path)

    assert "monitoringservice" not in imported
    assert "datadriftdetector" not in imported
    assert not any("router" in name for name in imported)


# 29. Deterministic repeated result
def test_deterministic_repeated_result():
    detector = ConceptDriftDetector()
    ref = LabeledWindow(
        y_true=[1, 0, 1, 1],
        y_pred=[1, 0, 1, 0],
    )
    cur = LabeledWindow(
        y_true=[1, 0, 1, 1],
        y_pred=[0, 1, 0, 1],
    )

    res1 = detector.analyze(ref, cur)
    res2 = detector.analyze(ref, cur)

    assert res1.status == res2.status
    assert res1.drift_detected == res2.drift_detected
    assert res1.drifted_metrics == res2.drifted_metrics
    for m1, m2 in zip(res1.metric_results, res2.metric_results):
        assert m1.metric_name == m2.metric_name
        assert m1.reference_value == m2.reference_value
        assert m1.current_value == m2.current_value
        assert m1.absolute_change == m2.absolute_change
        assert m1.degraded == m2.degraded


# Additional tests: Custom classes and sequence analysis
def test_custom_binary_classes():
    config = ConceptDriftConfiguration(positive_class="spam", negative_class="ham")
    detector = ConceptDriftDetector(config)

    ref = LabeledWindow(
        y_true=["spam", "ham", "spam", "ham"],
        y_pred=["spam", "ham", "spam", "ham"],
    )
    cur = LabeledWindow(
        y_true=["spam", "ham", "spam", "ham"],
        y_pred=["ham", "spam", "ham", "spam"],
    )

    res = detector.analyze(ref, cur)
    assert res.status == ConceptDriftStatus.DRIFTED
    assert res.reference_sample_size == 4
    assert res.current_sample_size == 4
    assert "accuracy" in res.drifted_metrics


def test_analyze_sequence():
    detector = ConceptDriftDetector()
    w1 = LabeledWindow(y_true=[0, 1] * 5, y_pred=[0, 1] * 5, observed_at=datetime.now(timezone.utc))
    w2 = LabeledWindow(y_true=[0, 1] * 5, y_pred=[0, 1] * 5, observed_at=datetime.now(timezone.utc))
    w3 = LabeledWindow(y_true=[0, 1] * 5, y_pred=[1, 0] * 5, observed_at=datetime.now(timezone.utc))

    results = detector.analyze_sequence([w1, w2, w3])
    assert len(results) == 2
    assert results[0].status == ConceptDriftStatus.NO_DRIFT
    assert results[1].status == ConceptDriftStatus.DRIFTED
