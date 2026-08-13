import pytest
from fastapi.testclient import TestClient

def test_successful_registration(client: TestClient):
    response = client.post("/api/auth/register", json={
        "full_name": "Test User",
        "username": "testuser",
        "email": "test@example.com",
        "password": "strongpassword123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "User registered successfully"
    assert "user" in data
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["role"] == "VIEWER"
    assert "id" in data["user"]
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]

def test_duplicate_username(client: TestClient):
    # First user
    client.post("/api/auth/register", json={
        "full_name": "Duplicate User 1",
        "username": "dupuser",
        "email": "first@example.com",
        "password": "password123"
    })
    # Second user with same username
    response = client.post("/api/auth/register", json={
        "full_name": "Duplicate User 2",
        "username": "dupuser",
        "email": "second@example.com",
        "password": "password123"
    })
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already registered"

def test_duplicate_email(client: TestClient):
    # First user
    client.post("/api/auth/register", json={
        "full_name": "User 1",
        "username": "user1",
        "email": "dup@example.com",
        "password": "password123"
    })
    # Second user with same email
    response = client.post("/api/auth/register", json={
        "full_name": "User 2",
        "username": "user2",
        "email": "dup@example.com",
        "password": "password123"
    })
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"

def test_invalid_email(client: TestClient):
    response = client.post("/api/auth/register", json={
        "full_name": "Test User",
        "username": "testuser",
        "email": "invalid-email",
        "password": "password123"
    })
    assert response.status_code == 422

def test_short_password(client: TestClient):
    response = client.post("/api/auth/register", json={
        "full_name": "Test User",
        "username": "testuser",
        "email": "test@example.com",
        "password": "short"
    })
    assert response.status_code == 422
