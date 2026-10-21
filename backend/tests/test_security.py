import pytest
from datetime import timedelta
import jwt
from uuid import uuid4

from app.auth.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.auth.exceptions import InvalidTokenError, ExpiredTokenError
from app.core.config import settings

def test_password_hashing():
    password = "supersecretpassword"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_create_and_decode_access_token():
    subject = str(uuid4())
    token = create_access_token(subject=subject)
    
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == subject
    assert payload["type"] == "access"

def test_create_and_decode_refresh_token():
    subject = str(uuid4())
    token = create_refresh_token(subject=subject)
    
    payload = decode_token(token, expected_type="refresh")
    assert payload["sub"] == subject
    assert payload["type"] == "refresh"

def test_refresh_token_rejected_as_access_token():
    subject = str(uuid4())
    token = create_refresh_token(subject=subject)
    
    with pytest.raises(InvalidTokenError) as exc_info:
        decode_token(token, expected_type="access")
    
    assert "Invalid token type" in str(exc_info.value.detail)

def test_expired_token_rejected():
    subject = str(uuid4())
    # Create token that expired 1 minute ago
    token = create_access_token(subject=subject, expires_delta=timedelta(minutes=-1))
    
    with pytest.raises(ExpiredTokenError):
        decode_token(token, expected_type="access")

def test_invalid_token_rejected():
    with pytest.raises(InvalidTokenError):
        decode_token("invalid.token.string", expected_type="access")

def test_missing_subject_rejected():
    # Create a token manually without 'sub' claim
    to_encode = {
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    with pytest.raises(InvalidTokenError) as exc_info:
        decode_token(encoded_jwt, expected_type="access")
        
    assert "Token missing subject claim" in str(exc_info.value.detail)
