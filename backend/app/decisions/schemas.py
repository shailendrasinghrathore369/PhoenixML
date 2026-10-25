import uuid
import math
from datetime import datetime
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.decisions.aimd import AIMDAction, AIMDPriority
from app.decisions.models import ApprovalStatus
from app.monitoring.data_drift import (
    FeatureDistribution,
    DataDriftConfiguration,
)
from app.monitoring.concept_drift import (
    LabeledWindow,
    ConceptDriftConfiguration,
)


class DecisionLogBase(BaseModel):
    model_id: uuid.UUID
    health_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    health_status: Optional[str] = None
    recommended_action: AIMDAction
    priority: AIMDPriority
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    rationale: str
    explanation: Optional[str] = None
    supporting_signals: Optional[Any] = None
    requires_human_approval: bool = True
    approval_status: ApprovalStatus = ApprovalStatus.PENDING

    @field_validator("rationale")
    @classmethod
    def validate_rationale_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("rationale must be a non-empty string")
        return v

    @field_validator("health_score")
    @classmethod
    def validate_health_score(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError("health_score cannot be NaN or Infinite")
            if not (0.0 <= v <= 100.0):
                raise ValueError("health_score must be between 0.0 and 100.0")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError("confidence cannot be NaN or Infinite")
            if not (0.0 <= v <= 1.0):
                raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class DecisionLogCreate(DecisionLogBase):
    created_at: Optional[datetime] = None

    @field_validator("created_at")
    @classmethod
    def validate_created_at_timezone(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        return v


class DecisionLogRead(DecisionLogBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecisionHistoryResponse(BaseModel):
    model_id: uuid.UUID
    total: int
    skip: int
    limit: int
    items: List[DecisionLogRead]

    model_config = ConfigDict(from_attributes=True)


class DecisionApprovalUpdate(BaseModel):
    """
    Schema for updating the human approval status of a DecisionLog record.
    Strictly forbids extra fields to ensure analytical and diagnostic fields cannot be altered.
    """
    approval_status: ApprovalStatus

    model_config = ConfigDict(extra="forbid")


class DataDriftEvaluationInput(BaseModel):
    """
    Payload for evaluating feature/data drift in a runtime evaluation request.
    """
    features: List[FeatureDistribution]
    config: Optional[DataDriftConfiguration] = None


class ConceptDriftEvaluationInput(BaseModel):
    """
    Payload for evaluating concept drift across labeled monitoring windows.
    """
    reference_window: LabeledWindow
    current_window: LabeledWindow
    config: Optional[ConceptDriftConfiguration] = None


class ModelEvaluationRequest(BaseModel):
    """
    Optional payload for runtime model evaluation requests, providing
    feature distributions for data drift detection and/or labeled validation windows
    for concept drift detection, alongside optional operational context.
    """
    data_drift: Optional[DataDriftEvaluationInput] = None
    concept_drift: Optional[ConceptDriftEvaluationInput] = None
    features: Optional[List[FeatureDistribution]] = None
    reference_window: Optional[LabeledWindow] = None
    current_window: Optional[LabeledWindow] = None
    data_drift_config: Optional[DataDriftConfiguration] = None
    concept_drift_config: Optional[ConceptDriftConfiguration] = None
    historical_maintenance_context: Optional[Dict[str, Any]] = None
    prediction_confidence: Optional[float] = None



