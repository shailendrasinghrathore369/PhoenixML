import pytest
import uuid
from fastapi.testclient import TestClient

from app.users.models import User, UserRole
from app.models.models import RegisteredModel, ModelStatus
from tests.conftest import TestingSessionLocal
from app.auth.security import get_password_hash

@pytest.fixture
def test_user_engine(client: TestClient):
    db = TestingSessionLocal()
    # Create ML Engineer User
    user = User(
        username="ml_engineer_api",
        email="api_ml@example.com",
        full_name="API Engineer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Login to get token
    response = client.post("/api/auth/login", data={"username": "ml_engineer_api", "password": "password123"})
    token = response.json()["access_token"]
    db.close()
    
    return {"user_id": user.id, "token": token}

@pytest.fixture
def test_user_viewer(client: TestClient):
    db = TestingSessionLocal()
    # Create Viewer User
    user = User(
        username="viewer_api",
        email="api_viewer@example.com",
        full_name="API Viewer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.VIEWER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post("/api/auth/login", data={"username": "viewer_api", "password": "password123"})
    token = response.json()["access_token"]
    db.close()
    
    return {"user_id": user.id, "token": token}

@pytest.fixture
def test_user_other(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="other_api",
        email="other_api@example.com",
        full_name="Other Engineer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post("/api/auth/login", data={"username": "other_api", "password": "password123"})
    token = response.json()["access_token"]
    db.close()
    
    return {"user_id": user.id, "token": token}

def test_unauthenticated_user_cannot_create_model(client: TestClient):
    response = client.post("/api/spam-models", json={"name": "Test", "framework": "scikit-learn"})
    assert response.status_code == 401

def test_authenticated_user_can_create_model(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    payload = {
        "name": "MySpamModel",
        "description": "A very good model",
        "framework": "TensorFlow",
        "algorithm": "Neural Network",
        "status": "DEVELOPMENT"
    }
    response = client.post("/api/spam-models", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "MySpamModel"
    assert data["owner_id"] == str(test_user_engine["user_id"])
    assert "id" in data
    assert "password" not in data

def test_viewer_cannot_create_model(client: TestClient, test_user_viewer):
    headers = {"Authorization": f"Bearer {test_user_viewer['token']}"}
    payload = {"name": "TestModel", "framework": "scikit-learn"}
    response = client.post("/api/spam-models", json=payload, headers=headers)
    assert response.status_code == 403

def test_authenticated_user_can_retrieve_their_model(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    create_response = client.post("/api/spam-models", json={"name": "RetrieveMe", "framework": "PyTorch"}, headers=headers)
    model_id = create_response.json()["id"]

    response = client.get(f"/api/spam-models/{model_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "RetrieveMe"

def test_authenticated_user_can_list_models(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    client.post("/api/spam-models", json={"name": "ListMe1", "framework": "PyTorch"}, headers=headers)
    client.post("/api/spam-models", json={"name": "ListMe2", "framework": "PyTorch"}, headers=headers)

    response = client.get("/api/spam-models", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

def test_authenticated_user_can_update_their_model(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    create_response = client.post("/api/spam-models", json={"name": "UpdateMe", "framework": "PyTorch"}, headers=headers)
    model_id = create_response.json()["id"]

    response = client.put(
        f"/api/spam-models/{model_id}", 
        json={"status": "ACTIVE"}, 
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ACTIVE"

def test_authenticated_user_can_delete_their_model(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    create_response = client.post("/api/spam-models", json={"name": "DeleteMe", "framework": "PyTorch"}, headers=headers)
    model_id = create_response.json()["id"]

    response = client.delete(f"/api/spam-models/{model_id}", headers=headers)
    assert response.status_code == 204

    # Verify deleted
    get_resp = client.get(f"/api/spam-models/{model_id}", headers=headers)
    assert get_resp.status_code == 404

def test_invalid_model_data_is_rejected(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    payload = {
        "name": "InvalidStatusModel",
        "framework": "scikit-learn",
        "status": "NONEXISTENT_STATUS" # INVALID enum
    }
    response = client.post("/api/spam-models", json=payload, headers=headers)
    assert response.status_code == 422

def test_nonexistent_model_returns_appropriate_error(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    fake_id = uuid.uuid4()
    response = client.get(f"/api/spam-models/{fake_id}", headers=headers)
    assert response.status_code == 404

def test_user_cannot_access_another_users_model(client: TestClient, test_user_engine, test_user_other):
    # ML Engineer creates model
    headers1 = {"Authorization": f"Bearer {test_user_engine['token']}"}
    create_response = client.post("/api/spam-models", json={"name": "SecretModel", "framework": "PyTorch"}, headers=headers1)
    model_id = create_response.json()["id"]

    # Other Engineer tries to access it
    headers2 = {"Authorization": f"Bearer {test_user_other['token']}"}
    get_resp = client.get(f"/api/spam-models/{model_id}", headers=headers2)
    assert get_resp.status_code == 404 # Concealed via 404

    put_resp = client.put(f"/api/spam-models/{model_id}", json={"status": "ACTIVE"}, headers=headers2)
    assert put_resp.status_code == 404

    del_resp = client.delete(f"/api/spam-models/{model_id}", headers=headers2)
    assert del_resp.status_code == 404

