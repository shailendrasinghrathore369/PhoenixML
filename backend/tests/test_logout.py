import pytest
from fastapi.testclient import TestClient
from datetime import timedelta

from tests.conftest import TestingSessionLocal
from app.users.models import User
from app.auth.security import get_password_hash, create_access_token, create_refresh_token

def setup_test_user() -> User:
    db = TestingSessionLocal()
    try:
        user = User(
            full_name="Logout Test User",
            username="logouttestuser",
            email="logout@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.expunge(user)
        return user
    finally:
        db.close()

def test_successful_logout(client: TestClient):
    user = setup_test_user()
    access_token = create_access_token(subject=user.id)
    
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Logout acknowledged. Client tokens should be discarded."

def test_logout_missing_token(client: TestClient):
    response = client.post("/api/auth/logout")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_logout_invalid_token(client: TestClient):
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer invalid.jwt.token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_logout_expired_token(client: TestClient):
    user = setup_test_user()
    expired_access_token = create_access_token(
        subject=user.id, 
        expires_delta=timedelta(minutes=-10)
    )
    
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {expired_access_token}"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"

def test_logout_rejects_refresh_token(client: TestClient):
    user = setup_test_user()
    refresh_token = create_refresh_token(subject=user.id)
    
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )
    
    assert response.status_code == 401
    assert "Invalid token type" in response.json()["detail"]

def test_stateless_architecture_preserves_token_validity(client: TestClient):
    """
    This test proves that because we have a stateless JWT architecture without
    a token blacklist, a mathematically valid token STILL WORKS even after
    the logout endpoint is called. The client is explicitly responsible 
    for deleting the token on their end.
    """
    user = setup_test_user()
    access_token = create_access_token(subject=user.id)
    
    # 1. Call logout
    logout_response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert logout_response.status_code == 200
    
    # 2. Re-use the token (it should still technically work since we don't have a DB blacklist)
    # To test this, we can just call logout again or any protected endpoint
    reused_response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert reused_response.status_code == 200
