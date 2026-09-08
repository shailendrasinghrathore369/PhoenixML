"""
Concept Drift Detection Foundation for PhoenixML.

This module detects concept drift by comparing model performance between
a historical (reference) labeled window and a current labeled window.

IMPORTANT ARCHITECTURAL NOTE:
Performance-based detection is an operational monitoring proxy for concept drift,
NOT a mathematical proof that the underlying conditional distribution P(Y|X)
has changed. In production spam filtering, evolving attack strategies,
vocabulary shifts, and changing spam proportions (virtual concept drift)
manifest as measurable degradation in classification metrics.

Pure analytical component:
- Independent of web frameworks, HTTP routers, and API layers
- Independent of persistence ORMs, database engines, and database sessions
- Independent of background orchestrators and monitoring services
- No automated maintenance actions taken
"""

import math
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, field_validator, model_validator


class ConceptDriftStatus(str, Enum):
    DRIFTED = "DRIFTED"
    NO_DRIFT = "NO_DRIFT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class LabeledWindow(BaseModel):
    """
    Domain representation of a labeled monitoring window.
    Contains ground-truth labels and model predictions, with optional timestamps.
    """
    y_true: List[Any]
    y_pred: List[Any]
    observed_at: Optional[datetime] = None
    window_end: Optional[datetime] = None


class ConceptDriftMetricResult(BaseModel):
    """
    Comparison result for a single performance metric across windows.
    """
    metric_name: str
    reference_value: Optional[float]
    current_value: Optional[float]
    absolute_change: Optional[float]
    degradation_threshold: float
    degraded: Optional[bool]


class ConceptDriftAnalysis(BaseModel):
    """
    Overall result of the concept drift analysis.
    """
    status: ConceptDriftStatus
    drift_detected: Optional[bool]
    reference_sample_size: int
    current_sample_size: int
    metric_results: List[ConceptDriftMetricResult]
    drifted_metrics: List[str]
    summary: str


class ConceptDriftConfiguration(BaseModel):
    """
    Configuration parameters for concept drift detection.
    """
    degradation_threshold: float = 0.05
    minimum_samples: int = 2
    positive_class: Any = 1
    negative_class: Any = 0

    @field_validator("degradation_threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("degradation_threshold must be strictly greater than 0.")
        return v

    @field_validator("minimum_samples")
    @classmethod
    def validate_minimum_samples(cls, v: int) -> int:
        if v < 2:
            raise ValueError("minimum_samples must be at least 2.")
        return v

    @model_validator(mode="after")
    def validate_classes(self) -> "ConceptDriftConfiguration":
        if self.positive_class == self.negative_class:
            raise ValueError("positive_class and negative_class must be distinct.")
        return self


class ConceptDriftDetector:
    """
    Detects concept drift via window-based performance comparison.

    Compares accuracy, precision, recall, and F1 score between a reference
    labeled window and a current labeled window. If any monitored metric
    degrades beyond the configurable degradation threshold, concept drift
    is signaled.
    """

    def __init__(self, config: Optional[ConceptDriftConfiguration] = None):
        self.config = config or ConceptDriftConfiguration()

    def _is_valid_value(self, val: Any) -> bool:
        if val is None:
            return False
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return False
        return True

    def _resolve_label(self, val: Any) -> Optional[int]:
        """
        Resolves a label or prediction into a canonical binary indicator (1 for positive, 0 for negative).
        Returns None if the value cannot be reliably mapped to either class.
        """
        if not self._is_valid_value(val):
            return None

        pos = self.config.positive_class
        neg = self.config.negative_class

        # Strict type and equality checking when classes are numeric
        if isinstance(pos, (int, float)) and isinstance(neg, (int, float)) and not isinstance(pos, bool) and not isinstance(neg, bool):
            if isinstance(val, bool):
                return None
            if isinstance(val, (int, float)):
                if val == pos:
                    return 1
                if val == neg:
                    return 0
                return None
            if isinstance(val, str):
                try:
                    s = val.strip()
                    val_int = int(s)
                    if val_int == int(pos):
                        return 1
                    if val_int == int(neg):
                        return 0
                except (ValueError, TypeError, OverflowError):
                    return None
            return None

        # Generic equality / string matching for string or boolean classes
        if val == pos:
            return 1
        if val == neg:
            return 0

        if isinstance(val, str) and isinstance(pos, str) and val.strip().lower() == pos.strip().lower():
            return 1
        if isinstance(val, str) and isinstance(neg, str) and val.strip().lower() == neg.strip().lower():
            return 0

        return None

    def _clean_and_validate_pairs(
        self, y_true: List[Any], y_pred: List[Any]
    ) -> Tuple[List[int], List[int]]:
        """
        Validates pair lengths and maps valid binary label/prediction pairs.
        Mismatched lengths raise ValueError. Invalid or unparseable labels are safely omitted.
        """
        if y_true is None or y_pred is None:
            raise ValueError("y_true and y_pred must not be None.")
        if len(y_true) != len(y_pred):
            raise ValueError("y_true and y_pred must have the same length.")

        clean_true: List[int] = []
        clean_pred: List[int] = []

        for t, p in zip(y_true, y_pred):
            resolved_t = self._resolve_label(t)
            resolved_p = self._resolve_label(p)

            if resolved_t is not None and resolved_p is not None:
                clean_true.append(resolved_t)
                clean_pred.append(resolved_p)

        return clean_true, clean_pred

    def _calculate_metrics(
        self, y_true: List[int], y_pred: List[int]
    ) -> Dict[str, Optional[float]]:
        """
        Calculates binary classification metrics (accuracy, precision, recall, f1_score).

        Zero-division policy:
        - Accuracy: None if total samples == 0, else (TP + TN) / total.
        - Precision: None if (TP + FP) == 0 (no positive predictions made).
        - Recall: None if (TP + FN) == 0 (no positive ground-truth labels).
        - F1 Score: None if precision or recall is None; 0.0 if precision + recall == 0.
        Undefined metrics are represented as None, not misleading zeros.
        """
        if not y_true:
            return {
                "accuracy": None,
                "precision": None,
                "recall": None,
                "f1_score": None,
            }

        tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
        tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

        total = len(y_true)
        accuracy = (tp + tn) / total if total > 0 else None

        precision = tp / (tp + fp) if (tp + fp) > 0 else None
        recall = tp / (tp + fn) if (tp + fn) > 0 else None

        if precision is not None and recall is not None:
            if (precision + recall) > 0:
                f1_score = 2.0 * (precision * recall) / (precision + recall)
            else:
                f1_score = 0.0
        else:
            f1_score = None

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
        }

    def _compare_metric(
        self, metric_name: str, ref_val: Optional[float], cur_val: Optional[float]
    ) -> ConceptDriftMetricResult:
        """
        Compares a metric between reference and current windows.
        change = current - reference.
        degraded is True if change <= -threshold (within floating-point tolerance).
        """
        if ref_val is None or cur_val is None:
            return ConceptDriftMetricResult(
                metric_name=metric_name,
                reference_value=ref_val,
                current_value=cur_val,
                absolute_change=None,
                degradation_threshold=self.config.degradation_threshold,
                degraded=None,
            )

        change = cur_val - ref_val
        # Tolerance for float rounding (e.g. 0.90 - 1.00 = -0.09999999999999998)
        degraded = change <= (-self.config.degradation_threshold + 1e-9)

        return ConceptDriftMetricResult(
            metric_name=metric_name,
            reference_value=ref_val,
            current_value=cur_val,
            absolute_change=change,
            degradation_threshold=self.config.degradation_threshold,
            degraded=degraded,
        )

    def analyze(
        self, reference_window: LabeledWindow, current_window: LabeledWindow
    ) -> ConceptDriftAnalysis:
        """
        Performs window-based concept drift analysis between reference and current windows.
        """
        if reference_window is None or current_window is None:
            raise ValueError("reference_window and current_window must not be None.")

        ref_true, ref_pred = self._clean_and_validate_pairs(
            reference_window.y_true, reference_window.y_pred
        )
        cur_true, cur_pred = self._clean_and_validate_pairs(
            current_window.y_true, current_window.y_pred
        )

        n_ref = len(ref_true)
        n_cur = len(cur_true)

        if n_ref < self.config.minimum_samples or n_cur < self.config.minimum_samples:
            return ConceptDriftAnalysis(
                status=ConceptDriftStatus.INSUFFICIENT_DATA,
                drift_detected=None,
                reference_sample_size=n_ref,
                current_sample_size=n_cur,
                metric_results=[],
                drifted_metrics=[],
                summary="Insufficient labeled samples in one or both windows.",
            )

        ref_metrics = self._calculate_metrics(ref_true, ref_pred)
        cur_metrics = self._calculate_metrics(cur_true, cur_pred)

        results: List[ConceptDriftMetricResult] = []
        drifted_metrics: List[str] = []

        for metric_name in ["accuracy", "precision", "recall", "f1_score"]:
            res = self._compare_metric(
                metric_name, ref_metrics[metric_name], cur_metrics[metric_name]
            )
            results.append(res)
            if res.degraded is True:
                drifted_metrics.append(metric_name)

        evaluable_metrics = [r for r in results if r.degraded is not None]
        if not evaluable_metrics:
            status = ConceptDriftStatus.INSUFFICIENT_DATA
            drift_detected = None
            summary = "Insufficient evaluable metric data to determine concept drift."
        elif drifted_metrics:
            status = ConceptDriftStatus.DRIFTED
            drift_detected = True
            summary = f"Concept drift detected. Degraded metrics: {', '.join(drifted_metrics)}."
        else:
            status = ConceptDriftStatus.NO_DRIFT
            drift_detected = False
            summary = "No significant concept drift (performance degradation) detected."

        return ConceptDriftAnalysis(
            status=status,
            drift_detected=drift_detected,
            reference_sample_size=n_ref,
            current_sample_size=n_cur,
            metric_results=results,
            drifted_metrics=drifted_metrics,
            summary=summary,
        )

    def analyze_sequence(
        self,
        windows: List[LabeledWindow],
        reference_window: Optional[LabeledWindow] = None,
    ) -> List[ConceptDriftAnalysis]:
        """
        Analyzes a sequence of labeled windows against a baseline reference window.
        If reference_window is not provided, the first window in the sequence is used as baseline.
        """
        if not windows:
            return []
        if reference_window is None and len(windows) < 2:
            return []

        base_ref = reference_window if reference_window is not None else windows[0]
        cur_windows = windows if reference_window is not None else windows[1:]

        return [self.analyze(base_ref, cur) for cur in cur_windows]
