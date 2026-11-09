import math
from typing import Optional, List, Dict
from enum import Enum
from pydantic import BaseModel, Field

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    INSUFFICIENT_DATA = "insufficient_data"

class HealthScoreConfiguration(BaseModel):
    """
    Explicit, configurable PhoenixML project policy for health assessment.
    """
    f1_weight: float = Field(default=0.40, ge=0.0)
    precision_weight: float = Field(default=0.25, ge=0.0)
    recall_weight: float = Field(default=0.25, ge=0.0)
    accuracy_weight: float = Field(default=0.10, ge=0.0)
    
    healthy_threshold: float = Field(default=80.0, ge=0.0, le=100.0)
    warning_threshold: float = Field(default=60.0, ge=0.0, le=100.0)

    def validate_policy(self):
        total_weight = self.f1_weight + self.precision_weight + self.recall_weight + self.accuracy_weight
        if total_weight <= 0:
            raise ValueError("Total configured weights must be greater than 0")
        if self.healthy_threshold <= self.warning_threshold:
            raise ValueError("healthy_threshold must be strictly greater than warning_threshold")

class HealthAssessmentResult(BaseModel):
    health_score: Optional[float]
    health_status: HealthStatus
    normalized_metrics: Dict[str, float]
    effective_weights: Dict[str, float]
    available_metrics: List[str]

class HealthAssessor:
    """
    Determines the formal health score and status of a model observation.
    Implements the Proposed PhoenixML Health Score Policy.
    """
    def __init__(self, config: Optional[HealthScoreConfiguration] = None):
        self.config = config or HealthScoreConfiguration()
        self.config.validate_policy()

    def _safe_float(self, val: Optional[float]) -> Optional[float]:
        if val is None:
            return None
        if math.isnan(val) or math.isinf(val):
            return None
        return val

    def assess(self, accuracy: Optional[float], precision: Optional[float], recall: Optional[float], f1_score: Optional[float]) -> HealthAssessmentResult:
        metrics = {
            "accuracy": self._safe_float(accuracy),
            "precision": self._safe_float(precision),
            "recall": self._safe_float(recall),
            "f1_score": self._safe_float(f1_score)
        }
        
        base_weights = {
            "accuracy": self.config.accuracy_weight,
            "precision": self.config.precision_weight,
            "recall": self.config.recall_weight,
            "f1_score": self.config.f1_weight
        }
        
        available_metrics = [k for k, v in metrics.items() if v is not None]
        
        if not available_metrics:
            return HealthAssessmentResult(
                health_score=None,
                health_status=HealthStatus.INSUFFICIENT_DATA,
                normalized_metrics={},
                effective_weights={},
                available_metrics=[]
            )
            
        available_weight_sum = sum(base_weights[k] for k in available_metrics)
        
        # In the very extreme case where available metrics map to 0 total weight config
        if available_weight_sum == 0:
            return HealthAssessmentResult(
                health_score=None,
                health_status=HealthStatus.INSUFFICIENT_DATA,
                normalized_metrics={},
                effective_weights={},
                available_metrics=available_metrics
            )
            
        effective_weights = {k: base_weights[k] / available_weight_sum for k in available_metrics}
        normalized_metrics = {k: metrics[k] * 100.0 for k in available_metrics} # type: ignore
        
        health_score = sum(normalized_metrics[k] * effective_weights[k] for k in available_metrics)
        # Numerical safety clamp [0, 100] just in case
        health_score = max(0.0, min(100.0, health_score))
        
        if health_score >= self.config.healthy_threshold:
            status = HealthStatus.HEALTHY
        elif health_score >= self.config.warning_threshold:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL
            
        return HealthAssessmentResult(
            health_score=health_score,
            health_status=status,
            normalized_metrics=normalized_metrics,
            effective_weights=effective_weights,
            available_metrics=available_metrics
        )
