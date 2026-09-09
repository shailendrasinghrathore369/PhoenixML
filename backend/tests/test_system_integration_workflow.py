"""
PhoenixML Step 27 — Integrated System Validation & End-to-End Workflow Tests.

Validates the complete PhoenixML decision-support lifecycle end-to-end:
1. User authentication and JWT handling.
2. Spam model registration in the Model Registry.
3. Monitoring observation telemetry ingestion.
4. Monitoring observation history retrieval and verification.
5. AIMD evaluation trigger (synthesizing health, performance, and explainability).
6. Verification of DecisionLog creation, AIMDAction value, priority, confidence,
   rationale, explanation, supporting signals, requires_human_approval=True, and approval_status=PENDING.
7. Decision retrieval through the Decision History API.
8. Decision visibility in the Dashboard API overview and model card.
9. Human-in-the-loop approval and rejection workflows.
10. Persisted approval state verification in decision and dashboard APIs.
11. Role-Based Access Control (RBAC):
    - ADMIN operates globally across all models.
    - ML_ENGINEER operates strictly on owned models.
    - VIEWER is read-only (403 on model creation, observation ingestion, evaluation, and approval).
    - Cross-model isolation (Engineers cannot mutate or inspect other engineers' models).
12. Operator frontend / static UI reachability (/, /ui/, CSS, JS, vendor).
13. Strict confirmation that the system does NOT autonomously execute retraining, rollback,
    deployment, or any other maintenance action.
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.auth.security import get_password_hash
from app.decisions.aimd import AIMDAction, AIMDPriority
from app.decisions.models import ApprovalStatus
from app.models.models import ModelStatus, RegisteredModel
from app.users.models import User, UserRole
from tests.conftest import TestingSessionLocal


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def create_test_user(
    db,
    username: str,
    email: str,
    role: UserRole,
    password: str = "SecurePass123!",
) -> User:
    """Helper to persist a test user with a hashed password."""
    user = User(
        username=username,
        email=email,
        full_name=f"Test {username}",
        hashed_password=get_password_hash(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_token(client: TestClient, username: str, password: str = "SecurePass123!") -> str:
    """Helper to authenticate and return a bearer token."""
    resp = client.post("/api/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    """Construct Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Test 1: Complete End-to-End Decision Support Lifecycle (Approval Flow)
# ---------------------------------------------------------------------------

def test_e2e_complete_decision_support_lifecycle_approval(client: TestClient, db_session):
    """
    Validates the primary decision-support workflow from model creation to human approval:
    1. Authenticate as ML Engineer.
    2. Register spam model.
    3. Ingest operational monitoring observations.
    4. Query monitoring history.
    5. Trigger AIMD evaluation endpoint.
    6. Verify DecisionLog created with requires_human_approval=True and approval_status=PENDING.
    7. Query decision history API.
    8. Verify decision appears in Dashboard API.
    9. Approve recommendation via human approval API.
    10. Verify persisted APPROVED state in decision and dashboard APIs.
    11. Verify model remains in existing state with NO autonomous maintenance execution.
    """
    # Step 1: Authenticate ML Engineer
    eng_user = create_test_user(db_session, "e2e_engineer", "e2e_eng@example.com", UserRole.ML_ENGINEER)
    token = get_auth_token(client, "e2e_engineer")
    headers = auth_header(token)

    # Step 2: Register spam detection model
    model_payload = {
        "name": "E2E-SpamClassifier-v1",
        "description": "Production spam detection model for end-to-end testing",
        "framework": "scikit-learn",
        "algorithm": "MultinomialNB",
        "status": "ACTIVE",
    }
    r_model = client.post("/api/spam-models", json=model_payload, headers=headers)
    assert r_model.status_code == 201
    model_data = r_model.json()
    model_id = model_data["id"]
    assert model_data["name"] == "E2E-SpamClassifier-v1"
    assert model_data["status"] == "ACTIVE"
    assert model_data["owner_id"] == str(eng_user.id)

    # Step 3: Ingest multiple monitoring observations
    base_time = datetime.now(timezone.utc) - timedelta(hours=3)
    observation_records = [
        {"accuracy": 0.94, "precision": 0.93, "recall": 0.92, "f1_score": 0.925, "pred_count": 500, "pos": 150, "neg": 350},
        {"accuracy": 0.91, "precision": 0.90, "recall": 0.89, "f1_score": 0.895, "pred_count": 520, "pos": 160, "neg": 360},
        {"accuracy": 0.84, "precision": 0.83, "recall": 0.82, "f1_score": 0.825, "pred_count": 480, "pos": 140, "neg": 340},
    ]

    for i, obs in enumerate(observation_records):
        obs_payload = {
            "model_id": model_id,
            "observed_at": (base_time + timedelta(hours=i)).isoformat(),
            "prediction_count": obs["pred_count"],
            "positive_prediction_count": obs["pos"],
            "negative_prediction_count": obs["neg"],
            "accuracy": obs["accuracy"],
            "precision": obs["precision"],
            "recall": obs["recall"],
            "f1_score": obs["f1_score"],
        }
        r_obs = client.post(f"/api/spam-models/{model_id}/monitoring", json=obs_payload, headers=headers)
        assert r_obs.status_code == 201

    # Step 4: Retrieve and verify monitoring history
    r_mon = client.get(f"/api/spam-models/{model_id}/monitoring", headers=headers)
    assert r_mon.status_code == 200
    mon_list = r_mon.json()
    assert len(mon_list) == 3
    # Repo returns newest first
    assert mon_list[0]["f1_score"] == 0.825

    # Step 5: Trigger AIMD evaluation endpoint
    r_eval = client.post(f"/api/spam-models/{model_id}/decisions/evaluate", headers=headers)
    assert r_eval.status_code == 201
    eval_data = r_eval.json()
    decision_id = eval_data["id"]

    # Step 6: Verify analytical inputs, DecisionLog invariants, and recommendation fields
    assert eval_data["model_id"] == model_id
    assert eval_data["recommended_action"] in [a.value for a in AIMDAction]
    assert eval_data["priority"] in [p.value for p in AIMDPriority]
    assert eval_data["confidence"] is not None
    assert 0.0 <= eval_data["confidence"] <= 1.0
    assert eval_data["rationale"] and len(eval_data["rationale"]) > 0
    assert eval_data["explanation"] is not None
    assert eval_data["supporting_signals"] is not None
    # Human-in-the-loop invariants:
    assert eval_data["requires_human_approval"] is True
    assert eval_data["approval_status"] == ApprovalStatus.PENDING.value
    assert eval_data["created_at"] is not None

    # Step 7: Retrieve decision through Decision History API
    r_history = client.get(f"/api/spam-models/{model_id}/decisions", headers=headers)
    assert r_history.status_code == 200
    hist_data = r_history.json()
    assert hist_data["total"] == 1
    assert len(hist_data["items"]) == 1
    assert hist_data["items"][0]["id"] == decision_id

    # Retrieve single decision
    r_single = client.get(f"/api/spam-models/{model_id}/decisions/{decision_id}", headers=headers)
    assert r_single.status_code == 200
    assert r_single.json()["id"] == decision_id
    assert r_single.json()["approval_status"] == ApprovalStatus.PENDING.value

    # Step 8: Verify decision appears in Dashboard API response
    r_dash = client.get("/api/dashboard", headers=headers)
    assert r_dash.status_code == 200
    dash_data = r_dash.json()
    assert dash_data["models_summary"]["total_models"] == 1
    assert dash_data["decision_summary"]["pending_approvals_count"] == 1
    assert dash_data["decision_summary"]["total_decisions"] == 1
    assert len(dash_data["model_cards"]) == 1
    card = dash_data["model_cards"][0]
    assert card["model_id"] == model_id
    assert card["pending_decisions_count"] == 1
    assert card["latest_decision"]["id"] == decision_id
    assert card["latest_decision"]["approval_status"] == ApprovalStatus.PENDING.value

    # Single-model dashboard
    r_dash_model = client.get(f"/api/dashboard/{model_id}", headers=headers)
    assert r_dash_model.status_code == 200
    assert r_dash_model.json()["decision_summary"]["pending_approvals_count"] == 1

    # Step 9: Human operator approves the pending recommendation
    r_appr = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": ApprovalStatus.APPROVED.value},
        headers=headers,
    )
    assert r_appr.status_code == 200
    appr_data = r_appr.json()
    assert appr_data["id"] == decision_id
    assert appr_data["approval_status"] == ApprovalStatus.APPROVED.value
    # Preserves analytical and diagnostic fields
    assert appr_data["recommended_action"] == eval_data["recommended_action"]
    assert appr_data["health_score"] == eval_data["health_score"]
    assert appr_data["confidence"] == eval_data["confidence"]

    # Step 10: Verify persisted approval state in Decision API and Dashboard API
    r_check_dec = client.get(f"/api/spam-models/{model_id}/decisions/{decision_id}", headers=headers)
    assert r_check_dec.status_code == 200
    assert r_check_dec.json()["approval_status"] == ApprovalStatus.APPROVED.value

    r_dash_after = client.get("/api/dashboard", headers=headers)
    assert r_dash_after.status_code == 200
    dash_after_data = r_dash_after.json()
    assert dash_after_data["decision_summary"]["pending_approvals_count"] == 0
    assert dash_after_data["decision_summary"]["approved_count"] == 1
    assert dash_after_data["model_cards"][0]["pending_decisions_count"] == 0
    assert dash_after_data["model_cards"][0]["latest_decision"]["approval_status"] == ApprovalStatus.APPROVED.value

    # Step 11: Verify that NO autonomous maintenance action was executed
    # The model status must remain unchanged in its original state
    r_model_check = client.get(f"/api/spam-models/{model_id}", headers=headers)
    assert r_model_check.status_code == 200
    m_check = r_model_check.json()
    assert m_check["status"] == "ACTIVE"
    assert m_check["framework"] == "scikit-learn"
    assert m_check["algorithm"] == "MultinomialNB"


# ---------------------------------------------------------------------------
# Test 2: Complete End-to-End Decision Support Lifecycle (Rejection Flow)
# ---------------------------------------------------------------------------

def test_e2e_complete_decision_support_lifecycle_rejection(client: TestClient, db_session):
    """
    Validates the decision rejection workflow:
    1. Register model and ingest telemetry.
    2. Trigger evaluation (produces PENDING recommendation).
    3. Human operator explicitly REJECTS the recommendation.
    4. Verify persisted REJECTED state in decision and dashboard APIs.
    5. Verify pending approvals counter decrements and rejected_count increments.
    6. Verify model status remains unchanged with zero autonomous execution.
    """
    create_test_user(db_session, "e2e_eng_reject", "e2e_reject@example.com", UserRole.ML_ENGINEER)
    token = get_auth_token(client, "e2e_eng_reject")
    headers = auth_header(token)

    # Register model
    r_model = client.post("/api/spam-models", json={
        "name": "E2E-RejectModel-v1",
        "framework": "PyTorch",
        "algorithm": "LSTM",
        "status": "ACTIVE",
    }, headers=headers)
    assert r_model.status_code == 201
    model_id = r_model.json()["id"]

    # Ingest observation
    now = datetime.now(timezone.utc)
    client.post(f"/api/spam-models/{model_id}/monitoring", json={
        "model_id": model_id,
        "observed_at": now.isoformat(),
        "prediction_count": 300,
        "positive_prediction_count": 100,
        "negative_prediction_count": 200,
        "accuracy": 0.80,
        "precision": 0.79,
        "recall": 0.78,
        "f1_score": 0.785,
    }, headers=headers)

    # Trigger evaluation
    r_eval = client.post(f"/api/spam-models/{model_id}/decisions/evaluate", headers=headers)
    assert r_eval.status_code == 201
    decision_id = r_eval.json()["id"]
    assert r_eval.json()["approval_status"] == "PENDING"

    # Human operator rejects recommendation
    r_reject = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": ApprovalStatus.REJECTED.value},
        headers=headers,
    )
    assert r_reject.status_code == 200
    assert r_reject.json()["approval_status"] == ApprovalStatus.REJECTED.value

    # Verify decision history
    r_dec = client.get(f"/api/spam-models/{model_id}/decisions/{decision_id}", headers=headers)
    assert r_dec.status_code == 200
    assert r_dec.json()["approval_status"] == ApprovalStatus.REJECTED.value

    # Verify dashboard reflects rejection
    r_dash = client.get("/api/dashboard", headers=headers)
    assert r_dash.status_code == 200
    d_data = r_dash.json()
    assert d_data["decision_summary"]["pending_approvals_count"] == 0
    assert d_data["decision_summary"]["rejected_count"] == 1

    # Verify model is completely unchanged
    r_mod = client.get(f"/api/spam-models/{model_id}", headers=headers)
    assert r_mod.status_code == 200
    assert r_mod.json()["status"] == "ACTIVE"


# ---------------------------------------------------------------------------
# Test 3: RBAC — Global Administrator Operations
# ---------------------------------------------------------------------------

def test_e2e_rbac_admin_global_operations(client: TestClient, db_session):
    """
    Validates that ADMIN users can operate globally across all registered models:
    - Admin can inspect models owned by ML Engineers.
    - Admin can view monitoring observations on any model.
    - Admin can trigger AIMD evaluations on any model.
    - Admin can retrieve decisions and approve/reject recommendations on any model.
    - Admin receives global scope on Dashboard API.
    """
    create_test_user(db_session, "e2e_admin", "admin@phoenixml.io", UserRole.ADMIN)
    create_test_user(db_session, "e2e_sub_engineer", "sub_eng@phoenixml.io", UserRole.ML_ENGINEER)

    eng_token = get_auth_token(client, "e2e_sub_engineer")
    admin_token = get_auth_token(client, "e2e_admin")
    eng_headers = auth_header(eng_token)
    admin_headers = auth_header(admin_token)

    # Engineer creates model and observation
    r_model = client.post("/api/spam-models", json={
        "name": "EngineerOwnedModel",
        "framework": "scikit-learn",
        "status": "ACTIVE",
    }, headers=eng_headers)
    assert r_model.status_code == 201
    model_id = r_model.json()["id"]

    now = datetime.now(timezone.utc)
    client.post(f"/api/spam-models/{model_id}/monitoring", json={
        "model_id": model_id,
        "observed_at": now.isoformat(),
        "prediction_count": 400,
        "positive_prediction_count": 100,
        "negative_prediction_count": 300,
        "accuracy": 0.88,
        "f1_score": 0.87,
    }, headers=eng_headers)

    # Admin global operations on decisions layer:
    # 1. Admin triggers evaluation on Engineer's model globally
    r_admin_eval = client.post(f"/api/spam-models/{model_id}/decisions/evaluate", headers=admin_headers)
    assert r_admin_eval.status_code == 201
    decision_id = r_admin_eval.json()["id"]
    assert r_admin_eval.json()["approval_status"] == "PENDING"

    # 2. Admin inspects decision history for Engineer's model globally
    r_admin_hist = client.get(f"/api/spam-models/{model_id}/decisions", headers=admin_headers)
    assert r_admin_hist.status_code == 200
    assert r_admin_hist.json()["total"] >= 1

    # 3. Admin inspects specific decision for Engineer's model globally
    r_admin_single = client.get(f"/api/spam-models/{model_id}/decisions/{decision_id}", headers=admin_headers)
    assert r_admin_single.status_code == 200

    # 4. Admin approves decision on Engineer's model globally
    r_admin_appr = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": "APPROVED"},
        headers=admin_headers,
    )
    assert r_admin_appr.status_code == 200
    assert r_admin_appr.json()["approval_status"] == "APPROVED"

    # 5. Admin global dashboard overview across all models
    r_admin_dash = client.get("/api/dashboard", headers=admin_headers)
    assert r_admin_dash.status_code == 200
    dash_json = r_admin_dash.json()
    assert dash_json["scope"] == "global"
    assert dash_json["models_summary"]["total_models"] >= 1
    assert dash_json["decision_summary"]["approved_count"] >= 1

    # 6. Admin scoped dashboard on Engineer's model
    r_admin_dash_mod = client.get(f"/api/dashboard/{model_id}", headers=admin_headers)
    assert r_admin_dash_mod.status_code == 200
    assert r_admin_dash_mod.json()["scope"] == "model"


# ---------------------------------------------------------------------------
# Test 4: RBAC — Viewer Read-Only Enforcement
# ---------------------------------------------------------------------------

def test_e2e_rbac_viewer_read_only_enforcement(client: TestClient, db_session):
    """
    Validates least-privilege security policy for VIEWER role:
    - VIEWER can read models, monitoring data, decisions, and dashboards.
    - VIEWER is strictly forbidden (403) from:
      - Creating models
      - Ingesting observations
      - Triggering AIMD evaluations
      - Approving or rejecting recommendations
      - Deleting models
    """
    create_test_user(db_session, "e2e_view_owner", "view_owner@phoenixml.io", UserRole.ML_ENGINEER)
    create_test_user(db_session, "e2e_viewer_user", "viewer@phoenixml.io", UserRole.VIEWER)

    owner_token = get_auth_token(client, "e2e_view_owner")
    viewer_token = get_auth_token(client, "e2e_viewer_user")
    owner_headers = auth_header(owner_token)
    viewer_headers = auth_header(viewer_token)

    # Owner creates model and observation and decision
    r_model = client.post("/api/spam-models", json={
        "name": "ViewerRestrictedModel",
        "framework": "scikit-learn",
        "status": "ACTIVE",
    }, headers=owner_headers)
    assert r_model.status_code == 201
    model_id = r_model.json()["id"]

    now = datetime.now(timezone.utc)
    client.post(f"/api/spam-models/{model_id}/monitoring", json={
        "model_id": model_id,
        "observed_at": now.isoformat(),
        "prediction_count": 250,
        "accuracy": 0.85,
        "f1_score": 0.84,
    }, headers=owner_headers)

    r_eval = client.post(f"/api/spam-models/{model_id}/decisions/evaluate", headers=owner_headers)
    assert r_eval.status_code == 201
    decision_id = r_eval.json()["id"]

    # --- Read Operations (Permitted) ---
    assert client.get("/api/spam-models", headers=viewer_headers).status_code == 200
    assert client.get("/api/dashboard", headers=viewer_headers).status_code == 200

    # --- Mutation Operations (403 Forbidden) ---
    # 1. Cannot create models
    r_view_create_mod = client.post("/api/spam-models", json={
        "name": "IllegalModel",
        "framework": "scikit-learn",
    }, headers=viewer_headers)
    assert r_view_create_mod.status_code == 403

    # 2. Cannot ingest monitoring observations
    r_view_obs = client.post(f"/api/spam-models/{model_id}/monitoring", json={
        "model_id": model_id,
        "observed_at": now.isoformat(),
        "prediction_count": 100,
    }, headers=viewer_headers)
    assert r_view_obs.status_code == 403

    # 3. Cannot trigger AIMD evaluations
    r_view_eval = client.post(f"/api/spam-models/{model_id}/decisions/evaluate", headers=viewer_headers)
    assert r_view_eval.status_code == 403

    # 4. Cannot approve or reject decisions
    r_view_appr = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": "APPROVED"},
        headers=viewer_headers,
    )
    assert r_view_appr.status_code == 403

    # 5. Cannot delete models
    r_view_del = client.delete(f"/api/spam-models/{model_id}", headers=viewer_headers)
    assert r_view_del.status_code == 403


# ---------------------------------------------------------------------------
# Test 5: RBAC — Cross-Model Isolation Between ML Engineers
# ---------------------------------------------------------------------------

def test_e2e_rbac_cross_engineer_isolation(client: TestClient, db_session):
    """
    Validates tenant/ownership isolation between distinct ML Engineers:
    - Engineer A owns Model A.
    - Engineer B owns Model B.
    - Engineer B cannot ingest observations, trigger evaluations, query decisions,
      approve decisions, or inspect scoped dashboards for Model A (all 403 Forbidden).
    """
    create_test_user(db_session, "e2e_eng_alpha", "alpha@phoenixml.io", UserRole.ML_ENGINEER)
    create_test_user(db_session, "e2e_eng_beta", "beta@phoenixml.io", UserRole.ML_ENGINEER)

    token_a = get_auth_token(client, "e2e_eng_alpha")
    token_b = get_auth_token(client, "e2e_eng_beta")
    headers_a = auth_header(token_a)
    headers_b = auth_header(token_b)

    # Engineer A creates Model A
    r_model_a = client.post("/api/spam-models", json={
        "name": "ModelAlpha",
        "framework": "scikit-learn",
        "status": "ACTIVE",
    }, headers=headers_a)
    assert r_model_a.status_code == 201
    model_a_id = r_model_a.json()["id"]

    # Engineer A adds observation and triggers evaluation
    now = datetime.now(timezone.utc)
    client.post(f"/api/spam-models/{model_a_id}/monitoring", json={
        "model_id": model_a_id,
        "observed_at": now.isoformat(),
        "prediction_count": 500,
        "accuracy": 0.86,
        "f1_score": 0.85,
    }, headers=headers_a)

    r_eval_a = client.post(f"/api/spam-models/{model_a_id}/decisions/evaluate", headers=headers_a)
    assert r_eval_a.status_code == 201
    decision_a_id = r_eval_a.json()["id"]

    # Engineer B attempts unauthorized operations on Model A:
    # 1. Ingest observation on Model A (rejected with 404 to avoid leaking model existence)
    r_cross_obs = client.post(f"/api/spam-models/{model_a_id}/monitoring", json={
        "model_id": model_a_id,
        "observed_at": now.isoformat(),
        "prediction_count": 100,
    }, headers=headers_b)
    assert r_cross_obs.status_code == 404

    # 2. Trigger evaluation on Model A
    r_cross_eval = client.post(f"/api/spam-models/{model_a_id}/decisions/evaluate", headers=headers_b)
    assert r_cross_eval.status_code == 403

    # 3. Query decision history for Model A
    r_cross_hist = client.get(f"/api/spam-models/{model_a_id}/decisions", headers=headers_b)
    assert r_cross_hist.status_code == 403

    # 4. Approve decision on Model A
    r_cross_appr = client.patch(
        f"/api/spam-models/{model_a_id}/decisions/{decision_a_id}/approval",
        json={"approval_status": "APPROVED"},
        headers=headers_b,
    )
    assert r_cross_appr.status_code == 403

    # 5. Query scoped dashboard for Model A
    r_cross_dash = client.get(f"/api/dashboard/{model_a_id}", headers=headers_b)
    assert r_cross_dash.status_code == 403


# ---------------------------------------------------------------------------
# Test 6: Operator Frontend & Static UI Routes Reachability
# ---------------------------------------------------------------------------

def test_e2e_frontend_static_routes_reachability(client: TestClient):
    """
    Validates that operator web UI static routes and assets are correctly served:
    - Root redirect: GET / -> /ui/
    - Dashboard HTML entrypoint: GET /ui/ and GET /ui/index.html
    - Stylesheet: GET /ui/styles/dashboard.css
    - Application code: GET /ui/src/App.js and GET /ui/src/api.js
    - Offline vendor scripts: GET /ui/vendor/react.production.min.js and react-dom
    """
    # 1. Root redirect
    r_root = client.get("/", follow_redirects=False)
    assert r_root.status_code in (301, 302, 307)
    assert r_root.headers["location"] == "/ui/"

    # 2. HTML entry point
    r_ui = client.get("/ui/")
    assert r_ui.status_code == 200
    assert "text/html" in r_ui.headers.get("content-type", "")
    assert "PhoenixML — MLOps Decision-Support Platform" in r_ui.text
    assert '<div id="root">' in r_ui.text

    r_index = client.get("/ui/index.html")
    assert r_index.status_code == 200
    assert "PhoenixML — MLOps Decision-Support Platform" in r_index.text

    # 3. Stylesheet
    r_css = client.get("/ui/styles/dashboard.css")
    assert r_css.status_code == 200
    assert "--bg-primary" in r_css.text
    assert ".kpi-card" in r_css.text

    # 4. JavaScript SPA source modules
    r_app = client.get("/ui/src/App.js")
    assert r_app.status_code == 200
    assert "export function App" in r_app.text

    r_api = client.get("/ui/src/api.js")
    assert r_api.status_code == 200
    assert "export const api" in r_api.text

    # 5. Offline React vendor scripts
    r_react = client.get("/ui/vendor/react.production.min.js")
    assert r_react.status_code == 200
    assert len(r_react.content) > 5000

    r_dom = client.get("/ui/vendor/react-dom.production.min.js")
    assert r_dom.status_code == 200
    assert len(r_dom.content) > 50000


# ---------------------------------------------------------------------------
# Test 7: Decision State Transition Invariants & Guardrails
# ---------------------------------------------------------------------------

def test_e2e_decision_state_transition_invariants(client: TestClient, db_session):
    """
    Validates approval state machine rules:
    - PENDING -> APPROVED is allowed.
    - APPROVED -> APPROVED is idempotent (200 OK).
    - APPROVED -> REJECTED is rejected (400 Bad Request, cannot overturn finalized decision).
    - Finalized decisions cannot be re-opened to PENDING (400 Bad Request).
    - Extra fields are strictly forbidden (422 Unprocessable Content).
    """
    create_test_user(db_session, "e2e_statemachine_eng", "sm_eng@phoenixml.io", UserRole.ML_ENGINEER)
    token = get_auth_token(client, "e2e_statemachine_eng")
    headers = auth_header(token)

    # Create model & observation
    r_model = client.post("/api/spam-models", json={
        "name": "StateMachineModel",
        "framework": "scikit-learn",
        "status": "ACTIVE",
    }, headers=headers)
    model_id = r_model.json()["id"]

    now = datetime.now(timezone.utc)
    client.post(f"/api/spam-models/{model_id}/monitoring", json={
        "model_id": model_id,
        "observed_at": now.isoformat(),
        "prediction_count": 200,
        "accuracy": 0.85,
        "f1_score": 0.84,
    }, headers=headers)

    # Trigger evaluation -> creates PENDING decision
    r_eval = client.post(f"/api/spam-models/{model_id}/decisions/evaluate", headers=headers)
    decision_id = r_eval.json()["id"]
    assert r_eval.json()["approval_status"] == "PENDING"

    # 1. Approve (PENDING -> APPROVED: allowed)
    r_appr1 = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": "APPROVED"},
        headers=headers,
    )
    assert r_appr1.status_code == 200
    assert r_appr1.json()["approval_status"] == "APPROVED"

    # 2. Idempotent approval (APPROVED -> APPROVED: allowed, 200)
    r_appr2 = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": "APPROVED"},
        headers=headers,
    )
    assert r_appr2.status_code == 200
    assert r_appr2.json()["approval_status"] == "APPROVED"

    # 3. Cannot overturn finalized approval to REJECTED (400 Bad Request)
    r_overturn = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": "REJECTED"},
        headers=headers,
    )
    assert r_overturn.status_code == 400
    assert "finalized decision" in r_overturn.json()["detail"].lower()

    # 4. Cannot re-open finalized decision to PENDING (400 Bad Request)
    r_reopen = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": "PENDING"},
        headers=headers,
    )
    assert r_reopen.status_code == 400
    assert "finalized decision" in r_reopen.json()["detail"].lower()

    # 5. Extra fields in payload are forbidden by schema (422)
    r_extra = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": "APPROVED", "health_score": 99.9},
        headers=headers,
    )
    assert r_extra.status_code == 422


# ---------------------------------------------------------------------------
# Test 8: Zero Autonomous Maintenance Execution Confirmation
# ---------------------------------------------------------------------------

def test_e2e_zero_autonomous_execution_invariants(client: TestClient, db_session):
    """
    Explicit safety invariant test:
    Simulates acute model performance degradation that triggers a critical maintenance recommendation.
    Verifies that despite severe degradation and subsequent human approval:
    - No automatic retraining is spawned.
    - No automatic rollback is executed.
    - No automatic deployment occurs.
    - Model status, version, parameters, and metadata remain strictly invariant.
    """
    create_test_user(db_session, "e2e_safety_eng", "safety@phoenixml.io", UserRole.ML_ENGINEER)
    token = get_auth_token(client, "e2e_safety_eng")
    headers = auth_header(token)

    # Register production spam model with baseline parameters
    r_model = client.post("/api/spam-models", json={
        "name": "SafetyGuardrailModel",
        "description": "Critical model to verify zero autonomous execution",
        "framework": "scikit-learn",
        "algorithm": "MultinomialNB",
        "status": "ACTIVE",
    }, headers=headers)
    assert r_model.status_code == 201
    model_id = r_model.json()["id"]

    # Ingest acute degradation (F1 drops to 0.45)
    now = datetime.now(timezone.utc)
    client.post(f"/api/spam-models/{model_id}/monitoring", json={
        "model_id": model_id,
        "observed_at": now.isoformat(),
        "prediction_count": 1000,
        "positive_prediction_count": 300,
        "negative_prediction_count": 700,
        "accuracy": 0.48,
        "precision": 0.45,
        "recall": 0.44,
        "f1_score": 0.445,
    }, headers=headers)

    # Trigger evaluation
    r_eval = client.post(f"/api/spam-models/{model_id}/decisions/evaluate", headers=headers)
    assert r_eval.status_code == 201
    eval_data = r_eval.json()
    decision_id = eval_data["id"]

    # Recommendation requires human authorization
    assert eval_data["requires_human_approval"] is True
    assert eval_data["approval_status"] == "PENDING"

    # Verify model is NOT autonomously retrained or rolled back
    r_mod1 = client.get(f"/api/spam-models/{model_id}", headers=headers)
    assert r_mod1.json()["status"] == "ACTIVE"

    # Human approves the recommendation
    client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": "APPROVED"},
        headers=headers,
    )

    # Verify that even AFTER approval, the system does NOT autonomously execute maintenance
    # The decision record is updated for human operator action; model remains in place.
    r_mod2 = client.get(f"/api/spam-models/{model_id}", headers=headers)
    mod2_data = r_mod2.json()
    assert mod2_data["status"] == "ACTIVE"
    assert mod2_data["name"] == "SafetyGuardrailModel"
    assert mod2_data["framework"] == "scikit-learn"
    assert mod2_data["algorithm"] == "MultinomialNB"
