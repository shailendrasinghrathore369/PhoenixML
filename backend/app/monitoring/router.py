import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import require_roles
from app.users.models import User, UserRole
from app.models.monitoring_schemas import MonitoringObservationCreate, MonitoringObservationRead
from app.monitoring.service import MonitoringService

router = APIRouter()

@router.post("/{model_id}/monitoring", response_model=MonitoringObservationRead, status_code=status.HTTP_201_CREATED)
def create_observation(
    model_id: uuid.UUID,
    observation_in: MonitoringObservationCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER)),
    service: MonitoringService = Depends()
):
    # Pass authenticated user. Service enforces that model_id in payload aligns with the URL model_id.
    return service.create_observation(observation_in, model_id, current_user.id)

@router.get("/{model_id}/monitoring", response_model=List[MonitoringObservationRead])
def list_observations(
    model_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    service: MonitoringService = Depends()
):
    return service.list_observations(model_id, current_user.id, skip=skip, limit=limit)

@router.get("/{model_id}/monitoring/{observation_id}", response_model=MonitoringObservationRead)
def get_observation(
    model_id: uuid.UUID,
    observation_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    service: MonitoringService = Depends()
):
    # Service fetches observation and validates its model_id and owner_id.
    # To fully enforce URL structure, we must ensure observation.model_id == model_id from URL
    obs = service.get_observation(observation_id, current_user.id)
    from fastapi import HTTPException
    if obs.model_id != model_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found")
    return obs

@router.delete("/{model_id}/monitoring/{observation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_observation(
    model_id: uuid.UUID,
    observation_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER)),
    service: MonitoringService = Depends()
):
    # We must ensure the observation is actually attached to this model_id to prevent URL manipulation.
    obs = service.get_observation(observation_id, current_user.id)
    from fastapi import HTTPException
    if obs.model_id != model_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found")
        
    service.delete_observation(observation_id, current_user.id)
