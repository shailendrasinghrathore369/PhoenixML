"""
FastAPI Router for Real Reference Spam ML Model Inference and Telemetry Evaluation.

Endpoints:
- POST /api/spam-models/{model_id}/predict:
  Runs deterministic batch or single SMS classification using the loaded .joblib artifact.
- POST /api/spam-models/{model_id}/evaluate-telemetry:
  Evaluates real predictions against ground-truth labels and generates/records genuine
  monitoring observations in PhoenixML.
"""

import uuid
from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.auth.dependencies import require_roles
from app.users.models import User, UserRole
from app.models.service import RegisteredModelService
from app.models.inference_service import SpamInferenceService
from app.models.inference_schemas import (
    PredictionInput,
    BatchPredictionInput,
    BatchPredictionResponse,
    LabeledEvaluationInput,
    TelemetryEvaluationResponse,
)

router = APIRouter()


def _authorize_model_access(
    model_id: uuid.UUID,
    current_user: User,
    model_service: RegisteredModelService,
    write_access: bool = False,
):
    """
    Validate model existence and user authorization.
    ADMIN: unrestricted access across all models.
    ML_ENGINEER: restricted to owned models.
    VIEWER: read-only access (inference predict allowed, evaluation telemetry creation forbidden).
    """
    if write_access and current_user.role == UserRole.VIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewers are not authorized to perform this operation",
        )

    owner_check = None if current_user.role == UserRole.ADMIN else current_user.id
    return model_service.get_model(model_id, owner_id=owner_check)


@router.post(
    "/{model_id}/predict",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict spam/ham for one or more SMS text messages",
)
def predict_sms(
    model_id: uuid.UUID,
    payload: Union[BatchPredictionInput, PredictionInput],
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.VIEWER)),
    db: Session = Depends(get_db),
    model_service: RegisteredModelService = Depends(),
):
    """
    Execute deterministic inference on SMS messages using the trained reference model.
    """
    _authorize_model_access(model_id, current_user, model_service, write_access=False)

    inference_service = SpamInferenceService(db=db, model_id=model_id)

    texts = [payload.text] if isinstance(payload, PredictionInput) else payload.texts
    results = inference_service.predict_batch(texts)

    spam_count = sum(1 for r in results if r.is_spam)
    ham_count = len(results) - spam_count

    return BatchPredictionResponse(
        model_id=model_id,
        model_name=inference_service.model_name,
        model_version=inference_service.model_version,
        total_predictions=len(results),
        spam_count=spam_count,
        ham_count=ham_count,
        predictions=results,
    )


@router.post(
    "/{model_id}/evaluate-telemetry",
    response_model=TelemetryEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate model predictions against ground truth and record monitoring telemetry",
)
def evaluate_model_telemetry(
    model_id: uuid.UUID,
    payload: LabeledEvaluationInput,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ML_ENGINEER)),
    db: Session = Depends(get_db),
    model_service: RegisteredModelService = Depends(),
):
    """
    Evaluate actual model predictions against legitimate ground truth labels.
    Calculates genuine performance metrics and persists a MonitoringObservation into PhoenixML.
    """
    model = _authorize_model_access(model_id, current_user, model_service, write_access=True)

    inference_service = SpamInferenceService(db=db, model_id=model_id)

    texts = None
    y_true = None
    if payload.samples:
        texts = [s.text for s in payload.samples]
        y_true = [s.y_true for s in payload.samples]

    response = inference_service.evaluate_and_record_telemetry(
        model_id=model_id,
        owner_id=model.owner_id,
        texts=texts,
        y_true=y_true,
        use_reference_test_set=payload.use_reference_test_set,
        sample_limit=payload.sample_limit,
        record_observation=payload.record_monitoring_observation,
    )

    return response
