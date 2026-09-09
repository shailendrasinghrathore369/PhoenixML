"""
Tests for PhoenixML Operator Dashboard UI Mounting, Static Assets, and End-to-End Workflow.
Covers Step 26: Operator Dashboard UI capability.
"""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.auth.security import get_password_hash
from app.models.models import ModelStatus, RegisteredModel
from app.users.models import User, UserRole


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ui_test_users(db_session, client: TestClient):
    """Create test users for ADMIN, ML_ENGINEER, and VIEWER roles."""
    admin = User(
        username="ui_admin",
        email="ui_admin@phoenixml.io",
        full_name="UI Admin User",
        hashed_password=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    engineer = User(
        username="ui_engineer",
        email="ui_engineer@phoenixml.io",
        full_name="UI Engineer User",
        hashed_password=get_password_hash("EngineerPass123!"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    viewer = User(
        username="ui_viewer",
        email="ui_viewer@phoenixml.io",
        full_name="UI Viewer User",
        hashed_password=get_password_hash("ViewerPass123!"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db_session.add_all([admin, engineer, viewer])
    db_session.commit()

    # Login tokens
    resp_admin = client.post("/api/auth/login", data={"username": "ui_admin", "password": "AdminPass123!"})
    token_admin = resp_admin.json()["access_token"]

    resp_eng = client.post("/api/auth/login", data={"username": "ui_engineer", "password": "EngineerPass123!"})
    token_eng = resp_eng.json()["access_token"]

    resp_view = client.post("/api/auth/login", data={"username": "ui_viewer", "password": "ViewerPass123!"})
    token_view = resp_view.json()["access_token"]

    return {
        "admin": {"user": admin, "token": token_admin},
        "engineer": {"user": engineer, "token": token_eng},
        "viewer": {"user": viewer, "token": token_view},
    }


# ---------------------------------------------------------------------------
# Tests: Static UI Mounting & Serving
# ---------------------------------------------------------------------------

def test_root_redirects_to_ui(client: TestClient):
    """GET / should redirect to /ui/ where operator frontend is mounted."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307)
    assert response.headers["location"] == "/ui/"


def test_ui_index_served(client: TestClient):
    """GET /ui/ serves the HTML dashboard entry point."""
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "PhoenixML — MLOps Decision-Support Platform" in response.text
    assert '<div id="root">' in response.text
    assert "styles/dashboard.css" in response.text
    assert "src/App.js" in response.text


def test_ui_index_html_direct(client: TestClient):
    """GET /ui/index.html serves index.html directly."""
    response = client.get("/ui/index.html")
    assert response.status_code == 200
    assert "PhoenixML — MLOps Decision-Support Platform" in response.text


def test_ui_static_css_served(client: TestClient):
    """GET /ui/styles/dashboard.css returns the operator stylesheet."""
    response = client.get("/ui/styles/dashboard.css")
    assert response.status_code == 200
    assert "--bg-primary" in response.text
    assert ".kpi-card" in response.text
    assert ".hitl-banner" in response.text


def test_ui_static_js_app_served(client: TestClient):
    """GET /ui/src/App.js returns the React application module."""
    response = client.get("/ui/src/App.js")
    assert response.status_code == 200
    assert "export function App" in response.text
    assert "DecisionReviewBox" in response.text
    assert "KPIGrid" in response.text


def test_ui_static_js_api_served(client: TestClient):
    """GET /ui/src/api.js returns the API client module."""
    response = client.get("/ui/src/api.js")
    assert response.status_code == 200
    assert "export const api" in response.text
    assert "getDashboardOverview" in response.text
    assert "updateApprovalStatus" in response.text


def test_ui_vendor_react_scripts_served(client: TestClient):
    """GET /ui/vendor/react.production.min.js and react-dom return valid scripts."""
    r_react = client.get("/ui/vendor/react.production.min.js")
    assert r_react.status_code == 200
    assert len(r_react.content) > 1000

    r_dom = client.get("/ui/vendor/react-dom.production.min.js")
    assert r_dom.status_code == 200
    assert len(r_dom.content) > 1000


def test_cors_headers_on_api_requests(client: TestClient):
    """Verify CORS middleware is active and allows requests from frontend origins."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in ("*", "http://localhost:3000")


# ---------------------------------------------------------------------------
# End-to-End Operator Workflow Integration
# ---------------------------------------------------------------------------

def test_end_to_end_operator_dashboard_workflow(client: TestClient, ui_test_users):
    """
    Test the complete operator dashboard workflow:
    1. Fetch dashboard overview (initially empty)
    2. Register model & ingest observations
    3. Verify dashboard reflects telemetry
    4. Trigger AIMD evaluation (generates recommendation requiring human approval)
    5. Verify dashboard displays pending decision
    6. Verify VIEWER role cannot trigger evaluation or approval (RBAC 403)
    7. ML Engineer approves recommendation (Human in the loop)
    8. Verify dashboard reflects APPROVED status and zero pending approvals
    """
    eng_token = ui_test_users["engineer"]["token"]
    viewer_token = ui_test_users["viewer"]["token"]
    eng_headers = {"Authorization": f"Bearer {eng_token}"}
    view_headers = {"Authorization": f"Bearer {viewer_token}"}

    # Step 1: Initial Dashboard Overview
    r_init = client.get("/api/dashboard", headers=eng_headers)
    assert r_init.status_code == 200
    data_init = r_init.json()
    assert data_init["models_summary"]["total_models"] == 0
    assert data_init["decision_summary"]["pending_approvals_count"] == 0

    # Step 2: Register a Spam Model
    model_payload = {
        "name": "SpamGuardian-v1",
        "version": "1.0.0",
        "framework": "scikit-learn",
        "algorithm": "MultinomialNB",
        "description": "Production spam classifier",
        "parameters": {"alpha": 0.1},
        "metrics": {"accuracy": 0.95, "f1_score": 0.94},
    }
    r_model = client.post("/api/spam-models", json=model_payload, headers=eng_headers)
    assert r_model.status_code == 201
    model_id = r_model.json()["id"]

    # Ingest 3 monitoring observations to establish telemetry
    base_time = datetime.now(timezone.utc)
    for i in range(3):
        obs_payload = {
            "model_id": model_id,
            "accuracy": 0.78,
            "precision": 0.77,
            "recall": 0.76,
            "f1_score": 0.765,
            "false_positive_rate": 0.05,
            "false_negative_rate": 0.08,
            "drift_score": 0.35,
            "sample_count": 500,
            "latency_ms": 42.0,
            "observed_at": (base_time).isoformat(),
        }
        r_obs = client.post(f"/api/spam-models/{model_id}/monitoring", json=obs_payload, headers=eng_headers)
        assert r_obs.status_code == 201

    # Step 3: Verify Dashboard Overview Reflects Model & Observations
    r_dash = client.get("/api/dashboard", headers=eng_headers)
    assert r_dash.status_code == 200
    dash_data = r_dash.json()
    assert dash_data["models_summary"]["total_models"] == 1
    assert dash_data["monitoring_summary"]["total_observations"] == 3
    assert len(dash_data["model_cards"]) == 1
    card = dash_data["model_cards"][0]
    assert card["name"] == "SpamGuardian-v1"
    assert card["observation_count"] == 3

    # Step 4: Viewer Attempts to Trigger Evaluation -> 403 Forbidden
    r_view_eval = client.post(f"/api/spam-models/{model_id}/decisions/evaluate", headers=view_headers)
    assert r_view_eval.status_code == 403

    # ML Engineer Triggers Evaluation -> 201 Created
    r_eval = client.post(f"/api/spam-models/{model_id}/decisions/evaluate", headers=eng_headers)
    assert r_eval.status_code == 201
    eval_data = r_eval.json()
    decision_id = eval_data["id"]
    assert eval_data["approval_status"] == "PENDING"
    assert eval_data["requires_human_approval"] is True

    # Step 5: Verify Dashboard Shows Pending Approval
    r_pending_dash = client.get("/api/dashboard", headers=eng_headers)
    assert r_pending_dash.status_code == 200
    pending_data = r_pending_dash.json()
    assert pending_data["decision_summary"]["pending_approvals_count"] == 1
    assert len(pending_data["decision_summary"]["recent_decisions"]) >= 1

    # Step 6: Viewer Attempts to Approve Decision -> 403 Forbidden
    r_view_appr = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": "APPROVED"},
        headers=view_headers,
    )
    assert r_view_appr.status_code == 403

    # Step 7: ML Engineer Approves Decision
    r_eng_appr = client.patch(
        f"/api/spam-models/{model_id}/decisions/{decision_id}/approval",
        json={"approval_status": "APPROVED"},
        headers=eng_headers,
    )
    assert r_eng_appr.status_code == 200
    assert r_eng_appr.json()["approval_status"] == "APPROVED"

    # Step 8: Verify Dashboard Reflects Approved Decision & 0 Pending Approvals
    r_final_dash = client.get("/api/dashboard", headers=eng_headers)
    assert r_final_dash.status_code == 200
    final_data = r_final_dash.json()
    assert final_data["decision_summary"]["pending_approvals_count"] == 0
    assert final_data["decision_summary"]["approved_count"] == 1
    assert final_data["model_cards"][0]["latest_decision"]["approval_status"] == "APPROVED"
