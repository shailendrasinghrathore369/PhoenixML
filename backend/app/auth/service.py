from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.auth.repository import UserRepository
from app.auth.schemas import UserCreate, UserResponse, Token, RefreshTokenRequest, AccessTokenResponse
from app.db.dependencies import get_db
from app.auth.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.auth.exceptions import AuthenticationError, InactiveUserError, InvalidTokenError, ExpiredTokenError
from datetime import datetime, timezone

class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = UserRepository(db)

    def register_user(self, user_in: UserCreate) -> dict:
        if self.repo.get_user_by_username(user_in.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered"
            )
        if self.repo.get_user_by_email(user_in.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        user = self.repo.create_user(user_in)
        return {
            "message": "User registered successfully",
            "user": user
        }

    def authenticate_user(self, email_or_username: str, password: str) -> dict:
        user = self.repo.get_user_by_email(email_or_username)
        if not user:
            user = self.repo.get_user_by_username(email_or_username)
            
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect email or password")
            
        if not user.is_active:
            raise InactiveUserError("Inactive user")
            
        # Update last login
        self.repo.update_last_login(user, datetime.now(timezone.utc))
        
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_token(self, request: RefreshTokenRequest) -> dict:
        try:
            payload = decode_token(request.refresh_token, expected_type="refresh")
            user_id_str = payload.get("sub")
            from uuid import UUID
            user_id = UUID(user_id_str)
        except ExpiredTokenError:
            raise  # Let expired token error bubble up
        except Exception:
            raise InvalidTokenError("Could not validate credentials")
            
        user = self.repo.get_user_by_id(user_id)
        if not user:
            # Masking "User not found" to prevent information leakage
            raise InvalidTokenError("Could not validate credentials")
            
        if not user.is_active:
            raise InactiveUserError("Inactive user")
            
        new_access_token = create_access_token(subject=user.id)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    def logout_user(self) -> dict:
        """
        Processes a logout request.
        Note: The current PhoenixML authentication architecture uses stateless signed JWTs.
        There is currently no server-side token revocation system (e.g. no TokenBlacklist table).
        Therefore, this endpoint acknowledges the logout request, but the client must actively 
        discard their access and refresh tokens. Existing tokens technically remain valid until expiration.
        """
        return {
            "message": "Logout acknowledged. Client tokens should be discarded."
        }
