"""
Tests for Real Reference Spam ML Model Registration in PhoenixML Model Registry.

Validates Step 2 of Real-Model Integration:
- Locating the genuine trained reference model artifact and metadata
- Building ModelCreate payload with correct fields and formatted metadata description
- Registering model via RegisteredModelRepository and RegisteredModelService
- Idempotent registration and duplicate handling
- Multi-version registration
- Retrieval via service and FastAPI router (/api/spam-models)
- Preservation of domain independence and HITL scope
"""

import os
import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.models.models import ModelStatus, RegisteredModel
from app.models.service import RegisteredModelService
from app.models.repository import RegisteredModelRepository
from app.models.reference_integration import (
    find_reference_metadata_file,
    find_reference_artifact_file,
    load_reference_metadata,
    format_reference_model_description,
    parse_reference_model_description,
    build_reference_model_payload,
    register_reference_spam_model,
    get_workspace_root,
)
from app.users.models import User, UserRole
from app.auth.security import get_password_hash
from tests.conftest import TestingSessionLocal


@pytest.fixture
def test_ml_user(client: TestClient):
    """Create and authenticate an ML Engineer user for testing registry interactions."""
    db = TestingSessionLocal()
    user = User(
        username="spam_ml_eng",
        email="spam_ml@phoenixml.local",
        full_name="Spam ML Engineer",
        hashed_password=get_password_hash("securepass123"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post(
        "/api/auth/login",
        data={"username": "spam_ml_eng", "password": "securepass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    db.close()

    return {"user_id": user.id, "token": token}


def test_reference_files_exist_on_disk():
    """Verify that genuine reference metadata and trained model artifact exist."""
    meta_path = find_reference_metadata_file()
    artifact_path = find_reference_artifact_file()

    assert meta_path.is_file(), f"Metadata not found: {meta_path}"
    assert artifact_path.is_file(), f"Artifact not found: {artifact_path}"
    assert meta_path.name == "model_metadata.json"
    assert artifact_path.name == "spam_classifier_v1.joblib"


def test_reference_metadata_content():
    """Verify metadata contents accurately describe the UCI SMS dataset and metrics."""
    meta = load_reference_metadata()

    assert meta["model_name"] == "SpamSMS-LogisticRegression"
    assert meta["model_version"] == "1.0.0"
    assert meta["dataset"]["total_samples"] == 5574
    assert meta["evaluation_metrics"]["accuracy"] >= 0.99
    assert meta["evaluation_metrics"]["precision"] >= 0.95
    assert meta["evaluation_metrics"]["recall"] >= 0.95
    assert meta["evaluation_metrics"]["f1_score"] >= 0.95


def test_description_formatting_and_parsing():
    """Verify description formatting safely fits within 1000 characters and parses cleanly."""
    meta = load_reference_metadata()
    artifact_path = find_reference_artifact_file()

    description = format_reference_model_description(meta, artifact_path)
    assert len(description) <= 1000
    assert "v1.0.0" in description
    assert "spam_classifier_v1.joblib" in description
    assert "Metrics:" in description
    assert "Local reference deployment" in description

    # Test round-trip parsing
    parsed = parse_reference_model_description(description)
    assert parsed["version"] == "1.0.0"
    assert "spam_classifier_v1.joblib" in parsed["artifact_path"]
    assert "SMS Spam Collection" in parsed["dataset"]
    assert parsed["metrics"]["acc"] == pytest.approx(0.9901, abs=1e-3)
    assert parsed["metrics"]["prec"] == pytest.approx(0.9600, abs=1e-3)
    assert parsed["metrics"]["rec"] == pytest.approx(0.9664, abs=1e-3)
    assert parsed["metrics"]["f1"] == pytest.approx(0.9632, abs=1e-3)


def test_build_reference_model_payload():
    """Verify payload construction conforms strictly to ModelCreate schema."""
    payload = build_reference_model_payload()

    assert payload.name == "SpamSMS-LogisticRegression"
    assert payload.framework == "scikit-learn"
    assert payload.algorithm == "TF-IDF + Logistic Regression"
    assert payload.status == ModelStatus.ACTIVE
    assert payload.description is not None
    assert "v1.0.0" in payload.description


def test_register_reference_spam_model_db(db_session, test_ml_user):
    """Verify registration writes real reference model into the database."""
    owner_id = test_ml_user["user_id"]

    registered = register_reference_spam_model(db_session, owner_id=owner_id)

    assert registered.id is not None
    assert registered.name == "SpamSMS-LogisticRegression"
    assert registered.framework == "scikit-learn"
    assert registered.algorithm == "TF-IDF + Logistic Regression"
    assert registered.status == ModelStatus.ACTIVE
    assert registered.owner_id == owner_id

    # Verify metadata encoded in description
    parsed = parse_reference_model_description(registered.description)
    assert parsed["version"] == "1.0.0"
    assert "spam_classifier_v1.joblib" in parsed["artifact_path"]

    # Verify artifact path referenced in description actually exists on filesystem
    ws_root = get_workspace_root()
    referenced_file = ws_root / parsed["artifact_path"]
    assert referenced_file.is_file()


def test_register_reference_model_idempotent(db_session, test_ml_user):
    """Verify that registering the same model twice with allow_duplicate=False returns existing record."""
    owner_id = test_ml_user["user_id"]

    model_1 = register_reference_spam_model(db_session, owner_id=owner_id, allow_duplicate=False)
    model_2 = register_reference_spam_model(db_session, owner_id=owner_id, allow_duplicate=False)

    assert model_1.id == model_2.id

    # Verify only 1 record exists in repository
    repo = RegisteredModelRepository(db_session)
    models = repo.list(owner_id=owner_id)
    assert len(models) == 1


def test_register_reference_model_versioned_names(db_session, test_ml_user):
    """Verify that multiple versions can be registered using versioned naming."""
    owner_id = test_ml_user["user_id"]

    base_model = register_reference_spam_model(
        db_session,
        owner_id=owner_id,
        name="SpamSMS-LogisticRegression",
        allow_duplicate=False,
    )
    v1_model = register_reference_spam_model(
        db_session,
        owner_id=owner_id,
        include_version_in_name=True,
        allow_duplicate=False,
    )

    assert base_model.name == "SpamSMS-LogisticRegression"
    assert v1_model.name == "SpamSMS-LogisticRegression:v1.0.0"
    assert base_model.id != v1_model.id


def test_service_registration_and_retrieval(db_session, test_ml_user):
    """Verify RegisteredModelService can register and retrieve model by ID and by name."""
    owner_id = test_ml_user["user_id"]
    service = RegisteredModelService(db_session)

    model = service.register_reference_model(owner_id=owner_id)
    assert model.name == "SpamSMS-LogisticRegression"

    # Retrieve by ID
    by_id = service.get_model(model.id, owner_id=owner_id)
    assert by_id.id == model.id

    # Retrieve by Name
    by_name = service.get_model_by_name("SpamSMS-LogisticRegression", owner_id=owner_id)
    assert by_name is not None
    assert by_name.id == model.id


def test_api_retrieval_of_registered_reference_model(client: TestClient, db_session, test_ml_user):
    """Verify real reference model registered in DB is retrievable via GET /api/spam-models."""
    owner_id = test_ml_user["user_id"]
    token = test_ml_user["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Register in DB
    registered = register_reference_spam_model(db_session, owner_id=owner_id)

    # 1. Retrieve list
    list_resp = client.get("/api/spam-models", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(item["id"] == str(registered.id) for item in items)

    # 2. Retrieve single model by ID
    get_resp = client.get(f"/api/spam-models/{registered.id}", headers=headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == str(registered.id)
    assert data["name"] == "SpamSMS-LogisticRegression"
    assert data["framework"] == "scikit-learn"
    assert data["algorithm"] == "TF-IDF + Logistic Regression"
    assert data["status"] == "ACTIVE"
    assert "spam_classifier_v1.joblib" in data["description"]


def test_api_create_from_reference_payload(client: TestClient, test_ml_user):
    """Verify that POST /api/spam-models accepts the reference payload directly."""
    token = test_ml_user["token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = build_reference_model_payload(name="SpamSMS-LogisticRegression-API")
    create_resp = client.post(
        "/api/spam-models",
        json=payload.model_dump(),
        headers=headers,
    )
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["name"] == "SpamSMS-LogisticRegression-API"
    assert created_data["framework"] == "scikit-learn"
    assert created_data["algorithm"] == "TF-IDF + Logistic Regression"
    assert created_data["status"] == "ACTIVE"
    assert "Artifact: ml_pipeline/artifacts/spam_classifier_v1.joblib" in created_data["description"]
