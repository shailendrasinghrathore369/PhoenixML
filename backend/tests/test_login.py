import pytest
from fastapi.testclient import TestClient
from tests.conftest import TestingSessionLocal
from app.users.models import User
from app.auth.security import get_password_hash

def setup_test_user(is_active: bool = True) -> dict:
    db = TestingSessionLocal()
    try:
        user = User(
            full_name="Login Test User",
            username="logintestuser" + ("_inactive" if not is_active else ""),
            email="login" + ("_inactive" if not is_active else "") + "@example.com",
            hashed_password=get_password_hash("loginpassword123"),
            is_active=is_active
        )
        db.add(user)
        db.commit()
        return {
            "email": user.email,
            "username": user.username,
            "password": "loginpassword123"
        }
    finally:
        db.close()

def test_successful_login(client: TestClient):
    user_data = setup_test_user()
    
    # Test login with email
    response = client.post("/api/auth/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "hashed_password" not in data
    assert "password" not in data

def test_successful_login_with_username(client: TestClient):
    user_data = setup_test_user()
    
    # Test login with username
    response = client.post("/api/auth/login", data={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_wrong_password(client: TestClient):
    user_data = setup_test_user()
    
    response = client.post("/api/auth/login", data={
        "username": user_data["email"],
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_non_existent_email(client: TestClient):
    response = client.post("/api/auth/login", data={
        "username": "doesnotexist@example.com",
        "password": "somepassword"
    })
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_inactive_user(client: TestClient):
    user_data = setup_test_user(is_active=False)
    
    response = client.post("/api/auth/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"

def test_last_login_updated(client: TestClient):
    user_data = setup_test_user()
    
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == user_data["email"]).first()
        initial_last_login = user.last_login
    finally:
        db.close()
        
    assert initial_last_login is None
    
    response = client.post("/api/auth/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    assert response.status_code == 200
    
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == user_data["email"]).first()
        assert user.last_login is not None
    finally:
        db.close()

def test_last_login_not_updated_on_failure(client: TestClient):
    user_data = setup_test_user()
    
    response = client.post("/api/auth/login", data={
        "username": user_data["email"],
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == user_data["email"]).first()
        assert user.last_login is None
    finally:
        db.close()
