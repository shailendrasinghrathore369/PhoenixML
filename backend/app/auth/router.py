from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.schemas import UserCreate, UserRegisterResponse, Token, RefreshTokenRequest, AccessTokenResponse
from app.auth.service import AuthService

router = APIRouter()

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, auth_service: AuthService = Depends()):
    return auth_service.register_user(user_in)

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends()
):
    return auth_service.authenticate_user(form_data.username, form_data.password)

@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends()
):
    return auth_service.refresh_token(request)
