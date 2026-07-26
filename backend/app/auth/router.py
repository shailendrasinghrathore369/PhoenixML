from fastapi import APIRouter, Depends, status
from app.auth.schemas import UserCreate, UserRegisterResponse
from app.auth.service import AuthService

router = APIRouter()

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, auth_service: AuthService = Depends()):
    return auth_service.register_user(user_in)
