import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.decisions.schemas import DecisionLogRead


class ModelSummary(BaseModel):
    """Aggregated model count summary by status."""
    total_models: int = 0
    active_models: int = 0
    development_models: int = 0
    archived_models: int = 0

    model_config = ConfigDict(from_attributes=True)


class MonitoringSummary(BaseModel):
    """Aggregated observation counts and latest observed metric benchmarks."""
    total_observations: int = 0
    latest_observation_at: Optional[datetime] = None
    latest_accuracy: Optional[float] = None
    latest_precision: Optional[float] = None
    latest_recall: Optional[float] = None
    latest_f1: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class HealthSummary(BaseModel):
    """Aggregated model health breakdown and overall fleet health status."""
    healthy_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    insufficient_data_count: int = 0
    system_health_status: str = "NO_MODELS"
    average_health_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class DecisionSummary(BaseModel):
    """
    Consolidated decision-support and human approval metrics.
    Highlights pending approval counts to enforce human-in-the-loop oversight.
    """
    total_decisions: int = 0
    pending_approvals_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    critical_priority_count: int = 0
    recent_decisions: List[DecisionLogRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ModelDashboardCard(BaseModel):
    """Consolidated summary card for an individual registered model on the dashboard."""
    model_id: uuid.UUID
    name: str
    status: str
    framework: str
    owner_id: uuid.UUID
    observation_count: int = 0
    latest_observation_at: Optional[datetime] = None
    latest_f1_score: Optional[float] = None
    latest_health_score: Optional[float] = None
    latest_health_status: Optional[str] = None
    latest_decision: Optional[DecisionLogRead] = None
    pending_decisions_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DashboardOverviewResponse(BaseModel):
    """
    Consolidated dashboard overview payload consumable by UI widgets and monitoring views.
    Includes model inventory, monitoring telemetry, health distribution, and pending AIMD approvals.
    """
    scope: str  # "global" (admin system-wide), "user" (scoped to owner), or "model" (single model)
    user_id: uuid.UUID
    generated_at: datetime
    models_summary: ModelSummary
    monitoring_summary: MonitoringSummary
    health_summary: HealthSummary
    decision_summary: DecisionSummary
    model_cards: List[ModelDashboardCard] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
