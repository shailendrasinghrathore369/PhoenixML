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
    ApprovalStatus,
    DecisionLogCreate,
    DecisionLogRepository,
)
from app.models.models import ModelStatus, RegisteredModel, MonitoringObservation
from app.models.monitoring_schemas import MonitoringObservationCreate
from app.models.monitoring_repository import MonitoringObservationRepository
from app.users.models import User, UserRole
from app.dashboard.schemas import DashboardOverviewResponse
from app.dashboard.service import DashboardService
from tests.conftest import TestingSessionLocal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_dashboard_admin(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="dash_admin",
        email="dash_admin@example.com",
        full_name="Dashboard Admin",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    resp = client.post("/api/auth/login", data={"username": "dash_admin", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = user.id
    db.close()
    return {"user_id": user_id, "token": token, "user": user}


@pytest.fixture
def test_dashboard_eng1(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="dash_eng1",
        email="dash_eng1@example.com",
        full_name="Dashboard Engineer One",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model1 = RegisteredModel(
        id=uuid.uuid4(),
        name="Eng1ModelAlpha",
        framework="Scikit-Learn",
        algorithm="LogisticRegression",
        owner_id=user.id,
        status=ModelStatus.ACTIVE,
    )
    model2 = RegisteredModel(
        id=uuid.uuid4(),
        name="Eng1ModelBeta",
        framework="PyTorch",
        algorithm="Transformer",
        owner_id=user.id,
        status=ModelStatus.DEVELOPMENT,
    )
    db.add_all([model1, model2])
    db.commit()
    db.refresh(model1)
    db.refresh(model2)

    resp = client.post("/api/auth/login", data={"username": "dash_eng1", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = user.id
    m1_id = model1.id
    m2_id = model2.id
    db.close()
    return {"user_id": user_id, "token": token, "model1_id": m1_id, "model2_id": m2_id, "user": user}


@pytest.fixture
def test_dashboard_eng2(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="dash_eng2",
        email="dash_eng2@example.com",
        full_name="Dashboard Engineer Two",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="Eng2ModelGamma",
        framework="TensorFlow",
        algorithm="CNN",
        owner_id=user.id,
        status=ModelStatus.ACTIVE,
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    resp = client.post("/api/auth/login", data={"username": "dash_eng2", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = user.id
    m_id = model.id
    db.close()
    return {"user_id": user_id, "token": token, "model_id": m_id, "user": user}


@pytest.fixture
def test_dashboard_viewer(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="dash_viewer",
        email="dash_viewer@example.com",
        full_name="Dashboard Viewer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    resp = client.post("/api/auth/login", data={"username": "dash_viewer", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = user.id
    db.close()
    return {"user_id": user_id, "token": token, "user": user}


def create_sample_observation(db, model_id: uuid.UUID, observed_at=None, f1=0.95, accuracy=0.95):
    repo = MonitoringObservationRepository(db)
    return repo.create(
        MonitoringObservationCreate(
            model_id=model_id,
            observed_at=observed_at or datetime.now(timezone.utc),
            prediction_count=1000,
            positive_prediction_count=100,
            negative_prediction_count=900,
            accuracy=accuracy,
            precision=f1,
            recall=f1,
            f1_score=f1,
        )
    )


def create_sample_decision(db, model_id: uuid.UUID, action=AIMDAction.CONTINUE_MONITORING, priority=AIMDPriority.LOW, status=ApprovalStatus.PENDING, score=90.0, created_at=None):
    repo = DecisionLogRepository(db)
    return repo.create(
        DecisionLogCreate(
            model_id=model_id,
            created_at=created_at or datetime.now(timezone.utc),
            health_score=score,
            health_status="healthy" if score >= 80 else ("warning" if score >= 60 else "critical"),
            recommended_action=action,
            priority=priority,
            confidence=0.9,
            rationale="Dashboard test rationale",
            explanation="Dashboard test explanation",
            requires_human_approval=True,
            approval_status=status,
        )
    )


# ---------------------------------------------------------------------------
# API Integration Tests
# ---------------------------------------------------------------------------

def test_dashboard_unauthenticated_returns_401(client: TestClient):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 401


def test_dashboard_viewer_empty_returns_clean_defaults(client: TestClient, test_dashboard_viewer):
    resp = client.get(
        "/api/dashboard",
        headers={"Authorization": f"Bearer {test_dashboard_viewer['token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scope"] == "user"
    assert data["models_summary"]["total_models"] == 0
    assert data["models_summary"]["active_models"] == 0
    assert data["monitoring_summary"]["total_observations"] == 0
    assert data["health_summary"]["system_health_status"] == "NO_MODELS"
    assert data["decision_summary"]["total_decisions"] == 0
    assert data["decision_summary"]["pending_approvals_count"] == 0
    assert data["model_cards"] == []


def test_dashboard_admin_sees_all_models(client: TestClient, test_dashboard_admin, test_dashboard_eng1, test_dashboard_eng2):
    resp = client.get(
        "/api/dashboard",
        headers={"Authorization": f"Bearer {test_dashboard_admin['token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scope"] == "global"
    # Admin sees at least model1, model2 (eng1) and model3 (eng2)
    assert data["models_summary"]["total_models"] >= 3
    card_ids = [c["model_id"] for c in data["model_cards"]]
    assert str(test_dashboard_eng1["model1_id"]) in card_ids
    assert str(test_dashboard_eng1["model2_id"]) in card_ids
    assert str(test_dashboard_eng2["model_id"]) in card_ids


def test_dashboard_engineer_sees_only_own_models(client: TestClient, test_dashboard_eng1, test_dashboard_eng2):
    resp = client.get(
        "/api/dashboard",
        headers={"Authorization": f"Bearer {test_dashboard_eng1['token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scope"] == "user"
    assert data["models_summary"]["total_models"] == 2
    assert data["models_summary"]["active_models"] == 1
    assert data["models_summary"]["development_models"] == 1
    card_ids = [c["model_id"] for c in data["model_cards"]]
    assert str(test_dashboard_eng1["model1_id"]) in card_ids
    assert str(test_dashboard_eng1["model2_id"]) in card_ids
    assert str(test_dashboard_eng2["model_id"]) not in card_ids


def test_dashboard_model_scoped_via_query_param(client: TestClient, test_dashboard_eng1):
    m1_id = test_dashboard_eng1["model1_id"]
    resp = client.get(
        f"/api/dashboard?model_id={m1_id}",
        headers={"Authorization": f"Bearer {test_dashboard_eng1['token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scope"] == "model"
    assert data["models_summary"]["total_models"] == 1
    assert len(data["model_cards"]) == 1
    assert data["model_cards"][0]["model_id"] == str(m1_id)
    assert data["model_cards"][0]["name"] == "Eng1ModelAlpha"


def test_dashboard_model_scoped_via_path_param(client: TestClient, test_dashboard_eng1):
    m1_id = test_dashboard_eng1["model1_id"]
    resp = client.get(
        f"/api/dashboard/{m1_id}",
        headers={"Authorization": f"Bearer {test_dashboard_eng1['token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scope"] == "model"
    assert data["models_summary"]["total_models"] == 1
    assert data["model_cards"][0]["model_id"] == str(m1_id)


def test_dashboard_model_scoped_nonexistent_returns_404(client: TestClient, test_dashboard_eng1):
    fake_id = uuid.uuid4()
    resp = client.get(
        f"/api/dashboard/{fake_id}",
        headers={"Authorization": f"Bearer {test_dashboard_eng1['token']}"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Model not found"


def test_dashboard_model_scoped_other_user_returns_403(client: TestClient, test_dashboard_eng1, test_dashboard_eng2):
    # Eng2 attempts to access Eng1's model dashboard
    m1_id = test_dashboard_eng1["model1_id"]
    resp = client.get(
        f"/api/dashboard/{m1_id}",
        headers={"Authorization": f"Bearer {test_dashboard_eng2['token']}"},
    )
    assert resp.status_code == 403


def test_dashboard_invalid_uuid_returns_422(client: TestClient, test_dashboard_eng1):
    resp = client.get(
        "/api/dashboard/invalid-uuid-string",
        headers={"Authorization": f"Bearer {test_dashboard_eng1['token']}"},
    )
    assert resp.status_code == 422


def test_dashboard_aggregates_health_and_monitoring(client: TestClient, test_dashboard_eng1):
    db = TestingSessionLocal()
    m1_id = test_dashboard_eng1["model1_id"]
    m2_id = test_dashboard_eng1["model2_id"]

    now = datetime.now(timezone.utc)
    create_sample_observation(db, m1_id, observed_at=now, f1=0.92, accuracy=0.94)
    create_sample_observation(db, m2_id, observed_at=now - timedelta(hours=1), f1=0.65, accuracy=0.68)
    db.close()

    resp = client.get(
        "/api/dashboard",
        headers={"Authorization": f"Bearer {test_dashboard_eng1['token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["monitoring_summary"]["total_observations"] == 2
    assert data["monitoring_summary"]["latest_observation_at"] is not None
    assert data["health_summary"]["healthy_count"] == 1
    assert data["health_summary"]["warning_count"] == 1
    assert data["health_summary"]["critical_count"] == 0
    assert data["health_summary"]["system_health_status"] == "WARNING"


def test_dashboard_decision_pending_approvals_count(client: TestClient, test_dashboard_eng1):
    db = TestingSessionLocal()
    m1_id = test_dashboard_eng1["model1_id"]

    create_sample_decision(db, m1_id, action=AIMDAction.CONTINUE_MONITORING, status=ApprovalStatus.PENDING)
    create_sample_decision(db, m1_id, action=AIMDAction.RETRAIN, priority=AIMDPriority.CRITICAL, status=ApprovalStatus.PENDING)
    create_sample_decision(db, m1_id, action=AIMDAction.DATA_COLLECTION, status=ApprovalStatus.APPROVED)
    db.close()

    resp = client.get(
        f"/api/dashboard/{m1_id}",
        headers={"Authorization": f"Bearer {test_dashboard_eng1['token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision_summary"]["total_decisions"] == 3
    # Human-in-the-loop: 2 pending approvals highlighted
    assert data["decision_summary"]["pending_approvals_count"] == 2
    assert data["decision_summary"]["approved_count"] == 1
    assert data["decision_summary"]["rejected_count"] == 0
    assert data["decision_summary"]["critical_priority_count"] == 1
    assert len(data["decision_summary"]["recent_decisions"]) == 3
    assert data["model_cards"][0]["pending_decisions_count"] == 2


def test_dashboard_recent_decisions_capped_at_five(client: TestClient, test_dashboard_eng1):
    db = TestingSessionLocal()
    m1_id = test_dashboard_eng1["model1_id"]

    base = datetime.now(timezone.utc)
    for i in range(8):
        create_sample_decision(
            db,
            m1_id,
            action=AIMDAction.CONTINUE_MONITORING,
            created_at=base + timedelta(minutes=i),
        )
    db.close()

    resp = client.get(
        f"/api/dashboard/{m1_id}",
        headers={"Authorization": f"Bearer {test_dashboard_eng1['token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision_summary"]["total_decisions"] == 8
    # Recent decisions capped at 5
    assert len(data["decision_summary"]["recent_decisions"]) == 5


# ---------------------------------------------------------------------------
# Direct Service Unit Tests
# ---------------------------------------------------------------------------

def test_service_get_dashboard_overview_admin(test_dashboard_admin, test_dashboard_eng1):
    db = TestingSessionLocal()
    service = DashboardService(db)

    overview = service.get_dashboard_overview(user=test_dashboard_admin["user"])
    assert isinstance(overview, DashboardOverviewResponse)
    assert overview.scope == "global"
    assert overview.models_summary.total_models >= 2
    db.close()


def test_service_get_dashboard_overview_user(test_dashboard_eng1):
    db = TestingSessionLocal()
    service = DashboardService(db)

    overview = service.get_dashboard_overview(user=test_dashboard_eng1["user"])
    assert isinstance(overview, DashboardOverviewResponse)
    assert overview.scope == "user"
    assert overview.models_summary.total_models == 2
    db.close()


def test_service_get_dashboard_overview_missing_model_raises_404(test_dashboard_eng1):
    db = TestingSessionLocal()
    service = DashboardService(db)
    fake_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        service.get_dashboard_overview(user=test_dashboard_eng1["user"], model_id=fake_id)
    assert exc_info.value.status_code == 404
    db.close()


def test_service_get_dashboard_overview_unauthorized_model_raises_403(test_dashboard_eng1, test_dashboard_eng2):
    db = TestingSessionLocal()
    service = DashboardService(db)
    m1_id = test_dashboard_eng1["model1_id"]

    with pytest.raises(AuthorizationError):
        service.get_dashboard_overview(user=test_dashboard_eng2["user"], model_id=m1_id)
    db.close()
