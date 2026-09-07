import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.models import ModelStatus

class ModelBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    framework: str = Field(..., min_length=1, max_length=50)
    algorithm: Optional[str] = Field(None, min_length=1, max_length=100)
    status: ModelStatus = Field(default=ModelStatus.DEVELOPMENT)

class ModelCreate(ModelBase):
    pass

class ModelUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    framework: Optional[str] = Field(None, min_length=1, max_length=50)
    algorithm: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[ModelStatus] = None

class ModelRead(ModelBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
