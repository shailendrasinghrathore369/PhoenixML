"""
Pydantic Schemas for Real Model Inference and Telemetry Evaluation.

Defines request and response schemas for:
- Single and batch SMS text prediction
- Labeled sample evaluation against ground-truth labels
- Telemetry generation and monitoring observation recording
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class PredictionInput(BaseModel):
    """Input payload for single SMS prediction."""
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(..., min_length=1, max_length=5000, description="SMS text message to classify")


class BatchPredictionInput(BaseModel):
    """Input payload for batch SMS prediction."""
    model_config = ConfigDict(str_strip_whitespace=True)
    texts: List[str] = Field(..., min_length=1, max_length=1500, description="List of SMS text messages")


class PredictionResult(BaseModel):
    """Structured prediction result for an individual SMS message."""
    text: str
    predicted_label: str = Field(..., description="'ham' or 'spam'")
    label_id: int = Field(..., description="0 for ham, 1 for spam")
    is_spam: bool
    spam_probability: float = Field(..., ge=0.0, le=1.0)
    ham_probability: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_name: str
    model_version: str


class BatchPredictionResponse(BaseModel):
    """Response payload for batch predictions."""
    model_id: Optional[uuid.UUID] = None
    model_name: str
    model_version: str
    total_predictions: int
    spam_count: int
    ham_count: int
    predictions: List[PredictionResult]


class LabeledSampleInput(BaseModel):
    """A single labeled SMS sample for ground-truth performance evaluation."""
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(..., min_length=1, max_length=5000)
    y_true: int = Field(..., ge=0, le=1, description="Ground truth label: 0=ham, 1=spam")


class LabeledEvaluationInput(BaseModel):
    """
    Input payload for evaluating the model on labeled data.
    
    Can evaluate custom supplied samples, or use the deterministic UCI holdout test set.
    """
    model_config = ConfigDict(str_strip_whitespace=True)
    samples: Optional[List[LabeledSampleInput]] = Field(
        None, description="Explicit list of labeled SMS samples to evaluate"
    )
    use_reference_test_set: bool = Field(
        default=False,
        description="If True, loads the deterministic UCI SMS Spam Collection holdout test set"
    )
    sample_limit: Optional[int] = Field(
        None, ge=1, le=2000, description="Optional cap on the number of samples to evaluate"
    )
    record_monitoring_observation: bool = Field(
        default=True,
        description="Whether to persist the calculated metrics into PhoenixML monitoring observations"
    )

    @model_validator(mode="after")
    def validate_source(self):
        if not self.use_reference_test_set and (not self.samples or len(self.samples) == 0):
            raise ValueError("Either 'samples' must be provided or 'use_reference_test_set' must be True")
        return self


class EvaluationMetricsResult(BaseModel):
    """Calculated performance metrics from actual model predictions."""
    accuracy: float = Field(..., ge=0.0, le=1.0)
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    f1_score: float = Field(..., ge=0.0, le=1.0)
    prediction_count: int = Field(..., ge=0)
    positive_prediction_count: int = Field(..., ge=0, description="Count of spam predictions")
    negative_prediction_count: int = Field(..., ge=0, description="Count of ham predictions")
    true_positives: int = Field(..., ge=0)
    false_positives: int = Field(..., ge=0)
    true_negatives: int = Field(..., ge=0)
    false_negatives: int = Field(..., ge=0)


class TelemetryEvaluationResponse(BaseModel):
    """Response containing calculated metrics and the resulting monitoring observation ID."""
    model_id: uuid.UUID
    model_name: str
    model_version: str
    evaluated_at: datetime
    metrics: EvaluationMetricsResult
    observation_id: Optional[uuid.UUID] = None
    observation_recorded: bool
    notes: Optional[str] = None
