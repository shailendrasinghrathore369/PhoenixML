import pytest
from fastapi.testclient import TestClient

from app.users.models import User, UserRole
from tests.conftest import TestingSessionLocal
from app.auth.security import get_password_hash

@pytest.fixture
def integration_user(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="integration_ml",
        email="integration@example.com",
        full_name="Integration Engineer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post("/api/auth/login", data={"username": "integration_ml", "password": "password123"})
    token = response.json()["access_token"]
    db.close()
    
    return {"user_id": str(user.id), "token": token}

def test_full_model_registry_lifecycle_integration(client: TestClient, integration_user):
    """
    End-to-End Integration Test for the Model Registry API.
    Verifies the entire lifecycle (Create -> Get -> Update -> List -> Delete)
    through HTTP to guarantee operational readiness.
    """
    headers = {"Authorization": f"Bearer {integration_user['token']}"}
    
    # 1. Create Model
    create_payload = {
        "name": "Integration Model",
        "description": "A model for end-to-end testing",
        "framework": "TensorFlow",
        "algorithm": "Deep Learning"
    }
    create_resp = client.post("/api/spam-models", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    
    model_data = create_resp.json()
    model_id = model_data["id"]
    
    # Verify serialization
    assert model_data["name"] == "Integration Model"
    assert model_data["framework"] == "TensorFlow"
    assert model_data["status"] == "DEVELOPMENT"
    assert model_data["owner_id"] == integration_user["user_id"]
    assert "created_at" in model_data
    assert "updated_at" in model_data
    assert "password" not in model_data

    # 2. Get Model
    get_resp = client.get(f"/api/spam-models/{model_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == model_id

    # 3. Update Model
    update_payload = {
        "status": "ACTIVE",
        "description": "Updated integration model"
    }
    update_resp = client.put(f"/api/spam-models/{model_id}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "ACTIVE"
    assert update_resp.json()["description"] == "Updated integration model"

    # 4. List Models
    list_resp = client.get("/api/spam-models?skip=0&limit=100", headers=headers)
    assert list_resp.status_code == 200
    models_list = list_resp.json()
    assert isinstance(models_list, list)
    assert any(m["id"] == model_id for m in models_list)

    # 5. Delete Model
    delete_resp = client.delete(f"/api/spam-models/{model_id}", headers=headers)
    assert delete_resp.status_code == 204

    # 6. Verify Deletion (Get should return 404)
    get_deleted_resp = client.get(f"/api/spam-models/{model_id}", headers=headers)
    assert get_deleted_resp.status_code == 404
