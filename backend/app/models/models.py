import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, func, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.users.models import User

class ModelStatus(str, PyEnum):
    DEVELOPMENT = 'DEVELOPMENT'
    ACTIVE = 'ACTIVE'
    ARCHIVED = 'ARCHIVED'

class RegisteredModel(Base):
    __tablename__ = 'registered_models'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    algorithm: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[ModelStatus] = mapped_column(Enum(ModelStatus), default=ModelStatus.DEVELOPMENT, nullable=False)
    
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Relationships
    owner: Mapped['User'] = relationship('User', back_populates='models')
    observations: Mapped[list['MonitoringObservation']] = relationship('MonitoringObservation', back_populates='model', cascade='all, delete-orphan')

class MonitoringObservation(Base):
    __tablename__ = 'monitoring_observations'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('registered_models.id', ondelete='CASCADE'), index=True, nullable=False
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    prediction_count: Mapped[int] = mapped_column(nullable=False, default=0)
    positive_prediction_count: Mapped[int] = mapped_column(nullable=False, default=0)
    negative_prediction_count: Mapped[int] = mapped_column(nullable=False, default=0)
    
    accuracy: Mapped[Optional[float]] = mapped_column(nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(nullable=True)
    f1_score: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Relationships
    model: Mapped['RegisteredModel'] = relationship('RegisteredModel', back_populates='observations')
