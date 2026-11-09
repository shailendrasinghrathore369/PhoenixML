import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.users.models import UserRole


class UserBase(BaseModel):
    full_name: str = Field(..., max_length=255)
    email: EmailStr
    username: str = Field(..., max_length=255)
    role: UserRole = UserRole.VIEWER
    is_active: bool = True
    is_verified: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserInDBBase(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserRead(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, max_length=255)

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
