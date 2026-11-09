import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.main import app
from app.users.models import User, UserRole
from app.auth.dependencies import require_roles, get_current_user
from app.auth.security import create_access_token, get_password_hash
from tests.conftest import TestingSessionLocal

# Temporary router attached to the main app specifically for this test file
rbac_test_router = APIRouter(prefix="/test-rbac")

@rbac_test_router.get("/admin-only")
def admin_only(user: User = Depends(require_roles(UserRole.ADMIN))):
    return {"message": f"Welcome Admin {user.username}"}

@rbac_test_router.get("/admin-and-ml")
def admin_and_ml(user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER))):
    return {"message": f"Welcome {user.role} {user.username}"}

@rbac_test_router.get("/viewer-only")
def viewer_only(user: User = Depends(require_roles(UserRole.VIEWER))):
    return {"message": f"Welcome Viewer {user.username}"}

# Attach router
app.include_router(rbac_test_router)

# Provide a client
client = TestClient(app)

def setup_test_user(role: UserRole) -> User:
    db = TestingSessionLocal()
    try:
        user = User(
            full_name=f"{role} User",
            username=f"{role.lower()}_user",
            email=f"{role.lower()}@example.com",
            hashed_password=get_password_hash("password123"),
            role=role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.expunge(user)
        return user
    finally:
        db.close()

def test_admin_can_access_admin_only_dependency():
    user = setup_test_user(UserRole.ADMIN)
    token = create_access_token(subject=user.id)
    
    response = client.get("/test-rbac/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == f"Welcome Admin {user.username}"

def test_ml_engineer_rejected_from_admin_only_dependency():
    user = setup_test_user(UserRole.ML_ENGINEER)
    token = create_access_token(subject=user.id)
    
    response = client.get("/test-rbac/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"

def test_viewer_rejected_from_admin_only_dependency():
    user = setup_test_user(UserRole.VIEWER)
    token = create_access_token(subject=user.id)
    
    response = client.get("/test-rbac/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"

def test_admin_accepted_by_admin_and_ml_dependency():
    user = setup_test_user(UserRole.ADMIN)
    token = create_access_token(subject=user.id)
    
    response = client.get("/test-rbac/admin-and-ml", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_ml_engineer_accepted_by_admin_and_ml_dependency():
    user = setup_test_user(UserRole.ML_ENGINEER)
    token = create_access_token(subject=user.id)
    
    response = client.get("/test-rbac/admin-and-ml", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_viewer_rejected_by_admin_and_ml_dependency():
    user = setup_test_user(UserRole.VIEWER)
    token = create_access_token(subject=user.id)
    
    response = client.get("/test-rbac/admin-and-ml", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"

def test_unauthenticated_requests_receive_401():
    response = client.get("/test-rbac/admin-only")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_authenticated_users_with_insufficient_permissions_receive_403():
    # A VIEWER trying to hit VIEWER-only works.
    viewer_user = setup_test_user(UserRole.VIEWER)
    token = create_access_token(subject=viewer_user.id)
    
    response = client.get("/test-rbac/viewer-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    # An ADMIN trying to hit VIEWER-only will fail (proving no false hierarchy)
    admin_user = setup_test_user(UserRole.ADMIN)
    admin_token = create_access_token(subject=admin_user.id)
    
    response = client.get("/test-rbac/viewer-only", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"
