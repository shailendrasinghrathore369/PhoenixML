"""
Comprehensive Tests for Real Reference Spam ML Model Inference and Telemetry Integration.

Validates Step 3 of Real-Model Integration:
1. Real artifact exists and loads safely.
2. Model identity and version are preserved.
3. Single SMS inference works and produces valid output structure.
4. Batch SMS inference works and preserves ordering.
5. Prediction output structure is complete and typed.
6. Probability values are valid (probabilities in [0, 1], sum to ~1.0, confidence >= 0.5).
7. Inference is deterministic across repeated calls.
8. Labeled evaluation uses real ground-truth labels and real predictions.
9. Calculated metrics are generated from predictions, not hardcoded.
10. Monitoring observation is generated using existing MonitoringObservation models and persisted.
11. Model identity is preserved throughout monitoring telemetry.
12. Existing decision evaluation pipeline (HealthAssessor -> Explainability -> AIMD) seamlessly
    consumes the generated observation and produces human-in-the-loop recommendations.
13. Concept drift detection can consume real prediction windows (LabeledWindow).
14. RBAC and security boundaries are enforced on inference/telemetry API routes.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.models.models import ModelStatus, RegisteredModel, MonitoringObservation
from app.models.service import RegisteredModelService
from app.models.reference_integration import register_reference_spam_model, get_workspace_root
from app.models.inference_service import SpamInferenceService
from app.models.inference_schemas import (
    PredictionResult,
    BatchPredictionResponse,
    EvaluationMetricsResult,
    TelemetryEvaluationResponse,
)
from app.monitoring.concept_drift import ConceptDriftDetector, ConceptDriftStatus, LabeledWindow
from app.decisions.service import DecisionService
from app.decisions.aimd import AIMDAction, AIMDPriority
from app.decisions.models import ApprovalStatus
from app.users.models import User, UserRole
from app.auth.security import get_password_hash
from tests.conftest import TestingSessionLocal


@pytest.fixture
def test_ml_engineer_user(client: TestClient):
    """Create and authenticate an ML Engineer user."""
    db = TestingSessionLocal()
    user = User(
        username="inference_engineer",
        email="inf_eng@phoenixml.local",
        full_name="Inference Engineer",
        hashed_password=get_password_hash("securepass123"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post(
        "/api/auth/login",
        data={"username": "inference_engineer", "password": "securepass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    db.close()

    return {"user_id": user.id, "token": token}


@pytest.fixture
def test_viewer_user(client: TestClient):
    """Create and authenticate a Viewer user."""
    db = TestingSessionLocal()
    user = User(
        username="inference_viewer",
        email="inf_viewer@phoenixml.local",
        full_name="Inference Viewer",
        hashed_password=get_password_hash("securepass123"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post(
        "/api/auth/login",
        data={"username": "inference_viewer", "password": "securepass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    db.close()

    return {"user_id": user.id, "token": token}


@pytest.fixture
def registered_spam_model(db_session, test_ml_engineer_user):
    """Register the reference Spam model in the test database."""
    owner_id = test_ml_engineer_user["user_id"]
    model = register_reference_spam_model(db_session, owner_id=owner_id)
    return model


# ---------------------------------------------------------------------------
# 1. Model Loading & Identity Tests
# ---------------------------------------------------------------------------

def test_inference_service_loads_real_artifact(db_session, registered_spam_model):
    """Requirement 1 & 2: Real artifact exists, loads safely, and preserves identity."""
    service = SpamInferenceService(db=db_session, model_id=registered_spam_model.id)
    pipeline = service.get_pipeline()

    assert pipeline is not None
    assert hasattr(pipeline, "predict_proba")
    assert service.model_name == "SpamSMS-LogisticRegression"
    assert service.model_version == "1.0.0"


# ---------------------------------------------------------------------------
# 2. Prediction Quality & Structure Tests
# ---------------------------------------------------------------------------

def test_single_sms_inference_structure_and_probabilities(db_session, registered_spam_model):
    """Requirements 3, 5, 6: Single SMS prediction structure and valid probability outputs."""
    service = SpamInferenceService(db=db_session, model_id=registered_spam_model.id)

    # Legitimate message
    ham_text = "Hey, are you free for lunch tomorrow at noon?"
    ham_res = service.predict_single(ham_text)

    assert isinstance(ham_res, PredictionResult)
    assert ham_res.text == ham_text
    assert ham_res.predicted_label == "ham"
    assert ham_res.label_id == 0
    assert not ham_res.is_spam
    assert 0.0 <= ham_res.spam_probability <= 1.0
    assert 0.0 <= ham_res.ham_probability <= 1.0
    assert pytest.approx(ham_res.spam_probability + ham_res.ham_probability, abs=1e-3) == 1.0
    assert ham_res.confidence >= 0.5
    assert ham_res.model_name == "SpamSMS-LogisticRegression"
    assert ham_res.model_version == "1.0.0"

    # Commercial spam message
    spam_text = "WINNER! You have won a £1000 cash prize! Text CLAIM to 88888 now to collect."
    spam_res = service.predict_single(spam_text)

    assert isinstance(spam_res, PredictionResult)
    assert spam_res.text == spam_text
    assert spam_res.predicted_label == "spam"
    assert spam_res.label_id == 1
    assert spam_res.is_spam
    assert spam_res.spam_probability > 0.5
    assert spam_res.confidence == spam_res.spam_probability


def test_batch_sms_inference_preserves_order(db_session, registered_spam_model):
    """Requirement 4: Batch inference processes multiple inputs and maintains sequence."""
    service = SpamInferenceService(db=db_session, model_id=registered_spam_model.id)
    texts = [
        "Are you going to the gym tonight?",
        "URGENT! Call 09061701461 to claim your guaranteed $5000 prize.",
        "Can you pick up milk on the way home?",
    ]

    results = service.predict_batch(texts)
    assert len(results) == 3
    assert results[0].text == texts[0]
    assert results[0].predicted_label == "ham"
    assert results[1].text == texts[1]
    assert results[1].predicted_label == "spam"
    assert results[2].text == texts[2]
    assert results[2].predicted_label == "ham"


def test_inference_is_deterministic(db_session, registered_spam_model):
    """Requirement 7: Identical inputs produce identical predictions across multiple runs."""
    service = SpamInferenceService(db=db_session, model_id=registered_spam_model.id)
    text = "Congratulations, you won a free vacation to Hawaii! Text WIN to 77777"

    run1 = service.predict_single(text)
    run2 = service.predict_single(text)
    run3 = service.predict_single(text)

    assert run1.predicted_label == run2.predicted_label == run3.predicted_label == "spam"
    assert run1.spam_probability == run2.spam_probability == run3.spam_probability
    assert run1.confidence == run2.confidence == run3.confidence


# ---------------------------------------------------------------------------
# 3. Labeled Evaluation & Non-Hardcoded Metrics Tests
# ---------------------------------------------------------------------------

def test_labeled_evaluation_calculates_real_metrics(db_session, registered_spam_model):
    """Requirements 8 & 9: Evaluation uses real y_true and calculates genuine metrics."""
    service = SpamInferenceService(db=db_session, model_id=registered_spam_model.id)

    # Controlled evaluation set with known ground truth
    texts = [
        "Hey, are you free for lunch tomorrow at 12?",                       # Ham (True=0)
        "Can you pick up some groceries on your way home?",                  # Ham (True=0)
        "Where should we meet for the project review?",                      # Ham (True=0)
        "WINNER! You won $1000! Text CLAIM to 88888 now.",                  # Spam (True=1)
        "URGENT! Call 09061701461 to claim your guaranteed cash reward.",    # Spam (True=1)
    ]
    y_true = [0, 0, 0, 1, 1]

    metrics = service.evaluate_labeled_data(texts, y_true)

    assert isinstance(metrics, EvaluationMetricsResult)
    assert metrics.prediction_count == 5
    assert metrics.positive_prediction_count == 2
    assert metrics.negative_prediction_count == 3
    assert metrics.true_positives == 2
    assert metrics.true_negatives == 3
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 0
    assert metrics.accuracy == 1.0
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1_score == 1.0


def test_reference_holdout_test_set_evaluation(db_session, registered_spam_model):
    """Requirement 7, 8, 9: Evaluates deterministic UCI test split without hardcoding."""
    service = SpamInferenceService(db=db_session, model_id=registered_spam_model.id)

    X_test, y_test = service.get_reference_test_data()
    assert len(X_test) == 1115
    assert len(y_test) == 1115
    assert y_test.count(0) == 966  # Ham count
    assert y_test.count(1) == 149  # Spam count

    # Run genuine inference on all 1,115 test samples
    metrics = service.evaluate_labeled_data(X_test, y_test)

    # Real calculated metrics match genuine model performance
    assert metrics.prediction_count == 1115
    assert metrics.accuracy == pytest.approx(0.9901, abs=1e-3)
    assert metrics.precision == pytest.approx(0.9600, abs=1e-3)
    assert metrics.recall == pytest.approx(0.9664, abs=1e-3)
    assert metrics.f1_score == pytest.approx(0.9632, abs=1e-3)
    assert metrics.true_positives == 144
    assert metrics.false_positives == 6
    assert metrics.false_negatives == 5
    assert metrics.true_negatives == 960


# ---------------------------------------------------------------------------
# 4. Monitoring Observation Telemetry Persistence Tests
# ---------------------------------------------------------------------------

def test_record_monitoring_observation(db_session, registered_spam_model, test_ml_engineer_user):
    """Requirements 10 & 11: Monitoring observation is created via existing mechanism and persisted."""
    owner_id = test_ml_engineer_user["user_id"]
    service = SpamInferenceService(db=db_session, model_id=registered_spam_model.id)

    # Evaluate on a representative sample
    X_sample, y_sample = service.get_reference_test_data(sample_limit=100)
    response = service.evaluate_and_record_telemetry(
        model_id=registered_spam_model.id,
        owner_id=owner_id,
        texts=X_sample,
        y_true=y_sample,
        record_observation=True,
    )

    assert response.observation_recorded
    assert response.observation_id is not None
    assert response.model_id == registered_spam_model.id
    assert response.model_name == "SpamSMS-LogisticRegression"
    assert response.metrics.prediction_count == 100

    # Query directly from DB to verify persistence in monitoring_observations
    obs = db_session.get(MonitoringObservation, response.observation_id)
    assert obs is not None
    assert obs.model_id == registered_spam_model.id
    assert obs.prediction_count == 100
    assert obs.accuracy == response.metrics.accuracy
    assert obs.precision == response.metrics.precision
    assert obs.recall == response.metrics.recall
    assert obs.f1_score == response.metrics.f1_score
    assert obs.positive_prediction_count + obs.negative_prediction_count == 100


# ---------------------------------------------------------------------------
# 5. Decision Pipeline Integration Tests (Health -> Explainability -> AIMD)
# ---------------------------------------------------------------------------

def test_end_to_end_telemetry_to_aimd_decision(db_session, registered_spam_model, test_ml_engineer_user):
    """Requirement 12: DecisionService evaluates real observation and produces AIMD recommendation."""
    owner_id = test_ml_engineer_user["user_id"]
    inf_service = SpamInferenceService(db=db_session, model_id=registered_spam_model.id)

    # 1. Generate real telemetry from real predictions on reference test split
    inf_service.evaluate_and_record_telemetry(
        model_id=registered_spam_model.id,
        owner_id=owner_id,
        use_reference_test_set=True,
        sample_limit=200,
        record_observation=True,
    )

    # 2. Evaluate model through existing DecisionService
    user = db_session.get(User, owner_id)
    decision_service = DecisionService(db=db_session)
    decision = decision_service.evaluate_model(
        model_id=registered_spam_model.id,
        user=user,
        as_read_schema=False,
    )

    # 3. Verify AIMD evaluation result
    assert decision is not None
    assert decision.model_id == registered_spam_model.id
    assert decision.requires_human_approval is True
    assert decision.approval_status == ApprovalStatus.PENDING
    assert decision.health_score is not None
    assert decision.health_score >= 80.0  # Healthy model
    assert decision.health_status == "healthy"
    assert decision.recommended_action == AIMDAction.CONTINUE_MONITORING
    assert decision.priority == AIMDPriority.LOW
    assert decision.explanation is not None
    assert "Healthy" in decision.explanation or "stable" in decision.explanation.lower() or "satisfactory" in decision.explanation.lower()


# ---------------------------------------------------------------------------
# 6. Concept Drift Integration Test using Real Predictions
# ---------------------------------------------------------------------------

def test_concept_drift_using_real_prediction_windows(db_session, registered_spam_model):
    """Validates that real predictions can form genuine LabeledWindows for ConceptDriftDetector."""
    service = SpamInferenceService(db=db_session, model_id=registered_spam_model.id)

    X_test, y_test = service.get_reference_test_data()

    # Split into reference window (first 200) and current window (next 200)
    ref_window = service.create_labeled_window(X_test[:200], y_test[:200])
    cur_window = service.create_labeled_window(X_test[200:400], y_test[200:400])

    assert len(ref_window.y_true) == 200
    assert len(ref_window.y_pred) == 200
    assert len(cur_window.y_true) == 200
    assert len(cur_window.y_pred) == 200

    # Analyze with domain ConceptDriftDetector
    detector = ConceptDriftDetector()
    analysis = detector.analyze(reference_window=ref_window, current_window=cur_window)

    assert analysis.status in (ConceptDriftStatus.NO_DRIFT, ConceptDriftStatus.DRIFTED)
    assert analysis.reference_sample_size == 200
    assert analysis.current_sample_size == 200
    assert len(analysis.metric_results) == 4  # accuracy, precision, recall, f1


# ---------------------------------------------------------------------------
# 7. FastAPI Route Integration & RBAC Tests
# ---------------------------------------------------------------------------

def test_api_predict_single_and_batch(client: TestClient, db_session, registered_spam_model, test_ml_engineer_user):
    """Requirement 13: POST /api/spam-models/{model_id}/predict returns predictions with valid RBAC."""
    token = test_ml_engineer_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    model_id = registered_spam_model.id

    payload = {
        "texts": [
            "Hey, are you free tonight?",
            "WINNER! Free vacation voucher. Call now!",
        ]
    }
    resp = client.post(f"/api/spam-models/{model_id}/predict", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_predictions"] == 2
    assert data["spam_count"] == 1
    assert data["ham_count"] == 1
    assert data["model_name"] == "SpamSMS-LogisticRegression"
    assert data["model_version"] == "1.0.0"
    assert data["predictions"][0]["predicted_label"] == "ham"
    assert data["predictions"][1]["predicted_label"] == "spam"


def test_api_evaluate_telemetry_endpoint(client: TestClient, db_session, registered_spam_model, test_ml_engineer_user):
    """Requirement 13: POST /api/spam-models/{model_id}/evaluate-telemetry creates real telemetry."""
    token = test_ml_engineer_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    model_id = registered_spam_model.id

    payload = {
        "samples": [
            {"text": "Hey what time are you coming over?", "y_true": 0},
            {"text": "URGENT! You won £1000 cash. Call 09061701461 to claim.", "y_true": 1},
        ],
        "record_monitoring_observation": True,
    }
    resp = client.post(f"/api/spam-models/{model_id}/evaluate-telemetry", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["observation_recorded"] is True
    assert data["observation_id"] is not None
    assert data["metrics"]["prediction_count"] == 2
    assert data["metrics"]["accuracy"] == 1.0


def test_api_viewer_cannot_record_telemetry(client: TestClient, db_session, registered_spam_model, test_viewer_user):
    """Requirement 13: VIEWER user is forbidden from creating monitoring telemetry (403 Forbidden)."""
    token = test_viewer_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    model_id = registered_spam_model.id

    payload = {
        "samples": [{"text": "Hello there", "y_true": 0}],
        "record_monitoring_observation": True,
    }
    resp = client.post(f"/api/spam-models/{model_id}/evaluate-telemetry", json=payload, headers=headers)
    assert resp.status_code == 403
    detail = resp.json()["detail"].lower()
    assert "not authorized" in detail or "permission" in detail


def test_api_unauthenticated_request_rejected(client: TestClient, registered_spam_model):
    """Requirement 13: Unauthenticated calls are rejected with 401 Unauthorized."""
    model_id = registered_spam_model.id
    resp = client.post(f"/api/spam-models/{model_id}/predict", json={"texts": ["Hello"]})
    assert resp.status_code == 401
