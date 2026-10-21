import math
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator
from scipy.stats import ks_2samp

class FeatureDistribution(BaseModel):
    feature_name: str
    reference_values: List[Any]
    current_values: List[Any]

class FeatureDriftResult(BaseModel):
    feature_name: str
    ks_statistic: Optional[float]
    p_value: Optional[float]
    threshold: float
    drift_detected: Optional[bool]
    reference_sample_size: int
    current_sample_size: int
    status: str

class DataDriftAnalysis(BaseModel):
    feature_results: List[FeatureDriftResult]
    drifted_features: List[str]
    drift_detected: Optional[bool]
    features_analyzed: int
    summary: str

class DataDriftConfiguration(BaseModel):
    alpha: float = 0.05
    minimum_samples: int = 2
    
    @field_validator('alpha')
    @classmethod
    def validate_alpha(cls, v: float) -> float:
        if not (0 < v < 1):
            raise ValueError("alpha must be strictly between 0 and 1.")
        return v
        
    @field_validator('minimum_samples')
    @classmethod
    def validate_minimum_samples(cls, v: int) -> int:
        if v < 2:
            raise ValueError("minimum_samples must be at least 2.")
        return v

class DataDriftDetector:
    """
    Detects statistical distribution shift (data drift) between reference and current
    feature distributions using the Kolmogorov-Smirnov (KS) two-sample test.
    """
    def __init__(self, config: Optional[DataDriftConfiguration] = None):
        self.config = config or DataDriftConfiguration()

    def _clean_numeric_data(self, values: List[Any]) -> List[float]:
        cleaned = []
        for v in values:
            if v is None:
                continue
            try:
                val = float(v)
            except (ValueError, TypeError):
                continue
            if math.isnan(val) or math.isinf(val):
                continue
            cleaned.append(val)
        return cleaned

    def analyze_feature(self, feature: FeatureDistribution) -> FeatureDriftResult:
        ref_clean = self._clean_numeric_data(feature.reference_values)
        cur_clean = self._clean_numeric_data(feature.current_values)
        
        n_ref = len(ref_clean)
        n_cur = len(cur_clean)
        
        if n_ref < self.config.minimum_samples or n_cur < self.config.minimum_samples:
            return FeatureDriftResult(
                feature_name=feature.feature_name,
                ks_statistic=None,
                p_value=None,
                threshold=self.config.alpha,
                drift_detected=None,
                reference_sample_size=n_ref,
                current_sample_size=n_cur,
                status="INSUFFICIENT_DATA"
            )
            
        result = ks_2samp(ref_clean, cur_clean)
        
        # ks_2samp returns a statistic and a pvalue
        drifted = result.pvalue < self.config.alpha
        
        return FeatureDriftResult(
            feature_name=feature.feature_name,
            ks_statistic=float(result.statistic),
            p_value=float(result.pvalue),
            threshold=self.config.alpha,
            drift_detected=drifted,
            reference_sample_size=n_ref,
            current_sample_size=n_cur,
            status="SUCCESS"
        )

    def analyze(self, features: List[FeatureDistribution]) -> DataDriftAnalysis:
        results = []
        drifted_features = []
        analyzed_count = 0
        
        for feature in features:
            res = self.analyze_feature(feature)
            results.append(res)
            
            if res.status == "SUCCESS":
                analyzed_count += 1
                if res.drift_detected:
                    drifted_features.append(res.feature_name)
                    
        if analyzed_count == 0:
            overall_drift = None
            summary = "Insufficient data to analyze any feature for drift."
        else:
            overall_drift = len(drifted_features) > 0
            if overall_drift:
                summary = f"Analyzed {analyzed_count} features. Detected drift in {len(drifted_features)} features ({', '.join(drifted_features)}) using alpha={self.config.alpha}."
            else:
                summary = f"Analyzed {analyzed_count} features. No significant drift detected (alpha={self.config.alpha})."
                
        return DataDriftAnalysis(
            feature_results=results,
            drifted_features=drifted_features,
            drift_detected=overall_drift,
            features_analyzed=analyzed_count,
            summary=summary
        )
