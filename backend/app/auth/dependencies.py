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
from app.users.models import User, UserRole

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

def require_roles(*allowed_roles: "UserRole"):
    """
    Dependency factory for Role-Based Access Control (RBAC).
    Ensures the current user (authenticated via get_current_user) has one of the explicitly required roles.
    
    This purely handles authorization (checking role permission), 
    relying on get_current_user to handle authentication (who is the user).
    
    If the user lacks permission, it throws a 403 Forbidden.
    
    Usage:
    @router.get("/admin-endpoint")
    def admin_endpoint(user: User = Depends(require_roles(UserRole.ADMIN))):
        ...
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            from app.auth.exceptions import AuthorizationError
            raise AuthorizationError(detail="Insufficient permissions")
        return current_user
        
    return role_checker
