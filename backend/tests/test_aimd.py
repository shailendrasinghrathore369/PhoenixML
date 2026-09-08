"""
Comprehensive unit and architectural test suite for the AIMD Decision Engine.
Tests cover all decision pathways, rollback safety invariants, confidence ratings,
human-in-the-loop contracts, explainability integration, and architecture decoupling.
"""

import math
import pytest
from datetime import datetime, timezone

from app.decisions.aimd import (
    AIMDAction,
    AIMDPriority,
    AIMDConfidence,
    AIMDContext,
    AIMDRecommendation,
    AIMDConfiguration,
    AIMDDecisionEngine,
)
from app.monitoring.health import HealthAssessmentResult, HealthStatus
from app.monitoring.performance import PerformanceAnalysis, PerformanceStatus, MetricTrend
from app.monitoring.data_drift import DataDriftAnalysis, FeatureDriftResult
from app.monitoring.concept_drift import (
    ConceptDriftAnalysis,
    ConceptDriftStatus,
    ConceptDriftMetricResult,
)
from app.monitoring.explainability import (
    ExplanationResult,
    ExplanationSignal,
    SignalCategory,
    SignalSeverity,
)


# ==============================================================================
# 1. Healthy & Stable Models
# ==============================================================================

def test_healthy_stable_model_recommends_continue_monitoring():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=92.5,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={"f1_score": 92.5, "precision": 90.0, "recall": 95.0},
            effective_weights={"f1_score": 0.4, "precision": 0.3, "recall": 0.3},
            available_metrics=["f1_score", "precision", "recall"]
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=5,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.STABLE,
            degraded_metrics=[],
            summary="Performance is stable."
        ),
        data_drift_analysis=DataDriftAnalysis(
            feature_results=[],
            drifted_features=[],
            drift_detected=False,
            features_analyzed=3,
            summary="No drift detected."
        ),
        concept_drift_analysis=ConceptDriftAnalysis(
            status=ConceptDriftStatus.NO_DRIFT,
            drift_detected=False,
            reference_sample_size=100,
            current_sample_size=100,
            metric_results=[],
            drifted_metrics=[],
            summary="No concept drift."
        )
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.CONTINUE_MONITORING
    assert rec.priority == AIMDPriority.LOW
    assert rec.confidence == AIMDConfidence.HIGH
    assert rec.requires_human_approval is True
    assert rec.health_score == 92.5
    assert rec.health_status == "healthy"
    assert any("health_healthy" in s for s in rec.supporting_signals)


def test_improving_performance_healthy_recommends_continue_monitoring():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=88.0,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={"f1_score": 88.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=4,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.IMPROVING,
            degraded_metrics=[],
            summary="Performance is improving."
        )
    )
    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.CONTINUE_MONITORING
    assert rec.priority == AIMDPriority.LOW
    assert rec.requires_human_approval is True


# ==============================================================================
# 2. Critical Health & Rollback Safety Invariant
# ==============================================================================

def test_critical_health_with_verified_rollback_target_recommends_rollback():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=45.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 45.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        historical_maintenance_context={
            "rollback_target_available": True,
            "previous_stable_version": "v1.2.0"
        }
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.ROLLBACK
    assert rec.priority == AIMDPriority.CRITICAL
    assert rec.requires_human_approval is True
    assert "Verified rollback target available (v1.2.0)" in rec.rationale
    assert rec.health_score == 45.0
    assert rec.health_status == "critical"


def test_critical_health_without_rollback_target_falls_back_to_retrain():
    engine = AIMDDecisionEngine()
    # Rollback context missing completely
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=42.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 42.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        historical_maintenance_context=None
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.RETRAIN
    assert rec.priority == AIMDPriority.CRITICAL
    assert rec.requires_human_approval is True
    assert "No historical maintenance context provided" in rec.rationale


def test_critical_health_with_target_available_false_falls_back_to_retrain():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=50.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 50.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        historical_maintenance_context={
            "rollback_target_available": False,
            "previous_stable_version": None
        }
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.RETRAIN
    assert rec.priority == AIMDPriority.CRITICAL
    assert rec.requires_human_approval is True
    assert "No verified rollback target model available" in rec.rationale


def test_severe_performance_collapse_with_low_score_triggers_critical():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=55.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 55.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=6,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.DEGRADED,
            degraded_metrics=["f1_score", "precision"],
            summary="Performance is degraded."
        ),
        historical_maintenance_context={
            "rollback_target_available": True,
            "previous_stable_version": "v2.0.1"
        }
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.ROLLBACK
    assert rec.priority == AIMDPriority.CRITICAL
    assert rec.confidence == AIMDConfidence.HIGH
    assert rec.requires_human_approval is True


# ==============================================================================
# 3. Concept Drift Handling
# ==============================================================================

def test_concept_drift_alone_recommends_retrain_high_priority():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=82.0,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={"f1_score": 82.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        concept_drift_analysis=ConceptDriftAnalysis(
            status=ConceptDriftStatus.DRIFTED,
            drift_detected=True,
            reference_sample_size=150,
            current_sample_size=150,
            metric_results=[
                ConceptDriftMetricResult(
                    metric_name="f1_score",
                    reference_value=0.90,
                    current_value=0.82,
                    absolute_change=-0.08,
                    degradation_threshold=0.05,
                    degraded=True
                )
            ],
            drifted_metrics=["f1_score"],
            summary="Concept drift detected in f1_score."
        )
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.RETRAIN
    assert rec.priority == AIMDPriority.HIGH
    assert rec.requires_human_approval is True
    assert "Concept drift detected" in rec.rationale
    assert "concept_drift_detected(f1_score)" in rec.supporting_signals


def test_concept_drift_with_degraded_performance_recommends_retrain_critical_priority():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=68.0,
            health_status=HealthStatus.WARNING,
            normalized_metrics={"f1_score": 68.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=10,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.DEGRADED,
            degraded_metrics=["f1_score", "recall"],
            summary="Degraded performance."
        ),
        concept_drift_analysis=ConceptDriftAnalysis(
            status=ConceptDriftStatus.DRIFTED,
            drift_detected=True,
            reference_sample_size=200,
            current_sample_size=200,
            metric_results=[],
            drifted_metrics=["f1_score", "recall"],
            summary="Concept drift detected."
        )
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.RETRAIN
    assert rec.priority == AIMDPriority.CRITICAL
    assert rec.confidence == AIMDConfidence.HIGH
    assert rec.requires_human_approval is True


# ==============================================================================
# 4. Performance Degradation Without Drift
# ==============================================================================

def test_performance_degradation_without_drift_recommends_human_review():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=65.0,
            health_status=HealthStatus.WARNING,
            normalized_metrics={"f1_score": 65.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=8,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.DEGRADED,
            degraded_metrics=["f1_score"],
            summary="Performance degraded."
        ),
        data_drift_analysis=DataDriftAnalysis(
            feature_results=[],
            drifted_features=[],
            drift_detected=False,
            features_analyzed=4,
            summary="No data drift."
        ),
        concept_drift_analysis=ConceptDriftAnalysis(
            status=ConceptDriftStatus.NO_DRIFT,
            drift_detected=False,
            reference_sample_size=100,
            current_sample_size=100,
            metric_results=[],
            drifted_metrics=[],
            summary="No concept drift."
        )
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.HUMAN_REVIEW
    assert rec.priority == AIMDPriority.HIGH
    assert rec.requires_human_approval is True
    assert "uncharacterized" in rec.rationale.lower()


def test_warning_health_alone_without_drift_recommends_human_review():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=72.0,
            health_status=HealthStatus.WARNING,
            normalized_metrics={"f1_score": 72.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        )
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.HUMAN_REVIEW
    assert rec.priority == AIMDPriority.MEDIUM
    assert rec.requires_human_approval is True


# ==============================================================================
# 5. Data Drift Handling (Without Performance Drop)
# ==============================================================================

def test_data_drift_single_feature_stable_performance_recommends_increased_monitoring():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=85.0,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={"f1_score": 85.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=5,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.STABLE,
            degraded_metrics=[],
            summary="Stable performance."
        ),
        data_drift_analysis=DataDriftAnalysis(
            feature_results=[
                FeatureDriftResult(
                    feature_name="char_length",
                    ks_statistic=0.35,
                    p_value=0.001,
                    threshold=0.05,
                    drift_detected=True,
                    reference_sample_size=100,
                    current_sample_size=100,
                    status="SUCCESS"
                )
            ],
            drifted_features=["char_length"],
            drift_detected=True,
            features_analyzed=3,
            summary="Data drift in char_length."
        )
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.INCREASED_MONITORING
    assert rec.priority == AIMDPriority.MEDIUM
    assert rec.requires_human_approval is True
    assert "increased monitoring" in rec.rationale.lower() or "increasing monitoring" in rec.rationale.lower()


def test_data_drift_multiple_features_stable_performance_recommends_data_collection():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=88.0,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={"f1_score": 88.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=5,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.STABLE,
            degraded_metrics=[],
            summary="Stable performance."
        ),
        data_drift_analysis=DataDriftAnalysis(
            feature_results=[],
            drifted_features=["num_links", "caps_ratio", "sender_reputation"],
            drift_detected=True,
            features_analyzed=5,
            summary="Multiple drifted features."
        )
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.DATA_COLLECTION
    assert rec.priority == AIMDPriority.MEDIUM
    assert rec.requires_human_approval is True
    assert "collecting and labeling" in rec.rationale.lower()


def test_data_drift_with_warning_health_recommends_retrain():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=68.0,
            health_status=HealthStatus.WARNING,
            normalized_metrics={"f1_score": 68.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        data_drift_analysis=DataDriftAnalysis(
            feature_results=[],
            drifted_features=["vocab_shift"],
            drift_detected=True,
            features_analyzed=4,
            summary="Data drift detected."
        )
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.RETRAIN
    assert rec.priority == AIMDPriority.HIGH
    assert rec.confidence == AIMDConfidence.HIGH
    assert rec.requires_human_approval is True


# ==============================================================================
# 6. Insufficient Data & Missing Signals
# ==============================================================================

def test_all_none_inputs_recommends_human_review_insufficient():
    engine = AIMDDecisionEngine()
    context = AIMDContext()

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.HUMAN_REVIEW
    assert rec.priority == AIMDPriority.MEDIUM
    assert rec.confidence == AIMDConfidence.INSUFFICIENT
    assert rec.requires_human_approval is True
    assert "insufficient" in rec.rationale.lower()
    assert "insufficient_data" in rec.supporting_signals


def test_insufficient_data_status_across_inputs_recommends_human_review():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=None,
            health_status=HealthStatus.INSUFFICIENT_DATA,
            normalized_metrics={},
            effective_weights={},
            available_metrics=[]
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=1,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.INSUFFICIENT_DATA,
            degraded_metrics=[],
            summary="Observations span zero time."
        ),
        concept_drift_analysis=ConceptDriftAnalysis(
            status=ConceptDriftStatus.INSUFFICIENT_DATA,
            drift_detected=None,
            reference_sample_size=1,
            current_sample_size=1,
            metric_results=[],
            drifted_metrics=[],
            summary="Insufficient labeled samples."
        )
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.HUMAN_REVIEW
    assert rec.priority == AIMDPriority.MEDIUM
    assert rec.confidence == AIMDConfidence.INSUFFICIENT
    assert rec.requires_human_approval is True


# ==============================================================================
# 7. Explainability Layer Integration
# ==============================================================================

def test_explainability_primary_factors_propagated_to_supporting_signals():
    engine = AIMDDecisionEngine()
    explanation = ExplanationResult(
        overall_summary="Model health is degraded. F1 score dropped significantly.",
        signals=[
            ExplanationSignal(
                category=SignalCategory.PERFORMANCE,
                severity=SignalSeverity.CRITICAL,
                title="Performance degraded",
                description="F1-score dropped by 12%",
                evidence={"metric": "f1_score", "drop": 0.12}
            )
        ],
        primary_factors=["Performance degradation in f1_score", "Feature distribution shift in num_links"],
        health_score=58.0,
        health_status="critical",
        has_explanation=True,
        confidence="high"
    )

    context = AIMDContext(
        explainability_result=explanation,
        historical_maintenance_context={"rollback_target_available": False}
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.RETRAIN
    assert rec.priority == AIMDPriority.CRITICAL
    assert rec.health_score == 58.0
    assert rec.health_status == "critical"
    assert "explainability_primary_factors" in rec.evidence_summary
    assert rec.evidence_summary["explainability_confidence"] == "high"
    assert any("factor(Performance degradation in f1_score)" in s for s in rec.supporting_signals)


def test_explainability_fallback_when_direct_health_is_none():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=None,
        explainability_result=ExplanationResult(
            overall_summary="Summary.",
            signals=[],
            primary_factors=["Stable metrics"],
            health_score=85.0,
            health_status="healthy",
            has_explanation=True,
            confidence="high"
        )
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.CONTINUE_MONITORING
    assert rec.health_score == 85.0
    assert rec.health_status == "healthy"


# ==============================================================================
# 8. Robustness, Math Safety, & Config
# ==============================================================================

def test_nan_inf_health_score_safely_ignored():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=None,
            health_status=HealthStatus.INSUFFICIENT_DATA,
            normalized_metrics={},
            effective_weights={},
            available_metrics=[]
        )
    )
    # Manually simulate float('nan') or float('inf')
    context.health_assessment.health_score = float('nan')
    rec = engine.evaluate(context)
    assert rec.health_score is None
    assert rec.action == AIMDAction.HUMAN_REVIEW


def test_custom_configuration_thresholds():
    custom_config = AIMDConfiguration(
        critical_health_threshold=70.0,
        warning_health_threshold=85.0,
        data_drift_collection_threshold=1
    )
    engine = AIMDDecisionEngine(config=custom_config)

    # Health score 68 is WARNING under default (60-80), but CRITICAL under custom (<70)
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=68.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 68.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        historical_maintenance_context={"rollback_target_available": True}
    )

    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.ROLLBACK
    assert rec.priority == AIMDPriority.CRITICAL


def test_deterministic_evaluation():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=55.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 55.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        historical_maintenance_context={"rollback_target_available": True, "previous_stable_version": "v1.0"}
    )

    rec1 = engine.evaluate(context)
    rec2 = engine.evaluate(context)
    assert rec1.action == rec2.action
    assert rec1.priority == rec2.priority
    assert rec1.rationale == rec2.rationale
    assert rec1.supporting_signals == rec2.supporting_signals
    assert rec1.confidence == rec2.confidence


# ==============================================================================
# 9. Strict Invariant: requires_human_approval is ALWAYS True
# ==============================================================================

@pytest.mark.parametrize("action_context", [
    AIMDContext(),  # Insufficient
    AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=95.0,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={"f1_score": 95.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        )
    ),  # Continue monitoring
    AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=30.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 30.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        historical_maintenance_context={"rollback_target_available": True}
    ),  # Rollback
    AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=30.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 30.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        )
    ),  # Retrain
])
def test_requires_human_approval_is_strictly_true(action_context):
    engine = AIMDDecisionEngine()
    rec = engine.evaluate(action_context)
    assert rec.requires_human_approval is True


# ==============================================================================
# 9b. Additional Historical Context & Edge Cases
# ==============================================================================

def test_empty_historical_dict_falls_back_to_retrain():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=35.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 35.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        historical_maintenance_context={}
    )
    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.RETRAIN
    assert rec.priority == AIMDPriority.CRITICAL
    assert rec.requires_human_approval is True


def test_target_model_version_in_historical_context():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=40.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 40.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        historical_maintenance_context={
            "rollback_target_available": True,
            "target_model_version": "v1.1-prod"
        }
    )
    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.ROLLBACK
    assert "Verified rollback target available (v1.1-prod)" in rec.rationale


def test_rollback_target_without_specific_version_string():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=38.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 38.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        historical_maintenance_context={
            "rollback_target_available": True
        }
    )
    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.ROLLBACK
    assert "Verified rollback target available" in rec.rationale


def test_prediction_confidence_safely_ignored_when_none():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=85.0,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={"f1_score": 85.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        prediction_confidence=None
    )
    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.CONTINUE_MONITORING


def test_corroboration_three_sources_high_confidence():
    engine = AIMDDecisionEngine()
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=40.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 40.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=5,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.DEGRADED,
            degraded_metrics=["f1_score"],
            summary="Degraded."
        ),
        concept_drift_analysis=ConceptDriftAnalysis(
            status=ConceptDriftStatus.DRIFTED,
            drift_detected=True,
            reference_sample_size=100,
            current_sample_size=100,
            metric_results=[],
            drifted_metrics=["f1_score"],
            summary="Drifted."
        ),
        historical_maintenance_context={"rollback_target_available": False}
    )
    rec = engine.evaluate(context)
    assert rec.action == AIMDAction.RETRAIN
    assert rec.priority == AIMDPriority.CRITICAL
    assert rec.confidence == AIMDConfidence.HIGH


def test_ambiguous_fallback_to_human_review():
    engine = AIMDDecisionEngine()
    # Construct an edge case where health status is not healthy, warning, or critical
    context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=75.0,
            health_status=HealthStatus.WARNING,
            normalized_metrics={"f1_score": 75.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"]
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=5,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.IMPROVING,
            degraded_metrics=[],
            summary="Improving."
        ),
        data_drift_analysis=DataDriftAnalysis(
            feature_results=[],
            drifted_features=[],
            drift_detected=False,
            features_analyzed=2,
            summary="No drift."
        )
    )
    rec = engine.evaluate(context)
    # Warning health with improving performance and no drift -> human review
    assert rec.action == AIMDAction.HUMAN_REVIEW
    assert rec.requires_human_approval is True


# ==============================================================================
# 10. Enum Definitions and Controlled Sets
# ==============================================================================

def test_enum_members_completeness():
    assert set(AIMDAction) == {
        AIMDAction.CONTINUE_MONITORING,
        AIMDAction.INCREASED_MONITORING,
        AIMDAction.RETRAIN,
        AIMDAction.ROLLBACK,
        AIMDAction.DATA_COLLECTION,
        AIMDAction.HUMAN_REVIEW,
    }
    assert set(AIMDPriority) == {
        AIMDPriority.CRITICAL,
        AIMDPriority.HIGH,
        AIMDPriority.MEDIUM,
        AIMDPriority.LOW,
    }
    assert set(AIMDConfidence) == {
        AIMDConfidence.HIGH,
        AIMDConfidence.MODERATE,
        AIMDConfidence.LOW,
        AIMDConfidence.INSUFFICIENT,
    }


# ==============================================================================
# 11. Architectural Decoupling: No Database, ORM, or FastAPI in aimd.py
# ==============================================================================

def test_architecture_aimd_pure_analytical():
    import ast
    with open("app/decisions/aimd.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename="app/decisions/aimd.py")

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

    forbidden_modules = [
        "sqlalchemy",
        "fastapi",
        "starlette",
        "celery",
        "mlflow",
        "requests",
        "httpx",
    ]

    for mod in forbidden_modules:
        assert not any(mod in imp for imp in imports), f"Forbidden module '{mod}' imported in aimd.py"

    forbidden_names = [
        "session",
        "depends",
        "httpexception",
        "apirouter",
        "monitoringservice",
        "modelregistryservice",
    ]
    for name in forbidden_names:
        assert name not in imports, f"Forbidden symbol '{name}' imported in aimd.py"
