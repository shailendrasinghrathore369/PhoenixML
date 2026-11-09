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
        username="approval_eng_user",
        email="approval_eng@example.com",
        full_name="Approval Engineer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="EngineersApprovalModel",
        framework="Scikit-Learn",
        owner_id=user.id,
        status=ModelStatus.ACTIVE,
    )
    db.add(model)
    db.commit()

    resp = client.post("/api/auth/login", data={"username": "approval_eng_user", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = str(user.id)
    model_id = str(model.id)
    db.close()
    return {"user_id": user_id, "token": token, "model_id": model_id}


@pytest.fixture
def test_user_other_engine(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="other_eng_user",
        email="other_eng@example.com",
        full_name="Other Engineer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="OtherEngineersApprovalModel",
        framework="Scikit-Learn",
        owner_id=user.id,
        status=ModelStatus.ACTIVE,
    )
    db.add(model)
    db.commit()

    resp = client.post("/api/auth/login", data={"username": "other_eng_user", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = str(user.id)
    model_id = str(model.id)
    db.close()
    return {"user_id": user_id, "token": token, "model_id": model_id}


@pytest.fixture
def test_user_viewer(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="approval_viewer_user",
        email="approval_viewer@example.com",
        full_name="Approval Viewer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="ViewersApprovalModel",
        framework="PyTorch",
        owner_id=user.id,
        status=ModelStatus.ACTIVE,
    )
    db.add(model)
    db.commit()

    resp = client.post("/api/auth/login", data={"username": "approval_viewer_user", "password": "password123"})
    token = resp.json()["access_token"]
    user_id = str(user.id)
    model_id = str(model.id)
    db.close()
    return {"user_id": user_id, "token": token, "model_id": model_id}


@pytest.fixture
def test_user_admin(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="approval_admin_user",
        email="approval_admin@example.com",
        full_name="Approval Admin",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="AdminsApprovalModel",
        framework="TensorFlow",
        owner_id=user.id,
        status=ModelStatus.ACTIVE,
    )
    db.add(model)
    db.commit()

    resp = client.post("/api/auth/login", data={"username": "approval_admin_user", "password": "password123"})
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
    approval_status=ApprovalStatus.PENDING,
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
        approval_status=approval_status,
    )
    rec = repo.create(dec_in)
    db.expunge(rec)
    return rec


# ---------------------------------------------------------------------------
# 1. Authentication Enforcement (401)
# ---------------------------------------------------------------------------

def test_unauthenticated_request_rejected(client: TestClient):
    model_id = str(uuid.uuid4())
    decision_id = str(uuid.uuid4())
    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": "APPROVED"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 2. Authorization & RBAC Enforcement
# ---------------------------------------------------------------------------

def test_owner_ml_engineer_can_approve(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    dec = seed_decision(db, model_id, approval_status=ApprovalStatus.PENDING)
    db.close()

    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{dec.id}/approval",
        headers=headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(dec.id)
    assert data["approval_status"] == ApprovalStatus.APPROVED.value


def test_owner_ml_engineer_can_reject(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    dec = seed_decision(db, model_id, approval_status=ApprovalStatus.PENDING)
    db.close()

    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{dec.id}/approval",
        headers=headers,
        json={"approval_status": "REJECTED"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(dec.id)
    assert data["approval_status"] == ApprovalStatus.REJECTED.value


def test_unauthorized_ml_engineer_cannot_modify_other_model(client: TestClient, test_user_engine, test_user_other_engine):
    eng1_model_id = test_user_engine["model_id"]
    eng2_headers = {"Authorization": f"Bearer {test_user_other_engine['token']}"}

    db = TestingSessionLocal()
    dec = seed_decision(db, eng1_model_id, approval_status=ApprovalStatus.PENDING)
    db.close()

    resp = client.patch(
        f"/api/spam-models/{eng1_model_id}/decisions/{dec.id}/approval",
        headers=eng2_headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp.status_code == 403
    assert "Not authorized" in resp.json()["detail"]


def test_viewer_cannot_approve_or_reject(client: TestClient, test_user_viewer, test_user_engine):
    viewer_headers = {"Authorization": f"Bearer {test_user_viewer['token']}"}
    viewer_model_id = test_user_viewer["model_id"]
    eng_model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    dec_viewer_model = seed_decision(db, viewer_model_id, approval_status=ApprovalStatus.PENDING)
    dec_eng_model = seed_decision(db, eng_model_id, approval_status=ApprovalStatus.PENDING)
    db.close()

    # Viewer cannot approve own model's decision
    resp1 = client.patch(
        f"/api/spam-models/{viewer_model_id}/decisions/{dec_viewer_model.id}/approval",
        headers=viewer_headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp1.status_code == 403

    # Viewer cannot reject engineer's model's decision
    resp2 = client.patch(
        f"/api/spam-models/{eng_model_id}/decisions/{dec_eng_model.id}/approval",
        headers=viewer_headers,
        json={"approval_status": "REJECTED"},
    )
    assert resp2.status_code == 403


def test_admin_can_approve_and_reject_any_model(client: TestClient, test_user_engine, test_user_admin):
    eng_model_id = test_user_engine["model_id"]
    admin_headers = {"Authorization": f"Bearer {test_user_admin['token']}"}

    db = TestingSessionLocal()
    dec1 = seed_decision(db, eng_model_id, approval_status=ApprovalStatus.PENDING)
    dec2 = seed_decision(db, eng_model_id, approval_status=ApprovalStatus.PENDING)
    db.close()

    # Admin approves
    resp1 = client.patch(
        f"/api/spam-models/{eng_model_id}/decisions/{dec1.id}/approval",
        headers=admin_headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp1.status_code == 200
    assert resp1.json()["approval_status"] == ApprovalStatus.APPROVED.value

    # Admin rejects
    resp2 = client.patch(
        f"/api/spam-models/{eng_model_id}/decisions/{dec2.id}/approval",
        headers=admin_headers,
        json={"approval_status": "REJECTED"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["approval_status"] == ApprovalStatus.REJECTED.value


# ---------------------------------------------------------------------------
# 3. Approval State Transitions & Idempotency
# ---------------------------------------------------------------------------

def test_transition_pending_to_approved(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    dec = seed_decision(db, model_id, approval_status=ApprovalStatus.PENDING)
    db.close()

    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{dec.id}/approval",
        headers=headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp.status_code == 200
    assert resp.json()["approval_status"] == "APPROVED"


def test_transition_pending_to_rejected(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    dec = seed_decision(db, model_id, approval_status=ApprovalStatus.PENDING)
    db.close()

    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{dec.id}/approval",
        headers=headers,
        json={"approval_status": "REJECTED"},
    )
    assert resp.status_code == 200
    assert resp.json()["approval_status"] == "REJECTED"


def test_transition_approved_to_approved_idempotent(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    dec = seed_decision(db, model_id, approval_status=ApprovalStatus.APPROVED)
    db.close()

    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{dec.id}/approval",
        headers=headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp.status_code == 200
    assert resp.json()["approval_status"] == "APPROVED"


def test_transition_rejected_to_rejected_idempotent(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    dec = seed_decision(db, model_id, approval_status=ApprovalStatus.REJECTED)
    db.close()

    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{dec.id}/approval",
        headers=headers,
        json={"approval_status": "REJECTED"},
    )
    assert resp.status_code == 200
    assert resp.json()["approval_status"] == "REJECTED"


def test_transition_approved_to_rejected_forbidden(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    dec = seed_decision(db, model_id, approval_status=ApprovalStatus.APPROVED)
    db.close()

    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{dec.id}/approval",
        headers=headers,
        json={"approval_status": "REJECTED"},
    )
    assert resp.status_code == 400
    assert "Cannot change approval status of a finalized decision" in resp.json()["detail"]


def test_transition_rejected_to_approved_forbidden(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    dec = seed_decision(db, model_id, approval_status=ApprovalStatus.REJECTED)
    db.close()

    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{dec.id}/approval",
        headers=headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp.status_code == 400
    assert "Cannot change approval status of a finalized decision" in resp.json()["detail"]


def test_transition_finalized_to_pending_forbidden(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    dec = seed_decision(db, model_id, approval_status=ApprovalStatus.APPROVED)
    db.close()

    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{dec.id}/approval",
        headers=headers,
        json={"approval_status": "PENDING"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 4. Model Boundary Isolation & 404 Handling
# ---------------------------------------------------------------------------

def test_cross_model_isolation_returns_404(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_a_id = test_user_engine["model_id"]

    db = TestingSessionLocal()
    model_b = RegisteredModel(
        id=uuid.uuid4(),
        name="EngineersSecondApprovalModel",
        framework="Scikit-Learn",
        owner_id=uuid.UUID(test_user_engine["user_id"]),
        status=ModelStatus.ACTIVE,
    )
    db.add(model_b)
    db.commit()

    dec_b = seed_decision(db, model_b.id, approval_status=ApprovalStatus.PENDING)
    db.close()

    # Attempting to approve dec_b using model_a_id must return 404
    resp = client.patch(
        f"/api/spam-models/{model_a_id}/decisions/{dec_b.id}/approval",
        headers=headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp.status_code == 404
    assert "Decision not found" in resp.json()["detail"]


def test_nonexistent_model_returns_404(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    random_model = str(uuid.uuid4())
    random_decision = str(uuid.uuid4())

    resp = client.patch(
        f"/api/spam-models/{random_model}/decisions/{random_decision}/approval",
        headers=headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp.status_code == 404
    assert "Model not found" in resp.json()["detail"]


def test_nonexistent_decision_returns_404(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]
    random_decision = str(uuid.uuid4())

    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{random_decision}/approval",
        headers=headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp.status_code == 404
    assert "Decision not found" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 5. Parameter & Payload Validation (422)
# ---------------------------------------------------------------------------

def test_validation_invalid_uuids(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]
    random_decision = str(uuid.uuid4())

    resp1 = client.patch(
        f"/api/spam-models/not-a-uuid/decisions/{random_decision}/approval",
        headers=headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp1.status_code == 422

    resp2 = client.patch(
        f"/api/spam-models/{model_id}/decisions/not-a-uuid/approval",
        headers=headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp2.status_code == 422


def test_validation_invalid_and_missing_payload(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]
    decision_id = str(uuid.uuid4())

    # Invalid enum
    resp1 = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        headers=headers,
        json={"approval_status": "NOT_A_VALID_STATUS"},
    )
    assert resp1.status_code == 422

    # Missing approval_status
    resp2 = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        headers=headers,
        json={},
    )
    assert resp2.status_code == 422

    # Extra fields forbidden (model_config extra='forbid')
    resp3 = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        headers=headers,
        json={"approval_status": "APPROVED", "recommended_action": "RETRAIN"},
    )
    assert resp3.status_code == 422


# ---------------------------------------------------------------------------
# 6. Data Integrity Preservation
# ---------------------------------------------------------------------------

def test_data_integrity_preserved_after_approval(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine["model_id"]

    complex_signals = {
        "drift_scores": {"feature_a": 0.45, "feature_b": 0.82},
        "critical_threshold": 0.5,
    }
    fixed_time = datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc)

    db = TestingSessionLocal()
    dec = seed_decision(
        db,
        model_id,
        action=AIMDAction.RETRAIN,
        priority=AIMDPriority.HIGH,
        confidence=0.87,
        rationale="Severe concept drift observed in incoming feature distribution.",
        explanation="Feature distribution shifted beyond allowable tolerance.",
        supporting_signals=complex_signals,
        created_at=fixed_time,
        health_score=62.4,
        health_status="warning",
        approval_status=ApprovalStatus.PENDING,
    )
    db.close()

    # Execute Approval
    resp = client.patch(
        f"/api/spam-models/{model_id}/decisions/{dec.id}/approval",
        headers=headers,
        json={"approval_status": "APPROVED"},
    )
    assert resp.status_code == 200
    body = resp.json()

    # Verify only approval_status changed while all other fields remained exactly identical
    assert body["id"] == str(dec.id)
    assert body["model_id"] == model_id
    assert body["approval_status"] == ApprovalStatus.APPROVED.value
    assert body["recommended_action"] == AIMDAction.RETRAIN.value
    assert body["priority"] == AIMDPriority.HIGH.value
    assert body["confidence"] == 0.87
    assert body["rationale"] == "Severe concept drift observed in incoming feature distribution."
    assert body["explanation"] == "Feature distribution shifted beyond allowable tolerance."
    assert body["supporting_signals"] == complex_signals
    assert body["health_score"] == 62.4
    assert body["health_status"] == "warning"
    assert body["requires_human_approval"] is True
    assert body["created_at"].startswith("2026-09-09T12:00:00")
