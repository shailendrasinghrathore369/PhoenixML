import math
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel

class PerformanceTrend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    INSUFFICIENT_DATA = "insufficient_data"

class MetricChange(BaseModel):
    metric_name: str
    old_value: float
    new_value: float
    absolute_change: float
    relative_change: Optional[float]
    trend: PerformanceTrend

class PerformanceAnalysisResult(BaseModel):
    overall_trend: PerformanceTrend
    metric_changes: Dict[str, MetricChange]
    configurable_threshold_used: float

class PerformanceAnalyzer:
    """
    Analyzes model performance observations to detect trends over time.
    This module operates on domain data and performs deterministic mathematical comparisons.
    """
    
    def __init__(self, degradation_threshold: float = 0.05):
        """
        Initialize the analyzer with a provisional threshold.
        
        Args:
            degradation_threshold: The threshold for detecting meaningful degradation 
                or improvement. This is a PROVISIONAL implementation default (5%), 
                not an official PhoenixML requirement. It should be made configurable 
                by the integrating service.
        """
        self.degradation_threshold = degradation_threshold
        self.supported_metrics = ["accuracy", "precision", "recall", "f1_score"]

    def _sort_observations(self, observations: List[Any]) -> List[Any]:
        """A. Observation ordering"""
        # Ensure chronological ordering by observed_at
        return sorted(observations, key=lambda obs: obs.observed_at)

    def _get_metric_value(self, obs: Any, metric: str) -> Optional[float]:
        value = getattr(obs, metric, None)
        if value is None:
            return None
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    def _compare_metric(self, old_value: float, new_value: float, metric_name: str) -> MetricChange:
        """B & C. Metric comparison and calculation"""
        abs_change = new_value - old_value
        rel_change = abs_change / old_value if old_value != 0 else None
        
        if abs_change <= -self.degradation_threshold:
            trend = PerformanceTrend.DEGRADING
        elif abs_change >= self.degradation_threshold:
            trend = PerformanceTrend.IMPROVING
        else:
            trend = PerformanceTrend.STABLE
            
        return MetricChange(
            metric_name=metric_name,
            old_value=old_value,
            new_value=new_value,
            absolute_change=abs_change,
            relative_change=rel_change,
            trend=trend
        )

    def _classify_overall_trend(self, metric_changes: Dict[str, MetricChange]) -> PerformanceTrend:
        """D. Classification of the resulting performance trend"""
        if not metric_changes:
            return PerformanceTrend.INSUFFICIENT_DATA
            
        # Provisional policy: 
        # If ANY metric is degrading, overall is degrading.
        # Else if ANY metric is improving, overall is improving.
        # Else stable.
        # This policy is a provisional implementation default.
        has_degrading = any(c.trend == PerformanceTrend.DEGRADING for c in metric_changes.values())
        has_improving = any(c.trend == PerformanceTrend.IMPROVING for c in metric_changes.values())
        
        if has_degrading:
            return PerformanceTrend.DEGRADING
        elif has_improving:
            return PerformanceTrend.IMPROVING
        else:
            return PerformanceTrend.STABLE

    def analyze(self, observations: List[Any]) -> PerformanceAnalysisResult:
        if not observations or len(observations) < 2:
            return PerformanceAnalysisResult(
                overall_trend=PerformanceTrend.INSUFFICIENT_DATA,
                metric_changes={},
                configurable_threshold_used=self.degradation_threshold
            )
            
        sorted_obs = self._sort_observations(observations)
        
        oldest = sorted_obs[0]
        newest = sorted_obs[-1]
        
        if oldest.observed_at == newest.observed_at:
             return PerformanceAnalysisResult(
                overall_trend=PerformanceTrend.INSUFFICIENT_DATA,
                metric_changes={},
                configurable_threshold_used=self.degradation_threshold
            )
        
        changes = {}
        for metric in self.supported_metrics:
            old_val = self._get_metric_value(oldest, metric)
            new_val = self._get_metric_value(newest, metric)
            
            if old_val is not None and new_val is not None:
                changes[metric] = self._compare_metric(old_val, new_val, metric)
                
        overall_trend = self._classify_overall_trend(changes)
        
        return PerformanceAnalysisResult(
            overall_trend=overall_trend,
            metric_changes=changes,
            configurable_threshold_used=self.degradation_threshold
        )
