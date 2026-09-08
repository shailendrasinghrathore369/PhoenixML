"""
Unit tests for Step 17: Explainability Analytical Layer.

Verifies deterministic rule-based explainability synthesis across monitoring observations,
health assessment, performance trends, data drift, and concept drift.
Ensures non-causal language, architecture independence, edge case safety, and strict separation
from downstream AIMD recommendation logic.
"""

import ast
from datetime import datetime, timezone
import math
from pathlib import Path
import pytest

from app.monitoring.concept_drift import (
    ConceptDriftAnalysis,
    ConceptDriftMetricResult,
    ConceptDriftStatus,
)
from app.monitoring.data_drift import (
    DataDriftAnalysis,
    FeatureDriftResult,
)
from app.monitoring.explainability import (
    ExplainabilityAnalyzer,
    ExplainabilityInput,
    ExplanationResult,
    ExplanationSignal,
    SignalCategory,
    SignalSeverity,
)
from app.monitoring.health import (
    HealthAssessmentResult,
    HealthStatus,
)
from app.monitoring.performance import (
    MetricTrend,
    PerformanceAnalysis,
    PerformanceStatus,
)


@pytest.fixture
def analyzer():
    return ExplainabilityAnalyzer()


# 1. Healthy model produces no alarming explanation
def test_healthy_model_produces_no_alarming_explanation(analyzer):
    health = HealthAssessmentResult(
        health_score=92.5,
        health_status=HealthStatus.HEALTHY,
        normalized_metrics={"accuracy": 95.0, "f1_score": 92.0},
        effective_weights={"accuracy": 0.5, "f1_score": 0.5},
        available_metrics=["accuracy", "f1_score"],
    )
    perf = PerformanceAnalysis(
        observation_count=10,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={},
        overall_status=PerformanceStatus.STABLE,
        degraded_metrics=[],
        summary="Performance is stable.",
    )
    data_drift = DataDriftAnalysis(
        feature_results=[],
        drifted_features=[],
        drift_detected=False,
        features_analyzed=5,
        summary="No drift detected.",
    )
    concept_drift = ConceptDriftAnalysis(
        status=ConceptDriftStatus.NO_DRIFT,
        drift_detected=False,
        reference_sample_size=100,
        current_sample_size=100,
        metric_results=[],
        drifted_metrics=[],
        summary="No concept drift detected.",
    )

    result = analyzer.explain(
        health_assessment=health,
        performance_analysis=perf,
        data_drift_analysis=data_drift,
        concept_drift_analysis=concept_drift,
    )

    assert result.has_explanation is True
    assert result.health_status == "healthy"
    assert math.isclose(result.health_score, 92.5)
    assert len(result.primary_factors) == 0
    assert result.confidence == "high"
    assert "operating within normal parameters" in result.overall_summary
    for signal in result.signals:
        assert signal.severity == SignalSeverity.INFO


# 2. Performance degradation is explained
def test_performance_degradation_is_explained(analyzer):
    perf = PerformanceAnalysis(
        observation_count=5,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={
            "f1_score": MetricTrend(
                metric_name="f1_score",
                earliest_value=0.92,
                latest_value=0.82,
                absolute_change=-0.10,
                percentage_change=-10.87,
                direction=PerformanceStatus.DEGRADED,
            )
        },
        overall_status=PerformanceStatus.DEGRADED,
        degraded_metrics=["f1_score"],
        summary="Performance is degraded. Degrading metrics: f1_score.",
    )

    result = analyzer.explain(performance_analysis=perf)

    assert result.has_explanation is True
    assert any("f1_score" in factor for factor in result.primary_factors)
    perf_signal = next(s for s in result.signals if s.category == SignalCategory.PERFORMANCE)
    assert perf_signal.severity == SignalSeverity.CRITICAL
    assert "f1_score" in perf_signal.description
    assert "Performance degradation" in result.overall_summary


# 3. Data drift is explained
def test_data_drift_is_explained(analyzer):
    data_drift = DataDriftAnalysis(
        feature_results=[
            FeatureDriftResult(
                feature_name="char_count",
                ks_statistic=0.28,
                p_value=0.002,
                threshold=0.05,
                drift_detected=True,
                reference_sample_size=100,
                current_sample_size=100,
                status="SUCCESS",
            )
        ],
        drifted_features=["char_count"],
        drift_detected=True,
        features_analyzed=1,
        summary="Data drift detected in char_count.",
    )

    result = analyzer.explain(data_drift_analysis=data_drift)

    assert result.has_explanation is True
    assert any("char_count" in factor for factor in result.primary_factors)
    dd_signal = next(s for s in result.signals if s.category == SignalCategory.DATA_DRIFT)
    assert dd_signal.severity == SignalSeverity.WARNING
    assert "char_count" in dd_signal.description
    assert "data drift" in result.overall_summary.lower()


# 4. Concept drift is explained
def test_concept_drift_is_explained(analyzer):
    concept_drift = ConceptDriftAnalysis(
        status=ConceptDriftStatus.DRIFTED,
        drift_detected=True,
        reference_sample_size=50,
        current_sample_size=50,
        metric_results=[
            ConceptDriftMetricResult(
                metric_name="precision",
                reference_value=0.95,
                current_value=0.80,
                absolute_change=-0.15,
                degradation_threshold=0.05,
                degraded=True,
            )
        ],
        drifted_metrics=["precision"],
        summary="Concept drift detected in precision.",
    )

    result = analyzer.explain(concept_drift_analysis=concept_drift)

    assert result.has_explanation is True
    assert any("precision" in factor for factor in result.primary_factors)
    cd_signal = next(s for s in result.signals if s.category == SignalCategory.CONCEPT_DRIFT)
    assert cd_signal.severity == SignalSeverity.CRITICAL
    assert "precision" in cd_signal.description
    assert "concept drift" in result.overall_summary.lower()


# 5. Multiple simultaneous signals
def test_multiple_simultaneous_signals(analyzer):
    health = HealthAssessmentResult(
        health_score=52.0,
        health_status=HealthStatus.CRITICAL,
        normalized_metrics={"accuracy": 60.0, "f1_score": 45.0},
        effective_weights={"accuracy": 0.5, "f1_score": 0.5},
        available_metrics=["accuracy", "f1_score"],
    )
    perf = PerformanceAnalysis(
        observation_count=8,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={},
        overall_status=PerformanceStatus.DEGRADED,
        degraded_metrics=["f1_score"],
        summary="Performance degraded.",
    )
    dd = DataDriftAnalysis(
        feature_results=[
            FeatureDriftResult(
                feature_name="spam_keyword_ratio",
                ks_statistic=0.35,
                p_value=0.0001,
                threshold=0.05,
                drift_detected=True,
                reference_sample_size=100,
                current_sample_size=100,
                status="SUCCESS",
            )
        ],
        drifted_features=["spam_keyword_ratio"],
        drift_detected=True,
        features_analyzed=1,
        summary="Drift detected.",
    )
    cd = ConceptDriftAnalysis(
        status=ConceptDriftStatus.DRIFTED,
        drift_detected=True,
        reference_sample_size=60,
        current_sample_size=60,
        metric_results=[
            ConceptDriftMetricResult(
                metric_name="f1_score",
                reference_value=0.90,
                current_value=0.75,
                absolute_change=-0.15,
                degradation_threshold=0.05,
                degraded=True,
            )
        ],
        drifted_metrics=["f1_score"],
        summary="Concept drift detected.",
    )

    result = analyzer.explain(
        health_assessment=health,
        performance_analysis=perf,
        data_drift_analysis=dd,
        concept_drift_analysis=cd,
    )

    assert result.has_explanation is True
    assert result.confidence == "high"
    assert len(result.primary_factors) >= 3
    assert "consistent with model degradation" in result.overall_summary


# 6. Signal prioritization (CRITICAL before WARNING before INFO)
def test_signal_prioritization(analyzer):
    health = HealthAssessmentResult(
        health_score=85.0,
        health_status=HealthStatus.HEALTHY,
        normalized_metrics={},
        effective_weights={},
        available_metrics=[],
    )  # INFO
    perf = PerformanceAnalysis(
        observation_count=5,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={},
        overall_status=PerformanceStatus.DEGRADED,
        degraded_metrics=["accuracy"],
        summary="degraded",
    )  # CRITICAL
    dd = DataDriftAnalysis(
        feature_results=[],
        drifted_features=["body_length"],
        drift_detected=True,
        features_analyzed=1,
        summary="drift",
    )  # WARNING

    result = analyzer.explain(
        health_assessment=health,
        performance_analysis=perf,
        data_drift_analysis=dd,
    )

    severities = [s.severity for s in result.signals]
    assert severities[0] == SignalSeverity.CRITICAL
    assert severities[1] == SignalSeverity.WARNING
    assert severities[2] == SignalSeverity.INFO


# 7. Insufficient data handling
def test_insufficient_data(analyzer):
    health = HealthAssessmentResult(
        health_score=None,
        health_status=HealthStatus.INSUFFICIENT_DATA,
        normalized_metrics={},
        effective_weights={},
        available_metrics=[],
    )
    perf = PerformanceAnalysis(
        observation_count=1,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={},
        overall_status=PerformanceStatus.INSUFFICIENT_DATA,
        degraded_metrics=[],
        summary="insufficient",
    )
    cd = ConceptDriftAnalysis(
        status=ConceptDriftStatus.INSUFFICIENT_DATA,
        drift_detected=None,
        reference_sample_size=1,
        current_sample_size=1,
        metric_results=[],
        drifted_metrics=[],
        summary="insufficient",
    )
    dd = DataDriftAnalysis(
        feature_results=[],
        drifted_features=[],
        drift_detected=None,
        features_analyzed=0,
        summary="insufficient",
    )

    result = analyzer.explain(
        health_assessment=health,
        performance_analysis=perf,
        concept_drift_analysis=cd,
        data_drift_analysis=dd,
    )

    assert result.has_explanation is False
    assert result.confidence == "none"
    assert result.primary_factors == []
    assert "Insufficient monitoring evidence" in result.overall_summary


# 8. Missing health score input
def test_missing_health_score(analyzer):
    perf = PerformanceAnalysis(
        observation_count=5,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={},
        overall_status=PerformanceStatus.DEGRADED,
        degraded_metrics=["recall"],
        summary="degraded",
    )

    result = analyzer.explain(health_assessment=None, performance_analysis=perf)

    assert result.has_explanation is True
    assert result.health_score is None
    assert result.health_status is None
    assert any("recall" in factor for factor in result.primary_factors)


# 9. Missing performance analysis input
def test_missing_performance_analysis(analyzer):
    health = HealthAssessmentResult(
        health_score=55.0,
        health_status=HealthStatus.CRITICAL,
        normalized_metrics={},
        effective_weights={},
        available_metrics=[],
    )

    result = analyzer.explain(health_assessment=health, performance_analysis=None)

    assert result.has_explanation is True
    assert result.health_status == "critical"
    assert len(result.signals) == 1
    assert result.signals[0].category == SignalCategory.HEALTH


# 10. Missing data drift analysis input
def test_missing_data_drift_analysis(analyzer):
    perf = PerformanceAnalysis(
        observation_count=5,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={},
        overall_status=PerformanceStatus.DEGRADED,
        degraded_metrics=["accuracy"],
        summary="degraded",
    )

    result = analyzer.explain(performance_analysis=perf, data_drift_analysis=None)

    assert result.has_explanation is True
    assert not any(s.category == SignalCategory.DATA_DRIFT for s in result.signals)


# 11. Missing concept drift analysis input
def test_missing_concept_drift_analysis(analyzer):
    perf = PerformanceAnalysis(
        observation_count=5,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={},
        overall_status=PerformanceStatus.DEGRADED,
        degraded_metrics=["accuracy"],
        summary="degraded",
    )

    result = analyzer.explain(performance_analysis=perf, concept_drift_analysis=None)

    assert result.has_explanation is True
    assert not any(s.category == SignalCategory.CONCEPT_DRIFT for s in result.signals)


# 12. None inputs
def test_none_inputs(analyzer):
    result = analyzer.explain(None, None, None, None)

    assert result.has_explanation is False
    assert result.confidence == "none"
    assert result.primary_factors == []
    assert result.signals == []
    assert "Insufficient monitoring evidence" in result.overall_summary


# 13. Empty analyses / input container
def test_empty_analyses(analyzer):
    container = ExplainabilityInput()
    result = analyzer.explain(input_data=container)

    assert result.has_explanation is False
    assert result.confidence == "none"
    assert result.primary_factors == []


# 14. NaN and Inf safety
def test_nan_inf_safety(analyzer):
    health = HealthAssessmentResult(
        health_score=float("nan"),
        health_status=HealthStatus.CRITICAL,
        normalized_metrics={},
        effective_weights={},
        available_metrics=[],
    )
    perf = PerformanceAnalysis(
        observation_count=5,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={
            "f1": MetricTrend(
                metric_name="f1",
                earliest_value=float("inf"),
                latest_value=0.5,
                absolute_change=float("-inf"),
                percentage_change=float("nan"),
                direction=PerformanceStatus.DEGRADED,
            )
        },
        overall_status=PerformanceStatus.DEGRADED,
        degraded_metrics=["f1"],
        summary="degraded",
    )

    result = analyzer.explain(health_assessment=health, performance_analysis=perf)

    assert result.has_explanation is True
    assert result.health_score is None  # Sanitized from NaN
    assert not math.isnan(result.health_score or 0.0)


# 15. No causal language claiming certainty
def test_no_causal_language_claiming_certainty(analyzer):
    health = HealthAssessmentResult(
        health_score=40.0,
        health_status=HealthStatus.CRITICAL,
        normalized_metrics={},
        effective_weights={},
        available_metrics=[],
    )
    perf = PerformanceAnalysis(
        observation_count=5,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={},
        overall_status=PerformanceStatus.DEGRADED,
        degraded_metrics=["accuracy", "f1_score"],
        summary="degraded",
    )
    dd = DataDriftAnalysis(
        feature_results=[],
        drifted_features=["f1", "f2"],
        drift_detected=True,
        features_analyzed=2,
        summary="drift",
    )

    result = analyzer.explain(
        health_assessment=health,
        performance_analysis=perf,
        data_drift_analysis=dd,
    )

    text_corpus = (
        result.overall_summary
        + " "
        + " ".join(s.description for s in result.signals)
        + " "
        + " ".join(result.primary_factors)
    ).lower()

    # Must NOT claim definitive causality or proof of failure cause
    forbidden_causal_phrases = [
        "caused by",
        "caused the model to fail",
        "proves that",
        "fault of",
        "root cause proven",
        "because feature",
    ]
    for phrase in forbidden_causal_phrases:
        assert phrase not in text_corpus, f"Found forbidden causal phrase: {phrase}"

    # Should use evidence-based associative phrasing
    assert "consistent with" in text_corpus or "accompanied by" in text_corpus or "observed" in text_corpus


# 16. Structured output validation
def test_structured_output_validation(analyzer):
    perf = PerformanceAnalysis(
        observation_count=3,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={},
        overall_status=PerformanceStatus.DEGRADED,
        degraded_metrics=["f1_score"],
        summary="degraded",
    )
    result = analyzer.explain(performance_analysis=perf)

    assert isinstance(result, ExplanationResult)
    assert isinstance(result.overall_summary, str)
    assert isinstance(result.signals, list)
    assert isinstance(result.primary_factors, list)
    assert isinstance(result.has_explanation, bool)
    assert isinstance(result.confidence, str)
    for s in result.signals:
        assert isinstance(s, ExplanationSignal)
        assert isinstance(s.category, SignalCategory)
        assert isinstance(s.severity, SignalSeverity)
        assert isinstance(s.evidence, dict)


# 17. Deterministic output
def test_deterministic_output(analyzer):
    health = HealthAssessmentResult(
        health_score=68.0,
        health_status=HealthStatus.WARNING,
        normalized_metrics={},
        effective_weights={},
        available_metrics=[],
    )
    dd = DataDriftAnalysis(
        feature_results=[],
        drifted_features=["subject_length"],
        drift_detected=True,
        features_analyzed=3,
        summary="drift",
    )

    res1 = analyzer.explain(health_assessment=health, data_drift_analysis=dd)
    res2 = analyzer.explain(health_assessment=health, data_drift_analysis=dd)

    assert res1.overall_summary == res2.overall_summary
    assert res1.primary_factors == res2.primary_factors
    assert res1.confidence == res2.confidence
    assert [s.title for s in res1.signals] == [s.title for s in res2.signals]


# 18. AIMD / Recommendation logic is strictly NOT present
def test_aimd_recommendation_logic_not_present(analyzer):
    health = HealthAssessmentResult(
        health_score=35.0,
        health_status=HealthStatus.CRITICAL,
        normalized_metrics={},
        effective_weights={},
        available_metrics=[],
    )
    perf = PerformanceAnalysis(
        observation_count=5,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={},
        overall_status=PerformanceStatus.DEGRADED,
        degraded_metrics=["f1_score", "recall"],
        summary="degraded",
    )

    result = analyzer.explain(health_assessment=health, performance_analysis=perf)

    full_text = (
        result.overall_summary
        + " "
        + " ".join(s.description for s in result.signals)
        + " "
        + " ".join(result.primary_factors)
    ).lower()

    # Maintenance recommendations must be absent from Explainability layer
    forbidden_recommendations = [
        "retrain the model",
        "retraining recommended",
        "rollback",
        "deploy new model",
        "replace deployed model",
        "recommended action",
    ]
    for rec in forbidden_recommendations:
        assert rec not in full_text, f"Found forbidden maintenance recommendation: {rec}"


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


# 19. Architecture independence from SQLAlchemy
def test_architecture_independence_sqlalchemy():
    module_path = Path(__file__).resolve().parent.parent / "app" / "monitoring" / "explainability.py"
    imported = _get_imports_from_file(module_path)

    assert not any("sqlalchemy" in name for name in imported)
    assert "session" not in imported
    assert "create_engine" not in imported


# 20. Architecture independence from FastAPI
def test_architecture_independence_fastapi():
    module_path = Path(__file__).resolve().parent.parent / "app" / "monitoring" / "explainability.py"
    imported = _get_imports_from_file(module_path)

    assert not any("fastapi" in name for name in imported)
    assert "depends" not in imported
    assert "apirouter" not in imported


# 21. Architecture independence from Service / Repository
def test_architecture_independence_service_repository():
    module_path = Path(__file__).resolve().parent.parent / "app" / "monitoring" / "explainability.py"
    imported = _get_imports_from_file(module_path)

    assert "monitoringservice" not in imported
    assert not any("router" in name for name in imported)
    assert not any("repository" in name for name in imported)


# 22. Confidence levels scale with evidence breadth
def test_confidence_levels(analyzer):
    # 1 signal = low
    res_1 = analyzer.explain(
        health_assessment=HealthAssessmentResult(
            health_score=85.0,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={},
            effective_weights={},
            available_metrics=[],
        )
    )
    assert res_1.confidence == "low"

    # 2 signals = moderate
    res_2 = analyzer.explain(
        health_assessment=HealthAssessmentResult(
            health_score=85.0,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={},
            effective_weights={},
            available_metrics=[],
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=5,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.STABLE,
            degraded_metrics=[],
            summary="stable",
        ),
    )
    assert res_2.confidence == "moderate"

    # 3 signals = high
    res_3 = analyzer.explain(
        health_assessment=HealthAssessmentResult(
            health_score=85.0,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={},
            effective_weights={},
            available_metrics=[],
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=5,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.STABLE,
            degraded_metrics=[],
            summary="stable",
        ),
        data_drift_analysis=DataDriftAnalysis(
            feature_results=[],
            drifted_features=[],
            drift_detected=False,
            features_analyzed=2,
            summary="no drift",
        ),
    )
    assert res_3.confidence == "high"
