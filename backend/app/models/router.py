from fastapi import APIRouter, Depends, status
from typing import List
import uuid

from app.auth.dependencies import get_current_user, require_roles
from app.users.models import User, UserRole
from app.models.service import RegisteredModelService
from app.models.schemas import ModelCreate, ModelRead, ModelUpdate

router = APIRouter()

@router.post("", response_model=ModelRead, status_code=status.HTTP_201_CREATED)
def create_registered_model(
    model_in: ModelCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER)),
    service: RegisteredModelService = Depends()
):
    return service.create_model(model_in, owner_id=current_user.id)

@router.get("", response_model=List[ModelRead])
def list_registered_models(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    service: RegisteredModelService = Depends()
):
    return service.list_models(skip=skip, limit=limit, owner_id=current_user.id)

@router.get("/{model_id}", response_model=ModelRead)
def get_registered_model(
    model_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    service: RegisteredModelService = Depends()
):
    return service.get_model(model_id, owner_id=current_user.id)

@router.put("/{model_id}", response_model=ModelRead)
def update_registered_model(
    model_id: uuid.UUID,
    model_in: ModelUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER)),
    service: RegisteredModelService = Depends()
):
    return service.update_model(model_id, model_in, owner_id=current_user.id)

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_registered_model(
    model_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER)),
    service: RegisteredModelService = Depends()
):
    service.delete_model(model_id, owner_id=current_user.id)
