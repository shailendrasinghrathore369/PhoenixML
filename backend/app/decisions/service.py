"""
Service layer for orchestrating AIMD decision evaluations and persisting
the resulting recommendations into the DecisionLog audit repository.
"""

import uuid
from typing import Any, Dict, List, Optional, Sequence, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.dependencies import get_db
from app.decisions.aimd import (
    AIMDAction,
    AIMDPriority,
    AIMDConfidence,
    AIMDContext,
    AIMDRecommendation,
    AIMDDecisionEngine,
)
from app.decisions.models import ApprovalStatus, DecisionLog
from app.decisions.schemas import DecisionLogCreate, DecisionLogRead
from app.decisions.repository import DecisionLogRepository
from app.models.repository import RegisteredModelRepository
from app.monitoring.concept_drift import ConceptDriftAnalysis
from app.monitoring.data_drift import DataDriftAnalysis
from app.monitoring.health import HealthAssessmentResult
from app.monitoring.performance import PerformanceAnalysis
from app.monitoring.explainability import ExplanationResult


AIMD_CONFIDENCE_SCORE_MAP: Dict[AIMDConfidence, float] = {
    AIMDConfidence.HIGH: 0.9,
    AIMDConfidence.MODERATE: 0.7,
    AIMDConfidence.LOW: 0.4,
    AIMDConfidence.INSUFFICIENT: 0.1,
}


class DecisionService:
    """
    Orchestration service for evaluating AIMD decision-support recommendations
    and persisting them to the immutable DecisionLog repository.

    Adheres strictly to the human-in-the-loop invariant: all recommendations
    require human approval (`requires_human_approval=True`) and initialize
    with `approval_status=ApprovalStatus.PENDING`.
    """

    def __init__(
        self,
        db: Optional[Session] = Depends(get_db),
        repository: Optional[DecisionLogRepository] = None,
        engine: Optional[AIMDDecisionEngine] = None,
        model_repository: Optional[RegisteredModelRepository] = None,
    ):
        self.db = db
        self.repo = repository or (DecisionLogRepository(db) if db is not None else None)
        self.model_repo = model_repository or (RegisteredModelRepository(db) if db is not None else None)
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

    def get_decision(self, decision_id: uuid.UUID) -> Optional[DecisionLog]:
        """Retrieve a persisted decision log by ID."""
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")
        return self.repo.get_by_id(decision_id)

    def list_decisions_by_model(
        self, model_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[DecisionLog]:
        """List decision logs for a given model ordered by created_at DESC."""
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")
        return self.repo.list_by_model(model_id, skip=skip, limit=limit)

    def count_decisions_by_model(self, model_id: uuid.UUID) -> int:
        """Count total decisions logged for a given model."""
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")
        return self.repo.count_by_model(model_id)

    def delete_decision(self, decision_id: uuid.UUID) -> bool:
        """Delete a decision log by ID."""
        if self.repo is None:
            raise RuntimeError("DecisionLogRepository is not configured for DecisionService")
        return self.repo.delete(decision_id)


AIMDDecisionService = DecisionService
