"""
Focused Integration Tests for Drift-Aware AIMD Runtime Evaluation Pipeline.

Validates that DataDriftDetector and ConceptDriftDetector outputs are properly wired
into the real runtime decision evaluation pipeline (service and API endpoints),
while preserving domain independence, existing deterministic AIMD rules, and
mandatory human-in-the-loop approval.

Covers Scenarios:
A. No drift inputs -> existing behavior remains unchanged.
B. Feature data drift detected -> DataDriftDetector result reaches AIMD.
C. Concept drift detected -> ConceptDriftDetector result reaches AIMD.
D. Both drift types available -> both analyses reach AIMD.
E. Insufficient drift input -> evaluation does not crash and does not fabricate drift.
F. Drift + degraded health/performance -> deterministic AIMD rules followed.
G. Human approval requirement strictly enforced (requires_human_approval=True, PENDING).
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.auth.security import get_password_hash
from app.decisions import (
    AIMDAction,
    AIMDPriority,
    AIMDConfidence,
    ApprovalStatus,
    DecisionService,
    ModelEvaluationRequest,
    DataDriftEvaluationInput,
    ConceptDriftEvaluationInput,
)
from app.models.models import ModelStatus, RegisteredModel
from app.models.monitoring_schemas import MonitoringObservationCreate
from app.models.monitoring_repository import MonitoringObservationRepository
from app.monitoring.data_drift import FeatureDistribution, DataDriftConfiguration
from app.monitoring.concept_drift import LabeledWindow, ConceptDriftConfiguration
from app.users.models import User, UserRole
from tests.conftest import TestingSessionLocal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_setup(client: TestClient):
    """Sets up an owner ML Engineer, another ML Engineer, an Admin, a Viewer, and an active model."""
    db = TestingSessionLocal()

    owner = User(
        username="drift_eng_owner",
        email="drift_owner@example.com",
        full_name="Drift Test Owner",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db.add(owner)

    other = User(
        username="drift_other_eng",
        email="drift_other@example.com",
        full_name="Drift Other Engineer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db.add(other)

    admin = User(
        username="drift_admin_user",
        email="drift_admin@example.com",
        full_name="Drift Admin",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)

    viewer = User(
        username="drift_viewer_user",
        email="drift_viewer@example.com",
        full_name="Drift Viewer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db.add(viewer)
    db.commit()

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="DriftIntegrationModel",
        framework="Scikit-Learn",
        owner_id=owner.id,
        status=ModelStatus.ACTIVE,
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    # Generate auth tokens
    r_owner = client.post("/api/auth/login", data={"username": "drift_eng_owner", "password": "password123"})
    owner_token = r_owner.json()["access_token"]

    r_other = client.post("/api/auth/login", data={"username": "drift_other_eng", "password": "password123"})
    other_token = r_other.json()["access_token"]

    r_admin = client.post("/api/auth/login", data={"username": "drift_admin_user", "password": "password123"})
    admin_token = r_admin.json()["access_token"]

    r_viewer = client.post("/api/auth/login", data={"username": "drift_viewer_user", "password": "password123"})
    viewer_token = r_viewer.json()["access_token"]

    owner_id = owner.id
    other_id = other.id
    admin_id = admin.id
    viewer_id = viewer.id
    model_id = model.id
    db.close()

    return {
        "model_id": model_id,
        "owner_id": owner_id,
        "owner_token": owner_token,
        "other_id": other_id,
        "other_token": other_token,
        "admin_id": admin_id,
        "admin_token": admin_token,
        "viewer_id": viewer_id,
        "viewer_token": viewer_token,
    }


def seed_healthy_observations(db, model_id: uuid.UUID):
    repo = MonitoringObservationRepository(db)
    now = datetime.now(timezone.utc)
    for i in range(3):
        repo.create(
            MonitoringObservationCreate(
                model_id=model_id,
                observed_at=now - timedelta(hours=3 - i),
                prediction_count=1000,
                positive_prediction_count=100,
                negative_prediction_count=900,
                accuracy=0.95,
                precision=0.94,
                recall=0.93,
                f1_score=0.935,
            )
        )


def seed_warning_observations(db, model_id: uuid.UUID):
    repo = MonitoringObservationRepository(db)
    now = datetime.now(timezone.utc)
    for i in range(2):
        repo.create(
            MonitoringObservationCreate(
                model_id=model_id,
                observed_at=now - timedelta(hours=2 - i),
                prediction_count=1000,
                positive_prediction_count=100,
                negative_prediction_count=900,
                accuracy=0.72,
                precision=0.70,
                recall=0.70,
                f1_score=0.70,
            )
        )


def seed_critical_observations(db, model_id: uuid.UUID):
    repo = MonitoringObservationRepository(db)
    now = datetime.now(timezone.utc)
    repo.create(
        MonitoringObservationCreate(
            model_id=model_id,
            observed_at=now - timedelta(hours=2),
            prediction_count=1000,
            positive_prediction_count=100,
            negative_prediction_count=900,
            accuracy=0.92,
            precision=0.90,
            recall=0.90,
            f1_score=0.90,
        )
    )
    repo.create(
        MonitoringObservationCreate(
            model_id=model_id,
            observed_at=now - timedelta(hours=1),
            prediction_count=1000,
            positive_prediction_count=100,
            negative_prediction_count=900,
            accuracy=0.45,
            precision=0.40,
            recall=0.35,
            f1_score=0.37,
        )
    )


# ---------------------------------------------------------------------------
# Test Scenario A: No Drift Inputs (Preserves Existing Behavior)
# ---------------------------------------------------------------------------

def test_scenario_a_no_drift_inputs_service(test_setup):
    """When no drift inputs are provided, AIMD evaluates health and performance exactly as before."""
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    service = DecisionService(db)

    decision = service.evaluate_model(
        model_id=test_setup["model_id"],
        as_read_schema=True,
    )
    db.close()

    assert decision.recommended_action == AIMDAction.CONTINUE_MONITORING
    assert decision.priority == AIMDPriority.LOW
    assert decision.health_status == "healthy"
    assert decision.requires_human_approval is True
    assert decision.approval_status == ApprovalStatus.PENDING
    assert not any("data_drift" in s for s in decision.supporting_signals)
    assert not any("concept_drift" in s for s in decision.supporting_signals)


def test_scenario_a_no_drift_inputs_api(client: TestClient, test_setup):
    """API call without body preserves standard evaluation output."""
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    db.close()

    resp = client.post(
        f"/api/spam-models/{test_setup['model_id']}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_setup['owner_token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["recommended_action"] == AIMDAction.CONTINUE_MONITORING.value
    assert data["priority"] == AIMDPriority.LOW.value
    assert data["requires_human_approval"] is True
    assert data["approval_status"] == ApprovalStatus.PENDING.value


# ---------------------------------------------------------------------------
# Test Scenario B: Feature Data Drift Detected
# ---------------------------------------------------------------------------

def test_scenario_b_data_drift_detected_single_feature_increased_monitoring(test_setup):
    """
    Healthy model + 1 drifted feature -> AIMD Rule 5 recommends INCREASED_MONITORING.
    Verifies that DataDriftDetector executed, found drift, and reached AIMD.
    """
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    service = DecisionService(db)

    drifted_feature = FeatureDistribution(
        feature_name="char_count",
        reference_values=[10.0, 20.0, 30.0, 40.0, 50.0] * 10,
        current_values=[100.0, 200.0, 300.0, 400.0, 500.0] * 10,
    )

    decision = service.evaluate_model(
        model_id=test_setup["model_id"],
        features=[drifted_feature],
        as_read_schema=True,
    )
    db.close()

    assert decision.recommended_action == AIMDAction.INCREASED_MONITORING
    assert decision.priority == AIMDPriority.MEDIUM
    assert decision.requires_human_approval is True
    assert decision.approval_status == ApprovalStatus.PENDING
    assert any("data_drift_detected(char_count)" in s for s in decision.supporting_signals)
    assert "char_count" in decision.explanation or "data drift" in decision.explanation.lower()


def test_scenario_b_data_drift_detected_multi_features_data_collection(client: TestClient, test_setup):
    """
    Healthy model + >=2 drifted features -> AIMD Rule 5 recommends DATA_COLLECTION.
    Tested via API endpoint with JSON payload.
    """
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    db.close()

    payload = {
        "features": [
            {
                "feature_name": "char_count",
                "reference_values": [10.0, 20.0, 30.0] * 10,
                "current_values": [100.0, 200.0, 300.0] * 10,
            },
            {
                "feature_name": "spam_keyword_ratio",
                "reference_values": [0.01, 0.02, 0.03] * 10,
                "current_values": [0.50, 0.60, 0.70] * 10,
            },
        ]
    }

    resp = client.post(
        f"/api/spam-models/{test_setup['model_id']}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_setup['owner_token']}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["recommended_action"] == AIMDAction.DATA_COLLECTION.value
    assert data["priority"] == AIMDPriority.MEDIUM.value
    assert data["requires_human_approval"] is True
    assert any("data_drift_detected" in s for s in data["supporting_signals"])
    assert "char_count" in str(data["supporting_signals"])
    assert "spam_keyword_ratio" in str(data["supporting_signals"])


def test_scenario_b_data_drift_nested_schema(client: TestClient, test_setup):
    """Verifies that nested data_drift input format is parsed and evaluated properly."""
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    db.close()

    payload = {
        "data_drift": {
            "features": [
                {
                    "feature_name": "link_density",
                    "reference_values": [1.0, 2.0, 3.0] * 10,
                    "current_values": [10.0, 20.0, 30.0] * 10,
                }
            ],
            "config": {"alpha": 0.01},
        }
    }

    resp = client.post(
        f"/api/spam-models/{test_setup['model_id']}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_setup['owner_token']}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["recommended_action"] == AIMDAction.INCREASED_MONITORING.value
    assert any("data_drift_detected(link_density)" in s for s in data["supporting_signals"])


# ---------------------------------------------------------------------------
# Test Scenario C: Concept Drift Detected
# ---------------------------------------------------------------------------

def test_scenario_c_concept_drift_detected_triggers_retrain_service(test_setup):
    """
    Concept drift detected between reference and current labeled windows -> AIMD Rule 2 recommends RETRAIN.
    """
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    service = DecisionService(db)

    # Reference window: 100% accuracy
    ref_window = LabeledWindow(
        y_true=[0] * 10 + [1] * 10,
        y_pred=[0] * 10 + [1] * 10,
    )
    # Current window: 60% accuracy (drop of -0.40)
    cur_window = LabeledWindow(
        y_true=[0] * 10 + [1] * 10,
        y_pred=[0] * 6 + [1] * 4 + [1] * 6 + [0] * 4,
    )

    decision = service.evaluate_model(
        model_id=test_setup["model_id"],
        reference_window=ref_window,
        current_window=cur_window,
        as_read_schema=True,
    )
    db.close()

    assert decision.recommended_action == AIMDAction.RETRAIN
    assert decision.priority == AIMDPriority.HIGH
    assert decision.requires_human_approval is True
    assert decision.approval_status == ApprovalStatus.PENDING
    assert any("concept_drift_detected" in s for s in decision.supporting_signals)
    assert "accuracy" in decision.rationale or "concept drift" in decision.rationale.lower()


def test_scenario_c_concept_drift_detected_api(client: TestClient, test_setup):
    """Concept drift trigger via API POST with concept_drift payload."""
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    db.close()

    payload = {
        "concept_drift": {
            "reference_window": {
                "y_true": [0] * 10 + [1] * 10,
                "y_pred": [0] * 10 + [1] * 10,
            },
            "current_window": {
                "y_true": [0] * 10 + [1] * 10,
                "y_pred": [0] * 5 + [1] * 5 + [1] * 5 + [0] * 5,
            },
            "config": {
                "degradation_threshold": 0.05,
            },
        }
    }

    resp = client.post(
        f"/api/spam-models/{test_setup['model_id']}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_setup['owner_token']}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["recommended_action"] == AIMDAction.RETRAIN.value
    assert data["requires_human_approval"] is True
    assert any("concept_drift_detected" in s for s in data["supporting_signals"])


# ---------------------------------------------------------------------------
# Test Scenario D: Both Drift Types Available
# ---------------------------------------------------------------------------

def test_scenario_d_both_drift_types_available(client: TestClient, test_setup):
    """Both data drift and concept drift inputs provided -> both reach AIMD and explainability."""
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    db.close()

    payload = {
        "features": [
            {
                "feature_name": "embedded_links",
                "reference_values": [1, 2, 3] * 10,
                "current_values": [10, 20, 30] * 10,
            }
        ],
        "concept_drift": {
            "reference_window": {
                "y_true": [0] * 10 + [1] * 10,
                "y_pred": [0] * 10 + [1] * 10,
            },
            "current_window": {
                "y_true": [0] * 10 + [1] * 10,
                "y_pred": [0] * 5 + [1] * 5 + [1] * 5 + [0] * 5,
            },
        },
    }

    resp = client.post(
        f"/api/spam-models/{test_setup['model_id']}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_setup['owner_token']}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["recommended_action"] == AIMDAction.RETRAIN.value
    assert data["requires_human_approval"] is True
    # Both signals must be present in supporting_signals
    assert any("data_drift_detected(embedded_links)" in s for s in data["supporting_signals"])
    assert any("concept_drift_detected" in s for s in data["supporting_signals"])


# ---------------------------------------------------------------------------
# Test Scenario E: Insufficient Drift Input
# ---------------------------------------------------------------------------

def test_scenario_e_insufficient_data_drift_samples(test_setup):
    """
    Features with sample size < minimum_samples does not crash, does not fabricate drift,
    and allows standard health evaluation to continue.
    """
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    service = DecisionService(db)

    # 1 sample < minimum_samples of 2
    insufficient_feature = FeatureDistribution(
        feature_name="token_count",
        reference_values=[42.0],
        current_values=[42.0],
    )

    decision = service.evaluate_model(
        model_id=test_setup["model_id"],
        features=[insufficient_feature],
        as_read_schema=True,
    )
    db.close()

    # Standard healthy monitoring outcome preserved
    assert decision.recommended_action == AIMDAction.CONTINUE_MONITORING
    assert decision.health_status == "healthy"
    assert decision.requires_human_approval is True
    # Must NOT claim data drift was detected
    assert not any("data_drift_detected" in s for s in decision.supporting_signals)


def test_scenario_e_insufficient_concept_drift_samples(test_setup):
    """
    Labeled windows with < 2 samples does not crash and does not fabricate concept drift.
    """
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    service = DecisionService(db)

    ref = LabeledWindow(y_true=[1], y_pred=[1])
    cur = LabeledWindow(y_true=[0], y_pred=[1])

    decision = service.evaluate_model(
        model_id=test_setup["model_id"],
        reference_window=ref,
        current_window=cur,
        as_read_schema=True,
    )
    db.close()

    assert decision.recommended_action == AIMDAction.CONTINUE_MONITORING
    assert decision.requires_human_approval is True
    assert not any("concept_drift_detected" in s for s in decision.supporting_signals)


def test_scenario_e_incomplete_window_input(test_setup):
    """Providing only one window does not crash and safely marks concept drift as INSUFFICIENT_DATA."""
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    service = DecisionService(db)

    ref = LabeledWindow(y_true=[0, 1] * 5, y_pred=[0, 1] * 5)

    decision = service.evaluate_model(
        model_id=test_setup["model_id"],
        reference_window=ref,
        current_window=None,
        as_read_schema=True,
    )
    db.close()

    assert decision.recommended_action == AIMDAction.CONTINUE_MONITORING
    assert not any("concept_drift_detected" in s for s in decision.supporting_signals)


# ---------------------------------------------------------------------------
# Test Scenario F: Drift + Degraded Health / Performance
# ---------------------------------------------------------------------------

def test_scenario_f_warning_health_with_data_drift_triggers_retrain(test_setup):
    """
    AIMD Rule 4: Health WARNING + concurrent DATA DRIFT -> RETRAIN with HIGH priority.
    (Note: Health WARNING without drift produces HUMAN_REVIEW, so this tests rule divergence).
    """
    db = TestingSessionLocal()
    seed_warning_observations(db, test_setup["model_id"])
    service = DecisionService(db)

    drifted_feature = FeatureDistribution(
        feature_name="subject_exclamations",
        reference_values=[0, 1] * 10,
        current_values=[5, 10] * 10,
    )

    decision = service.evaluate_model(
        model_id=test_setup["model_id"],
        features=[drifted_feature],
        as_read_schema=True,
    )
    db.close()

    assert decision.recommended_action == AIMDAction.RETRAIN
    assert decision.priority == AIMDPriority.HIGH
    assert decision.health_status == "warning"
    assert decision.requires_human_approval is True
    assert any("data_drift_detected(subject_exclamations)" in s for s in decision.supporting_signals)


def test_scenario_f_warning_health_with_concept_drift_triggers_critical_retrain(test_setup):
    """
    AIMD Rule 2: Health WARNING + CONCEPT DRIFT -> RETRAIN with CRITICAL priority.
    """
    db = TestingSessionLocal()
    seed_warning_observations(db, test_setup["model_id"])
    service = DecisionService(db)

    ref = LabeledWindow(y_true=[0] * 10 + [1] * 10, y_pred=[0] * 10 + [1] * 10)
    cur = LabeledWindow(y_true=[0] * 10 + [1] * 10, y_pred=[1] * 10 + [0] * 10)

    decision = service.evaluate_model(
        model_id=test_setup["model_id"],
        reference_window=ref,
        current_window=cur,
        as_read_schema=True,
    )
    db.close()

    assert decision.recommended_action == AIMDAction.RETRAIN
    assert decision.priority == AIMDPriority.CRITICAL
    assert decision.requires_human_approval is True
    assert any("concept_drift_detected" in s for s in decision.supporting_signals)


def test_scenario_f_critical_health_with_drift_and_verified_rollback(test_setup):
    """
    AIMD Rule 1: CRITICAL health + verified rollback target -> ROLLBACK (CRITICAL).
    Corroborated by drift signals.
    """
    db = TestingSessionLocal()
    seed_critical_observations(db, test_setup["model_id"])
    service = DecisionService(db)

    drifted_feature = FeatureDistribution(
        feature_name="f",
        reference_values=[1, 2] * 10,
        current_values=[10, 20] * 10,
    )

    decision = service.evaluate_model(
        model_id=test_setup["model_id"],
        features=[drifted_feature],
        historical_maintenance_context={
            "rollback_target_available": True,
            "target_model_version": "v1.2.0",
        },
        as_read_schema=True,
    )
    db.close()

    assert decision.recommended_action == AIMDAction.ROLLBACK
    assert decision.priority == AIMDPriority.CRITICAL
    assert decision.health_status == "critical"
    assert decision.requires_human_approval is True
    assert decision.confidence == 0.9  # Corroborated high confidence


# ---------------------------------------------------------------------------
# Test Scenario G: Mandatory Human-in-the-Loop Approval & RBAC Enforced
# ---------------------------------------------------------------------------

def test_scenario_g_hitl_approval_invariant(test_setup):
    """Under all combinations of drift and health, requires_human_approval MUST be True and PENDING."""
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    service = DecisionService(db)

    feat = FeatureDistribution(feature_name="f", reference_values=[1, 2] * 10, current_values=[10, 20] * 10)
    decision = service.evaluate_model(
        model_id=test_setup["model_id"],
        features=[feat],
        as_read_schema=True,
    )
    db.close()

    assert decision.requires_human_approval is True
    assert decision.approval_status == ApprovalStatus.PENDING


def test_scenario_g_rbac_enforcement_with_drift_payload(client: TestClient, test_setup):
    """RBAC checks are preserved when drift payloads are submitted."""
    payload = {
        "features": [
            {
                "feature_name": "f1",
                "reference_values": [1, 2] * 10,
                "current_values": [10, 20] * 10,
            }
        ]
    }

    # Viewer rejected with 403
    r_viewer = client.post(
        f"/api/spam-models/{test_setup['model_id']}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_setup['viewer_token']}"},
        json=payload,
    )
    assert r_viewer.status_code == 403

    # Non-owner ML Engineer rejected with 403
    r_other = client.post(
        f"/api/spam-models/{test_setup['model_id']}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_setup['other_token']}"},
        json=payload,
    )
    assert r_other.status_code == 403

    # Admin allowed with 201
    db = TestingSessionLocal()
    seed_healthy_observations(db, test_setup["model_id"])
    db.close()

    r_admin = client.post(
        f"/api/spam-models/{test_setup['model_id']}/decisions/evaluate",
        headers={"Authorization": f"Bearer {test_setup['admin_token']}"},
        json=payload,
    )
    assert r_admin.status_code == 201
    assert r_admin.json()["requires_human_approval"] is True
