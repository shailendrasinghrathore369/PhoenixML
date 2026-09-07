import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.users.models import User, UserRole
from app.models.models import RegisteredModel, ModelStatus
from app.auth.security import get_password_hash
from tests.conftest import TestingSessionLocal

@pytest.fixture
def test_user_engine(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="integration_eng",
        email="int_eng@example.com",
        full_name="Int Engineer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="IntegrationModel",
        framework="PyTorch",
        owner_id=user.id,
        status=ModelStatus.ACTIVE
    )
    db.add(model)
    db.commit()

    response = client.post("/api/auth/login", data={"username": "integration_eng", "password": "password123"})
    token = response.json()["access_token"]
    
    user_id = str(user.id)
    model_id = str(model.id)
    db.close()
    
    return {"user_id": user_id, "token": token, "model_id": model_id}

@pytest.fixture
def test_user_viewer(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="integration_viewer",
        email="int_view@example.com",
        full_name="Int Viewer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.VIEWER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="IntegrationViewerModel",
        framework="scikit-learn",
        owner_id=user.id,
        status=ModelStatus.DEVELOPMENT
    )
    db.add(model)
    db.commit()

    response = client.post("/api/auth/login", data={"username": "integration_viewer", "password": "password123"})
    token = response.json()["access_token"]
    
    user_id = str(user.id)
    model_id = str(model.id)
    db.close()
    
    return {"user_id": user_id, "token": token, "model_id": model_id}

@pytest.fixture
def test_user_admin(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="integration_admin",
        email="int_admin@example.com",
        full_name="Int Admin",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="IntegrationAdminModel",
        framework="TensorFlow",
        owner_id=user.id,
        status=ModelStatus.ACTIVE
    )
    db.add(model)
    db.commit()

    response = client.post("/api/auth/login", data={"username": "integration_admin", "password": "password123"})
    token = response.json()["access_token"]
    
    user_id = str(user.id)
    model_id = str(model.id)
    db.close()
    
    return {"user_id": user_id, "token": token, "model_id": model_id}

# A. Complete lifecycle (create -> list -> detail -> delete -> verify deleted)
def test_integration_complete_lifecycle(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine['model_id']
    
    # 1. Create
    payload = {
        "model_id": model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 100,
        "positive_prediction_count": 20,
        "negative_prediction_count": 80,
        "accuracy": 0.95
    }
    
    resp_create = client.post(f"/api/spam-models/{model_id}/observations", json=payload, headers=headers)
    assert resp_create.status_code == 201
    created_obs = resp_create.json()
    obs_id = created_obs["id"]
    assert created_obs["accuracy"] == 0.95
    assert created_obs["prediction_count"] == 100
    
    # 2. List
    resp_list = client.get(f"/api/spam-models/{model_id}/observations", headers=headers)
    assert resp_list.status_code == 200
    observations = resp_list.json()
    assert len(observations) == 1
    assert observations[0]["id"] == obs_id
    
    # 3. Detail
    resp_detail = client.get(f"/api/spam-models/{model_id}/observations/{obs_id}", headers=headers)
    assert resp_detail.status_code == 200
    assert resp_detail.json()["id"] == obs_id
    
    # 4. Delete
    resp_delete = client.delete(f"/api/spam-models/{model_id}/observations/{obs_id}", headers=headers)
    assert resp_delete.status_code == 204
    assert not resp_delete.content # Response body must be empty
    
    # 5. Verify deleted
    resp_detail_missing = client.get(f"/api/spam-models/{model_id}/observations/{obs_id}", headers=headers)
    assert resp_detail_missing.status_code == 404
    
    resp_list_empty = client.get(f"/api/spam-models/{model_id}/observations", headers=headers)
    assert resp_list_empty.status_code == 200
    assert len(resp_list_empty.json()) == 0

# B. Multi-user isolation
def test_integration_multi_user_isolation(client: TestClient, test_user_engine, test_user_viewer):
    eng_headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    view_headers = {"Authorization": f"Bearer {test_user_viewer['token']}"}
    eng_model_id = test_user_engine['model_id']
    
    # Engineer creates observation
    payload = {
        "model_id": eng_model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 50
    }
    resp_create = client.post(f"/api/spam-models/{eng_model_id}/observations", json=payload, headers=eng_headers)
    obs_id = resp_create.json()["id"]
    
    # Viewer tries to access it
    resp_list = client.get(f"/api/spam-models/{eng_model_id}/observations", headers=view_headers)
    assert resp_list.status_code == 404
    
    resp_detail = client.get(f"/api/spam-models/{eng_model_id}/observations/{obs_id}", headers=view_headers)
    assert resp_detail.status_code == 404
    
    # Note: VIEWER gets 403 on POST because of RBAC dependency evaluating first,
    # but if an Engineer tried, they would get 404 on the model.
    resp_delete = client.delete(f"/api/spam-models/{eng_model_id}/observations/{obs_id}", headers=view_headers)
    assert resp_delete.status_code == 403

def test_integration_multi_user_isolation_engineer(client: TestClient, test_user_engine, test_user_admin):
    # Engineer attempts to create on Admin's model
    eng_headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    admin_model_id = test_user_admin['model_id']
    
    payload = {
        "model_id": admin_model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 50
    }
    resp_create = client.post(f"/api/spam-models/{admin_model_id}/observations", json=payload, headers=eng_headers)
    assert resp_create.status_code == 404

# C. RBAC
def test_integration_rbac(client: TestClient, test_user_viewer, test_user_admin):
    view_headers = {"Authorization": f"Bearer {test_user_viewer['token']}"}
    admin_headers = {"Authorization": f"Bearer {test_user_admin['token']}"}
    
    view_model_id = test_user_viewer['model_id']
    admin_model_id = test_user_admin['model_id']
    
    payload_view = {
        "model_id": view_model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 10
    }
    
    # Viewer cannot create
    resp_view_create = client.post(f"/api/spam-models/{view_model_id}/observations", json=payload_view, headers=view_headers)
    assert resp_view_create.status_code == 403
    
    # Admin can create
    payload_admin = {
        "model_id": admin_model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 10
    }
    resp_admin_create = client.post(f"/api/spam-models/{admin_model_id}/observations", json=payload_admin, headers=admin_headers)
    assert resp_admin_create.status_code == 201
    
    # Admin can delete
    obs_id = resp_admin_create.json()["id"]
    resp_admin_delete = client.delete(f"/api/spam-models/{admin_model_id}/observations/{obs_id}", headers=admin_headers)
    assert resp_admin_delete.status_code == 204

# D. Authentication
def test_integration_authentication(client: TestClient):
    model_id = str(uuid.uuid4())
    obs_id = str(uuid.uuid4())
    
    assert client.get(f"/api/spam-models/{model_id}/observations").status_code == 401
    assert client.post(f"/api/spam-models/{model_id}/observations", json={}).status_code == 401
    assert client.get(f"/api/spam-models/{model_id}/observations/{obs_id}").status_code == 401
    assert client.delete(f"/api/spam-models/{model_id}/observations/{obs_id}").status_code == 401
    
    headers = {"Authorization": "Bearer invalid_token"}
    assert client.get(f"/api/spam-models/{model_id}/observations", headers=headers).status_code == 401

# E. Invalid UUIDs
def test_integration_invalid_uuids(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine['model_id']
    
    assert client.get("/api/spam-models/not-a-uuid/observations", headers=headers).status_code == 422
    assert client.get(f"/api/spam-models/{model_id}/observations/not-a-uuid", headers=headers).status_code == 422

# F. Invalid request bodies
def test_integration_invalid_request_bodies(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine['model_id']
    
    # Missing required field
    payload1 = {"prediction_count": 10}
    assert client.post(f"/api/spam-models/{model_id}/observations", json=payload1, headers=headers).status_code == 422
    
    # Negative prediction count
    payload2 = {
        "model_id": model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": -5
    }
    assert client.post(f"/api/spam-models/{model_id}/observations", json=payload2, headers=headers).status_code == 422
    
    # Inconsistent predictions
    payload3 = {
        "model_id": model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 10,
        "positive_prediction_count": 8,
        "negative_prediction_count": 5
    }
    assert client.post(f"/api/spam-models/{model_id}/observations", json=payload3, headers=headers).status_code == 422
    
    # Out of range metrics
    payload4 = {
        "model_id": model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 10,
        "accuracy": 1.5
    }
    assert client.post(f"/api/spam-models/{model_id}/observations", json=payload4, headers=headers).status_code == 422
    
    # URL / Body model_id mismatch
    payload5 = {
        "model_id": str(uuid.uuid4()),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 10
    }
    resp_mismatch = client.post(f"/api/spam-models/{model_id}/observations", json=payload5, headers=headers)
    assert resp_mismatch.status_code == 422

# G. Pagination limits
def test_integration_pagination_limits(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine['model_id']
    
    assert client.get(f"/api/spam-models/{model_id}/observations?skip=-1", headers=headers).status_code == 422
    assert client.get(f"/api/spam-models/{model_id}/observations?limit=0", headers=headers).status_code == 422
    assert client.get(f"/api/spam-models/{model_id}/observations?limit=101", headers=headers).status_code == 422

# H. Wrong model_id + valid observation_id
def test_integration_wrong_model_id_valid_observation(client: TestClient, test_user_engine, test_user_admin):
    eng_headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    eng_model_id = test_user_engine['model_id']
    
    payload = {
        "model_id": eng_model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 50
    }
    resp_create = client.post(f"/api/spam-models/{eng_model_id}/observations", json=payload, headers=eng_headers)
    obs_id = resp_create.json()["id"]
    
    # Try to access it with wrong model ID, but owned by Engineer
    # We create a second model for Engineer
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "integration_eng").first()
    model2 = RegisteredModel(
        id=uuid.uuid4(),
        name="IntegrationModel2",
        framework="PyTorch",
        owner_id=user.id,
        status=ModelStatus.ACTIVE
    )
    db.add(model2)
    db.commit()
    model2_id = str(model2.id)
    db.close()
    
    resp_wrong_model = client.get(f"/api/spam-models/{model2_id}/observations/{obs_id}", headers=eng_headers)
    assert resp_wrong_model.status_code == 404

# I. Empty list behavior
def test_integration_empty_list_behavior(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine['model_id']
    
    resp_list = client.get(f"/api/spam-models/{model_id}/observations", headers=headers)
    assert resp_list.status_code == 200
    assert resp_list.json() == []

# J. Multiple observations and pagination
def test_integration_multiple_observations_pagination(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine['model_id']
    
    for i in range(5):
        payload = {
            "model_id": model_id,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "prediction_count": i * 10
        }
        client.post(f"/api/spam-models/{model_id}/observations", json=payload, headers=headers)
        
    resp_list = client.get(f"/api/spam-models/{model_id}/observations?skip=1&limit=2", headers=headers)
    assert resp_list.status_code == 200
    data = resp_list.json()
    assert len(data) == 2

# K. Response schema verify
def test_integration_response_schema(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine['model_id']
    
    observed_at_str = datetime.now(timezone.utc).isoformat()
    payload = {
        "model_id": model_id,
        "observed_at": observed_at_str,
        "prediction_count": 100
    }
    
    resp = client.post(f"/api/spam-models/{model_id}/observations", json=payload, headers=headers)
    data = resp.json()
    
    assert "id" in data
    assert "model_id" in data
    assert "observed_at" in data
    assert "prediction_count" in data
    assert "accuracy" in data
    assert data["prediction_count"] == 100
    # ensure uuid serialized
    assert isinstance(data["id"], str)
    assert isinstance(data["model_id"], str)
