"""
Explainability Analytical Layer for PhoenixML.

This module converts observed monitoring signals (health assessment, performance trends,
data drift, and concept drift) into structured, human-interpretable operational explanations.

IMPORTANT SCIENTIFIC LIMITATION:
This component provides evidence-based operational explanations from monitoring observations.
It does NOT establish formal mathematical or causal relationships. Statistical correlation,
feature distribution shift, or performance drops are reported as associated signals and
supporting evidence ("consistent with", "associated with", "observed signal"), NOT as definitive
causal proofs that a specific feature or drift caused model failure.

ARCHITECTURAL BOUNDARIES:
- Pure analytical component decoupled from persistence and web layers.
- NO dependencies on SQLAlchemy, database sessions, or ORM models.
- NO dependencies on FastAPI, HTTP routers, or web handlers.
- NO dependencies on MonitoringService or repository layers.
- DOES NOT generate maintenance recommendations (e.g. "retrain", "rollback").
  Recommendation generation is strictly reserved for the downstream AIMD engine.
"""

import math
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.monitoring.concept_drift import ConceptDriftAnalysis, ConceptDriftStatus
from app.monitoring.data_drift import DataDriftAnalysis
from app.monitoring.health import HealthAssessmentResult, HealthStatus
from app.monitoring.performance import PerformanceAnalysis, PerformanceStatus


class SignalCategory(str, Enum):
    HEALTH = "health"
    PERFORMANCE = "performance"
    CONCEPT_DRIFT = "concept_drift"
    DATA_DRIFT = "data_drift"


class SignalSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ExplanationSignal(BaseModel):
    """
    Individual analytical signal contributing to model explainability.
    """
    category: SignalCategory
    severity: SignalSeverity
    title: str
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)


class ExplainabilityInput(BaseModel):
    """
    Domain container aggregating upstream analytical outputs for explainability evaluation.
    """
    performance_analysis: Optional[PerformanceAnalysis] = None
    health_assessment: Optional[HealthAssessmentResult] = None
    data_drift_analysis: Optional[DataDriftAnalysis] = None
    concept_drift_analysis: Optional[ConceptDriftAnalysis] = None


class ExplanationResult(BaseModel):
    """
    Structured explainability output consumable by human operators and the downstream AIMD engine.
    """
    overall_summary: str
    signals: List[ExplanationSignal] = Field(default_factory=list)
    primary_factors: List[str] = Field(default_factory=list)
    health_score: Optional[float] = None
    health_status: Optional[str] = None
    has_explanation: bool = False
    confidence: str = "none"  # "high", "moderate", "low", "none"


class ExplainabilityAnalyzer:
    """
    Synthesizes monitoring, drift, and performance signals into a deterministic,
    evidence-based explanation of model condition without claiming causality.
    """

    @staticmethod
    def _is_valid_float(val: Any) -> bool:
        if val is None:
            return False
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            return False
        if math.isnan(val) or math.isinf(val):
            return False
        return True

    def _analyze_health(
        self, health: Optional[HealthAssessmentResult]
    ) -> Optional[ExplanationSignal]:
        if health is None:
            return None

        score = health.health_score if self._is_valid_float(health.health_score) else None
        status = health.health_status

        if status == HealthStatus.CRITICAL:
            score_str = f"{score:.1f}/100" if score is not None else "unavailable"
            return ExplanationSignal(
                category=SignalCategory.HEALTH,
                severity=SignalSeverity.CRITICAL,
                title="Critical Model Health Condition",
                description=f"Model health evaluated as critical (score: {score_str}), indicating substantial operational risk across weighted performance metrics.",
                evidence={
                    "health_score": score,
                    "health_status": status.value,
                    "available_metrics": health.available_metrics,
                    "normalized_metrics": health.normalized_metrics,
                },
            )
        elif status == HealthStatus.WARNING:
            score_str = f"{score:.1f}/100" if score is not None else "unavailable"
            return ExplanationSignal(
                category=SignalCategory.HEALTH,
                severity=SignalSeverity.WARNING,
                title="Model Health Warning",
                description=f"Model health evaluated in warning range (score: {score_str}), indicating moderate operational degradation across weighted metrics.",
                evidence={
                    "health_score": score,
                    "health_status": status.value,
                    "available_metrics": health.available_metrics,
                    "normalized_metrics": health.normalized_metrics,
                },
            )
        elif status == HealthStatus.HEALTHY:
            score_str = f"{score:.1f}/100" if score is not None else "unavailable"
            return ExplanationSignal(
                category=SignalCategory.HEALTH,
                severity=SignalSeverity.INFO,
                title="Healthy Model Condition",
                description=f"Model health score is healthy (score: {score_str}) within standard operational parameters.",
                evidence={
                    "health_score": score,
                    "health_status": status.value,
                    "available_metrics": health.available_metrics,
                    "normalized_metrics": health.normalized_metrics,
                },
            )
        elif status == HealthStatus.INSUFFICIENT_DATA:
            return ExplanationSignal(
                category=SignalCategory.HEALTH,
                severity=SignalSeverity.INFO,
                title="Insufficient Health Data",
                description="Insufficient monitoring observations available to compute an operational health score.",
                evidence={
                    "health_score": None,
                    "health_status": status.value,
                },
            )
        return None

    def _analyze_performance(
        self, perf: Optional[PerformanceAnalysis]
    ) -> Optional[ExplanationSignal]:
        if perf is None:
            return None

        status = perf.overall_status
        degraded = perf.degraded_metrics or []

        if status == PerformanceStatus.DEGRADED:
            metrics_summary = []
            metric_evidence = {}
            for m in degraded:
                trend = perf.metric_trends.get(m)
                if trend:
                    chg = trend.absolute_change if self._is_valid_float(trend.absolute_change) else 0.0
                    pct = trend.percentage_change if self._is_valid_float(trend.percentage_change) else None
                    if pct is not None:
                        metrics_summary.append(f"{m} ({chg:+.3f} abs, {pct:+.1f}%)")
                    else:
                        metrics_summary.append(f"{m} ({chg:+.3f} abs)")
                    metric_evidence[m] = {
                        "earliest": trend.earliest_value,
                        "latest": trend.latest_value,
                        "absolute_change": trend.absolute_change,
                        "percentage_change": trend.percentage_change,
                    }
                else:
                    metrics_summary.append(m)

            desc = f"Performance degradation observed in {len(degraded)} metric(s): {', '.join(metrics_summary)}."
            return ExplanationSignal(
                category=SignalCategory.PERFORMANCE,
                severity=SignalSeverity.CRITICAL,
                title="Performance Metric Degradation",
                description=desc,
                evidence={
                    "overall_status": status.value,
                    "degraded_metrics": degraded,
                    "metric_trends": metric_evidence,
                    "observation_count": perf.observation_count,
                },
            )
        elif status == PerformanceStatus.STABLE:
            return ExplanationSignal(
                category=SignalCategory.PERFORMANCE,
                severity=SignalSeverity.INFO,
                title="Stable Performance Trend",
                description="Performance metrics remain stable across observed monitoring intervals within configured threshold bounds.",
                evidence={
                    "overall_status": status.value,
                    "observation_count": perf.observation_count,
                },
            )
        elif status == PerformanceStatus.IMPROVING:
            return ExplanationSignal(
                category=SignalCategory.PERFORMANCE,
                severity=SignalSeverity.INFO,
                title="Improving Performance Trend",
                description="Model performance indicates an improving trend across monitored evaluation intervals.",
                evidence={
                    "overall_status": status.value,
                    "observation_count": perf.observation_count,
                },
            )
        elif status == PerformanceStatus.INSUFFICIENT_DATA:
            return ExplanationSignal(
                category=SignalCategory.PERFORMANCE,
                severity=SignalSeverity.INFO,
                title="Insufficient Performance Trend Data",
                description="Insufficient historical observations available to establish performance trends.",
                evidence={
                    "overall_status": status.value,
                    "observation_count": perf.observation_count,
                },
            )
        return None

    def _analyze_concept_drift(
        self, cd: Optional[ConceptDriftAnalysis]
    ) -> Optional[ExplanationSignal]:
        if cd is None:
            return None

        status = cd.status
        drifted = cd.drifted_metrics or []

        if status == ConceptDriftStatus.DRIFTED or cd.drift_detected is True:
            metric_details = []
            evidence_metrics = {}
            for res in cd.metric_results:
                if res.degraded:
                    chg_str = f"{res.absolute_change:+.3f}" if self._is_valid_float(res.absolute_change) else "N/A"
                    metric_details.append(f"{res.metric_name} (drop: {chg_str})")
                evidence_metrics[res.metric_name] = {
                    "reference_value": res.reference_value,
                    "current_value": res.current_value,
                    "absolute_change": res.absolute_change,
                    "degraded": res.degraded,
                }

            desc = f"Concept drift detected via performance drop between labeled windows in: {', '.join(metric_details)}."
            return ExplanationSignal(
                category=SignalCategory.CONCEPT_DRIFT,
                severity=SignalSeverity.CRITICAL,
                title="Concept Drift Detected",
                description=desc,
                evidence={
                    "drift_detected": True,
                    "status": status.value,
                    "drifted_metrics": drifted,
                    "reference_sample_size": cd.reference_sample_size,
                    "current_sample_size": cd.current_sample_size,
                    "metric_details": evidence_metrics,
                },
            )
        elif status == ConceptDriftStatus.NO_DRIFT or cd.drift_detected is False:
            return ExplanationSignal(
                category=SignalCategory.CONCEPT_DRIFT,
                severity=SignalSeverity.INFO,
                title="No Concept Drift Detected",
                description="Window-based performance comparison between reference and current windows shows no degradation exceeding configured threshold.",
                evidence={
                    "drift_detected": False,
                    "status": status.value,
                    "reference_sample_size": cd.reference_sample_size,
                    "current_sample_size": cd.current_sample_size,
                },
            )
        elif status == ConceptDriftStatus.INSUFFICIENT_DATA or cd.drift_detected is None:
            return ExplanationSignal(
                category=SignalCategory.CONCEPT_DRIFT,
                severity=SignalSeverity.INFO,
                title="Insufficient Concept Drift Data",
                description="Insufficient labeled sample observations available to evaluate concept drift.",
                evidence={
                    "drift_detected": None,
                    "status": status.value,
                    "reference_sample_size": cd.reference_sample_size,
                    "current_sample_size": cd.current_sample_size,
                },
            )
        return None

    def _analyze_data_drift(
        self, dd: Optional[DataDriftAnalysis]
    ) -> Optional[ExplanationSignal]:
        if dd is None:
            return None

        drifted = dd.drifted_features or []

        if dd.drift_detected is True:
            feat_details = []
            evidence_features = {}
            for res in dd.feature_results:
                if res.drift_detected:
                    ks_str = f"KS={res.ks_statistic:.3f}" if self._is_valid_float(res.ks_statistic) else "N/A"
                    p_str = f"p={res.p_value:.4f}" if self._is_valid_float(res.p_value) else "N/A"
                    feat_details.append(f"{res.feature_name} ({ks_str}, {p_str})")
                evidence_features[res.feature_name] = {
                    "ks_statistic": res.ks_statistic,
                    "p_value": res.p_value,
                    "drift_detected": res.drift_detected,
                    "status": res.status,
                }

            desc = f"Statistically significant distribution shift observed in {len(drifted)} feature(s): {', '.join(feat_details)}."
            return ExplanationSignal(
                category=SignalCategory.DATA_DRIFT,
                severity=SignalSeverity.WARNING,
                title="Input Data Drift Detected",
                description=desc,
                evidence={
                    "drift_detected": True,
                    "drifted_features": drifted,
                    "features_analyzed": dd.features_analyzed,
                    "feature_details": evidence_features,
                },
            )
        elif dd.drift_detected is False:
            return ExplanationSignal(
                category=SignalCategory.DATA_DRIFT,
                severity=SignalSeverity.INFO,
                title="No Data Drift Detected",
                description=f"All {dd.features_analyzed} analyzed feature distribution(s) remain stable without statistically significant drift.",
                evidence={
                    "drift_detected": False,
                    "features_analyzed": dd.features_analyzed,
                },
            )
        else:
            return ExplanationSignal(
                category=SignalCategory.DATA_DRIFT,
                severity=SignalSeverity.INFO,
                title="Insufficient Data Drift Data",
                description="Insufficient valid numeric observations available to evaluate data drift.",
                evidence={
                    "drift_detected": None,
                    "features_analyzed": dd.features_analyzed,
                },
            )

    def _compose_summary(
        self,
        health: Optional[HealthAssessmentResult],
        perf: Optional[PerformanceAnalysis],
        cd: Optional[ConceptDriftAnalysis],
        dd: Optional[DataDriftAnalysis],
        critical_signals: List[ExplanationSignal],
        warning_signals: List[ExplanationSignal],
    ) -> str:
        """
        Synthesizes an evidence-based, non-causal summary of model health and drift.
        Uses associative terminology ('accompanied by', 'consistent with', 'observed signals').
        """
        if not critical_signals and not warning_signals:
            score = health.health_score if (health and self._is_valid_float(health.health_score)) else None
            if score is not None:
                return f"Model is operating within normal parameters with healthy health score ({score:.1f}/100), stable performance trends, and no significant drift detected."
            return "Model is operating within normal parameters with stable performance and no significant drift detected."

        parts = []

        # Health aspect
        if health and health.health_status in (HealthStatus.CRITICAL, HealthStatus.WARNING):
            score = health.health_score if self._is_valid_float(health.health_score) else None
            score_txt = f" (health score: {score:.1f}/100)" if score is not None else ""
            parts.append(f"Model health is evaluated as {health.health_status.value}{score_txt}")

        # Performance aspect
        if perf and perf.overall_status == PerformanceStatus.DEGRADED:
            degraded_list = perf.degraded_metrics or []
            if degraded_list:
                parts.append(f"performance degradation observed in {', '.join(degraded_list)}")

        # Concept drift aspect
        if cd and (cd.status == ConceptDriftStatus.DRIFTED or cd.drift_detected is True):
            cd_list = cd.drifted_metrics or []
            if cd_list:
                parts.append(f"concept drift detected in {', '.join(cd_list)}")
            else:
                parts.append("concept drift detected across labeled monitoring windows")

        # Data drift aspect
        if dd and dd.drift_detected is True:
            drifted_feats = dd.drifted_features or []
            parts.append(f"statistically significant data drift observed in {len(drifted_feats)} feature(s) ({', '.join(drifted_feats)})")

        if len(parts) == 1:
            base = parts[0][0].upper() + parts[0][1:]
            return f"{base}. This observed signal is consistent with model degradation."

        main_clauses = ", accompanied by ".join(parts)
        main_clauses = main_clauses[0].upper() + main_clauses[1:]
        return f"{main_clauses}. These observed signals are consistent with model degradation."

    def explain(
        self,
        performance_analysis: Optional[PerformanceAnalysis] = None,
        health_assessment: Optional[HealthAssessmentResult] = None,
        data_drift_analysis: Optional[DataDriftAnalysis] = None,
        concept_drift_analysis: Optional[ConceptDriftAnalysis] = None,
        input_data: Optional[ExplainabilityInput] = None,
    ) -> ExplanationResult:
        """
        Executes explainability synthesis across available analytical signals.
        """
        if input_data is not None:
            perf = input_data.performance_analysis or performance_analysis
            health = input_data.health_assessment or health_assessment
            data_drift = input_data.data_drift_analysis or data_drift_analysis
            concept_drift = input_data.concept_drift_analysis or concept_drift_analysis
        else:
            perf = performance_analysis
            health = health_assessment
            data_drift = data_drift_analysis
            concept_drift = concept_drift_analysis

        # Evaluate individual signals
        raw_signals: List[Optional[ExplanationSignal]] = [
            self._analyze_health(health),
            self._analyze_performance(perf),
            self._analyze_concept_drift(concept_drift),
            self._analyze_data_drift(data_drift),
        ]
        signals = [s for s in raw_signals if s is not None]

        # Determine substantive evidence count
        health_substantive = bool(
            health and health.health_status and health.health_status != HealthStatus.INSUFFICIENT_DATA
        )
        perf_substantive = bool(
            perf and perf.overall_status and perf.overall_status != PerformanceStatus.INSUFFICIENT_DATA and perf.observation_count >= 2
        )
        cd_substantive = bool(
            concept_drift and concept_drift.status and concept_drift.status != ConceptDriftStatus.INSUFFICIENT_DATA and concept_drift.drift_detected is not None
        )
        dd_substantive = bool(
            data_drift and data_drift.drift_detected is not None and data_drift.features_analyzed > 0
        )

        substantive_count = sum([health_substantive, perf_substantive, cd_substantive, dd_substantive])

        # Handle zero substantive inputs / insufficient evidence
        if substantive_count == 0:
            return ExplanationResult(
                overall_summary="Insufficient monitoring evidence to determine the primary cause of degradation.",
                signals=signals,
                primary_factors=[],
                health_score=None,
                health_status=(health.health_status.value if (health and health.health_status) else None),
                has_explanation=False,
                confidence="none",
            )

        # Confidence calculation based on evaluated signal breadth
        if substantive_count >= 3:
            confidence = "high"
        elif substantive_count == 2:
            confidence = "moderate"
        else:
            confidence = "low"

        # Categorize signals by severity
        critical_signals = [s for s in signals if s.severity == SignalSeverity.CRITICAL]
        warning_signals = [s for s in signals if s.severity == SignalSeverity.WARNING]

        # Prioritize signals deterministically:
        # 1. Severity: CRITICAL (0), WARNING (1), INFO (2)
        # 2. Category: HEALTH (0), PERFORMANCE (1), CONCEPT_DRIFT (2), DATA_DRIFT (3)
        severity_rank = {SignalSeverity.CRITICAL: 0, SignalSeverity.WARNING: 1, SignalSeverity.INFO: 2}
        category_rank = {
            SignalCategory.HEALTH: 0,
            SignalCategory.PERFORMANCE: 1,
            SignalCategory.CONCEPT_DRIFT: 2,
            SignalCategory.DATA_DRIFT: 3,
        }

        signals.sort(key=lambda s: (severity_rank[s.severity], category_rank[s.category], s.title))

        # Extract primary factors driving degraded or warning condition
        primary_factors = []
        for s in signals:
            if s.severity in (SignalSeverity.CRITICAL, SignalSeverity.WARNING):
                if s.category == SignalCategory.HEALTH:
                    score = health.health_score if (health and self._is_valid_float(health.health_score)) else None
                    score_txt = f" ({score:.1f}/100)" if score is not None else ""
                    primary_factors.append(f"{s.title}{score_txt}")
                elif s.category == SignalCategory.PERFORMANCE:
                    degraded_list = perf.degraded_metrics if perf else []
                    primary_factors.append(f"Performance degradation in {', '.join(degraded_list)}")
                elif s.category == SignalCategory.CONCEPT_DRIFT:
                    cd_list = concept_drift.drifted_metrics if concept_drift else []
                    primary_factors.append(f"Concept drift detected in {', '.join(cd_list)}")
                elif s.category == SignalCategory.DATA_DRIFT:
                    dd_list = data_drift.drifted_features if data_drift else []
                    primary_factors.append(f"Data drift detected in {', '.join(dd_list)}")

        summary = self._compose_summary(health, perf, concept_drift, data_drift, critical_signals, warning_signals)

        h_score = health.health_score if (health and self._is_valid_float(health.health_score)) else None
        h_status = health.health_status.value if (health and health.health_status) else None

        return ExplanationResult(
            overall_summary=summary,
            signals=signals,
            primary_factors=primary_factors,
            health_score=h_score,
            health_status=h_status,
            has_explanation=True,
            confidence=confidence,
        )
