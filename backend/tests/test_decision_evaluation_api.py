import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.auth.exceptions import AuthorizationError
from app.auth.security import get_password_hash
from app.decisions import (
    AIMDAction,
    AIMDPriority,
    AIMDConfidence,
    ApprovalStatus,
    DecisionLog,
    DecisionLogRead,
    DecisionLogRepository,
    DecisionService,
)
from app.models.models import ModelStatus, RegisteredModel, MonitoringObservation
from app.models.monitoring_schemas import MonitoringObservationCreate
from app.models.monitoring_repository import MonitoringObservationRepository
from app.users.models import User, UserRole
from tests.conftest import TestingSessionLocal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_owner_engineer(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="eval_eng_owner",
        email="eval_owner@example.com",
        full_name="Evaluation Owner",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="EngineersEvalModel",
        framework="Scikit-Learn",
        owner_id=user.id,
        status=ModelStatus.ACTIVE,
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    resp = client.post("/api/auth/login", data={"username": "eval_eng_owner", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = user.id
    model_id = model.id
    db.close()
    return {"user_id": user_id, "token": token, "model_id": model_id}


@pytest.fixture
def test_other_engineer(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="eval_other_eng",
        email="eval_other@example.com",
        full_name="Other Evaluation Engineer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="OtherEngineersEvalModel",
        framework="Scikit-Learn",
        owner_id=user.id,
        status=ModelStatus.ACTIVE,
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    resp = client.post("/api/auth/login", data={"username": "eval_other_eng", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = user.id
    model_id = model.id
    db.close()
    return {"user_id": user_id, "token": token, "model_id": model_id}


@pytest.fixture
def test_viewer(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="eval_viewer",
        email="eval_viewer@example.com",
        full_name="Evaluation Viewer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    resp = client.post("/api/auth/login", data={"username": "eval_viewer", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = user.id
    db.close()
    return {"user_id": user_id, "token": token}


@pytest.fixture
def test_admin(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="eval_admin",
        email="eval_admin@example.com",
        full_name="Evaluation Admin",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    resp = client.post("/api/auth/login", data={"username": "eval_admin", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = user.id
    db.close()
    return {"user_id": user_id, "token": token}


def seed_observations(db, model_id: uuid.UUID, obs_data: list):
    """Helper to insert monitoring observations into DB."""
    repo = MonitoringObservationRepository(db)
    created = []
    for d in obs_data:
        obs_in = MonitoringObservationCreate(
            model_id=model_id,
            observed_at=d["observed_at"],
            prediction_count=d.get("prediction_count", 1000),
            positive_prediction_count=d.get("positive_prediction_count", 100),
            negative_prediction_count=d.get("negative_prediction_count", 900),
            accuracy=d.get("accuracy", 0.95),
            precision=d.get("precision", 0.95),
            recall=d.get("recall", 0.95),
            f1_score=d.get("f1_score", 0.95),
        )
        created.append(repo.create(obs_in))
    return created


# ---------------------------------------------------------------------------
# API Endpoint Tests: POST /api/spam-models/{model_id}/decisions/evaluate
# ---------------------------------------------------------------------------

def test_evaluate_unauthenticated_returns_401(client: TestClient, test_owner_engineer):
    model_id = test_owner_engineer["model_id"]
    resp = client.post(f"/api/spam-models/{model_id}/decisions/evaluate")
    assert resp.status_code == 401


def test_evaluate_viewer_returns_403(client: TestClient, test_owner_engineer, test_viewer):
    model_id = test_owner_engineer["model_id"]
    resp = client.post(
        f"/api/spam-models/{model_id}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_viewer['token']}"},
    )
    assert resp.status_code == 403


def test_evaluate_non_owner_engineer_returns_403(client: TestClient, test_owner_engineer, test_other_engineer):
    model_id = test_owner_engineer["model_id"]
    resp = client.post(
        f"/api/spam-models/{model_id}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_other_engineer['token']}"},
    )
    assert resp.status_code == 403


def test_evaluate_nonexistent_model_returns_404(client: TestClient, test_owner_engineer):
    fake_id = uuid.uuid4()
    resp = client.post(
        f"/api/spam-models/{fake_id}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_owner_engineer['token']}"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Model not found"


def test_evaluate_invalid_uuid_returns_422(client: TestClient, test_owner_engineer):
    resp = client.post(
        "/api/spam-models/not-a-valid-uuid/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_owner_engineer['token']}"},
    )
    assert resp.status_code == 422


def test_evaluate_zero_observations_returns_human_review(client: TestClient, test_owner_engineer):
    model_id = test_owner_engineer["model_id"]
    resp = client.post(
        f"/api/spam-models/{model_id}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_owner_engineer['token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["model_id"] == str(model_id)
    assert data["recommended_action"] == AIMDAction.HUMAN_REVIEW.value
    assert data["priority"] == AIMDPriority.MEDIUM.value
    assert data["requires_human_approval"] is True
    assert data["approval_status"] == ApprovalStatus.PENDING.value
    assert "insufficient_data" in data["supporting_signals"]


def test_evaluate_healthy_observations_returns_continue_monitoring(client: TestClient, test_owner_engineer):
    model_id = test_owner_engineer["model_id"]
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    seed_observations(
        db,
        model_id,
        [
            {"observed_at": now - timedelta(hours=2), "accuracy": 0.94, "precision": 0.93, "recall": 0.92, "f1_score": 0.925},
            {"observed_at": now - timedelta(hours=1), "accuracy": 0.95, "precision": 0.94, "recall": 0.93, "f1_score": 0.935},
        ],
    )
    db.close()

    resp = client.post(
        f"/api/spam-models/{model_id}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_owner_engineer['token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["model_id"] == str(model_id)
    assert data["recommended_action"] == AIMDAction.CONTINUE_MONITORING.value
    assert data["priority"] == AIMDPriority.LOW.value
    assert data["health_status"] == "healthy"
    assert data["health_score"] is not None
    assert data["health_score"] >= 80.0
    assert data["requires_human_approval"] is True
    assert data["approval_status"] == ApprovalStatus.PENDING.value
    assert data["confidence"] == 0.9


def test_evaluate_critical_degradation_returns_retrain(client: TestClient, test_owner_engineer):
    model_id = test_owner_engineer["model_id"]
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    seed_observations(
        db,
        model_id,
        [
            {"observed_at": now - timedelta(hours=2), "accuracy": 0.92, "precision": 0.90, "recall": 0.90, "f1_score": 0.90},
            {"observed_at": now - timedelta(hours=1), "accuracy": 0.50, "precision": 0.45, "recall": 0.40, "f1_score": 0.42},
        ],
    )
    db.close()

    resp = client.post(
        f"/api/spam-models/{model_id}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_owner_engineer['token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["model_id"] == str(model_id)
    # Critical health without verified rollback context safely falls back to RETRAIN
    assert data["recommended_action"] == AIMDAction.RETRAIN.value
    assert data["priority"] == AIMDPriority.CRITICAL.value
    assert data["health_status"] == "critical"
    assert data["health_score"] is not None
    assert data["health_score"] < 60.0
    assert data["requires_human_approval"] is True
    assert data["approval_status"] == ApprovalStatus.PENDING.value
    assert data["confidence"] == 0.9


def test_evaluate_warning_health_returns_human_review(client: TestClient, test_owner_engineer):
    model_id = test_owner_engineer["model_id"]
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    seed_observations(
        db,
        model_id,
        [
            {"observed_at": now - timedelta(hours=2), "accuracy": 0.72, "precision": 0.70, "recall": 0.70, "f1_score": 0.70},
            {"observed_at": now - timedelta(hours=1), "accuracy": 0.72, "precision": 0.70, "recall": 0.70, "f1_score": 0.70},
        ],
    )
    db.close()

    resp = client.post(
        f"/api/spam-models/{model_id}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_owner_engineer['token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["model_id"] == str(model_id)
    # AIMD Rule 3: Warning health without detected drift recommends HUMAN_REVIEW to avoid uncharacterized retraining
    assert data["recommended_action"] == AIMDAction.HUMAN_REVIEW.value
    assert data["priority"] == AIMDPriority.MEDIUM.value
    assert data["health_status"] == "warning"
    assert 60.0 <= data["health_score"] < 80.0
    assert data["requires_human_approval"] is True
    assert data["approval_status"] == ApprovalStatus.PENDING.value


def test_evaluate_admin_can_evaluate_any_model(client: TestClient, test_owner_engineer, test_admin):
    model_id = test_owner_engineer["model_id"]
    resp = client.post(
        f"/api/spam-models/{model_id}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_admin['token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["model_id"] == str(model_id)
    assert data["requires_human_approval"] is True


def test_evaluate_alias_post_decisions_endpoint(client: TestClient, test_owner_engineer):
    model_id = test_owner_engineer["model_id"]
    resp = client.post(
        f"/api/spam-models/{model_id}/decisions",
        headers={"Authorization": f"Bearer {test_owner_engineer['token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["model_id"] == str(model_id)
    assert data["requires_human_approval"] is True


# ---------------------------------------------------------------------------
# Direct Service Unit Tests: DecisionService.evaluate_model
# ---------------------------------------------------------------------------

def test_service_evaluate_model_single_observation(test_owner_engineer):
    db = TestingSessionLocal()
    service = DecisionService(db)
    model_id = test_owner_engineer["model_id"]

    now = datetime.now(timezone.utc)
    seed_observations(
        db,
        model_id,
        [{"observed_at": now, "accuracy": 0.95, "precision": 0.94, "recall": 0.93, "f1_score": 0.94}],
    )

    decision = service.evaluate_model(model_id=model_id, as_read_schema=False)
    assert isinstance(decision, DecisionLog)
    assert decision.model_id == model_id
    assert decision.recommended_action == AIMDAction.CONTINUE_MONITORING
    assert decision.priority == AIMDPriority.LOW
    assert decision.health_status == "healthy"
    assert decision.requires_human_approval is True
    assert decision.approval_status == ApprovalStatus.PENDING
    db.close()


def test_service_evaluate_model_chronological_sorting_robustness(test_owner_engineer):
    """
    Even if observations were inserted in out-of-order timestamps,
    evaluate_model sorts chronologically so performance and health are accurately evaluated.
    """
    db = TestingSessionLocal()
    service = DecisionService(db)
    model_id = test_owner_engineer["model_id"]

    now = datetime.now(timezone.utc)
    # Insert newer first, then older
    seed_observations(
        db,
        model_id,
        [
            {"observed_at": now, "accuracy": 0.96, "precision": 0.95, "recall": 0.94, "f1_score": 0.95},
            {"observed_at": now - timedelta(hours=5), "accuracy": 0.85, "precision": 0.85, "recall": 0.85, "f1_score": 0.85},
        ],
    )

    decision = service.evaluate_model(model_id=model_id, as_read_schema=True)
    assert isinstance(decision, DecisionLogRead)
    assert decision.health_status == "healthy"
    assert decision.recommended_action == AIMDAction.CONTINUE_MONITORING
    db.close()


def test_service_evaluate_model_viewer_rejected(test_owner_engineer, test_viewer):
    db = TestingSessionLocal()
    service = DecisionService(db)
    model_id = test_owner_engineer["model_id"]

    viewer_user = User(
        id=test_viewer["user_id"],
        username="eval_viewer",
        role=UserRole.VIEWER,
    )

    with pytest.raises(AuthorizationError) as exc_info:
        service.evaluate_model(model_id=model_id, user=viewer_user)
    assert "Viewers are not authorized" in str(exc_info.value.detail)
    db.close()


def test_service_evaluate_model_non_owner_rejected(test_owner_engineer, test_other_engineer):
    db = TestingSessionLocal()
    service = DecisionService(db)
    model_id = test_owner_engineer["model_id"]

    other_user = User(
        id=test_other_engineer["user_id"],
        username="eval_other_eng",
        role=UserRole.ML_ENGINEER,
    )

    with pytest.raises(AuthorizationError):
        service.evaluate_model(model_id=model_id, user=other_user)
    db.close()


def test_service_evaluate_model_missing_model_raises_404():
    db = TestingSessionLocal()
    service = DecisionService(db)
    fake_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        service.evaluate_model(model_id=fake_id)
    assert exc_info.value.status_code == 404
    db.close()


def test_service_evaluate_model_missing_obs_repo_raises_runtime_error():
    service = DecisionService(db=None)
    with pytest.raises(RuntimeError) as exc_info:
        service.evaluate_model(model_id=uuid.uuid4())
    # RegisteredModelRepository checked first
    assert "RegisteredModelRepository is not configured" in str(exc_info.value)
