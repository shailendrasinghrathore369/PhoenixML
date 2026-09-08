import uuid
from typing import List, Optional, Sequence
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.decisions.models import DecisionLog
from app.decisions.schemas import DecisionLogCreate


class DecisionLogRepository:
    """
    Persistence repository for AIMD DecisionLog entities.
    Handles CRUD operations without containing business logic or decision calculations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, decision_in: DecisionLogCreate) -> DecisionLog:
        created_at = decision_in.created_at or datetime.now(timezone.utc)
        db_decision = DecisionLog(
            model_id=decision_in.model_id,
            created_at=created_at,
            health_score=decision_in.health_score,
            health_status=decision_in.health_status,
            recommended_action=decision_in.recommended_action,
            priority=decision_in.priority,
            confidence=decision_in.confidence,
            rationale=decision_in.rationale,
            explanation=decision_in.explanation,
            supporting_signals=decision_in.supporting_signals,
            requires_human_approval=decision_in.requires_human_approval,
            approval_status=decision_in.approval_status,
        )
        self.db.add(db_decision)
        self.db.commit()
        self.db.refresh(db_decision)
        if db_decision.created_at.tzinfo is None:
            db_decision.created_at = db_decision.created_at.replace(tzinfo=timezone.utc)
        return db_decision

    def get_by_id(self, decision_id: uuid.UUID) -> Optional[DecisionLog]:
        db_decision = self.db.execute(
            select(DecisionLog).where(DecisionLog.id == decision_id)
        ).scalar_one_or_none()
        if db_decision and db_decision.created_at.tzinfo is None:
            db_decision.created_at = db_decision.created_at.replace(tzinfo=timezone.utc)
        return db_decision

    def list_by_model(
        self, model_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[DecisionLog]:
        results = list(
            self.db.execute(
                select(DecisionLog)
                .where(DecisionLog.model_id == model_id)
                .order_by(DecisionLog.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )
        for dec in results:
            if dec.created_at.tzinfo is None:
                dec.created_at = dec.created_at.replace(tzinfo=timezone.utc)
        return results

    def count_by_model(self, model_id: uuid.UUID) -> int:
        return (
            self.db.execute(
                select(func.count(DecisionLog.id)).where(DecisionLog.model_id == model_id)
            ).scalar()
            or 0
        )

    def delete(self, decision_id: uuid.UUID) -> bool:
        db_decision = self.get_by_id(decision_id)
        if db_decision:
            self.db.delete(db_decision)
            self.db.commit()
            return True
        return False
