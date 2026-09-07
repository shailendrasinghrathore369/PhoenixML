import math
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class PerformanceStatus(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADED = "degraded"
    INSUFFICIENT_DATA = "insufficient_data"

class MetricTrend(BaseModel):
    metric_name: str
    earliest_value: float
    latest_value: float
    absolute_change: float
    percentage_change: Optional[float]
    direction: PerformanceStatus

class PerformanceAnalysis(BaseModel):
    observation_count: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    metric_trends: Dict[str, MetricTrend]
    overall_status: PerformanceStatus
    degraded_metrics: List[str]
    summary: str

class PerformanceAnalyzer:
    """
    Analyzes model performance observations to detect trends over time.
    This module operates on domain data and performs deterministic mathematical comparisons.
    """
    
    def __init__(self, degradation_threshold: float = 0.05):
        """
        Initialize the analyzer with a degradation threshold policy.
        
        Args:
            degradation_threshold: The threshold for detecting meaningful degradation 
                or improvement. Default is 0.05 (5 percentage points).
        """
        self.degradation_threshold = degradation_threshold
        self.supported_metrics = ["accuracy", "precision", "recall", "f1_score"]

    def _sort_observations(self, observations: List[Any]) -> List[Any]:
        """Ensure chronological ordering by observed_at."""
        return sorted(observations, key=lambda obs: obs.observed_at)

    def _get_metric_value(self, obs: Any, metric: str) -> Optional[float]:
        value = getattr(obs, metric, None)
        if value is None:
            return None
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    def _compare_metric(self, earliest_value: float, latest_value: float, metric_name: str) -> MetricTrend:
        """Calculate the absolute and percentage change for a metric."""
        abs_change = latest_value - earliest_value
        pct_change = ((latest_value - earliest_value) / earliest_value * 100) if earliest_value != 0 else None
        
        if abs_change <= -self.degradation_threshold:
            direction = PerformanceStatus.DEGRADED
        elif abs_change >= self.degradation_threshold:
            direction = PerformanceStatus.IMPROVING
        else:
            direction = PerformanceStatus.STABLE
            
        return MetricTrend(
            metric_name=metric_name,
            earliest_value=earliest_value,
            latest_value=latest_value,
            absolute_change=abs_change,
            percentage_change=pct_change,
            direction=direction
        )

    def _classify_overall_status(self, metric_trends: Dict[str, MetricTrend]) -> PerformanceStatus:
        """Classify the overall performance status based on individual metric trends."""
        if not metric_trends:
            return PerformanceStatus.INSUFFICIENT_DATA
            
        has_degraded = any(c.direction == PerformanceStatus.DEGRADED for c in metric_trends.values())
        has_improving = any(c.direction == PerformanceStatus.IMPROVING for c in metric_trends.values())
        
        if has_degraded:
            return PerformanceStatus.DEGRADED
        elif has_improving:
            return PerformanceStatus.IMPROVING
        else:
            return PerformanceStatus.STABLE

    def analyze(self, observations: List[Any]) -> PerformanceAnalysis:
        if not observations or len(observations) < 2:
            return PerformanceAnalysis(
                observation_count=len(observations),
                start_time=observations[0].observed_at if observations else None,
                end_time=observations[0].observed_at if observations else None,
                metric_trends={},
                overall_status=PerformanceStatus.INSUFFICIENT_DATA,
                degraded_metrics=[],
                summary="Insufficient data to compute performance trends."
            )
            
        sorted_obs = self._sort_observations(observations)
        
        earliest = sorted_obs[0]
        latest = sorted_obs[-1]
        
        if earliest.observed_at == latest.observed_at:
             return PerformanceAnalysis(
                observation_count=len(observations),
                start_time=earliest.observed_at,
                end_time=latest.observed_at,
                metric_trends={},
                overall_status=PerformanceStatus.INSUFFICIENT_DATA,
                degraded_metrics=[],
                summary="Observations span zero time. Insufficient data for trends."
            )
        
        trends = {}
        degraded_metrics = []
        for metric in self.supported_metrics:
            earliest_val = self._get_metric_value(earliest, metric)
            latest_val = self._get_metric_value(latest, metric)
            
            if earliest_val is not None and latest_val is not None:
                trend = self._compare_metric(earliest_val, latest_val, metric)
                trends[metric] = trend
                if trend.direction == PerformanceStatus.DEGRADED:
                    degraded_metrics.append(metric)
                
        overall_status = self._classify_overall_status(trends)
        
        summary = f"Performance is {overall_status.value}."
        if degraded_metrics:
            summary += f" Degrading metrics: {', '.join(degraded_metrics)}."
        elif overall_status == PerformanceStatus.INSUFFICIENT_DATA:
            summary = "Insufficient valid metrics to compute performance trends."
            
        return PerformanceAnalysis(
            observation_count=len(observations),
            start_time=earliest.observed_at,
            end_time=latest.observed_at,
            metric_trends=trends,
            overall_status=overall_status,
            degraded_metrics=degraded_metrics,
            summary=summary
        )
