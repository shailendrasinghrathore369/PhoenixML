import pytest
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional

from app.monitoring.performance import (
    PerformanceAnalyzer,
    PerformanceStatus,
    PerformanceAnalysis
)

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
    return PerformanceAnalyzer(degradation_threshold=0.05)

def test_insufficient_data_empty(analyzer):
    result = analyzer.analyze([])
    assert result.overall_status == PerformanceStatus.INSUFFICIENT_DATA
    assert len(result.metric_trends) == 0
    assert result.observation_count == 0

def test_insufficient_data_single_obs(analyzer):
    obs = MockObservation(observed_at=datetime.now(timezone.utc), accuracy=0.9)
    result = analyzer.analyze([obs])
    assert result.overall_status == PerformanceStatus.INSUFFICIENT_DATA
    assert result.observation_count == 1

def test_duplicate_timestamps(analyzer):
    t = datetime.now(timezone.utc)
    obs1 = MockObservation(observed_at=t, accuracy=0.9)
    obs2 = MockObservation(observed_at=t, accuracy=0.8)
    result = analyzer.analyze([obs1, obs2])
    assert result.overall_status == PerformanceStatus.INSUFFICIENT_DATA
    assert result.observation_count == 2

def test_chronological_ordering(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs_new = MockObservation(observed_at=t2, accuracy=0.80)
    obs_old = MockObservation(observed_at=t1, accuracy=0.90)
    
    result = analyzer.analyze([obs_new, obs_old])
    
    assert result.overall_status == PerformanceStatus.DEGRADED
    assert result.metric_trends["accuracy"].earliest_value == 0.90
    assert result.metric_trends["accuracy"].latest_value == 0.80

def test_improving_performance(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.80)
    obs2 = MockObservation(observed_at=t2, accuracy=0.86)
    
    result = analyzer.analyze([obs1, obs2])
    assert result.overall_status == PerformanceStatus.IMPROVING
    assert result.metric_trends["accuracy"].direction == PerformanceStatus.IMPROVING

def test_degrading_performance(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90)
    obs2 = MockObservation(observed_at=t2, accuracy=0.84)
    
    result = analyzer.analyze([obs1, obs2])
    assert result.overall_status == PerformanceStatus.DEGRADED
    assert result.metric_trends["accuracy"].direction == PerformanceStatus.DEGRADED
    assert "accuracy" in result.degraded_metrics

def test_stable_performance_identical(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90)
    obs2 = MockObservation(observed_at=t2, accuracy=0.90)
    
    result = analyzer.analyze([obs1, obs2])
    assert result.overall_status == PerformanceStatus.STABLE
    assert result.metric_trends["accuracy"].direction == PerformanceStatus.STABLE

def test_stable_performance_within_threshold(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90)
    obs2 = MockObservation(observed_at=t2, accuracy=0.86)
    
    result = analyzer.analyze([obs1, obs2])
    assert result.overall_status == PerformanceStatus.STABLE
    assert result.metric_trends["accuracy"].direction == PerformanceStatus.STABLE

def test_missing_accuracy(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, precision=0.90)
    obs2 = MockObservation(observed_at=t2, precision=0.80)
    
    result = analyzer.analyze([obs1, obs2])
    assert "accuracy" not in result.metric_trends
    assert result.metric_trends["precision"].direction == PerformanceStatus.DEGRADED
    assert result.overall_status == PerformanceStatus.DEGRADED

def test_missing_precision_recall_f1(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90, precision=None, recall=0.8, f1_score=None)
    obs2 = MockObservation(observed_at=t2, accuracy=0.90, precision=0.8, recall=None, f1_score=None)
    
    result = analyzer.analyze([obs1, obs2])
    assert "precision" not in result.metric_trends
    assert "recall" not in result.metric_trends
    assert "f1_score" not in result.metric_trends
    assert "accuracy" in result.metric_trends
    assert result.overall_status == PerformanceStatus.STABLE

def test_partially_missing_metrics(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90, f1_score=0.80)
    obs2 = MockObservation(observed_at=t2, accuracy=None, f1_score=0.74)
    
    result = analyzer.analyze([obs1, obs2])
    assert "accuracy" not in result.metric_trends
    assert "f1_score" in result.metric_trends
    assert result.metric_trends["f1_score"].direction == PerformanceStatus.DEGRADED
    assert result.overall_status == PerformanceStatus.DEGRADED

def test_all_metrics_missing(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1)
    obs2 = MockObservation(observed_at=t2)
    
    result = analyzer.analyze([obs1, obs2])
    assert len(result.metric_trends) == 0
    assert result.overall_status == PerformanceStatus.INSUFFICIENT_DATA

def test_zero_earliest_value(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.0)
    obs2 = MockObservation(observed_at=t2, accuracy=0.1)
    
    result = analyzer.analyze([obs1, obs2])
    assert result.metric_trends["accuracy"].percentage_change is None
    assert result.metric_trends["accuracy"].direction == PerformanceStatus.IMPROVING

def test_nan_infinity_protection(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=float('nan'), precision=float('inf'))
    obs2 = MockObservation(observed_at=t2, accuracy=0.90, precision=0.90)
    
    result = analyzer.analyze([obs1, obs2])
    assert "accuracy" not in result.metric_trends
    assert "precision" not in result.metric_trends
    assert result.overall_status == PerformanceStatus.INSUFFICIENT_DATA

def test_configurable_threshold():
    strict_analyzer = PerformanceAnalyzer(degradation_threshold=0.01)
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90)
    obs2 = MockObservation(observed_at=t2, accuracy=0.88)
    
    result = strict_analyzer.analyze([obs1, obs2])
    assert result.overall_status == PerformanceStatus.DEGRADED
    
    loose_analyzer = PerformanceAnalyzer(degradation_threshold=0.10)
    result2 = loose_analyzer.analyze([obs1, obs2])
    assert result2.overall_status == PerformanceStatus.STABLE

def test_deterministic_output(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90)
    obs2 = MockObservation(observed_at=t2, accuracy=0.84)
    
    result1 = analyzer.analyze([obs1, obs2])
    result2 = analyzer.analyze([obs1, obs2])
    
    assert result1.overall_status == result2.overall_status
    assert result1.metric_trends["accuracy"].absolute_change == result2.metric_trends["accuracy"].absolute_change

def test_summary_and_degraded_metrics(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    obs1 = MockObservation(observed_at=t1, accuracy=0.90, precision=0.90)
    obs2 = MockObservation(observed_at=t2, accuracy=0.84, precision=0.84)
    
    result = analyzer.analyze([obs1, obs2])
    assert "accuracy" in result.degraded_metrics
    assert "precision" in result.degraded_metrics
    assert "Performance is degraded." in result.summary
    assert "accuracy" in result.summary
    assert "precision" in result.summary

def test_analyzer_no_db_queries():
    # Architecture Verification test
    with open("app/monitoring/performance.py", "r") as f:
        content = f.read()
    
    assert "session.query" not in content
    assert "db.execute" not in content
    assert "Session" not in content
    assert "Depends" not in content

def test_degradation_threshold_boundary(analyzer):
    t1 = datetime.now(timezone.utc)
    t2 = t1 + timedelta(days=1)
    
    # Exactly -0.05
    obs1 = MockObservation(observed_at=t1, accuracy=0.90)
    obs2 = MockObservation(observed_at=t2, accuracy=0.85)
    
    result = analyzer.analyze([obs1, obs2])
    assert result.overall_status == PerformanceStatus.DEGRADED
    
    # Exactly 0.05
    obs3 = MockObservation(observed_at=t1, accuracy=0.85)
    obs4 = MockObservation(observed_at=t2, accuracy=0.90)
    
    result2 = analyzer.analyze([obs3, obs4])
    assert result2.overall_status == PerformanceStatus.IMPROVING
