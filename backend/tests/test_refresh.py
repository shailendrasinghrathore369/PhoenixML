import pytest
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from tests.conftest import TestingSessionLocal
from app.users.models import User
from app.auth.security import get_password_hash, create_access_token, create_refresh_token
from app.core.config import settings

def setup_test_user(is_active: bool = True) -> User:
    db = TestingSessionLocal()
    try:
        user = User(
            full_name="Refresh Test User",
            username="refreshtestuser" + ("_inactive" if not is_active else ""),
            email="refresh" + ("_inactive" if not is_active else "") + "@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=is_active
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        # Detach user from session to return safely
        db.expunge(user)
        return user
    finally:
        db.close()

def test_successful_refresh(client: TestClient):
    user = setup_test_user()
    refresh_token = create_refresh_token(subject=user.id)
    
    response = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "refresh_token" not in data

def test_access_token_rejected_as_refresh(client: TestClient):
    user = setup_test_user()
    access_token = create_access_token(subject=user.id)
    
    response = client.post("/api/auth/refresh", json={
        "refresh_token": access_token
    })
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_expired_refresh_token_rejected(client: TestClient):
    user = setup_test_user()
    refresh_token = create_refresh_token(subject=user.id, expires_delta=timedelta(minutes=-10))
    
    response = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"

def test_malformed_refresh_token_rejected(client: TestClient):
    response = client.post("/api/auth/refresh", json={
        "refresh_token": "not.a.valid.jwt"
    })
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_tampered_refresh_token_rejected(client: TestClient):
    user = setup_test_user()
    refresh_token = create_refresh_token(subject=user.id)
    # Alter the token string
    tampered_token = refresh_token[:-5] + "aaaaa"
    
    response = client.post("/api/auth/refresh", json={
        "refresh_token": tampered_token
    })
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_refresh_token_without_subject_rejected(client: TestClient):
    to_encode = {
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "type": "refresh",
        "iat": datetime.now(timezone.utc)
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    response = client.post("/api/auth/refresh", json={
        "refresh_token": encoded_jwt
    })
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_non_existent_user_rejected(client: TestClient):
    refresh_token = create_refresh_token(subject=uuid4())
    
    response = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_inactive_user_rejected(client: TestClient):
    user = setup_test_user(is_active=False)
    refresh_token = create_refresh_token(subject=user.id)
    
    response = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"
