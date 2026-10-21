"""
Dashboard Module for PhoenixML.
Provides consolidated system activity, model inventory, monitoring telemetry,
health assessments, and AIMD recommendation overviews.
"""

from app.dashboard.schemas import (
    ModelSummary,
    MonitoringSummary,
    HealthSummary,
    DecisionSummary,
    ModelDashboardCard,
    DashboardOverviewResponse,
)
from app.dashboard.service import DashboardService
from app.dashboard.router import router

__all__ = [
    "ModelSummary",
    "MonitoringSummary",
    "HealthSummary",
    "DecisionSummary",
    "ModelDashboardCard",
    "DashboardOverviewResponse",
    "DashboardService",
    "router",
]
