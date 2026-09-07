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
