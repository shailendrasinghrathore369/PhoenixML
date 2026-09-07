import pytest
import math
from app.monitoring.data_drift import (
    DataDriftConfiguration,
    DataDriftDetector,
    FeatureDistribution,
    DataDriftAnalysis,
    FeatureDriftResult
)

def test_identical_distributions():
    detector = DataDriftDetector()
    feature = FeatureDistribution(
        feature_name="test_feature",
        reference_values=[1.0, 2.0, 3.0, 4.0, 5.0] * 10,
        current_values=[1.0, 2.0, 3.0, 4.0, 5.0] * 10
    )
    result = detector.analyze([feature])
    
    assert result.features_analyzed == 1
    assert result.drift_detected is False
    assert len(result.drifted_features) == 0
    assert result.feature_results[0].drift_detected is False
    assert result.feature_results[0].ks_statistic == 0.0
    assert result.feature_results[0].p_value == 1.0

def test_shifted_distributions():
    detector = DataDriftDetector()
    feature = FeatureDistribution(
        feature_name="test_feature",
        reference_values=[1.0, 2.0, 3.0, 4.0, 5.0] * 10,
        current_values=[10.0, 11.0, 12.0, 13.0, 14.0] * 10
    )
    result = detector.analyze([feature])
    
    assert result.features_analyzed == 1
    assert result.drift_detected is True
    assert result.drifted_features == ["test_feature"]
    assert result.feature_results[0].drift_detected is True
    assert result.feature_results[0].p_value < 0.05
    assert result.feature_results[0].ks_statistic > 0.0

def test_multiple_features():
    detector = DataDriftDetector()
    stable = FeatureDistribution(
        feature_name="stable",
        reference_values=[1, 2, 3, 4] * 10,
        current_values=[1, 2, 3, 4] * 10
    )
    shifted = FeatureDistribution(
        feature_name="shifted",
        reference_values=[1, 2, 3, 4] * 10,
        current_values=[10, 20, 30, 40] * 10
    )
    
    result = detector.analyze([stable, shifted])
    assert result.features_analyzed == 2
    assert result.drift_detected is True
    assert "shifted" in result.drifted_features
    assert "stable" not in result.drifted_features

def test_alpha_threshold_configuration():
    # If alpha is extremely small, it will not flag drift easily
    # A small difference should trigger drift with high alpha, but not low alpha.
    ref = [1.0] * 50 + [2.0] * 50
    cur = [1.0] * 30 + [2.0] * 70
    
    strict_detector = DataDriftDetector(DataDriftConfiguration(alpha=0.0001))
    loose_detector = DataDriftDetector(DataDriftConfiguration(alpha=0.5))
    
    feature = FeatureDistribution(feature_name="f1", reference_values=ref, current_values=cur)
    
    strict_res = strict_detector.analyze([feature])
    loose_res = loose_detector.analyze([feature])
    
    assert strict_res.drift_detected is False
    assert loose_res.drift_detected is True

def test_alpha_validation():
    with pytest.raises(ValueError):
        DataDriftConfiguration(alpha=-0.1)
    with pytest.raises(ValueError):
        DataDriftConfiguration(alpha=1.1)

def test_minimum_sample_validation():
    with pytest.raises(ValueError):
        DataDriftConfiguration(minimum_samples=1)

def test_empty_reference():
    detector = DataDriftDetector()
    feature = FeatureDistribution(feature_name="f", reference_values=[], current_values=[1,2,3])
    res = detector.analyze([feature])
    
    assert res.features_analyzed == 0
    assert res.drift_detected is None
    assert res.feature_results[0].status == "INSUFFICIENT_DATA"

def test_empty_current():
    detector = DataDriftDetector()
    feature = FeatureDistribution(feature_name="f", reference_values=[1,2,3], current_values=[])
    res = detector.analyze([feature])
    
    assert res.features_analyzed == 0
    assert res.drift_detected is None

def test_insufficient_samples():
    detector = DataDriftDetector(DataDriftConfiguration(minimum_samples=5))
    feature = FeatureDistribution(feature_name="f", reference_values=[1,2], current_values=[1,2])
    res = detector.analyze([feature])
    assert res.features_analyzed == 0
    assert res.feature_results[0].status == "INSUFFICIENT_DATA"

def test_nan_infinity_none():
    detector = DataDriftDetector(DataDriftConfiguration(minimum_samples=2))
    feature = FeatureDistribution(
        feature_name="f", 
        reference_values=[1.0, 2.0, None, float('nan'), float('inf'), -float('inf'), "invalid"], 
        current_values=[1.0, 2.0, 3.0]
    )
    res = detector.analyze([feature])
    assert res.features_analyzed == 1
    # Only 1.0 and 2.0 are valid from reference
    assert res.feature_results[0].reference_sample_size == 2
    assert res.feature_results[0].current_sample_size == 3

def test_summary_output():
    detector = DataDriftDetector()
    stable = FeatureDistribution(
        feature_name="stable",
        reference_values=[1, 2, 3, 4] * 10,
        current_values=[1, 2, 3, 4] * 10
    )
    res = detector.analyze([stable])
    assert "Analyzed 1 features. No significant drift detected" in res.summary

def test_deterministic_output():
    detector = DataDriftDetector()
    feature = FeatureDistribution(
        feature_name="test_feature",
        reference_values=[1.0, 2.0, 3.0, 4.0, 5.0] * 10,
        current_values=[10.0, 11.0, 12.0, 13.0, 14.0] * 10
    )
    res1 = detector.analyze([feature])
    res2 = detector.analyze([feature])
    
    assert res1.feature_results[0].ks_statistic == res2.feature_results[0].ks_statistic
    assert res1.feature_results[0].p_value == res2.feature_results[0].p_value

def test_architecture_no_db_dependencies():
    with open("app/monitoring/data_drift.py", "r") as f:
        content = f.read()
    
    assert "sqlalchemy" not in content.lower()
    assert "fastapi" not in content.lower()
    assert "session" not in content.lower()
    assert "Depends" not in content
    assert "router" not in content.lower()
