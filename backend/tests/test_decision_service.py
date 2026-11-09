import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auth.security import get_password_hash
from app.decisions import (
    AIMDAction,
    AIMDPriority,
    AIMDConfidence,
    AIMDContext,
    AIMDRecommendation,
    AIMDDecisionEngine,
    ApprovalStatus,
    DecisionLog,
    DecisionLogCreate,
    DecisionLogRead,
    DecisionLogRepository,
    DecisionService,
    AIMDDecisionService,
)
from app.decisions.service import AIMD_CONFIDENCE_SCORE_MAP
from app.models.models import ModelStatus, RegisteredModel
from app.users.models import User, UserRole
from app.monitoring.health import HealthAssessmentResult, HealthStatus
from app.monitoring.performance import PerformanceAnalysis, PerformanceStatus
from app.monitoring.data_drift import DataDriftAnalysis
from app.monitoring.concept_drift import ConceptDriftAnalysis, ConceptDriftStatus
from app.monitoring.explainability import ExplanationResult
from tests.conftest import TestingSessionLocal


@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    user = User(
        username="decision_svc_user",
        email="dec_svc@example.com",
        full_name="Decision Service Admin",
        hashed_password=get_password_hash("securepass123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture
def test_model(test_user):
    db = TestingSessionLocal()
    model = RegisteredModel(
        id=uuid.uuid4(),
        name="SpamDecisionServiceTestModel",
        framework="Scikit-Learn",
        status=ModelStatus.ACTIVE,
        owner_id=test_user.id,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    yield model

    db_model = db.get(RegisteredModel, model.id)
    if db_model:
        db.delete(db_model)
        db.commit()
    db.close()


@pytest.fixture
def healthy_context():
    return AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=95.0,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={"f1_score": 95.0, "precision": 94.0, "recall": 96.0},
            effective_weights={"f1_score": 0.4, "precision": 0.3, "recall": 0.3},
            available_metrics=["f1_score", "precision", "recall"],
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=5,
            start_time=datetime.now(timezone.utc) - timedelta(hours=5),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.STABLE,
            degraded_metrics=[],
            summary="Performance is stable across all indicators.",
        ),
        data_drift_analysis=DataDriftAnalysis(
            feature_results=[],
            drifted_features=[],
            drift_detected=False,
            features_analyzed=3,
            summary="No significant data drift detected.",
        ),
        concept_drift_analysis=ConceptDriftAnalysis(
            status=ConceptDriftStatus.NO_DRIFT,
            drift_detected=False,
            reference_sample_size=100,
            current_sample_size=100,
            metric_results=[],
            drifted_metrics=[],
            summary="No concept drift detected.",
        ),
        explainability_result=ExplanationResult(
            overall_summary="Operational health is optimal; model exhibits high classification reliability.",
            signals=[],
            primary_factors=[],
            health_score=95.0,
            health_status="healthy",
            has_explanation=True,
            confidence="high",
        ),
    )


# ---------------------------------------------------------------------------
# 1. Successful AIMD Decision Creation, Persistence, and Model Association
# ---------------------------------------------------------------------------

def test_evaluate_and_persist_success(test_model, healthy_context):
    db = TestingSessionLocal()
    service = DecisionService(db)

    persisted = service.evaluate_and_persist(model_id=test_model.id, context=healthy_context)

    assert persisted is not None
    assert persisted.id is not None
    assert isinstance(persisted.id, uuid.UUID)
    assert persisted.model_id == test_model.id
    assert persisted.recommended_action == AIMDAction.CONTINUE_MONITORING
    assert persisted.priority == AIMDPriority.LOW
    assert persisted.confidence == AIMD_CONFIDENCE_SCORE_MAP[AIMDConfidence.HIGH]
    assert "acceptable operational limits" in persisted.rationale
    assert persisted.explanation == healthy_context.explainability_result.overall_summary
    assert persisted.health_score == 95.0
    assert persisted.health_status == "healthy"
    assert persisted.requires_human_approval is True
    assert persisted.approval_status == ApprovalStatus.PENDING
    assert persisted.created_at is not None
    assert persisted.created_at.tzinfo is not None

    # Verify query through service
    fetched = service.get_decision(persisted.id)
    assert fetched is not None
    assert fetched.id == persisted.id
    assert fetched.model_id == test_model.id
    db.close()


def test_alias_AIMDDecisionService():
    assert AIMDDecisionService is DecisionService


def test_service_aliases(test_model, healthy_context):
    db = TestingSessionLocal()
    service = DecisionService(db)

    d1 = service.create_decision(model_id=test_model.id, context=healthy_context)
    assert d1.id is not None

    d2 = service.evaluate_and_log(model_id=test_model.id, context=healthy_context)
    assert d2.id is not None

    count = service.count_decisions_by_model(test_model.id)
    assert count >= 2
    db.close()


# ---------------------------------------------------------------------------
# 2. Action, Priority, Confidence, and Signal Preservation Across Pathways
# ---------------------------------------------------------------------------

def test_critical_health_retrain_persistence(test_model):
    db = TestingSessionLocal()
    service = DecisionService(db)

    critical_context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=42.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 42.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"],
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=3,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.DEGRADED,
            degraded_metrics=["f1_score"],
            summary="F1 score collapsed.",
        ),
        historical_maintenance_context={"rollback_target_available": False},
    )

    persisted = service.evaluate_and_persist(model_id=test_model.id, context=critical_context)

    assert persisted.recommended_action == AIMDAction.RETRAIN
    assert persisted.priority == AIMDPriority.CRITICAL
    assert persisted.confidence == AIMD_CONFIDENCE_SCORE_MAP[AIMDConfidence.HIGH]
    assert "CRITICAL" in persisted.rationale
    assert persisted.requires_human_approval is True
    assert persisted.approval_status == ApprovalStatus.PENDING
    assert any("health_critical" in s for s in persisted.supporting_signals)
    db.close()


def test_rollback_safety_persistence(test_model):
    db = TestingSessionLocal()
    service = DecisionService(db)

    rollback_context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=35.0,
            health_status=HealthStatus.CRITICAL,
            normalized_metrics={"f1_score": 35.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"],
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=4,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.DEGRADED,
            degraded_metrics=["f1_score"],
            summary="Severe degradation.",
        ),
        historical_maintenance_context={
            "rollback_target_available": True,
            "previous_stable_version": "v1.0.0",
        },
    )

    persisted = service.evaluate_and_persist(model_id=test_model.id, context=rollback_context)

    assert persisted.recommended_action == AIMDAction.ROLLBACK
    assert persisted.priority == AIMDPriority.CRITICAL
    assert persisted.confidence == AIMD_CONFIDENCE_SCORE_MAP[AIMDConfidence.HIGH]
    assert "Immediate rollback" in persisted.rationale
    assert persisted.requires_human_approval is True
    assert persisted.approval_status == ApprovalStatus.PENDING
    db.close()


def test_data_drift_collection_persistence(test_model):
    db = TestingSessionLocal()
    service = DecisionService(db)

    drift_context = AIMDContext(
        health_assessment=HealthAssessmentResult(
            health_score=85.0,
            health_status=HealthStatus.HEALTHY,
            normalized_metrics={"f1_score": 85.0},
            effective_weights={"f1_score": 1.0},
            available_metrics=["f1_score"],
        ),
        performance_analysis=PerformanceAnalysis(
            observation_count=5,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            metric_trends={},
            overall_status=PerformanceStatus.STABLE,
            degraded_metrics=[],
            summary="Stable",
        ),
        data_drift_analysis=DataDriftAnalysis(
            feature_results=[],
            drifted_features=["url_count", "urgency_words", "subject_length"],
            drift_detected=True,
            features_analyzed=3,
            summary="Data drift detected in 3 features.",
        ),
    )

    persisted = service.evaluate_and_persist(model_id=test_model.id, context=drift_context)

    assert persisted.recommended_action == AIMDAction.DATA_COLLECTION
    assert persisted.priority == AIMDPriority.MEDIUM
    assert persisted.confidence == AIMD_CONFIDENCE_SCORE_MAP[AIMDConfidence.HIGH]
    assert "Statistical data drift detected" in persisted.rationale
    assert persisted.requires_human_approval is True
    assert persisted.approval_status == ApprovalStatus.PENDING
    db.close()


# ---------------------------------------------------------------------------
# 3. Explicit Overrides for Explanation, Confidence, and Signals
# ---------------------------------------------------------------------------

def test_explicit_overrides_preserved(test_model, healthy_context):
    db = TestingSessionLocal()
    service = DecisionService(db)

    custom_explanation = "Manual engineer diagnosis: routine inspection."
    custom_confidence = 0.88
    custom_signals = {"source": "custom_audit", "tags": ["manual", "override"]}

    persisted = service.evaluate_and_persist(
        model_id=test_model.id,
        context=healthy_context,
        explanation=custom_explanation,
        confidence=custom_confidence,
        supporting_signals=custom_signals,
    )

    assert persisted.explanation == custom_explanation
    assert persisted.confidence == custom_confidence
    assert persisted.supporting_signals == custom_signals
    assert persisted.requires_human_approval is True
    assert persisted.approval_status == ApprovalStatus.PENDING
    db.close()


def test_individual_keyword_arguments(test_model):
    db = TestingSessionLocal()
    service = DecisionService(db)

    health = HealthAssessmentResult(
        health_score=91.0,
        health_status=HealthStatus.HEALTHY,
        normalized_metrics={"f1_score": 91.0},
        effective_weights={"f1_score": 1.0},
        available_metrics=["f1_score"],
    )
    perf = PerformanceAnalysis(
        observation_count=2,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        metric_trends={},
        overall_status=PerformanceStatus.STABLE,
        degraded_metrics=[],
        summary="Stable",
    )

    persisted = service.evaluate_and_persist(
        model_id=test_model.id,
        health_assessment=health,
        performance_analysis=perf,
    )

    assert persisted.recommended_action == AIMDAction.CONTINUE_MONITORING
    assert persisted.health_score == 91.0
    assert persisted.health_status == "healthy"
    db.close()


# ---------------------------------------------------------------------------
# 4. Engine Invocation Verification (No Decision Rule Duplication)
# ---------------------------------------------------------------------------

def test_engine_is_invoked_rather_than_duplicated(healthy_context):
    mock_engine = MagicMock(spec=AIMDDecisionEngine)
    mock_repo = MagicMock(spec=DecisionLogRepository)

    expected_rec = AIMDRecommendation(
        action=AIMDAction.HUMAN_REVIEW,
        priority=AIMDPriority.HIGH,
        rationale="Synthetic test recommendation from mock engine.",
        supporting_signals=["mock_signal_1", "mock_signal_2"],
        health_score=75.0,
        health_status="warning",
        confidence=AIMDConfidence.MODERATE,
        requires_human_approval=True,
    )
    mock_engine.evaluate.return_value = expected_rec

    mock_created = DecisionLog(
        id=uuid.uuid4(),
        model_id=uuid.uuid4(),
        recommended_action=AIMDAction.HUMAN_REVIEW,
        priority=AIMDPriority.HIGH,
        confidence=0.7,
        rationale="Synthetic test recommendation from mock engine.",
        requires_human_approval=True,
        approval_status=ApprovalStatus.PENDING,
    )
    mock_repo.create.return_value = mock_created

    service = DecisionService(repository=mock_repo, engine=mock_engine)

    model_id = uuid.uuid4()
    result = service.evaluate_and_persist(model_id=model_id, context=healthy_context)

    # Verify AIMDDecisionEngine.evaluate was called exactly once with the provided context
    mock_engine.evaluate.assert_called_once_with(healthy_context)

    # Verify DecisionLogRepository.create was called with schema matching engine recommendation
    mock_repo.create.assert_called_once()
    create_arg = mock_repo.create.call_args[0][0]
    assert isinstance(create_arg, DecisionLogCreate)
    assert create_arg.model_id == model_id
    assert create_arg.recommended_action == AIMDAction.HUMAN_REVIEW
    assert create_arg.priority == AIMDPriority.HIGH
    assert create_arg.confidence == 0.7
    assert create_arg.rationale == "Synthetic test recommendation from mock engine."
    assert create_arg.supporting_signals == ["mock_signal_1", "mock_signal_2"]
    assert create_arg.requires_human_approval is True
    assert create_arg.approval_status == ApprovalStatus.PENDING
    assert result == mock_created


# ---------------------------------------------------------------------------
# 5. Repository & Database Error Handling
# ---------------------------------------------------------------------------

def test_database_failure_rolls_back_and_raises(healthy_context):
    mock_db = MagicMock()
    mock_repo = MagicMock(spec=DecisionLogRepository)
    mock_repo.create.side_effect = SQLAlchemyError("Database connection dropped")

    service = DecisionService(db=mock_db, repository=mock_repo)

    with pytest.raises(SQLAlchemyError, match="Database connection dropped"):
        service.evaluate_and_persist(model_id=uuid.uuid4(), context=healthy_context)

    mock_db.rollback.assert_called_once()


def test_foreign_key_violation_in_database(healthy_context):
    db = TestingSessionLocal()
    service = DecisionService(db)
    non_existent_model_id = uuid.uuid4()

    with pytest.raises(IntegrityError):
        service.evaluate_and_persist(model_id=non_existent_model_id, context=healthy_context)

    db.close()


def test_unconfigured_repository_raises_runtime_error(healthy_context):
    service = DecisionService(db=None)
    with pytest.raises(RuntimeError, match="DecisionLogRepository is not configured"):
        service.evaluate_and_persist(model_id=uuid.uuid4(), context=healthy_context)


# ---------------------------------------------------------------------------
# 6. Pagination, Listing, and Deletion Delegations
# ---------------------------------------------------------------------------

def test_service_listing_and_deletion(test_model, healthy_context):
    db = TestingSessionLocal()
    service = DecisionService(db)

    dec = service.evaluate_and_persist(model_id=test_model.id, context=healthy_context)
    results = service.list_decisions_by_model(test_model.id)
    assert len(results) >= 1
    assert any(d.id == dec.id for d in results)

    success = service.delete_decision(dec.id)
    assert success is True

    fetched = service.get_decision(dec.id)
    assert fetched is None
    db.close()


# ---------------------------------------------------------------------------
# 7. Confidence Mapping Logic
# ---------------------------------------------------------------------------

def test_map_confidence_helper():
    # Enums
    assert DecisionService._map_confidence(AIMDConfidence.HIGH) == 0.9
    assert DecisionService._map_confidence(AIMDConfidence.MODERATE) == 0.7
    assert DecisionService._map_confidence(AIMDConfidence.LOW) == 0.4
    assert DecisionService._map_confidence(AIMDConfidence.INSUFFICIENT) == 0.1

    # String representations
    assert DecisionService._map_confidence("HIGH") == 0.9
    assert DecisionService._map_confidence("MODERATE") == 0.7

    # Explicit override
    assert DecisionService._map_confidence(AIMDConfidence.LOW, override_confidence=0.99) == 0.99

    # Direct float
    assert DecisionService._map_confidence(0.85) == 0.85

    # Context prediction confidence fallback
    assert DecisionService._map_confidence(None, context_prediction_confidence=0.78) == 0.78

    # Unresolvable
    assert DecisionService._map_confidence(None) is None
