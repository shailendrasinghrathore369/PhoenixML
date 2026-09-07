import uuid
from typing import Sequence, Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.monitoring_repository import MonitoringObservationRepository
from app.models.repository import RegisteredModelRepository
from app.models.monitoring_schemas import MonitoringObservationCreate
from app.models.models import MonitoringObservation

class MonitoringObservationService:
    def __init__(self, db: Session = Depends(get_db)):
        self.obs_repo = MonitoringObservationRepository(db)
        self.model_repo = RegisteredModelRepository(db)

    def _get_and_authorize_model(self, model_id: uuid.UUID, owner_id: Optional[uuid.UUID] = None):
        model = self.model_repo.get_by_id(model_id)
        if not model or (owner_id and model.owner_id != owner_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        return model

    def create_observation(
        self,
        model_id: uuid.UUID,
        observation_in: MonitoringObservationCreate,
        owner_id: Optional[uuid.UUID] = None
    ) -> MonitoringObservation:
        self._get_and_authorize_model(model_id, owner_id)
        
        # Ensure the observation is explicitly tied to the validated model_id
        if observation_in.model_id != model_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="URL model_id and body model_id do not match"
            )
            
        return self.obs_repo.create(observation_in)

    def get_observation(
        self,
        observation_id: uuid.UUID,
        owner_id: Optional[uuid.UUID] = None
    ) -> MonitoringObservation:
        obs = self.obs_repo.get_by_id(observation_id)
        if not obs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observation not found"
            )
        
        # Verify ownership via model
        model = self.model_repo.get_by_id(obs.model_id)
        if not model or (owner_id and model.owner_id != owner_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observation not found"
            )
            
        return obs

    def list_observations(
        self,
        model_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        owner_id: Optional[uuid.UUID] = None
    ) -> Sequence[MonitoringObservation]:
        self._get_and_authorize_model(model_id, owner_id)
        return self.obs_repo.list_by_model(model_id, skip=skip, limit=limit)

    def delete_observation(
        self,
        observation_id: uuid.UUID,
        owner_id: Optional[uuid.UUID] = None
    ) -> None:
        obs = self.get_observation(observation_id, owner_id=owner_id)
        self.obs_repo.delete(obs.id)
