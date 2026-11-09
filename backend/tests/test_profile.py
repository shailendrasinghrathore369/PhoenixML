import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from tests.conftest import TestingSessionLocal
from app.users.models import User, UserRole
from app.auth.security import get_password_hash, create_access_token

def setup_test_user(suffix: str = "1", role: UserRole = UserRole.VIEWER) -> User:
    db = TestingSessionLocal()
    try:
        user = User(
            full_name=f"Profile Test User {suffix}",
            username=f"profiletestuser{suffix}",
            email=f"profile{suffix}@example.com",
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

def test_get_current_profile(client: TestClient):
    user = setup_test_user("A")
    token = create_access_token(subject=user.id)
    
    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert "hashed_password" not in data

def test_unauthenticated_user_cannot_get_profile(client: TestClient):
    response = client.get("/api/users/me")
    assert response.status_code == 401

def test_update_profile_full_name(client: TestClient):
    user = setup_test_user("B")
    token = create_access_token(subject=user.id)
    
    response = client.patch(
        "/api/users/me", 
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Updated Name"}
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"

def test_update_profile_username(client: TestClient):
    user = setup_test_user("C")
    token = create_access_token(subject=user.id)
    
    response = client.patch(
        "/api/users/me", 
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "newusername_c"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "newusername_c"

def test_update_profile_email(client: TestClient):
    user = setup_test_user("D")
    token = create_access_token(subject=user.id)
    
    response = client.patch(
        "/api/users/me", 
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "newemail_d@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "newemail_d@example.com"

def test_update_duplicate_username_rejected(client: TestClient):
    user1 = setup_test_user("E1")
    user2 = setup_test_user("E2")
    
    token = create_access_token(subject=user2.id)
    
    response = client.patch(
        "/api/users/me", 
        headers={"Authorization": f"Bearer {token}"},
        json={"username": user1.username}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already registered"

def test_update_duplicate_email_rejected(client: TestClient):
    user1 = setup_test_user("F1")
    user2 = setup_test_user("F2")
    
    token = create_access_token(subject=user2.id)
    
    response = client.patch(
        "/api/users/me", 
        headers={"Authorization": f"Bearer {token}"},
        json={"email": user1.email}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"

def test_update_protected_fields_ignored(client: TestClient):
    user = setup_test_user("G")
    token = create_access_token(subject=user.id)
    original_id = str(user.id)
    
    # Send all protected fields in the payload
    # The Pydantic schema will either strip them or reject them.
    # Since they aren't in UserProfileUpdate, they should be ignored.
    payload = {
        "full_name": "Hack Attempt",
        "role": UserRole.ADMIN,
        "is_active": False,
        "is_verified": True,
        "id": str(uuid4())
    }
    
    response = client.patch(
        "/api/users/me", 
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["full_name"] == "Hack Attempt"
    assert data["role"] == UserRole.VIEWER  # Unchanged
    assert data["is_active"] is True        # Unchanged
    assert data["is_verified"] is False     # Unchanged
    assert data["id"] == original_id        # Unchanged
    assert "hashed_password" not in data

def test_change_password_success(client: TestClient):
    user = setup_test_user("H")
    token = create_access_token(subject=user.id)
    
    # 1. Change password
    response = client.post(
        "/api/users/me/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "password123",
            "new_password": "new_secure_password"
        }
    )
    assert response.status_code == 200
    assert "Password updated successfully" in response.json()["message"]
    
    # 2. Login with old password fails
    login_old = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "password123"}
    )
    assert login_old.status_code == 401
    
    # 3. Login with new password succeeds
    login_new = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "new_secure_password"}
    )
    assert login_new.status_code == 200
    assert "access_token" in login_new.json()

def test_change_password_wrong_current_password(client: TestClient):
    user = setup_test_user("I")
    token = create_access_token(subject=user.id)
    
    response = client.post(
        "/api/users/me/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "wrongpassword",
            "new_password": "new_secure_password"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect current password"
