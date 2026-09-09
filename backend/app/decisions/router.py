"""
Decision History API Router for PhoenixML.
Provides authenticated, role-based read access to model maintenance recommendations and audit logs.
"""

import uuid
from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import require_roles
from app.users.models import User, UserRole
from app.decisions.schemas import DecisionLogRead, DecisionHistoryResponse
from app.decisions.service import DecisionService, get_decision_service

router = APIRouter()


@router.get(
    "/{model_id}/decisions",
    response_model=DecisionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="List decision history for a model",
    description="Retrieve paginated AIMD decision history for a registered model, ordered newest first with total count.",
)
def list_decisions(
    model_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Number of decision records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of decision records to return"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    service: DecisionService = Depends(get_decision_service),
) -> DecisionHistoryResponse:
    return service.get_decision_history(
        model_id=model_id,
        user=current_user,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{model_id}/decisions/{decision_id}",
    response_model=DecisionLogRead,
    status_code=status.HTTP_200_OK,
    summary="Retrieve single decision",
    description="Retrieve a specific AIMD decision record by ID ensuring it belongs to the specified model.",
)
def get_decision(
    model_id: uuid.UUID,
    decision_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    service: DecisionService = Depends(get_decision_service),
) -> DecisionLogRead:
    return service.get_decision_for_model(
        model_id=model_id,
        decision_id=decision_id,
        user=current_user,
        as_read_schema=True,
    )
