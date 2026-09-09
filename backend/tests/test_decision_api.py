import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.auth.security import get_password_hash
from app.decisions import (
    AIMDAction,
    AIMDPriority,
    ApprovalStatus,
    DecisionLogCreate,
    DecisionLogRepository,
)
from app.models.models import ModelStatus, RegisteredModel
from app.users.models import User, UserRole
from tests.conftest import TestingSessionLocal


@pytest.fixture
def test_user_engine(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="api_eng_user",
        email="api_eng@example.com",
        full_name="API Engineer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="EngineersSpamModel",
        framework="Scikit-Learn",
        owner_id=user.id,
        status=ModelStatus.ACTIVE,
    )
    db.add(model)
    db.commit()

    resp = client.post("/api/auth/login", data={"username": "api_eng_user", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = str(user.id)
    model_id = str(model.id)
    db.close()
    return {"user_id": user_id, "token": token, "model_id": model_id}


@pytest.fixture
def test_user_viewer(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="api_viewer_user",
        email="api_viewer@example.com",
        full_name="API Viewer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="ViewersSpamModel",
        framework="PyTorch",
        owner_id=user.id,
        status=ModelStatus.ACTIVE,
    )
    db.add(model)
    db.commit()

    resp = client.post("/api/auth/login", data={"username": "api_viewer_user", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = str(user.id)
    model_id = str(model.id)
    db.close()
    return {"user_id": user_id, "token": token, "model_id": model_id}


@pytest.fixture
def test_user_admin(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="api_admin_user",
        email="api_admin@example.com",
        full_name="API Admin",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="AdminsSpamModel",
        framework="TensorFlow",
        owner_id=user.id,
        status=ModelStatus.ACTIVE,
    )
    db.add(model)
    db.commit()

    resp = client.post("/api/auth/login", data={"username": "api_admin_user", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = str(user.id)
    model_id = str(model.id)
    db.close()
    return {"user_id": user_id, "token": token, "model_id": model_id}


def seed_decision(
    db,
    model_id,
    action=AIMDAction.CONTINUE_MONITORING,
    priority=AIMDPriority.LOW,
    confidence=0.9,
    rationale="Test decision rationale.",
    explanation="Test diagnostic explanation.",
    supporting_signals=None,
    created_at=None,
    health_score=88.5,
    health_status="healthy",
):
    repo = DecisionLogRepository(db)
    dec_in = DecisionLogCreate(
        model_id=uuid.UUID(str(model_id)),
        created_at=created_at or datetime.now(timezone.utc),
        health_score=health_score,
        health_status=health_status,
        recommended_action=action,
        priority=priority,
        confidence=confidence,
        rationale=rationale,
        explanation=explanation,
        supporting_signals=supporting_signals or ["sig_1", "sig_2"],
        requires_human_approval=True,
        approval_status=ApprovalStatus.PENDING,
    )
    rec = repo.create(dec_in)
    db.expunge(rec)
    return rec


# ---------------------------------------------------------------------------
# 1. Authentication Enforcement (401)
# ---------------------------------------------------------------------------

def test_unauthenticated_requests_rejected(client: TestClient):
    model_id = str(uuid.uuid4())
    decision_id = str(uuid.uuid4())

    resp_list = client.get(f"/api/spam-models/{model_id}/decisions")
    assert resp_list.status_code == 401

    resp_get = client.get(f"/api/spam-models/{model_id}/decisions/{decision_id}")
    assert resp_get.status_code == 401


# ---------------------------------------------------------------------------
# 2. Authenticated Query Success (List & Single Decision)
# ---------------------------------------------------------------------------

def test_authenticated_list_and_single_decision_success(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    dec = seed_decision(db, model_id, action=AIMDAction.CONTINUE_MONITORING)
    db.close()

    # List
    resp_list = client.get(f"/api/spam-models/{model_id}/decisions", headers=headers)
    assert resp_list.status_code == 200
    data_list = resp_list.json()
    assert data_list["model_id"] == model_id
    assert data_list["total"] >= 1
    assert data_list["skip"] == 0
    assert data_list["limit"] == 100
    assert len(data_list["items"]) >= 1
    assert any(item["id"] == str(dec.id) for item in data_list["items"])

    # Single
    resp_single = client.get(f"/api/spam-models/{model_id}/decisions/{dec.id}", headers=headers)
    assert resp_single.status_code == 200
    data_single = resp_single.json()
    assert data_single["id"] == str(dec.id)
    assert data_single["model_id"] == model_id
    assert data_single["recommended_action"] == AIMDAction.CONTINUE_MONITORING.value


# ---------------------------------------------------------------------------
# 3. Pagination & Newest-First Ordering
# ---------------------------------------------------------------------------

def test_pagination_and_newest_first_ordering(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    base_time = datetime.now(timezone.utc)
    dec_ids = []
    for i in range(5):
        t = base_time - timedelta(minutes=10 * (5 - i))
        dec = seed_decision(db, model_id, created_at=t)
        dec_ids.append(str(dec.id))
    db.close()

    # Verify Newest-First: dec_ids[4] (newest) must appear before dec_ids[0] (oldest)
    resp_all = client.get(f"/api/spam-models/{model_id}/decisions?limit=100", headers=headers)
    assert resp_all.status_code == 200
    item_ids = [item["id"] for item in resp_all.json()["items"]]
    assert item_ids.index(dec_ids[4]) < item_ids.index(dec_ids[0])

    # Pagination: Page 1 (limit=2)
    resp_p1 = client.get(f"/api/spam-models/{model_id}/decisions?skip=0&limit=2", headers=headers)
    assert resp_p1.status_code == 200
    p1_data = resp_p1.json()
    assert len(p1_data["items"]) == 2
    assert p1_data["skip"] == 0
    assert p1_data["limit"] == 2
    assert p1_data["total"] >= 5

    # Page 2 (skip=2, limit=2)
    resp_p2 = client.get(f"/api/spam-models/{model_id}/decisions?skip=2&limit=2", headers=headers)
    assert resp_p2.status_code == 200
    p2_data = resp_p2.json()
    assert len(p2_data["items"]) == 2

    # Disjoint check
    p1_ids = {item["id"] for item in p1_data["items"]}
    p2_ids = {item["id"] for item in p2_data["items"]}
    assert p1_ids.isdisjoint(p2_ids)


# ---------------------------------------------------------------------------
# 4. Empty Decision History
# ---------------------------------------------------------------------------

def test_empty_decision_history(client: TestClient, test_user_viewer):
    headers = {"Authorization": f"Bearer {test_user_viewer['token']}"}
    model_id = test_user_viewer["model_id"]

    resp = client.get(f"/api/spam-models/{model_id}/decisions", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_id"] == model_id
    assert data["total"] == 0
    assert data["items"] == []


# ---------------------------------------------------------------------------
# 5. Nonexistent Model and Decision Handling (404)
# ---------------------------------------------------------------------------

def test_nonexistent_model_returns_404(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    non_existent_model = str(uuid.uuid4())
    random_decision = str(uuid.uuid4())

    resp_list = client.get(f"/api/spam-models/{non_existent_model}/decisions", headers=headers)
    assert resp_list.status_code == 404
    assert "Model not found" in resp_list.json()["detail"]

    resp_get = client.get(f"/api/spam-models/{non_existent_model}/decisions/{random_decision}", headers=headers)
    assert resp_get.status_code == 404
    assert "Model not found" in resp_get.json()["detail"]


def test_nonexistent_decision_returns_404(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]
    random_decision = str(uuid.uuid4())

    resp = client.get(f"/api/spam-models/{model_id}/decisions/{random_decision}", headers=headers)
    assert resp.status_code == 404
    assert "Decision not found" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 6. Cross-Model Isolation (404)
# ---------------------------------------------------------------------------

def test_cross_model_decision_access_forbidden(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_a_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    # Create second model owned by the same engineer
    model_b = RegisteredModel(
        id=uuid.uuid4(),
        name="EngineersSecondSpamModel",
        framework="Scikit-Learn",
        owner_id=uuid.UUID(test_user_engine["user_id"]),
        status=ModelStatus.ACTIVE,
    )
    db.add(model_b)
    db.commit()

    dec_b = seed_decision(db, model_b.id, action=AIMDAction.ROLLBACK)
    db.close()

    # Requesting dec_b via model_a_id URL must fail with 404
    resp = client.get(f"/api/spam-models/{model_a_id}/decisions/{dec_b.id}", headers=headers)
    assert resp.status_code == 404
    assert "Decision not found" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 7. Authorization & RBAC Enforcement (403 for unauthorized users, 200 for ADMIN)
# ---------------------------------------------------------------------------

def test_unauthorized_user_receives_403(client: TestClient, test_user_engine, test_user_viewer):
    eng_model_id = test_user_engine["model_id"]
    viewer_headers = {"Authorization": f"Bearer {test_user_viewer['token']}"}

    db = TestingSessionLocal()
    dec = seed_decision(db, eng_model_id)
    db.close()

    # Viewer cannot list Engineer's model decisions
    resp_list = client.get(f"/api/spam-models/{eng_model_id}/decisions", headers=viewer_headers)
    assert resp_list.status_code == 403
    assert "Not authorized" in resp_list.json()["detail"]

    # Viewer cannot retrieve Engineer's decision
    resp_get = client.get(f"/api/spam-models/{eng_model_id}/decisions/{dec.id}", headers=viewer_headers)
    assert resp_get.status_code == 403
    assert "Not authorized" in resp_get.json()["detail"]


def test_admin_can_access_any_model_decisions(client: TestClient, test_user_engine, test_user_admin):
    eng_model_id = test_user_engine["model_id"]
    admin_headers = {"Authorization": f"Bearer {test_user_admin['token']}"}

    db = TestingSessionLocal()
    dec = seed_decision(db, eng_model_id, action=AIMDAction.RETRAIN, priority=AIMDPriority.HIGH)
    db.close()

    # Admin lists Engineer's model decisions
    resp_list = client.get(f"/api/spam-models/{eng_model_id}/decisions", headers=admin_headers)
    assert resp_list.status_code == 200
    assert any(item["id"] == str(dec.id) for item in resp_list.json()["items"])

    # Admin retrieves Engineer's decision
    resp_get = client.get(f"/api/spam-models/{eng_model_id}/decisions/{dec.id}", headers=admin_headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == str(dec.id)


def test_viewer_can_access_own_model_decisions(client: TestClient, test_user_viewer):
    viewer_model_id = test_user_viewer["model_id"]
    viewer_headers = {"Authorization": f"Bearer {test_user_viewer['token']}"}

    db = TestingSessionLocal()
    dec = seed_decision(db, viewer_model_id, action=AIMDAction.CONTINUE_MONITORING)
    db.close()

    # Viewer can access their own model's history
    resp_list = client.get(f"/api/spam-models/{viewer_model_id}/decisions", headers=viewer_headers)
    assert resp_list.status_code == 200

    resp_get = client.get(f"/api/spam-models/{viewer_model_id}/decisions/{dec.id}", headers=viewer_headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == str(dec.id)


# ---------------------------------------------------------------------------
# 8. Complete DecisionLog Field Preservation in API Responses
# ---------------------------------------------------------------------------

def test_complete_decision_log_fields_in_api_response(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    complex_signals = {
        "drifted_features": ["urgency_score", "link_density"],
        "metric_shifts": {"f1_score": -0.06},
    }

    db = TestingSessionLocal()
    dec = seed_decision(
        db,
        model_id,
        action=AIMDAction.DATA_COLLECTION,
        priority=AIMDPriority.HIGH,
        confidence=0.88,
        rationale="Feature distribution shift detected requiring sample collection.",
        explanation="Explainability layer indicates link_density shifted significantly.",
        supporting_signals=complex_signals,
        health_score=71.5,
        health_status="warning",
    )
    db.close()

    resp = client.get(f"/api/spam-models/{model_id}/decisions/{dec.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["id"] == str(dec.id)
    assert body["model_id"] == model_id
    assert body["health_score"] == 71.5
    assert body["health_status"] == "warning"
    assert body["recommended_action"] == AIMDAction.DATA_COLLECTION.value
    assert body["priority"] == AIMDPriority.HIGH.value
    assert body["confidence"] == 0.88
    assert body["rationale"] == "Feature distribution shift detected requiring sample collection."
    assert body["explanation"] == "Explainability layer indicates link_density shifted significantly."
    assert body["supporting_signals"] == complex_signals
    assert body["requires_human_approval"] is True
    assert body["approval_status"] == ApprovalStatus.PENDING.value
    assert "created_at" in body
    assert body["created_at"] is not None


# ---------------------------------------------------------------------------
# 9. Parameter Validation (UUID and Pagination Limits)
# ---------------------------------------------------------------------------

def test_validation_invalid_uuid(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    resp1 = client.get("/api/spam-models/invalid-uuid/decisions", headers=headers)
    assert resp1.status_code == 422

    resp2 = client.get(f"/api/spam-models/{model_id}/decisions/invalid-uuid", headers=headers)
    assert resp2.status_code == 422


def test_validation_pagination_bounds(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    resp_neg_skip = client.get(f"/api/spam-models/{model_id}/decisions?skip=-1", headers=headers)
    assert resp_neg_skip.status_code == 422

    resp_zero_limit = client.get(f"/api/spam-models/{model_id}/decisions?limit=0", headers=headers)
    assert resp_zero_limit.status_code == 422

    resp_high_limit = client.get(f"/api/spam-models/{model_id}/decisions?limit=101", headers=headers)
    assert resp_high_limit.status_code == 422
