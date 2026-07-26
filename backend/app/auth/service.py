from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.auth.repository import UserRepository
from app.auth.schemas import UserCreate, UserResponse
from app.db.dependencies import get_db

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
