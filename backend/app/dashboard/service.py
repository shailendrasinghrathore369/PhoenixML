import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.exceptions import AuthorizationError
from app.users.models import User, UserRole
from app.models.models import RegisteredModel, ModelStatus, MonitoringObservation
from app.models.repository import RegisteredModelRepository
from app.models.monitoring_repository import MonitoringObservationRepository
from app.decisions.models import DecisionLog, ApprovalStatus
from app.decisions.aimd import AIMDPriority
from app.decisions.repository import DecisionLogRepository
from app.decisions.schemas import DecisionLogRead
from app.monitoring.health import HealthAssessor
from app.dashboard.schemas import (
    ModelSummary,
    MonitoringSummary,
    HealthSummary,
    DecisionSummary,
    ModelDashboardCard,
    DashboardOverviewResponse,
)


class DashboardService:
    """
    Aggregation and orchestration service for the PhoenixML Dashboard.
    Consolidates model registry status, monitoring telemetry, health assessments,
    and AIMD decision approvals with role-based access control.
    """

    def __init__(
        self,
        db: Session,
        model_repo: Optional[RegisteredModelRepository] = None,
        obs_repo: Optional[MonitoringObservationRepository] = None,
        decision_repo: Optional[DecisionLogRepository] = None,
    ):
        self.db = db
        self.model_repo = model_repo or RegisteredModelRepository(db)
        self.obs_repo = obs_repo or MonitoringObservationRepository(db)
        self.decision_repo = decision_repo or DecisionLogRepository(db)

    def get_dashboard_overview(
        self,
        user: User,
        model_id: Optional[uuid.UUID] = None,
    ) -> DashboardOverviewResponse:
        """
        Synthesize consolidated dashboard overview metrics.

        RBAC rules:
        - ADMIN: Retrieves global fleet overview across all registered models.
        - ML_ENGINEER / VIEWER: Retrieves overview scoped strictly to models owned by user.
        - If model_id is specified:
            - Validates model exists (404 Not Found if missing).
            - Validates ownership (403 Forbidden if not owned and user is not ADMIN).
            - Returns focused metrics for that specific model.
        """
        # 1. Scope and retrieve models in scope
        if model_id is not None:
            model = self.model_repo.get_by_id(model_id)
            if not model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Model not found",
                )
            if user.role != UserRole.ADMIN and model.owner_id != user.id:
                raise AuthorizationError(detail="Not authorized to access dashboard for this model")
            models: List[RegisteredModel] = [model]
            scope = "model"
        else:
            if user.role == UserRole.ADMIN:
                models = list(self.model_repo.list(skip=0, limit=1000))
                scope = "global"
            else:
                models = list(self.model_repo.list(skip=0, limit=1000, owner_id=user.id))
                scope = "user"

        # 2. Model inventory summary
        total_models = len(models)
        active_models = sum(1 for m in models if m.status == ModelStatus.ACTIVE)
        development_models = sum(1 for m in models if m.status == ModelStatus.DEVELOPMENT)
        archived_models = sum(1 for m in models if m.status == ModelStatus.ARCHIVED)

        models_summary = ModelSummary(
            total_models=total_models,
            active_models=active_models,
            development_models=development_models,
            archived_models=archived_models,
        )

        # 3. Process each model for observations, health, and decisions
        model_cards: List[ModelDashboardCard] = []
        all_decisions: List[DecisionLog] = []
        total_observations = 0
        latest_obs_time: Optional[datetime] = None
        latest_obs_overall: Optional[MonitoringObservation] = None

        health_assessor = HealthAssessor()

        for m in models:
            # Monitoring observations (newest first from repo)
            observations = self.obs_repo.list_by_model(m.id, skip=0, limit=100)
            obs_count = len(observations)
            total_observations += obs_count

            latest_m_obs = observations[0] if observations else None
            if latest_m_obs:
                if latest_obs_time is None or latest_m_obs.observed_at > latest_obs_time:
                    latest_obs_time = latest_m_obs.observed_at
                    latest_obs_overall = latest_m_obs

            # Decision logs (newest first from repo)
            decisions = self.decision_repo.list_by_model(m.id, skip=0, limit=100)
            all_decisions.extend(decisions)
            latest_m_dec = decisions[0] if decisions else None
            pending_m_count = sum(1 for d in decisions if d.approval_status == ApprovalStatus.PENDING)

            # Determine latest health metrics for model card
            if latest_m_dec and latest_m_dec.health_score is not None:
                h_score = latest_m_dec.health_score
                h_status = latest_m_dec.health_status
            elif latest_m_obs:
                health_res = health_assessor.assess(
                    accuracy=latest_m_obs.accuracy,
                    precision=latest_m_obs.precision,
                    recall=latest_m_obs.recall,
                    f1_score=latest_m_obs.f1_score,
                )
                h_score = health_res.health_score
                h_status = health_res.health_status.value if health_res.health_status else None
            else:
                h_score = None
                h_status = "insufficient_data"

            model_cards.append(
                ModelDashboardCard(
                    model_id=m.id,
                    name=m.name,
                    status=m.status.value if hasattr(m.status, "value") else str(m.status),
                    framework=m.framework,
                    owner_id=m.owner_id,
                    observation_count=obs_count,
                    latest_observation_at=latest_m_obs.observed_at if latest_m_obs else None,
                    latest_f1_score=latest_m_obs.f1_score if latest_m_obs else None,
                    latest_health_score=h_score,
                    latest_health_status=h_status,
                    latest_decision=DecisionLogRead.model_validate(latest_m_dec) if latest_m_dec else None,
                    pending_decisions_count=pending_m_count,
                )
            )

        # 4. Monitoring summary aggregation
        monitoring_summary = MonitoringSummary(
            total_observations=total_observations,
            latest_observation_at=latest_obs_time,
            latest_accuracy=latest_obs_overall.accuracy if latest_obs_overall else None,
            latest_precision=latest_obs_overall.precision if latest_obs_overall else None,
            latest_recall=latest_obs_overall.recall if latest_obs_overall else None,
            latest_f1=latest_obs_overall.f1_score if latest_obs_overall else None,
        )

        # 5. Health summary aggregation
        healthy_count = sum(1 for c in model_cards if c.latest_health_status == "healthy")
        warning_count = sum(1 for c in model_cards if c.latest_health_status == "warning")
        critical_count = sum(1 for c in model_cards if c.latest_health_status == "critical")
        insufficient_data_count = sum(
            1 for c in model_cards if c.latest_health_status in ("insufficient_data", None)
        )

        valid_health_scores = [c.latest_health_score for c in model_cards if c.latest_health_score is not None]
        avg_health = (
            round(sum(valid_health_scores) / len(valid_health_scores), 2)
            if valid_health_scores
            else None
        )

        if total_models == 0:
            system_status = "NO_MODELS"
        elif critical_count > 0:
            system_status = "CRITICAL"
        elif warning_count > 0:
            system_status = "WARNING"
        elif healthy_count > 0:
            system_status = "HEALTHY"
        else:
            system_status = "INSUFFICIENT_DATA"

        health_summary = HealthSummary(
            healthy_count=healthy_count,
            warning_count=warning_count,
            critical_count=critical_count,
            insufficient_data_count=insufficient_data_count,
            system_health_status=system_status,
            average_health_score=avg_health,
        )

        # 6. Decision and human-in-the-loop approval summary aggregation
        all_decisions.sort(key=lambda d: d.created_at, reverse=True)
        total_decisions = len(all_decisions)
        pending_approvals = sum(1 for d in all_decisions if d.approval_status == ApprovalStatus.PENDING)
        approved_count = sum(1 for d in all_decisions if d.approval_status == ApprovalStatus.APPROVED)
        rejected_count = sum(1 for d in all_decisions if d.approval_status == ApprovalStatus.REJECTED)
        critical_priority_count = sum(1 for d in all_decisions if d.priority == AIMDPriority.CRITICAL)

        recent_decisions = [DecisionLogRead.model_validate(d) for d in all_decisions[:5]]

        decision_summary = DecisionSummary(
            total_decisions=total_decisions,
            pending_approvals_count=pending_approvals,
            approved_count=approved_count,
            rejected_count=rejected_count,
            critical_priority_count=critical_priority_count,
            recent_decisions=recent_decisions,
        )

        return DashboardOverviewResponse(
            scope=scope,
            user_id=user.id,
            generated_at=datetime.now(timezone.utc),
            models_summary=models_summary,
            monitoring_summary=monitoring_summary,
            health_summary=health_summary,
            decision_summary=decision_summary,
            model_cards=model_cards,
        )
