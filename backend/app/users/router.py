from fastapi import APIRouter, Depends
from app.users.models import User
from app.users.schemas import UserRead, UserProfileUpdate, UserPasswordChange
from app.users.service import UserService
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/me", response_model=UserRead, summary="Get Current Profile")
def get_current_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the profile of the currently authenticated user.
    """
    return current_user

@router.patch("/me", response_model=UserRead, summary="Update Current Profile")
def update_current_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends()
):
    """
    Update the profile of the currently authenticated user.
    Only allows updating non-sensitive fields such as full_name, username, and email.
    """
    return user_service.update_profile(current_user, profile_data)

@router.post(
    "/me/change-password", 
    summary="Change Password",
    description="Changes the authenticated user's password. Note: Because the current architecture is stateless, existing JWT tokens remain valid until expiration."
)
def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends()
):
    """
    Change the password of the currently authenticated user.
    """
    return user_service.change_password(current_user, password_data)
