from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional
import uuid

from app.auth.dependencies import get_current_user, require_roles
from app.users.models import User, UserRole
from app.models.service import RegisteredModelService
from app.models.schemas import ModelCreate, ModelRead, ModelUpdate

router = APIRouter()

def _get_owner_filter(current_user: User) -> Optional[uuid.UUID]:
    """ADMIN has fleet-wide scope; other roles remain owner-scoped."""
    return None if current_user.role == UserRole.ADMIN else current_user.id

@router.post("", response_model=ModelRead, status_code=status.HTTP_201_CREATED)
def create_registered_model(
    model_in: ModelCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER)),
    service: RegisteredModelService = Depends()
):
    return service.create_model(model_in, owner_id=current_user.id)

@router.get("", response_model=List[ModelRead])
def list_registered_models(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    service: RegisteredModelService = Depends()
):
    return service.list_models(skip=skip, limit=limit, owner_id=_get_owner_filter(current_user))

@router.get("/{model_id}", response_model=ModelRead)
def get_registered_model(
    model_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    service: RegisteredModelService = Depends()
):
    return service.get_model(model_id, owner_id=_get_owner_filter(current_user))

@router.put("/{model_id}", response_model=ModelRead)
def update_registered_model(
    model_id: uuid.UUID,
    model_in: ModelUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER)),
    service: RegisteredModelService = Depends()
):
    return service.update_model(model_id, model_in, owner_id=_get_owner_filter(current_user))

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_registered_model(
    model_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER)),
    service: RegisteredModelService = Depends()
):
    service.delete_model(model_id, owner_id=_get_owner_filter(current_user))
