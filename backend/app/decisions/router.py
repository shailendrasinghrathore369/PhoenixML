"""
Decision History API Router for PhoenixML.
Provides authenticated, role-based read access to model maintenance recommendations and audit logs.
"""

import uuid
from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import require_roles
from app.users.models import User, UserRole
from app.decisions.schemas import (
    DecisionLogRead,
    DecisionHistoryResponse,
    DecisionApprovalUpdate,
)
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


@router.patch(
    "/{model_id}/decisions/{decision_id}/approval",
    response_model=DecisionLogRead,
    status_code=status.HTTP_200_OK,
    summary="Update decision approval status",
    description="Update the human approval status of a specific AIMD decision record (PENDING to APPROVED or REJECTED).",
)
def update_decision_approval(
    model_id: uuid.UUID,
    decision_id: uuid.UUID,
    approval_in: DecisionApprovalUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    service: DecisionService = Depends(get_decision_service),
) -> DecisionLogRead:
    return service.update_approval_status(
        model_id=model_id,
        decision_id=decision_id,
        approval_status=approval_in.approval_status,
        user=current_user,
        as_read_schema=True,
    )


@router.post(
    "/{model_id}/decisions/evaluate",
    response_model=DecisionLogRead,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger AIMD model evaluation",
    description="Trigger an AIMD decision-support evaluation for a registered model based on its monitoring observations. Synthesizes health assessment, performance trends, and explainability signals, persisting a new recommendation requiring human approval.",
)
@router.post(
    "/{model_id}/decisions",
    response_model=DecisionLogRead,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def trigger_model_evaluation(
    model_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER)),
    service: DecisionService = Depends(get_decision_service),
) -> DecisionLogRead:
    return service.evaluate_model(
        model_id=model_id,
        user=current_user,
        as_read_schema=True,
    )


