import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.models import MonitoringObservation
from app.models.monitoring_schemas import MonitoringObservationCreate

class MonitoringObservationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, observation_in: MonitoringObservationCreate) -> MonitoringObservation:
        db_obs = MonitoringObservation(
            model_id=observation_in.model_id,
            observed_at=observation_in.observed_at,
            prediction_count=observation_in.prediction_count,
            positive_prediction_count=observation_in.positive_prediction_count,
            negative_prediction_count=observation_in.negative_prediction_count,
            accuracy=observation_in.accuracy,
            precision=observation_in.precision,
            recall=observation_in.recall,
            f1_score=observation_in.f1_score
        )
        self.db.add(db_obs)
        self.db.commit()
        self.db.refresh(db_obs)
        return db_obs

    def get_by_id(self, observation_id: uuid.UUID) -> Optional[MonitoringObservation]:
        return self.db.execute(
            select(MonitoringObservation).where(MonitoringObservation.id == observation_id)
        ).scalar_one_or_none()

    def list_by_model(self, model_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[MonitoringObservation]:
        return list(
            self.db.execute(
                select(MonitoringObservation)
                .where(MonitoringObservation.model_id == model_id)
                .order_by(MonitoringObservation.observed_at.desc())
                .offset(skip)
                .limit(limit)
            ).scalars().all()
        )

    def delete(self, observation_id: uuid.UUID) -> bool:
        db_obs = self.get_by_id(observation_id)
        if db_obs:
            self.db.delete(db_obs)
            self.db.commit()
            return True
        return False
