"""
Service layer for orchestrating AIMD decision evaluations, persisting
recommendations into the DecisionLog audit repository, and querying decision history.
"""

import uuid
from typing import Any, Dict, List, Optional, Sequence, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status

from app.db.dependencies import get_db
from app.auth.exceptions import AuthorizationError
from app.users.models import User, UserRole
from app.models.models import RegisteredModel
from app.decisions.aimd import (
    AIMDAction,
    AIMDPriority,
    AIMDConfidence,
    AIMDContext,
    AIMDRecommendation,
    AIMDDecisionEngine,
)
from app.decisions.models import ApprovalStatus, DecisionLog
from app.decisions.schemas import (
    DecisionLogCreate,
    DecisionLogRead,
    DecisionHistoryResponse,
)
from app.decisions.repository import DecisionLogRepository
from app.models.repository import RegisteredModelRepository
from app.models.monitoring_repository import MonitoringObservationRepository
from app.monitoring.concept_drift import ConceptDriftAnalysis
from app.monitoring.data_drift import DataDriftAnalysis
from app.monitoring.health import HealthAssessor, HealthAssessmentResult, HealthStatus
from app.monitoring.performance import PerformanceAnalyzer, PerformanceAnalysis, PerformanceStatus
from app.monitoring.explainability import ExplainabilityAnalyzer, ExplanationResult


AIMD_CONFIDENCE_SCORE_MAP: Dict[AIMDConfidence, float] = {
    AIMDConfidence.HIGH: 0.9,
    AIMDConfidence.MODERATE: 0.7,
    AIMDConfidence.LOW: 0.4,
    AIMDConfidence.INSUFFICIENT: 0.1,
}


class DecisionService:
    """
    Orchestration and query service for AIMD decision-support recommendations
    and persistent audit history.

    Adheres strictly to the human-in-the-loop invariant: all recommendations
    require human approval (`requires_human_approval=True`) and initialize
    with `approval_status=ApprovalStatus.PENDING`.

    Provides secure read/query capabilities with model ownership and RBAC enforcement.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        repository: Optional[DecisionLogRepository] = None,
        engine: Optional[AIMDDecisionEngine] = None,
        model_repository: Optional[RegisteredModelRepository] = None,
        obs_repository: Optional[MonitoringObservationRepository] = None,
    ):
        self.db = db
        self.repo = repository or (DecisionLogRepository(db) if db is not None else None)
        self.model_repo = model_repository or (RegisteredModelRepository(db) if db is not None else None)
        self.obs_repo = obs_repository or (MonitoringObservationRepository(db) if db is not None else None)
        self.engine = engine or AIMDDecisionEngine()

    @staticmethod
    def _map_confidence(
        recommendation_confidence: Any,
        override_confidence: Optional[float] = None,
        context_prediction_confidence: Optional[float] = None,
    ) -> Optional[float]:
        """
        Normalize AIMD recommendation confidence rating into a 0.0 - 1.0 float score.
        """
        if override_confidence is not None:
            return float(override_confidence)
        if isinstance(recommendation_confidence, (int, float)) and not isinstance(recommendation_confidence, bool):
            return float(recommendation_confidence)
        if isinstance(recommendation_confidence, AIMDConfidence):
            return AIMD_CONFIDENCE_SCORE_MAP.get(recommendation_confidence, 0.5)
        if isinstance(recommendation_confidence, str):
            try:
                return AIMD_CONFIDENCE_SCORE_MAP[AIMDConfidence(recommendation_confidence)]
            except (ValueError, KeyError):
                pass
        if context_prediction_confidence is not None:
            return float(context_prediction_confidence)
        return None

    def _get_and_authorize_model(
        self,
        model_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
    ) -> RegisteredModel:
        """
        Validate that the model exists and enforce ownership / RBAC policies.
        - Model non-existent -> 404 Not Found
        - User provided and is not owner (and not ADMIN) -> 403 Forbidden
        """
        if self.model_repo is None:
            raise RuntimeError("RegisteredModelRepository is not configured for DecisionService")

        model = self.model_repo.get_by_id(model_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found",
            )

        if user is not None:
            if isinstance(user, User):
                user_id = user.id
                is_admin = (user.role == UserRole.ADMIN)
            elif isinstance(user, uuid.UUID):
                user_id = user
                is_admin = False
            elif isinstance(user, str):
                try:
                    user_id = uuid.UUID(user)
                    is_admin = False
                except ValueError:
                    user_id = None
                    is_admin = False
            else:
                user_id = getattr(user, "id", None)
                is_admin = (getattr(user, "role", None) == UserRole.ADMIN)

            if not is_admin and model.owner_id != user_id:
                raise AuthorizationError(detail="Not authorized to access this model's decision history")

        return model

    def evaluate_and_persist(
        self,
        model_id: uuid.UUID,
        context: Optional[AIMDContext] = None,
        *,
        health_assessment: Optional[HealthAssessmentResult] = None,
        performance_analysis: Optional[PerformanceAnalysis] = None,
        data_drift_analysis: Optional[DataDriftAnalysis] = None,
        concept_drift_analysis: Optional[ConceptDriftAnalysis] = None,
        explainability_result: Optional[ExplanationResult] = None,
        prediction_confidence: Optional[float] = None,
        historical_maintenance_context: Optional[Dict[str, Any]] = None,
        explanation: Optional[str] = None,
        confidence: Optional[float] = None,
        supporting_signals: Optional[Any] = None,
        created_at: Optional[datetime] = None,
    ) -> DecisionLog:
        """
        Evaluate operational context using the AIMD Decision Engine and persist
        the generated recommendation into the DecisionLog repository.
        """
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")

        # 1. Build or normalize AIMD context
        if context is None:
            context = AIMDContext(
                health_assessment=health_assessment,
                performance_analysis=performance_analysis,
                data_drift_analysis=data_drift_analysis,
                concept_drift_analysis=concept_drift_analysis,
                explainability_result=explainability_result,
                prediction_confidence=prediction_confidence,
                historical_maintenance_context=historical_maintenance_context,
            )

        # 2. Invoke the AIMD Decision Engine (pure analytical logic, never duplicated here)
        recommendation: AIMDRecommendation = self.engine.evaluate(context)

        # 3. Resolve explanation from explainability layer or caller override
        resolved_explanation = explanation
        if resolved_explanation is None and context.explainability_result is not None:
            resolved_explanation = context.explainability_result.overall_summary

        # 4. Resolve confidence score (0.0 to 1.0)
        resolved_confidence = self._map_confidence(
            recommendation_confidence=recommendation.confidence,
            override_confidence=confidence,
            context_prediction_confidence=context.prediction_confidence,
        )

        # 5. Resolve supporting signals
        resolved_signals = (
            supporting_signals
            if supporting_signals is not None
            else list(recommendation.supporting_signals)
        )

        # 6. Construct DecisionLogCreate schema payload ensuring human-in-the-loop invariants
        decision_in = DecisionLogCreate(
            model_id=model_id,
            created_at=created_at,
            health_score=recommendation.health_score,
            health_status=recommendation.health_status,
            recommended_action=recommendation.action,
            priority=recommendation.priority,
            confidence=resolved_confidence,
            rationale=recommendation.rationale,
            explanation=resolved_explanation,
            supporting_signals=resolved_signals,
            requires_human_approval=True,
            approval_status=ApprovalStatus.PENDING,
        )

        # 7. Persist via repository with transaction failure safety
        try:
            return self.repo.create(decision_in)
        except Exception:
            if self.db is not None:
                self.db.rollback()
            raise

    def create_decision(
        self,
        model_id: uuid.UUID,
        context: Optional[AIMDContext] = None,
        **kwargs
    ) -> DecisionLog:
        """Alias for evaluate_and_persist."""
        return self.evaluate_and_persist(model_id=model_id, context=context, **kwargs)

    def evaluate_and_log(
        self,
        model_id: uuid.UUID,
        context: Optional[AIMDContext] = None,
        **kwargs
    ) -> DecisionLog:
        """Alias for evaluate_and_persist."""
        return self.evaluate_and_persist(model_id=model_id, context=context, **kwargs)

    def get_decision(
        self,
        decision_id: uuid.UUID,
        model_id: Optional[uuid.UUID] = None,
        user: Optional[Union[User, uuid.UUID]] = None,
        raise_if_not_found: bool = False,
        as_read_schema: bool = False,
    ) -> Optional[Union[DecisionLog, DecisionLogRead]]:
        """
        Retrieve a single decision log by decision ID.
        - If model_id is provided, enforces that the decision is associated with that model.
        - If user is provided, validates that the user is authorized for the model.
        - If raise_if_not_found is True (or model_id/user is provided and not found), raises 404.
        """
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")

        # When model_id is specified, authorize model access first
        if model_id is not None:
            self._get_and_authorize_model(model_id, user)
            db_decision = self.repo.get_by_id_and_model(decision_id, model_id)
        else:
            db_decision = self.repo.get_by_id(decision_id)
            if db_decision is not None and user is not None:
                self._get_and_authorize_model(db_decision.model_id, user)

        if db_decision is None:
            if model_id is not None or user is not None or raise_if_not_found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Decision not found",
                )
            return None

        if as_read_schema:
            return DecisionLogRead.model_validate(db_decision)
        return db_decision

    def get_decision_for_model(
        self,
        model_id: uuid.UUID,
        decision_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
        as_read_schema: bool = False,
    ) -> Union[DecisionLog, DecisionLogRead]:
        """
        Retrieve a single decision scoped to a specific model with authorization checks.
        Raises 404 if not found or belongs to another model.
        Raises 403 if unauthorized.
        """
        return self.get_decision(
            decision_id=decision_id,
            model_id=model_id,
            user=user,
            raise_if_not_found=True,
            as_read_schema=as_read_schema,
        )

    def list_decisions_for_model(
        self,
        model_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
        skip: int = 0,
        limit: int = 100,
        as_read_schema: bool = False,
    ) -> Sequence[Union[DecisionLog, DecisionLogRead]]:
        """
        List decisions for a specific registered model with ownership/RBAC validation,
        chronological ordering (newest first), and pagination.
        """
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")

        self._get_and_authorize_model(model_id, user)
        results = self.repo.list_by_model(model_id, skip=skip, limit=limit)

        if as_read_schema:
            return [DecisionLogRead.model_validate(d) for d in results]
        return results

    def list_decisions(
        self,
        model_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
        skip: int = 0,
        limit: int = 100,
        as_read_schema: bool = False,
    ) -> Sequence[Union[DecisionLog, DecisionLogRead]]:
        """Alias for list_decisions_for_model."""
        return self.list_decisions_for_model(
            model_id=model_id,
            user=user,
            skip=skip,
            limit=limit,
            as_read_schema=as_read_schema,
        )

    def list_decisions_by_model(
        self,
        model_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        user: Optional[Union[User, uuid.UUID]] = None,
        as_read_schema: bool = False,
    ) -> Sequence[Union[DecisionLog, DecisionLogRead]]:
        """List decision logs for a given model ordered by created_at DESC with optional authorization."""
        if user is not None:
            return self.list_decisions_for_model(
                model_id=model_id,
                user=user,
                skip=skip,
                limit=limit,
                as_read_schema=as_read_schema,
            )
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")
        results = self.repo.list_by_model(model_id, skip=skip, limit=limit)
        if as_read_schema:
            return [DecisionLogRead.model_validate(d) for d in results]
        return results

    def count_decisions_for_model(
        self,
        model_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
    ) -> int:
        """Count total decisions logged for a given model with authorization check."""
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")
        self._get_and_authorize_model(model_id, user)
        return self.repo.count_by_model(model_id)

    def count_decisions(
        self,
        model_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
    ) -> int:
        """Alias for count_decisions_for_model."""
        return self.count_decisions_for_model(model_id=model_id, user=user)

    def count_decisions_by_model(
        self,
        model_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
    ) -> int:
        """Count total decisions logged for a given model."""
        if user is not None:
            return self.count_decisions_for_model(model_id=model_id, user=user)
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")
        return self.repo.count_by_model(model_id)

    def get_decision_history(
        self,
        model_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> DecisionHistoryResponse:
        """
        Retrieve paginated decision history with total count and read schemas for a model.
        Ideal for dashboard and history API consumption.
        """
        self._get_and_authorize_model(model_id, user)
        total = self.repo.count_by_model(model_id)
        records = self.repo.list_by_model(model_id, skip=skip, limit=limit)
        items = [DecisionLogRead.model_validate(d) for d in records]
        return DecisionHistoryResponse(
            model_id=model_id,
            total=total,
            skip=skip,
            limit=limit,
            items=items,
        )

    def delete_decision(self, decision_id: uuid.UUID) -> bool:
        """Delete a decision log by ID."""
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")
        return self.repo.delete(decision_id)

    def update_approval_status(
        self,
        model_id: uuid.UUID,
        decision_id: uuid.UUID,
        approval_status: ApprovalStatus,
        user: Optional[Union[User, uuid.UUID]] = None,
        as_read_schema: bool = True,
    ) -> Union[DecisionLog, DecisionLogRead]:
        """
        Update the human approval status of a decision log record.

        Enforces:
        - Model existence (404 if not found).
        - Ownership and RBAC policies:
            - ADMIN can operate across all models.
            - ML_ENGINEER can only operate on models they own (403 if not owner).
            - VIEWER is not authorized to approve/reject (403 Forbidden under least-privilege policy).
        - Cross-model isolation: decision must belong to model_id (404 if not found).
        - State transition rules:
            - PENDING -> APPROVED (allowed)
            - PENDING -> REJECTED (allowed)
            - APPROVED -> APPROVED (idempotent 200)
            - REJECTED -> REJECTED (idempotent 200)
            - APPROVED -> REJECTED (rejected 400)
            - REJECTED -> APPROVED (rejected 400)
            - Finalized decisions cannot be re-opened to PENDING (rejected 400)
        - Preserves all analytical and diagnostic fields.
        """
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")

        # 1. Enforce RBAC: VIEWER cannot approve/reject
        user_role = getattr(user, "role", None)
        if user_role == UserRole.VIEWER or user_role == "VIEWER":
            raise AuthorizationError(detail="Viewers are not authorized to approve or reject decisions")

        # 2. Authorize model ownership (ADMIN allowed; ML_ENGINEER owner allowed; others 403; nonexistent model 404)
        model = self._get_and_authorize_model(model_id, user)

        # 3. Retrieve decision with row-level locking for update
        decision = self.repo.get_by_id_and_model_for_update(decision_id, model_id)
        if not decision:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Decision not found for this model",
            )

        # 4. Check state transitions
        if decision.approval_status == approval_status:
            # Idempotent: status already matches
            if as_read_schema:
                return DecisionLogRead.model_validate(decision)
            return decision

        if decision.approval_status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change approval status of a finalized decision (currently {decision.approval_status.value}).",
            )

        if approval_status == ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transition a decision back to PENDING.",
            )

        # 5. Apply update via repository
        updated_decision = self.repo.update_approval_status(
            decision_id=decision_id,
            model_id=model_id,
            approval_status=approval_status,
        )
        if not updated_decision:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Decision not found for this model",
            )

        if as_read_schema:
            return DecisionLogRead.model_validate(updated_decision)
        return updated_decision

    def approve_decision(
        self,
        model_id: uuid.UUID,
        decision_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
        as_read_schema: bool = True,
    ) -> Union[DecisionLog, DecisionLogRead]:
        """Convenience method to approve a decision."""
        return self.update_approval_status(
            model_id=model_id,
            decision_id=decision_id,
            approval_status=ApprovalStatus.APPROVED,
            user=user,
            as_read_schema=as_read_schema,
        )

    def reject_decision(
        self,
        model_id: uuid.UUID,
        decision_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
        as_read_schema: bool = True,
    ) -> Union[DecisionLog, DecisionLogRead]:
        """Convenience method to reject a decision."""
        return self.update_approval_status(
            model_id=model_id,
            decision_id=decision_id,
            approval_status=ApprovalStatus.REJECTED,
            user=user,
            as_read_schema=as_read_schema,
        )

    def evaluate_model(
        self,
        model_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
        as_read_schema: bool = True,
        historical_maintenance_context: Optional[Dict[str, Any]] = None,
        prediction_confidence: Optional[float] = None,
    ) -> Union[DecisionLog, DecisionLogRead]:
        """
        Evaluate operational monitoring observations for a registered model using the
        analytical layers (HealthAssessor, PerformanceAnalyzer, ExplainabilityAnalyzer)
        and the AIMD Decision Engine, persisting the recommendation to the DecisionLog repository.

        Enforces:
        - Model existence (404 Not Found if model does not exist)
        - RBAC and ownership:
            - ADMIN can evaluate any model
            - ML_ENGINEER can only evaluate models they own (403 Forbidden if not owner)
            - VIEWER cannot trigger evaluations (403 Forbidden under least-privilege policy)
        - Invariants:
            - Always initializes with requires_human_approval=True
            - Always initializes with approval_status=ApprovalStatus.PENDING
            - Pure analytical logic is delegated to existing domain assessors/analyzers/engine
        """
        # 1. Enforce RBAC: VIEWER cannot trigger evaluation
        user_role = getattr(user, "role", None)
        if user_role == UserRole.VIEWER or user_role == "VIEWER":
            raise AuthorizationError(detail="Viewers are not authorized to trigger model evaluation")

        # 2. Authorize model existence and ownership
        model = self._get_and_authorize_model(model_id, user)

        # 3. Verify observation repository is configured
        if self.obs_repo is None:
            raise RuntimeError("MonitoringObservationRepository is not configured for DecisionService")

        # 4. Fetch monitoring observations for model (ordered newest-first by repo)
        observations = self.obs_repo.list_by_model(model_id, skip=0, limit=1000)

        # 5. Synthesize analytical context
        if observations:
            # Sort chronologically (oldest to newest) for performance trend analysis
            sorted_obs = sorted(observations, key=lambda o: o.observed_at)
            latest_obs = sorted_obs[-1]

            health_assessor = HealthAssessor()
            health_result = health_assessor.assess(
                accuracy=latest_obs.accuracy,
                precision=latest_obs.precision,
                recall=latest_obs.recall,
                f1_score=latest_obs.f1_score,
            )

            perf_analyzer = PerformanceAnalyzer()
            perf_result = perf_analyzer.analyze(sorted_obs)

            explainer = ExplainabilityAnalyzer()
            expl_result = explainer.explain(
                performance_analysis=perf_result,
                health_assessment=health_result,
            )

            context = AIMDContext(
                health_assessment=health_result,
                performance_analysis=perf_result,
                explainability_result=expl_result,
                historical_maintenance_context=historical_maintenance_context,
                prediction_confidence=prediction_confidence,
            )
        else:
            # Handle zero observations: graceful insufficient data synthesis
            health_assessor = HealthAssessor()
            health_result = health_assessor.assess(None, None, None, None)

            perf_analyzer = PerformanceAnalyzer()
            perf_result = perf_analyzer.analyze([])

            explainer = ExplainabilityAnalyzer()
            expl_result = explainer.explain(
                performance_analysis=perf_result,
                health_assessment=health_result,
            )

            context = AIMDContext(
                health_assessment=health_result,
                performance_analysis=perf_result,
                explainability_result=expl_result,
                historical_maintenance_context=historical_maintenance_context,
                prediction_confidence=prediction_confidence,
            )

        # 6. Evaluate and persist recommendation into DecisionLog
        decision = self.evaluate_and_persist(model_id=model_id, context=context)

        # 7. Return schema or ORM model as requested
        if as_read_schema:
            return DecisionLogRead.model_validate(decision)
        return decision

    def trigger_evaluation(
        self,
        model_id: uuid.UUID,
        user: Optional[Union[User, uuid.UUID]] = None,
        as_read_schema: bool = True,
        historical_maintenance_context: Optional[Dict[str, Any]] = None,
        prediction_confidence: Optional[float] = None,
    ) -> Union[DecisionLog, DecisionLogRead]:
        """Convenience alias for evaluate_model."""
        return self.evaluate_model(
            model_id=model_id,
            user=user,
            as_read_schema=as_read_schema,
            historical_maintenance_context=historical_maintenance_context,
            prediction_confidence=prediction_confidence,
        )



AIMDDecisionService = DecisionService
 
 
def get_decision_service(db: Session = Depends(get_db)) -> DecisionService:
    """FastAPI dependency provider for DecisionService."""
    return DecisionService(db=db)
