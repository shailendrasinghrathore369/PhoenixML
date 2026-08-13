from pydantic import BaseModel, EmailStr, Field, ConfigDict
import uuid
from datetime import datetime
from app.users.models import UserRole

class UserCreate(BaseModel):
    full_name: str = Field(..., max_length=255)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserRegisterResponse(BaseModel):
    message: str
    user: UserResponse
