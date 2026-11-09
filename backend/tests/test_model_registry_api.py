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

@pytest.fixture
def test_user_admin(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="admin_api_fixture",
        email="api_admin_fixture@example.com",
        full_name="API Admin Fixture",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post("/api/auth/login", data={"username": "admin_api_fixture", "password": "password123"})
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

def test_invalid_empty_name_is_rejected(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    payload = {
        "name": "   ",
        "framework": "scikit-learn"
    }
    response = client.post("/api/spam-models", json=payload, headers=headers)
    assert response.status_code == 422

def test_valid_lifecycle_transitions(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    
    # Created in DEVELOPMENT by default
    create_resp = client.post("/api/spam-models", json={"name": "LifeCycle", "framework": "PyTorch"}, headers=headers)
    assert create_resp.status_code == 201
    model_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "DEVELOPMENT"

    # Update to ACTIVE
    put_active = client.put(f"/api/spam-models/{model_id}", json={"status": "ACTIVE"}, headers=headers)
    assert put_active.status_code == 200
    assert put_active.json()["status"] == "ACTIVE"

    # Update to ARCHIVED
    put_archived = client.put(f"/api/spam-models/{model_id}", json={"status": "ARCHIVED"}, headers=headers)
    assert put_archived.status_code == 200
    assert put_archived.json()["status"] == "ARCHIVED"

def test_invalid_pagination(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    resp1 = client.get("/api/spam-models?skip=-1&limit=10", headers=headers)
    assert resp1.status_code == 422
    
    resp2 = client.get("/api/spam-models?skip=0&limit=0", headers=headers)
    assert resp2.status_code == 422
    
    resp3 = client.get("/api/spam-models?skip=0&limit=101", headers=headers)
    assert resp3.status_code == 422

def test_valid_pagination(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    client.post("/api/spam-models", json={"name": "Page1", "framework": "PT"}, headers=headers)
    client.post("/api/spam-models", json={"name": "Page2", "framework": "PT"}, headers=headers)
    
    resp = client.get("/api/spam-models?skip=0&limit=1", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_malformed_model_uuid(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    response = client.get("/api/spam-models/not-a-uuid", headers=headers)
    assert response.status_code == 422

def test_admin_write_access(client: TestClient):
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    # Create Admin User
    user = User(
        username="admin_api",
        email="api_admin@example.com",
        full_name="API Admin",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post("/api/auth/login", data={"username": "admin_api", "password": "password123"})
    token = response.json()["access_token"]
    db.close()
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"name": "AdminModel", "framework": "scikit-learn"}
    create_response = client.post("/api/spam-models", json=payload, headers=headers)
    assert create_response.status_code == 201

def test_viewer_read_access(client: TestClient, test_user_viewer):
    # To test viewer read access, we need the viewer to own a model.
    # Since viewer can't create, we insert one manually.
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    model = RegisteredModel(
        id=uuid.uuid4(),
        name="ViewerModel",
        framework="PT",
        owner_id=test_user_viewer["user_id"],
        status=ModelStatus.DEVELOPMENT
    )
    db.add(model)
    db.commit()
    
    headers = {"Authorization": f"Bearer {test_user_viewer['token']}"}
    resp = client.get("/api/spam-models", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert resp.json()[0]["name"] == "ViewerModel"
    db.close()

def test_admin_fleet_visibility_lists_models_across_multiple_engineers(client: TestClient, test_user_engine, test_user_other, test_user_admin):
    # Engineer 1 creates model
    headers1 = {"Authorization": f"Bearer {test_user_engine['token']}"}
    resp1 = client.post("/api/spam-models", json={"name": "FleetModel-Eng1", "framework": "PyTorch"}, headers=headers1)
    assert resp1.status_code == 201

    # Engineer 2 creates model
    headers2 = {"Authorization": f"Bearer {test_user_other['token']}"}
    resp2 = client.post("/api/spam-models", json={"name": "FleetModel-Eng2", "framework": "Scikit-Learn"}, headers=headers2)
    assert resp2.status_code == 201

    # Admin lists all models across fleet
    admin_headers = {"Authorization": f"Bearer {test_user_admin['token']}"}
    resp_admin = client.get("/api/spam-models", headers=admin_headers)
    assert resp_admin.status_code == 200
    names = [m["name"] for m in resp_admin.json()]
    assert "FleetModel-Eng1" in names
    assert "FleetModel-Eng2" in names

    # Verify owner_ids match respective creators
    model1 = next(m for m in resp_admin.json() if m["name"] == "FleetModel-Eng1")
    model2 = next(m for m in resp_admin.json() if m["name"] == "FleetModel-Eng2")
    assert model1["owner_id"] == str(test_user_engine["user_id"])
    assert model2["owner_id"] == str(test_user_other["user_id"])

def test_admin_can_retrieve_engineer_owned_model(client: TestClient, test_user_engine, test_user_admin):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    resp = client.post("/api/spam-models", json={"name": "EngModel-ToRetrieve", "framework": "PyTorch"}, headers=headers)
    model_id = resp.json()["id"]

    admin_headers = {"Authorization": f"Bearer {test_user_admin['token']}"}
    get_resp = client.get(f"/api/spam-models/{model_id}", headers=admin_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "EngModel-ToRetrieve"
    assert get_resp.json()["owner_id"] == str(test_user_engine["user_id"])

def test_admin_can_update_and_delete_engineer_owned_model(client: TestClient, test_user_engine, test_user_admin):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    resp = client.post("/api/spam-models", json={"name": "EngModel-ToMutate", "framework": "PyTorch"}, headers=headers)
    model_id = resp.json()["id"]

    admin_headers = {"Authorization": f"Bearer {test_user_admin['token']}"}

    # Admin updates model
    put_resp = client.put(
        f"/api/spam-models/{model_id}",
        json={"status": "ACTIVE", "description": "Admin updated description"},
        headers=admin_headers
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["status"] == "ACTIVE"
    assert put_resp.json()["description"] == "Admin updated description"

    # Admin deletes model
    del_resp = client.delete(f"/api/spam-models/{model_id}", headers=admin_headers)
    assert del_resp.status_code == 204

    # Verify deleted for both admin and engineer
    assert client.get(f"/api/spam-models/{model_id}", headers=admin_headers).status_code == 404
    assert client.get(f"/api/spam-models/{model_id}", headers=headers).status_code == 404

def test_ml_engineer_cannot_list_another_engineers_models(client: TestClient, test_user_engine, test_user_other):
    # Engineer 1 creates model
    headers1 = {"Authorization": f"Bearer {test_user_engine['token']}"}
    client.post("/api/spam-models", json={"name": "Exclusive-Eng1", "framework": "PyTorch"}, headers=headers1)

    # Engineer 2 creates model
    headers2 = {"Authorization": f"Bearer {test_user_other['token']}"}
    client.post("/api/spam-models", json={"name": "Exclusive-Eng2", "framework": "TensorFlow"}, headers=headers2)

    # Engineer 1 only sees their model
    resp1 = client.get("/api/spam-models", headers=headers1)
    assert resp1.status_code == 200
    names1 = [m["name"] for m in resp1.json()]
    assert "Exclusive-Eng1" in names1
    assert "Exclusive-Eng2" not in names1

    # Engineer 2 only sees their model
    resp2 = client.get("/api/spam-models", headers=headers2)
    assert resp2.status_code == 200
    names2 = [m["name"] for m in resp2.json()]
    assert "Exclusive-Eng2" in names2
    assert "Exclusive-Eng1" not in names2

def test_viewer_cannot_mutate_models(client: TestClient, test_user_engine, test_user_viewer):
    headers_eng = {"Authorization": f"Bearer {test_user_engine['token']}"}
    create_resp = client.post("/api/spam-models", json={"name": "Protected-Model", "framework": "PyTorch"}, headers=headers_eng)
    model_id = create_resp.json()["id"]

    headers_viewer = {"Authorization": f"Bearer {test_user_viewer['token']}"}

    # Viewer cannot create
    post_resp = client.post("/api/spam-models", json={"name": "Viewer-Attempt", "framework": "PyTorch"}, headers=headers_viewer)
    assert post_resp.status_code == 403

    # Viewer cannot update
    put_resp = client.put(f"/api/spam-models/{model_id}", json={"status": "ACTIVE"}, headers=headers_viewer)
    assert put_resp.status_code == 403

    # Viewer cannot delete
    del_resp = client.delete(f"/api/spam-models/{model_id}", headers=headers_viewer)
    assert del_resp.status_code == 403
