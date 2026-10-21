import uuid
from typing import Sequence, Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.repository import RegisteredModelRepository
from app.models.schemas import ModelCreate, ModelUpdate
from app.models.models import RegisteredModel

class RegisteredModelService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = RegisteredModelRepository(db)

    def create_model(self, model_in: ModelCreate, owner_id: uuid.UUID) -> RegisteredModel:
        return self.repo.create(model_in, owner_id=owner_id)

    def get_model(self, model_id: uuid.UUID, owner_id: Optional[uuid.UUID] = None) -> RegisteredModel:
        model = self.repo.get_by_id(model_id)
        if not model or (owner_id and model.owner_id != owner_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        return model

    def list_models(self, skip: int = 0, limit: int = 100, owner_id: Optional[uuid.UUID] = None) -> Sequence[RegisteredModel]:
        return self.repo.list(skip=skip, limit=limit, owner_id=owner_id)

    def update_model(self, model_id: uuid.UUID, model_in: ModelUpdate, owner_id: Optional[uuid.UUID] = None) -> RegisteredModel:
        model = self.get_model(model_id, owner_id=owner_id)
        return self.repo.update(model, model_in)

    def delete_model(self, model_id: uuid.UUID, owner_id: Optional[uuid.UUID] = None) -> None:
        model = self.get_model(model_id, owner_id=owner_id)
        self.repo.delete(model)
