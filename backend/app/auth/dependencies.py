from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from uuid import UUID

from app.auth.security import decode_token
from app.auth.exceptions import InvalidTokenError, InactiveUserError, AuthenticationError
from app.auth.service import AuthService
from app.auth.repository import UserRepository
from app.db.dependencies import get_db
from sqlalchemy.orm import Session
from app.users.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> User:
    try:
        payload = decode_token(token, expected_type="access")
        user_id_str = payload.get("sub")
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise InvalidTokenError("Invalid subject format")
            
        user = auth_service.repo.get_user_by_id(user_id)
        if not user:
            raise InvalidTokenError("User not found")
            
        if not user.is_active:
            raise InactiveUserError("Inactive user")
            
        return user
    except Exception as e:
        if isinstance(e, (AuthenticationError, InactiveUserError)):
            raise e
        raise InvalidTokenError()
