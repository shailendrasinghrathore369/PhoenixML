import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi import HTTPException

from app.auth.exceptions import AuthorizationError
from app.auth.security import get_password_hash
from app.decisions import (
    AIMDAction,
    AIMDPriority,
    AIMDConfidence,
    AIMDContext,
    ApprovalStatus,
    DecisionLog,
    DecisionLogCreate,
    DecisionLogRead,
    DecisionHistoryResponse,
    DecisionLogRepository,
    DecisionService,
)
from app.models.models import ModelStatus, RegisteredModel
from app.users.models import User, UserRole
from app.monitoring.health import HealthAssessmentResult, HealthStatus
from app.monitoring.performance import PerformanceAnalysis, PerformanceStatus
from app.monitoring.data_drift import DataDriftAnalysis
from app.monitoring.concept_drift import ConceptDriftAnalysis, ConceptDriftStatus
from app.monitoring.explainability import ExplanationResult
from tests.conftest import TestingSessionLocal


@pytest.fixture
def test_owner():
    db = TestingSessionLocal()
    user = User(
        username="model_owner_user",
        email="owner@example.com",
        full_name="Model Owner",
        hashed_password=get_password_hash("securepass123"),
        role=UserRole.ML_ENGINEER,
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
def other_user():
    db = TestingSessionLocal()
    user = User(
        username="unauthorized_viewer",
        email="viewer@example.com",
        full_name="Unauthorized Viewer",
        hashed_password=get_password_hash("securepass123"),
        role=UserRole.VIEWER,
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
def admin_user():
    db = TestingSessionLocal()
    user = User(
        username="admin_auditor",
        email="auditor@example.com",
        full_name="Admin Auditor",
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
def test_model(test_owner):
    db = TestingSessionLocal()
    model = RegisteredModel(
        id=uuid.uuid4(),
        name="SpamDetectionProductionModel",
        framework="Scikit-Learn",
        status=ModelStatus.ACTIVE,
        owner_id=test_owner.id,
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
def second_model(test_owner):
    db = TestingSessionLocal()
    model = RegisteredModel(
        id=uuid.uuid4(),
        name="SecondarySpamModel",
        framework="PyTorch",
        status=ModelStatus.ACTIVE,
        owner_id=test_owner.id,
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


def create_sample_decision(db, model_id, action=AIMDAction.CONTINUE_MONITORING, priority=AIMDPriority.LOW, created_at=None):
    repo = DecisionLogRepository(db)
    dec_in = DecisionLogCreate(
        model_id=model_id,
        created_at=created_at or datetime.now(timezone.utc),
        health_score=85.0,
        health_status="healthy",
        recommended_action=action,
        priority=priority,
        confidence=0.9,
        rationale="Automated test decision rationale.",
        explanation="Analytical diagnostic explanation.",
        supporting_signals=["signal_alpha", "signal_beta"],
        requires_human_approval=True,
        approval_status=ApprovalStatus.PENDING,
    )
    return repo.create(dec_in)


# ---------------------------------------------------------------------------
# 1. Retrieve Single Decision by Decision ID & Non-Existent Handlers
# ---------------------------------------------------------------------------

def test_get_decision_by_id_success(test_model, test_owner):
    db = TestingSessionLocal()
    service = DecisionService(db)

    created = create_sample_decision(db, test_model.id)

    # 1. As ORM model
    retrieved = service.get_decision(
        decision_id=created.id,
        model_id=test_model.id,
        user=test_owner,
    )
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.model_id == test_model.id
    assert retrieved.recommended_action == created.recommended_action

    # 2. As read schema
    read_schema = service.get_decision(
        decision_id=created.id,
        model_id=test_model.id,
        user=test_owner,
        as_read_schema=True,
    )
    assert isinstance(read_schema, DecisionLogRead)
    assert read_schema.id == created.id
    assert read_schema.model_id == test_model.id
    db.close()


def test_get_decision_for_model_helper(test_model, test_owner):
    db = TestingSessionLocal()
    service = DecisionService(db)

    created = create_sample_decision(db, test_model.id)
    retrieved = service.get_decision_for_model(
        model_id=test_model.id,
        decision_id=created.id,
        user=test_owner,
    )
    assert retrieved.id == created.id
    db.close()


def test_get_nonexistent_decision_raises_404(test_model, test_owner):
    db = TestingSessionLocal()
    service = DecisionService(db)
    non_existent_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        service.get_decision(
            decision_id=non_existent_id,
            model_id=test_model.id,
            user=test_owner,
        )
    assert exc_info.value.status_code == 404
    assert "Decision not found" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info2:
        service.get_decision_for_model(
            model_id=test_model.id,
            decision_id=non_existent_id,
            user=test_owner,
        )
    assert exc_info2.value.status_code == 404
    db.close()


def test_get_decision_nonexistent_model_raises_404(test_owner):
    db = TestingSessionLocal()
    service = DecisionService(db)
    non_existent_model = uuid.uuid4()
    some_decision_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        service.get_decision(
            decision_id=some_decision_id,
            model_id=non_existent_model,
            user=test_owner,
        )
    assert exc_info.value.status_code == 404
    assert "Model not found" in exc_info.value.detail
    db.close()


# ---------------------------------------------------------------------------
# 2. List Decisions, Newest-First Ordering, and Pagination
# ---------------------------------------------------------------------------

def test_list_decisions_for_model(test_model, test_owner):
    db = TestingSessionLocal()
    service = DecisionService(db)

    d1 = create_sample_decision(db, test_model.id, action=AIMDAction.CONTINUE_MONITORING)
    d2 = create_sample_decision(db, test_model.id, action=AIMDAction.RETRAIN)

    results = service.list_decisions_for_model(test_model.id, user=test_owner)
    assert len(results) >= 2
    result_ids = [d.id for d in results]
    assert d1.id in result_ids
    assert d2.id in result_ids

    # Verify as read schema
    schema_results = service.list_decisions_for_model(test_model.id, user=test_owner, as_read_schema=True)
    assert all(isinstance(d, DecisionLogRead) for d in schema_results)
    db.close()


def test_newest_first_chronological_ordering(test_model, test_owner):
    db = TestingSessionLocal()
    service = DecisionService(db)

    base_time = datetime.now(timezone.utc)
    t_old = base_time - timedelta(hours=2)
    t_mid = base_time - timedelta(hours=1)
    t_new = base_time

    d_old = create_sample_decision(db, test_model.id, created_at=t_old)
    d_mid = create_sample_decision(db, test_model.id, created_at=t_mid)
    d_new = create_sample_decision(db, test_model.id, created_at=t_new)

    results = service.list_decisions_for_model(test_model.id, user=test_owner)
    ids = [d.id for d in results]

    # Verify strictly newest first: d_new before d_mid before d_old
    assert ids.index(d_new.id) < ids.index(d_mid.id) < ids.index(d_old.id)
    db.close()


def test_pagination_skip_and_limit(test_model, test_owner):
    db = TestingSessionLocal()
    service = DecisionService(db)

    base_time = datetime.now(timezone.utc)
    decisions = []
    for i in range(5):
        t = base_time - timedelta(minutes=10 * (5 - i))
        decisions.append(create_sample_decision(db, test_model.id, created_at=t))

    # Page 1: skip=0, limit=2
    page1 = service.list_decisions_for_model(test_model.id, user=test_owner, skip=0, limit=2)
    assert len(page1) == 2

    # Page 2: skip=2, limit=2
    page2 = service.list_decisions_for_model(test_model.id, user=test_owner, skip=2, limit=2)
    assert len(page2) == 2

    # Page 3: skip=4, limit=2
    page3 = service.list_decisions_for_model(test_model.id, user=test_owner, skip=4, limit=2)
    assert len(page3) >= 1

    # Ensure no overlap between page 1 and page 2
    p1_ids = {d.id for d in page1}
    p2_ids = {d.id for d in page2}
    assert p1_ids.isdisjoint(p2_ids)
    db.close()


# ---------------------------------------------------------------------------
# 3. Total / Count and DecisionHistoryResponse Structure
# ---------------------------------------------------------------------------

def test_total_count_and_history_response(test_model, test_owner):
    db = TestingSessionLocal()
    service = DecisionService(db)

    for i in range(3):
        create_sample_decision(db, test_model.id)

    total_count = service.count_decisions_for_model(test_model.id, user=test_owner)
    assert total_count >= 3

    history = service.get_decision_history(
        model_id=test_model.id,
        user=test_owner,
        skip=1,
        limit=2,
    )
    assert isinstance(history, DecisionHistoryResponse)
    assert history.model_id == test_model.id
    assert history.total == total_count
    assert history.skip == 1
    assert history.limit == 2
    assert len(history.items) == 2
    assert all(isinstance(item, DecisionLogRead) for item in history.items)
    db.close()


# ---------------------------------------------------------------------------
# 4. Model Ownership and RBAC Protection
# ---------------------------------------------------------------------------

def test_unauthorized_user_rejected_with_403(test_model, test_owner, other_user):
    db = TestingSessionLocal()
    service = DecisionService(db)

    created = create_sample_decision(db, test_model.id)

    # 1. Listing rejected
    with pytest.raises(HTTPException) as exc1:
        service.list_decisions_for_model(test_model.id, user=other_user)
    assert exc1.value.status_code == 403

    # 2. Single retrieval rejected
    with pytest.raises(HTTPException) as exc2:
        service.get_decision(created.id, model_id=test_model.id, user=other_user)
    assert exc2.value.status_code == 403

    # 3. Count rejected
    with pytest.raises(HTTPException) as exc3:
        service.count_decisions_for_model(test_model.id, user=other_user)
    assert exc3.value.status_code == 403

    # 4. History response rejected
    with pytest.raises(HTTPException) as exc4:
        service.get_decision_history(test_model.id, user=other_user)
    assert exc4.value.status_code == 403
    db.close()


def test_admin_can_access_any_model_history(test_model, admin_user):
    db = TestingSessionLocal()
    service = DecisionService(db)

    created = create_sample_decision(db, test_model.id)

    # Admin user is NOT the model owner, but has ADMIN role
    retrieved = service.get_decision(created.id, model_id=test_model.id, user=admin_user)
    assert retrieved.id == created.id

    listing = service.list_decisions_for_model(test_model.id, user=admin_user)
    assert len(listing) >= 1

    count = service.count_decisions_for_model(test_model.id, user=admin_user)
    assert count >= 1
    db.close()


# ---------------------------------------------------------------------------
# 5. Cross-Model Isolation
# ---------------------------------------------------------------------------

def test_multiple_models_cannot_expose_each_others_history(test_model, second_model, test_owner):
    db = TestingSessionLocal()
    service = DecisionService(db)

    dec_a = create_sample_decision(db, test_model.id, action=AIMDAction.CONTINUE_MONITORING)
    dec_b = create_sample_decision(db, second_model.id, action=AIMDAction.ROLLBACK)

    # Model A query never returns Model B decisions
    results_a = service.list_decisions_for_model(test_model.id, user=test_owner)
    ids_a = {d.id for d in results_a}
    assert dec_a.id in ids_a
    assert dec_b.id not in ids_a

    # Model B query never returns Model A decisions
    results_b = service.list_decisions_for_model(second_model.id, user=test_owner)
    ids_b = {d.id for d in results_b}
    assert dec_b.id in ids_b
    assert dec_a.id not in ids_b

    # Attempting to fetch dec_b using test_model.id returns 404 (Decision not found for model)
    with pytest.raises(HTTPException) as exc_info:
        service.get_decision(
            decision_id=dec_b.id,
            model_id=test_model.id,
            user=test_owner,
        )
    assert exc_info.value.status_code == 404
    db.close()


# ---------------------------------------------------------------------------
# 6. Empty Decision History
# ---------------------------------------------------------------------------

def test_empty_decision_history(second_model, test_owner):
    db = TestingSessionLocal()
    service = DecisionService(db)

    results = service.list_decisions_for_model(second_model.id, user=test_owner)
    assert len(results) == 0

    count = service.count_decisions_for_model(second_model.id, user=test_owner)
    assert count == 0

    history = service.get_decision_history(second_model.id, user=test_owner)
    assert history.total == 0
    assert len(history.items) == 0
    db.close()


# ---------------------------------------------------------------------------
# 7. Preservation of All AIMD DecisionLog Fields in Read Schema
# ---------------------------------------------------------------------------

def test_preservation_of_all_aimd_fields(test_model, test_owner):
    db = TestingSessionLocal()
    service = DecisionService(db)
    repo = DecisionLogRepository(db)

    custom_signals = {
        "drifted_features": ["urgency_score", "link_density"],
        "metric_shifts": {"f1_score": -0.08, "precision": -0.12},
    }

    dec_in = DecisionLogCreate(
        model_id=test_model.id,
        health_score=68.4,
        health_status="warning",
        recommended_action=AIMDAction.DATA_COLLECTION,
        priority=AIMDPriority.HIGH,
        confidence=0.88,
        rationale="Feature distribution drift observed with mild health warning.",
        explanation="Diagnostic explainability factor: link_density shifted significantly.",
        supporting_signals=custom_signals,
        requires_human_approval=True,
        approval_status=ApprovalStatus.PENDING,
    )
    created = repo.create(dec_in)

    read_model = service.get_decision(
        decision_id=created.id,
        model_id=test_model.id,
        user=test_owner,
        as_read_schema=True,
    )

    assert isinstance(read_model, DecisionLogRead)
    assert read_model.id == created.id
    assert read_model.model_id == test_model.id
    assert read_model.health_score == 68.4
    assert read_model.health_status == "warning"
    assert read_model.recommended_action == AIMDAction.DATA_COLLECTION
    assert read_model.priority == AIMDPriority.HIGH
    assert read_model.confidence == 0.88
    assert read_model.rationale == "Feature distribution drift observed with mild health warning."
    assert read_model.explanation == "Diagnostic explainability factor: link_density shifted significantly."
    assert read_model.supporting_signals == custom_signals
    assert read_model.requires_human_approval is True
    assert read_model.approval_status == ApprovalStatus.PENDING
    assert read_model.created_at is not None
    assert read_model.created_at.tzinfo is not None
    db.close()


# ---------------------------------------------------------------------------
# 8. Repository Query Method: get_by_id_and_model Direct Test
# ---------------------------------------------------------------------------

def test_repository_get_by_id_and_model_directly(test_model, second_model):
    db = TestingSessionLocal()
    repo = DecisionLogRepository(db)

    dec = create_sample_decision(db, test_model.id)

    # Correct model matches
    found = repo.get_by_id_and_model(dec.id, test_model.id)
    assert found is not None
    assert found.id == dec.id

    # Mismatched model returns None
    wrong_model = repo.get_by_id_and_model(dec.id, second_model.id)
    assert wrong_model is None

    # Non-existent decision returns None
    non_existent = repo.get_by_id_and_model(uuid.uuid4(), test_model.id)
    assert non_existent is None
    db.close()
