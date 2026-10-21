import math
import uuid
from datetime import datetime, timezone, timedelta
import inspect
import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.auth.security import get_password_hash
from app.decisions import (
    AIMDAction,
    AIMDPriority,
    ApprovalStatus,
    DecisionLog,
    DecisionLogCreate,
    DecisionLogRead,
    DecisionLogRepository,
)
from app.models.models import ModelStatus, RegisteredModel
from app.users.models import User, UserRole
from tests.conftest import TestingSessionLocal


@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    user = User(
        username="decision_user",
        email="decision@example.com",
        full_name="Decision Admin",
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
        name="SpamDecisionModel",
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


# ---------------------------------------------------------------------------
# CRUD & Repository Tests
# ---------------------------------------------------------------------------

def test_create_valid_decision_log(test_model):
    """Scenario 1 & 18: Successfully persist valid DecisionLog with auto-generated UUID."""
    db = TestingSessionLocal()
    repo = DecisionLogRepository(db)

    dec_in = DecisionLogCreate(
        model_id=test_model.id,
        health_score=85.5,
        health_status="HEALTHY",
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        confidence=0.92,
        rationale="System metrics are well within acceptable operating bounds.",
        explanation="No significant drift or performance loss observed.",
        supporting_signals={"f1_score": 0.95, "drift_ratio": 0.05},
        requires_human_approval=True,
        approval_status=ApprovalStatus.PENDING,
    )
    created = repo.create(dec_in)

    assert created.id is not None
    assert isinstance(created.id, uuid.UUID)
    assert created.model_id == test_model.id
    assert created.health_score == 85.5
    assert created.health_status == "HEALTHY"
    assert created.recommended_action == AIMDAction.CONTINUE_MONITORING
    assert created.priority == AIMDPriority.LOW
    assert created.confidence == 0.92
    assert created.rationale == "System metrics are well within acceptable operating bounds."
    assert created.explanation == "No significant drift or performance loss observed."
    assert created.supporting_signals == {"f1_score": 0.95, "drift_ratio": 0.05}
    assert created.requires_human_approval is True
    assert created.approval_status == ApprovalStatus.PENDING
    assert created.created_at is not None
    assert created.created_at.tzinfo is not None
    db.close()


def test_get_decision_log_by_id(test_model):
    """Scenario 2: Retrieve a persisted decision log by its UUID."""
    db = TestingSessionLocal()
    repo = DecisionLogRepository(db)

    dec_in = DecisionLogCreate(
        model_id=test_model.id,
        recommended_action=AIMDAction.RETRAIN,
        priority=AIMDPriority.HIGH,
        rationale="Significant performance degradation detected on incoming batch.",
    )
    created = repo.create(dec_in)

    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.recommended_action == AIMDAction.RETRAIN
    assert fetched.priority == AIMDPriority.HIGH
    assert fetched.created_at.tzinfo is not None

    # Non-existent ID returns None
    assert repo.get_by_id(uuid.uuid4()) is None
    db.close()


def test_list_decisions_by_model(test_model):
    """Scenario 3: List decisions by model ordered descending by created_at with pagination."""
    db = TestingSessionLocal()
    repo = DecisionLogRepository(db)

    base_time = datetime.now(timezone.utc)
    d1 = repo.create(
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action=AIMDAction.CONTINUE_MONITORING,
            priority=AIMDPriority.LOW,
            rationale="Initial check.",
            created_at=base_time - timedelta(minutes=10),
        )
    )
    d2 = repo.create(
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action=AIMDAction.INCREASED_MONITORING,
            priority=AIMDPriority.MEDIUM,
            rationale="Slight data drift detected.",
            created_at=base_time - timedelta(minutes=5),
        )
    )
    d3 = repo.create(
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action=AIMDAction.RETRAIN,
            priority=AIMDPriority.HIGH,
            rationale="Persistent drift leading to accuracy drop.",
            created_at=base_time,
        )
    )

    # All decisions (ordered DESC by created_at)
    results = repo.list_by_model(test_model.id)
    assert len(results) >= 3
    ids = [d.id for d in results]
    assert ids.index(d3.id) < ids.index(d2.id) < ids.index(d1.id)

    # Pagination: skip and limit
    page_1 = repo.list_by_model(test_model.id, skip=0, limit=2)
    assert len(page_1) == 2
    assert page_1[0].id == d3.id
    assert page_1[1].id == d2.id

    page_2 = repo.list_by_model(test_model.id, skip=2, limit=2)
    assert len(page_2) >= 1
    assert page_2[0].id == d1.id
    db.close()


def test_count_decisions_by_model(test_model, test_user):
    """Scenario 4: Count decisions for a given model accurately."""
    db = TestingSessionLocal()
    repo = DecisionLogRepository(db)

    # Another model for isolation
    other_model = RegisteredModel(
        id=uuid.uuid4(),
        name="OtherModel",
        framework="PyTorch",
        status=ModelStatus.ACTIVE,
        owner_id=test_user.id,
    )
    db.add(other_model)
    db.commit()

    assert repo.count_by_model(test_model.id) == 0

    repo.create(
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action=AIMDAction.CONTINUE_MONITORING,
            priority=AIMDPriority.LOW,
            rationale="Model check 1.",
        )
    )
    repo.create(
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action=AIMDAction.RETRAIN,
            priority=AIMDPriority.HIGH,
            rationale="Model check 2.",
        )
    )
    repo.create(
        DecisionLogCreate(
            model_id=other_model.id,
            recommended_action=AIMDAction.ROLLBACK,
            priority=AIMDPriority.CRITICAL,
            rationale="Other model check.",
        )
    )

    assert repo.count_by_model(test_model.id) == 2
    assert repo.count_by_model(other_model.id) == 1

    db.delete(other_model)
    db.commit()
    db.close()


def test_delete_decision(test_model):
    """Scenario 5: Delete decision log by UUID; verify True/False semantics."""
    db = TestingSessionLocal()
    repo = DecisionLogRepository(db)

    created = repo.create(
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action=AIMDAction.HUMAN_REVIEW,
            priority=AIMDPriority.HIGH,
            rationale="Severe unidentifiable concept shift.",
        )
    )

    assert repo.get_by_id(created.id) is not None
    assert repo.delete(created.id) is True
    assert repo.get_by_id(created.id) is None
    # Deleting again returns False
    assert repo.delete(created.id) is False
    assert repo.delete(uuid.uuid4()) is False
    db.close()


# ---------------------------------------------------------------------------
# Enum & Schema Boundary Validation Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("action", [
    AIMDAction.CONTINUE_MONITORING,
    AIMDAction.INCREASED_MONITORING,
    AIMDAction.RETRAIN,
    AIMDAction.ROLLBACK,
    AIMDAction.DATA_COLLECTION,
    AIMDAction.HUMAN_REVIEW,
])
def test_valid_aimd_action_enum(test_model, action):
    """Scenario 6: Valid AIMDAction enums are accepted and stored."""
    dec = DecisionLogCreate(
        model_id=test_model.id,
        recommended_action=action,
        priority=AIMDPriority.MEDIUM,
        rationale="Checking valid action enum.",
    )
    assert dec.recommended_action == action


def test_invalid_aimd_action_enum_rejected(test_model):
    """Scenario 7: Invalid AIMDAction enum values are rejected by schema."""
    with pytest.raises(ValidationError):
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action="AUTONOMOUS_DEPLOY",  # Invalid! Autonomous actions are forbidden
            priority=AIMDPriority.LOW,
            rationale="Testing invalid action.",
        )


@pytest.mark.parametrize("priority", [
    AIMDPriority.CRITICAL,
    AIMDPriority.HIGH,
    AIMDPriority.MEDIUM,
    AIMDPriority.LOW,
])
def test_valid_aimd_priority_enum(test_model, priority):
    """Scenario 8: Valid AIMDPriority enums are accepted and stored."""
    dec = DecisionLogCreate(
        model_id=test_model.id,
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=priority,
        rationale="Checking valid priority enum.",
    )
    assert dec.priority == priority


def test_invalid_aimd_priority_enum_rejected(test_model):
    """Scenario 9: Invalid AIMDPriority enum values are rejected by schema."""
    with pytest.raises(ValidationError):
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action=AIMDAction.CONTINUE_MONITORING,
            priority="URGENT",  # Invalid priority
            rationale="Testing invalid priority.",
        )


@pytest.mark.parametrize("valid_score", [0.0, 50.0, 100.0, None])
def test_valid_health_score_range(test_model, valid_score):
    """Scenario 10a: Health score within 0.0 to 100.0 (or None) is accepted."""
    dec = DecisionLogCreate(
        model_id=test_model.id,
        health_score=valid_score,
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        rationale="Valid health score.",
    )
    assert dec.health_score == valid_score


@pytest.mark.parametrize("invalid_score", [-0.01, 100.01, -50.0, 150.0, float("nan"), float("inf"), float("-inf")])
def test_invalid_health_score_rejected(test_model, invalid_score):
    """Scenario 10b: Out-of-bounds, NaN, or Inf health scores are strictly rejected."""
    with pytest.raises(ValidationError):
        DecisionLogCreate(
            model_id=test_model.id,
            health_score=invalid_score,
            recommended_action=AIMDAction.CONTINUE_MONITORING,
            priority=AIMDPriority.LOW,
            rationale="Testing invalid health score.",
        )


@pytest.mark.parametrize("valid_conf", [0.0, 0.5, 1.0, None])
def test_valid_confidence_range(test_model, valid_conf):
    """Scenario 11a: Confidence float within 0.0 to 1.0 (or None) is accepted."""
    dec = DecisionLogCreate(
        model_id=test_model.id,
        confidence=valid_conf,
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        rationale="Valid confidence.",
    )
    assert dec.confidence == valid_conf


@pytest.mark.parametrize("invalid_conf", [-0.01, 1.01, -1.0, 2.0, float("nan"), float("inf"), float("-inf")])
def test_invalid_confidence_rejected(test_model, invalid_conf):
    """Scenario 11b: Out-of-bounds, NaN, or Inf confidence values are strictly rejected."""
    with pytest.raises(ValidationError):
        DecisionLogCreate(
            model_id=test_model.id,
            confidence=invalid_conf,
            recommended_action=AIMDAction.CONTINUE_MONITORING,
            priority=AIMDPriority.LOW,
            rationale="Testing invalid confidence.",
        )


@pytest.mark.parametrize("empty_rationale", ["", "   ", "\t\n"])
def test_non_empty_rationale_validation(test_model, empty_rationale):
    """Scenario 12: Empty or whitespace-only rationale is rejected."""
    with pytest.raises(ValidationError):
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action=AIMDAction.CONTINUE_MONITORING,
            priority=AIMDPriority.LOW,
            rationale=empty_rationale,
        )


def test_requires_human_approval_defaults_to_true(test_model):
    """Scenario 13: requires_human_approval defaults to True (Human-in-the-loop guarantee)."""
    dec = DecisionLogCreate(
        model_id=test_model.id,
        recommended_action=AIMDAction.RETRAIN,
        priority=AIMDPriority.HIGH,
        rationale="Requires review before production action.",
    )
    assert dec.requires_human_approval is True


def test_approval_status_defaults_to_pending(test_model):
    """Scenario 14: approval_status defaults to ApprovalStatus.PENDING."""
    dec = DecisionLogCreate(
        model_id=test_model.id,
        recommended_action=AIMDAction.RETRAIN,
        priority=AIMDPriority.HIGH,
        rationale="Testing default approval status.",
    )
    assert dec.approval_status == ApprovalStatus.PENDING


@pytest.mark.parametrize("status", [
    ApprovalStatus.PENDING,
    ApprovalStatus.APPROVED,
    ApprovalStatus.REJECTED,
])
def test_valid_approval_status_enum(test_model, status):
    """Scenario 15a: Valid ApprovalStatus values are accepted."""
    dec = DecisionLogCreate(
        model_id=test_model.id,
        recommended_action=AIMDAction.RETRAIN,
        priority=AIMDPriority.HIGH,
        rationale="Testing approval status.",
        approval_status=status,
    )
    assert dec.approval_status == status


def test_invalid_approval_status_rejected(test_model):
    """Scenario 15b: Invalid ApprovalStatus values are rejected."""
    with pytest.raises(ValidationError):
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action=AIMDAction.RETRAIN,
            priority=AIMDPriority.HIGH,
            rationale="Testing invalid approval status.",
            approval_status="AUTO_DEPLOYED",  # Invalid
        )


def test_supporting_signals_json_persistence(test_model):
    """Scenario 16: Complex JSON structures in supporting_signals persist accurately."""
    db = TestingSessionLocal()
    repo = DecisionLogRepository(db)

    complex_signals = {
        "drift_detected": True,
        "features_drifted": ["length", "link_count", "urgency_score"],
        "shap_importance": {"urgency_score": 0.35, "keyword_spam": 0.28},
        "observation_counts": [100, 150, 200],
    }

    dec = repo.create(
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action=AIMDAction.DATA_COLLECTION,
            priority=AIMDPriority.MEDIUM,
            rationale="Data shift in key spam keywords.",
            supporting_signals=complex_signals,
        )
    )

    fetched = repo.get_by_id(dec.id)
    assert fetched.supporting_signals == complex_signals
    assert fetched.supporting_signals["features_drifted"] == ["length", "link_count", "urgency_score"]
    db.close()


def test_timezone_aware_created_at(test_model):
    """Scenario 17: created_at must be timezone-aware; naive datetimes rejected in schema."""
    naive_dt = datetime(2026, 9, 8, 12, 0, 0)
    with pytest.raises(ValidationError, match="timezone-aware"):
        DecisionLogCreate(
            model_id=test_model.id,
            recommended_action=AIMDAction.CONTINUE_MONITORING,
            priority=AIMDPriority.LOW,
            rationale="Testing naive datetime rejection.",
            created_at=naive_dt,
        )

    # Valid UTC timezone
    utc_dt = datetime(2026, 9, 8, 12, 0, 0, tzinfo=timezone.utc)
    dec = DecisionLogCreate(
        model_id=test_model.id,
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        rationale="Testing valid timezone-aware datetime.",
        created_at=utc_dt,
    )
    assert dec.created_at == utc_dt


def test_foreign_key_constraint(db_session):
    """Scenario 19: Foreign key constraint fails when model_id does not exist."""
    non_existent_id = uuid.uuid4()
    repo = DecisionLogRepository(db_session)
    dec_in = DecisionLogCreate(
        model_id=non_existent_id,
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        rationale="Testing foreign key constraint violation.",
    )
    with pytest.raises(IntegrityError):
        repo.create(dec_in)
    db_session.rollback()


def test_model_decisions_relationship_and_cascade(test_user):
    """Scenario 20: RegisteredModel has 1-to-many relationship and cascades delete on decisions."""
    db = TestingSessionLocal()
    model = RegisteredModel(
        id=uuid.uuid4(),
        name="CascadeTestModel",
        framework="Scikit-Learn",
        status=ModelStatus.ACTIVE,
        owner_id=test_user.id,
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    repo = DecisionLogRepository(db)
    dec1 = repo.create(
        DecisionLogCreate(
            model_id=model.id,
            recommended_action=AIMDAction.RETRAIN,
            priority=AIMDPriority.HIGH,
            rationale="Performance dropped below acceptable threshold.",
        )
    )
    dec2 = repo.create(
        DecisionLogCreate(
            model_id=model.id,
            recommended_action=AIMDAction.CONTINUE_MONITORING,
            priority=AIMDPriority.LOW,
            rationale="Routine monitoring check completed.",
        )
    )

    # 1-to-many relationship verification
    db_model = db.get(RegisteredModel, model.id)
    assert len(db_model.decisions) == 2
    decision_ids = {d.id for d in db_model.decisions}
    assert dec1.id in decision_ids
    assert dec2.id in decision_ids

    # Cascade delete / orphan prevention verification
    db.delete(db_model)
    db.commit()

    assert repo.get_by_id(dec1.id) is None
    assert repo.get_by_id(dec2.id) is None
    db.close()


def test_architectural_decoupling():
    """Scenario 21: Verify DecisionLogRepository is cleanly decoupled from web/auth layers."""
    repo_file = inspect.getsource(DecisionLogRepository)
    # Must not contain FastAPI request/response constructs
    assert "FastAPI" not in repo_file
    assert "Request" not in repo_file
    assert "Response" not in repo_file
    assert "HTTPException" not in repo_file
    # Must not contain analytical decision engine calculation logic
    assert "AIMDDecisionEngine" not in repo_file
    assert "HealthAssessor" not in repo_file


def test_decision_log_read_schema_from_orm(test_model):
    """Scenario 22: DecisionLogRead correctly parses ORM model."""
    db = TestingSessionLocal()
    repo = DecisionLogRepository(db)

    dec_in = DecisionLogCreate(
        model_id=test_model.id,
        health_score=90.0,
        health_status="HEALTHY",
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        confidence=0.95,
        rationale="All systems normal.",
    )
    db_decision = repo.create(dec_in)

    read_schema = DecisionLogRead.model_validate(db_decision)
    assert read_schema.id == db_decision.id
    assert read_schema.model_id == test_model.id
    assert read_schema.health_score == 90.0
    assert read_schema.health_status == "HEALTHY"
    assert read_schema.recommended_action == AIMDAction.CONTINUE_MONITORING
    assert read_schema.priority == AIMDPriority.LOW
    assert read_schema.confidence == 0.95
    assert read_schema.rationale == "All systems normal."
    assert read_schema.requires_human_approval is True
    assert read_schema.approval_status == ApprovalStatus.PENDING
    db.close()


def test_optional_fields_can_be_none(test_model):
    """Scenario 23: Optional fields can safely be None."""
    db = TestingSessionLocal()
    repo = DecisionLogRepository(db)

    dec_in = DecisionLogCreate(
        model_id=test_model.id,
        health_score=None,
        health_status=None,
        confidence=None,
        explanation=None,
        supporting_signals=None,
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        rationale="Minimal decision log entry with optional fields omitted.",
    )
    created = repo.create(dec_in)

    assert created.health_score is None
    assert created.health_status is None
    assert created.confidence is None
    assert created.explanation is None
    assert created.supporting_signals is None
    db.close()
