import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.users.models import User, UserRole
from app.models.models import RegisteredModel, ModelStatus
from tests.conftest import TestingSessionLocal
from app.auth.security import get_password_hash

@pytest.fixture
def test_user_engine(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="mon_ml_eng",
        email="mon_ml@example.com",
        full_name="Monitoring ML Eng",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ML_ENGINEER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="EngineersModel",
        framework="PT",
        owner_id=user.id,
        status=ModelStatus.ACTIVE
    )
    db.add(model)
    db.commit()

    response = client.post("/api/auth/login", data={"username": "mon_ml_eng", "password": "password123"})
    token = response.json()["access_token"]
    user_id = str(user.id)
    model_id_str = str(model.id)
    db.close()
    
    return {"user_id": user_id, "token": token, "model_id": model_id_str}

@pytest.fixture
def test_user_viewer(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="mon_viewer",
        email="mon_viewer@example.com",
        full_name="Monitoring Viewer",
        hashed_password=get_password_hash("password123"),
        role=UserRole.VIEWER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="ViewersModel",
        framework="PT",
        owner_id=user.id,
        status=ModelStatus.ACTIVE
    )
    db.add(model)
    db.commit()

    response = client.post("/api/auth/login", data={"username": "mon_viewer", "password": "password123"})
    token = response.json()["access_token"]
    user_id = str(user.id)
    model_id_str = str(model.id)
    db.close()
    
    return {"user_id": user_id, "token": token, "model_id": model_id_str}

@pytest.fixture
def test_user_admin(client: TestClient):
    db = TestingSessionLocal()
    user = User(
        username="mon_admin",
        email="mon_admin@example.com",
        full_name="Monitoring Admin",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="AdminsModel",
        framework="PT",
        owner_id=user.id,
        status=ModelStatus.ACTIVE
    )
    db.add(model)
    db.commit()

    response = client.post("/api/auth/login", data={"username": "mon_admin", "password": "password123"})
    token = response.json()["access_token"]
    user_id = str(user.id)
    model_id_str = str(model.id)
    db.close()
    
    return {"user_id": user_id, "token": token, "model_id": model_id_str}

def test_unauthenticated_access(client: TestClient):
    model_id = str(uuid.uuid4())
    obs_id = str(uuid.uuid4())
    
    resp_create = client.post(f"/api/spam-models/{model_id}/monitoring", json={})
    assert resp_create.status_code == 401

    resp_list = client.get(f"/api/spam-models/{model_id}/monitoring")
    assert resp_list.status_code == 401

    resp_get = client.get(f"/api/spam-models/{model_id}/monitoring/{obs_id}")
    assert resp_get.status_code == 401

    resp_delete = client.delete(f"/api/spam-models/{model_id}/monitoring/{obs_id}")
    assert resp_delete.status_code == 401

def test_viewer_rbac(client: TestClient, test_user_viewer):
    headers = {"Authorization": f"Bearer {test_user_viewer['token']}"}
    model_id = test_user_viewer['model_id']
    obs_id = str(uuid.uuid4())
    
    # Cannot create
    payload = {
        "model_id": model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 100
    }
    resp_create = client.post(f"/api/spam-models/{model_id}/monitoring", json=payload, headers=headers)
    assert resp_create.status_code == 403

    # Can list
    resp_list = client.get(f"/api/spam-models/{model_id}/monitoring", headers=headers)
    assert resp_list.status_code == 200

    # Cannot delete
    resp_delete = client.delete(f"/api/spam-models/{model_id}/monitoring/{obs_id}", headers=headers)
    assert resp_delete.status_code == 403

def test_lifecycle_and_rbac_engine(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine['model_id']
    
    payload = {
        "model_id": model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 100,
        "accuracy": 0.95
    }
    
    # Create
    resp_create = client.post(f"/api/spam-models/{model_id}/monitoring", json=payload, headers=headers)
    assert resp_create.status_code == 201
    obs = resp_create.json()
    assert "id" in obs
    assert obs["accuracy"] == 0.95
    assert obs["model_id"] == model_id
    obs_id = obs["id"]
    
    # List
    resp_list = client.get(f"/api/spam-models/{model_id}/monitoring", headers=headers)
    assert resp_list.status_code == 200
    assert len(resp_list.json()) == 1
    
    # Get Detail
    resp_detail = client.get(f"/api/spam-models/{model_id}/monitoring/{obs_id}", headers=headers)
    assert resp_detail.status_code == 200
    assert resp_detail.json()["id"] == obs_id
    
    # Delete
    resp_delete = client.delete(f"/api/spam-models/{model_id}/monitoring/{obs_id}", headers=headers)
    assert resp_delete.status_code == 204
    
    # Verify Deletion
    resp_verify = client.get(f"/api/spam-models/{model_id}/monitoring/{obs_id}", headers=headers)
    assert resp_verify.status_code == 404

def test_admin_rbac(client: TestClient, test_user_admin):
    headers = {"Authorization": f"Bearer {test_user_admin['token']}"}
    model_id = test_user_admin['model_id']
    
    payload = {
        "model_id": model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 50
    }
    
    resp_create = client.post(f"/api/spam-models/{model_id}/monitoring", json=payload, headers=headers)
    assert resp_create.status_code == 201
    obs_id = resp_create.json()["id"]

    resp_delete = client.delete(f"/api/spam-models/{model_id}/monitoring/{obs_id}", headers=headers)
    assert resp_delete.status_code == 204

def test_ownership_concealment(client: TestClient, test_user_engine, test_user_viewer):
    # Engineer creates observation on their model
    headers_eng = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine['model_id']
    
    payload = {
        "model_id": model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 10
    }
    resp_create = client.post(f"/api/spam-models/{model_id}/monitoring", json=payload, headers=headers_eng)
    obs_id = resp_create.json()["id"]
    
    # Viewer attempts to access Engineer's model/monitoring
    headers_viewer = {"Authorization": f"Bearer {test_user_viewer['token']}"}
    
    # Cannot list
    resp_list = client.get(f"/api/spam-models/{model_id}/monitoring", headers=headers_viewer)
    assert resp_list.status_code == 404 # 404 not 403 to prevent data leakage
    
    # Cannot get detail
    resp_get = client.get(f"/api/spam-models/{model_id}/monitoring/{obs_id}", headers=headers_viewer)
    assert resp_get.status_code == 404
    
    # Cannot create
    resp_create_other = client.post(f"/api/spam-models/{model_id}/monitoring", json=payload, headers=headers_viewer)
    assert resp_create_other.status_code == 403 # Wait, 403 for VIEWER, but since it checks model existence it should be 404
    # Wait, the Depends(require_roles) runs before the router body, so VIEWER gets 403 first on POST. This is acceptable.

def test_create_another_user_model_engine(client: TestClient, test_user_engine, test_user_admin):
    # Engineer tries to create on Admin's model
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    admin_model_id = test_user_admin['model_id']
    
    payload = {
        "model_id": admin_model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 10
    }
    resp_create = client.post(f"/api/spam-models/{admin_model_id}/monitoring", json=payload, headers=headers)
    assert resp_create.status_code == 404 # Masked

def test_validation_invalid_uuid(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    
    resp_list = client.get("/api/spam-models/invalid-uuid/monitoring", headers=headers)
    assert resp_list.status_code == 422
    
    resp_get = client.get(f"/api/spam-models/{test_user_engine['model_id']}/monitoring/invalid-uuid", headers=headers)
    assert resp_get.status_code == 422

def test_validation_pagination(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine['model_id']
    
    resp_skip = client.get(f"/api/spam-models/{model_id}/monitoring?skip=-1", headers=headers)
    assert resp_skip.status_code == 422
    
    resp_limit_low = client.get(f"/api/spam-models/{model_id}/monitoring?limit=0", headers=headers)
    assert resp_limit_low.status_code == 422
    
    resp_limit_high = client.get(f"/api/spam-models/{model_id}/monitoring?limit=101", headers=headers)
    assert resp_limit_high.status_code == 422

def test_validation_invalid_body(client: TestClient, test_user_engine):
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    model_id = test_user_engine['model_id']
    
    # Missing observed_at
    payload = {
        "model_id": model_id,
        "prediction_count": 10
    }
    resp_create = client.post(f"/api/spam-models/{model_id}/monitoring", json=payload, headers=headers)
    assert resp_create.status_code == 422

def test_architecture_router():
    # Verify the router is strictly HTTP/API focused
    with open("app/monitoring/router.py", "r") as f:
        content = f.read()
        
    assert "session.query(" not in content
    assert "db.execute(" not in content
    assert "MonitoringObservationRepository" not in content
    assert "MonitoringService" in content
    assert "require_roles" in content
    assert "Depends(" in content

def test_viewer_get_detail_success(client: TestClient, test_user_viewer):
    # 1. VIEWER successfully retrieves observation detail
    from tests.conftest import TestingSessionLocal
    from app.models.models import MonitoringObservation
    db = TestingSessionLocal()
    
    model_id = uuid.UUID(test_user_viewer['model_id'])
    obs = MonitoringObservation(
        id=uuid.uuid4(),
        model_id=model_id,
        observed_at=datetime.now(timezone.utc),
        prediction_count=200,
        accuracy=0.99
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    obs_id_str = str(obs.id)
    db.close()
    
    headers = {"Authorization": f"Bearer {test_user_viewer['token']}"}
    
    resp_detail = client.get(f"/api/spam-models/{model_id}/monitoring/{obs_id_str}", headers=headers)
    assert resp_detail.status_code == 200
    data = resp_detail.json()
    assert data["id"] == obs_id_str
    assert data["prediction_count"] == 200
    assert data["accuracy"] == 0.99

def test_admin_list_success(client: TestClient, test_user_admin):
    # 2. ADMIN successfully lists observations
    headers = {"Authorization": f"Bearer {test_user_admin['token']}"}
    model_id = test_user_admin['model_id']
    
    # Create
    payload = {
        "model_id": model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 50
    }
    client.post(f"/api/spam-models/{model_id}/monitoring", json=payload, headers=headers)
    
    resp_list = client.get(f"/api/spam-models/{model_id}/monitoring", headers=headers)
    assert resp_list.status_code == 200
    assert len(resp_list.json()) >= 1

def test_admin_detail_success(client: TestClient, test_user_admin):
    # 3. ADMIN successfully retrieves observation detail
    headers = {"Authorization": f"Bearer {test_user_admin['token']}"}
    model_id = test_user_admin['model_id']
    
    # Create
    payload = {
        "model_id": model_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "prediction_count": 50
    }
    resp_create = client.post(f"/api/spam-models/{model_id}/monitoring", json=payload, headers=headers)
    obs_id = resp_create.json()["id"]
    
    resp_detail = client.get(f"/api/spam-models/{model_id}/monitoring/{obs_id}", headers=headers)
    assert resp_detail.status_code == 200
    assert resp_detail.json()["id"] == obs_id

def test_nonexistent_model_returns_404(client: TestClient, test_user_engine):
    # 4. A genuinely nonexistent model UUID returns 404
    headers = {"Authorization": f"Bearer {test_user_engine['token']}"}
    nonexistent_model_id = str(uuid.uuid4())
    
    resp_list = client.get(f"/api/spam-models/{nonexistent_model_id}/monitoring", headers=headers)
    assert resp_list.status_code == 404
