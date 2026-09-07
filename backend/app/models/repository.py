import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import RegisteredModel
from app.models.schemas import ModelCreate, ModelUpdate

class RegisteredModelRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, model_in: ModelCreate, owner_id: uuid.UUID) -> RegisteredModel:
        db_model = RegisteredModel(
            name=model_in.name,
            description=model_in.description,
            framework=model_in.framework,
            algorithm=model_in.algorithm,
            status=model_in.status,
            owner_id=owner_id
        )
        self.session.add(db_model)
        self.session.commit()
        self.session.refresh(db_model)
        return db_model

    def get_by_id(self, model_id: uuid.UUID) -> Optional[RegisteredModel]:
        return self.session.get(RegisteredModel, model_id)

    def list(self, skip: int = 0, limit: int = 100, owner_id: Optional[uuid.UUID] = None) -> Sequence[RegisteredModel]:
        stmt = select(RegisteredModel)
        if owner_id:
            stmt = stmt.where(RegisteredModel.owner_id == owner_id)
        stmt = stmt.offset(skip).limit(limit)
        return self.session.execute(stmt).scalars().all()

    def update(self, db_model: RegisteredModel, model_in: ModelUpdate) -> RegisteredModel:
        update_data = model_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_model, field, value)

        self.session.add(db_model)
        self.session.commit()
        self.session.refresh(db_model)
        return db_model

    def delete(self, db_model: RegisteredModel) -> None:
        self.session.delete(db_model)
        self.session.commit()
