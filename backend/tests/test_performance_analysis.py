import pytest
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional

from app.monitoring.performance import (
    PerformanceAnalyzer,
    PerformanceTrend,
    PerformanceAnalysisResult
)

# Mock observation for unit testing without the database
@dataclass
class MockObservation:
    observed_at: datetime
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    prediction_count: int = 100

@pytest.fixture
def analyzer():
    # Use default provisional threshold 0.05
    return PerformanceAnalyzer(degradation_threshold=0.05)

def test_insufficient_data_empty(analyzer):
    result = analyzer.analyze([])
    assert result.overall_trend == PerformanceTrend.INSUFFICIENT_DATA
    assert len(result.metric_changes) == 0

def test_insufficient_data_single_obs(analyzer):
    obs = MockObservation(observed_at=datetime.now(timezone.utc), accuracy=0.9)
    result = analyzer.analyze([obs])
    assert result.overall_trend == PerformanceTrend.INSUFFICIENT_DATA

def test_duplicate_timestamps(analyzer):
    t = datetime.now(timezone.utc)
    obs1 = MockObservation(observed_at=t, accuracy=0.9)
    obs2 = MockObservation(observed_at=t, accuracy=0.8)
    result = analyzer.analyze([obs1, obs2])
    assert result.overall_trend == PerformanceTrend.INSUFFICIENT_DATA

def test_chronological_ordering(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs_new = MockObservation(observed_at=t2, accuracy=0.80)
    obs_old = MockObservation(observed_at=t1, accuracy=0.90)
    
    # Pass out of order
    result = analyzer.analyze([obs_new, obs_old])
    
    # Should evaluate old (0.90) -> new (0.80) = DEGRADING (-0.10)
    assert result.overall_trend == PerformanceTrend.DEGRADING
    assert result.metric_changes["accuracy"].old_value == 0.90
    assert result.metric_changes["accuracy"].new_value == 0.80

def test_improving_performance(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.80)
    obs2 = MockObservation(observed_at=t2, accuracy=0.86)
    
    result = analyzer.analyze([obs1, obs2])
    assert result.overall_trend == PerformanceTrend.IMPROVING
    assert result.metric_changes["accuracy"].trend == PerformanceTrend.IMPROVING

def test_degrading_performance(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90)
    obs2 = MockObservation(observed_at=t2, accuracy=0.84)
    
    result = analyzer.analyze([obs1, obs2])
    assert result.overall_trend == PerformanceTrend.DEGRADING
    assert result.metric_changes["accuracy"].trend == PerformanceTrend.DEGRADING

def test_stable_performance_identical(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90)
    obs2 = MockObservation(observed_at=t2, accuracy=0.90)
    
    result = analyzer.analyze([obs1, obs2])
    assert result.overall_trend == PerformanceTrend.STABLE
    assert result.metric_changes["accuracy"].trend == PerformanceTrend.STABLE

def test_stable_performance_within_threshold(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90)
    # -0.04 drop is less than the 0.05 threshold
    obs2 = MockObservation(observed_at=t2, accuracy=0.86)
    
    result = analyzer.analyze([obs1, obs2])
    assert result.overall_trend == PerformanceTrend.STABLE
    assert result.metric_changes["accuracy"].trend == PerformanceTrend.STABLE

def test_missing_accuracy(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, precision=0.90)
    obs2 = MockObservation(observed_at=t2, precision=0.80)
    
    result = analyzer.analyze([obs1, obs2])
    assert "accuracy" not in result.metric_changes
    assert result.metric_changes["precision"].trend == PerformanceTrend.DEGRADING
    assert result.overall_trend == PerformanceTrend.DEGRADING

def test_missing_precision_recall_f1(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90, precision=None, recall=0.8, f1_score=None)
    obs2 = MockObservation(observed_at=t2, accuracy=0.90, precision=0.8, recall=None, f1_score=None)
    
    result = analyzer.analyze([obs1, obs2])
    # precision, recall, f1_score are missing from either oldest or newest, so they can't be compared
    assert "precision" not in result.metric_changes
    assert "recall" not in result.metric_changes
    assert "f1_score" not in result.metric_changes
    assert "accuracy" in result.metric_changes
    assert result.overall_trend == PerformanceTrend.STABLE

def test_partially_missing_metrics(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90, f1_score=0.80)
    obs2 = MockObservation(observed_at=t2, accuracy=None, f1_score=0.74)
    
    result = analyzer.analyze([obs1, obs2])
    assert "accuracy" not in result.metric_changes
    assert "f1_score" in result.metric_changes
    assert result.metric_changes["f1_score"].trend == PerformanceTrend.DEGRADING
    assert result.overall_trend == PerformanceTrend.DEGRADING

def test_all_metrics_missing(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1)
    obs2 = MockObservation(observed_at=t2)
    
    result = analyzer.analyze([obs1, obs2])
    assert len(result.metric_changes) == 0
    assert result.overall_trend == PerformanceTrend.INSUFFICIENT_DATA

def test_zero_old_value(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.0)
    obs2 = MockObservation(observed_at=t2, accuracy=0.1)
    
    result = analyzer.analyze([obs1, obs2])
    assert result.metric_changes["accuracy"].relative_change is None
    assert result.metric_changes["accuracy"].trend == PerformanceTrend.IMPROVING

def test_nan_infinity_protection(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=float('nan'), precision=float('inf'))
    obs2 = MockObservation(observed_at=t2, accuracy=0.90, precision=0.90)
    
    result = analyzer.analyze([obs1, obs2])
    assert "accuracy" not in result.metric_changes
    assert "precision" not in result.metric_changes
    assert result.overall_trend == PerformanceTrend.INSUFFICIENT_DATA

def test_configurable_threshold():
    # Strict threshold
    strict_analyzer = PerformanceAnalyzer(degradation_threshold=0.01)
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90)
    obs2 = MockObservation(observed_at=t2, accuracy=0.88)
    
    result = strict_analyzer.analyze([obs1, obs2])
    assert result.overall_trend == PerformanceTrend.DEGRADING
    
    # Loose threshold
    loose_analyzer = PerformanceAnalyzer(degradation_threshold=0.10)
    result2 = loose_analyzer.analyze([obs1, obs2])
    assert result2.overall_trend == PerformanceTrend.STABLE

def test_deterministic_output(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90)
    obs2 = MockObservation(observed_at=t2, accuracy=0.84)
    
    result1 = analyzer.analyze([obs1, obs2])
    result2 = analyzer.analyze([obs1, obs2])
    
    assert result1.overall_trend == result2.overall_trend
    assert result1.metric_changes["accuracy"].absolute_change == result2.metric_changes["accuracy"].absolute_change
