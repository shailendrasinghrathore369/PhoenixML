import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.auth.dependencies import require_roles
from app.users.models import User, UserRole
from app.dashboard.schemas import DashboardOverviewResponse
from app.dashboard.service import DashboardService

router = APIRouter()


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    """Dependency provider for DashboardService."""
    return DashboardService(db=db)


@router.get(
    "/dashboard",
    response_model=DashboardOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve consolidated dashboard overview",
    description=(
        "Retrieve consolidated system overview, model metrics, monitoring telemetry, "
        "health status distribution, and pending AIMD recommendation counts. "
        "Admins receive a fleet-wide overview; ML Engineers and Viewers receive metrics "
        "strictly scoped to their accessible models."
    ),
)
def get_dashboard(
    model_id: Optional[uuid.UUID] = Query(
        None,
        description="Optional model ID to scope dashboard metrics to a single registered model",
    ),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardOverviewResponse:
    return service.get_dashboard_overview(user=current_user, model_id=model_id)


@router.get(
    "/dashboard/{model_id}",
    response_model=DashboardOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve model-specific dashboard overview",
    description=(
        "Retrieve consolidated dashboard metrics for a single registered model. "
        "Enforces model existence and ownership policies."
    ),
)
def get_model_dashboard(
    model_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardOverviewResponse:
    return service.get_dashboard_overview(user=current_user, model_id=model_id)
