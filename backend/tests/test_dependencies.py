import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from fastapi import HTTPException

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token
from app.auth.exceptions import InvalidTokenError, InactiveUserError
from app.users.models import User
from app.auth.service import AuthService

def test_get_current_user_active():
    user_id = uuid4()
    token = create_access_token(subject=str(user_id))
    
    mock_auth_service = Mock(spec=AuthService)
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.is_active = True
    
    mock_auth_service.repo = Mock()
    mock_auth_service.repo.get_user_by_id.return_value = mock_user
    
    user = get_current_user(token, mock_auth_service)
    assert user == mock_user

def test_get_current_user_inactive():
    user_id = uuid4()
    token = create_access_token(subject=str(user_id))
    
    mock_auth_service = Mock(spec=AuthService)
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.is_active = False
    
    mock_auth_service.repo = Mock()
    mock_auth_service.repo.get_user_by_id.return_value = mock_user
    
    with pytest.raises(InactiveUserError):
        get_current_user(token, mock_auth_service)

def test_get_current_user_not_found():
    user_id = uuid4()
    token = create_access_token(subject=str(user_id))
    
    mock_auth_service = Mock(spec=AuthService)
    mock_auth_service.repo = Mock()
    mock_auth_service.repo.get_user_by_id.return_value = None
    
    with pytest.raises(InvalidTokenError) as exc_info:
        get_current_user(token, mock_auth_service)
        
    assert "User not found" in str(exc_info.value.detail)

def test_get_current_user_invalid_token():
    mock_auth_service = Mock(spec=AuthService)
    
    with pytest.raises(InvalidTokenError):
        get_current_user("invalid.token.string", mock_auth_service)
