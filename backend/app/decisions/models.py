import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Any, TYPE_CHECKING

from sqlalchemy import String, DateTime, func, Enum, ForeignKey, Float, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.decisions.aimd import AIMDAction, AIMDPriority

if TYPE_CHECKING:
    from app.models.models import RegisteredModel


class ApprovalStatus(str, PyEnum):
    """
    Approval state for AIMD maintenance recommendations.
    Ensures human oversight before production deployment or rollback actions.
    """
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DecisionLog(Base):
    """
    SQLAlchemy model persisting AIMD recommendation history.
    Stores deterministic decision-support outputs and approval state for human review.
    """
    __tablename__ = "decision_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("registered_models.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    health_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    health_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    recommended_action: Mapped[AIMDAction] = mapped_column(
        Enum(AIMDAction, name="aimdaction", native_enum=True), nullable=False
    )
    priority: Mapped[AIMDPriority] = mapped_column(
        Enum(AIMDPriority, name="aimdpriority", native_enum=True), nullable=False
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supporting_signals: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approvalstatus", native_enum=True),
        default=ApprovalStatus.PENDING,
        nullable=False
    )

    # Relationships
    model: Mapped["RegisteredModel"] = relationship("RegisteredModel", back_populates="decisions")
