"""
Service Layer for Real ML Model Inference and Telemetry Integration.

Bridges the trained reference SpamSMS-LogisticRegression model (.joblib)
to PhoenixML's monitoring observation and AIMD decision evaluation pipeline.

Key Guarantees:
- Pure offline training: PhoenixML only executes inference using serialized artifacts.
- Deterministic predictions: identical SMS inputs yield identical predictions and probabilities.
- Non-fabricated ground truth: performance telemetry is computed strictly from actual predictions
  evaluated against legitimate ground-truth labels (either explicitly provided or drawn from the
  deterministic UCI SMS Spam Collection holdout test set).
- Reuses existing PhoenixML monitoring observation and decision evaluation models.
- Decision-support only: strictly produces observations/recommendations with mandatory human approval.
"""

from __future__ import annotations

import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import joblib
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import ModelStatus, RegisteredModel, MonitoringObservation
from app.models.repository import RegisteredModelRepository
from app.models.monitoring_repository import MonitoringObservationRepository
from app.models.monitoring_schemas import MonitoringObservationCreate
from app.models.reference_integration import (
    find_reference_artifact_file,
    find_reference_metadata_file,
    load_reference_metadata,
    parse_reference_model_description,
    get_workspace_root,
)
from app.models.inference_schemas import (
    PredictionResult,
    BatchPredictionResponse,
    EvaluationMetricsResult,
    TelemetryEvaluationResponse,
)
from app.monitoring.concept_drift import LabeledWindow

logger = logging.getLogger(__name__)

# Ensure workspace root is in sys.path so joblib can unpickle custom pipeline steps (e.g. clean_text)
_ws_root = get_workspace_root()
if str(_ws_root) not in sys.path:
    sys.path.insert(0, str(_ws_root))


class SpamInferenceService:
    """
    Inference adapter connecting the trained scikit-learn reference pipeline
    to PhoenixML's monitoring repository and decision services.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        model_id: Optional[uuid.UUID] = None,
        model_path: Optional[Union[str, Path]] = None,
        metadata_path: Optional[Union[str, Path]] = None,
    ):
        self.db = db
        self.model_id = model_id
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.model_repo = RegisteredModelRepository(db) if db is not None else None
        self.obs_repo = MonitoringObservationRepository(db) if db is not None else None

        # Lazy loaded pipeline and metadata
        self._pipeline: Optional[Pipeline] = None
        self._metadata: Optional[Dict[str, Any]] = None
        self._model_name: Optional[str] = None
        self._model_version: Optional[str] = None

    def _resolve_paths_and_identity(self) -> Tuple[Path, Optional[Path]]:
        """
        Determine the concrete file paths for the artifact and metadata,
        extracting them from the registered model in DB if available, or fall back to defaults.
        """
        artifact_path: Optional[Path] = None
        metadata_path: Optional[Path] = None

        if self.model_id and self.model_repo:
            db_model = self.model_repo.get_by_id(self.model_id)
            if not db_model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Registered model {self.model_id} not found",
                )
            self._model_name = db_model.name
            parsed_desc = parse_reference_model_description(db_model.description)
            if parsed_desc.get("version"):
                self._model_version = parsed_desc["version"]
            if parsed_desc.get("artifact_path"):
                candidate = get_workspace_root() / parsed_desc["artifact_path"]
                if candidate.is_file():
                    artifact_path = candidate

        # Fallback to explicit or discovered paths
        if not artifact_path:
            artifact_path = find_reference_artifact_file(self.model_path)

        if not metadata_path:
            try:
                metadata_path = find_reference_metadata_file(self.metadata_path)
            except FileNotFoundError:
                metadata_path = None

        return artifact_path, metadata_path

    def get_pipeline(self) -> Pipeline:
        """Load and return the memoized sklearn Pipeline artifact."""
        if self._pipeline is None:
            # Ensure workspace root is in sys.path
            ws_root = get_workspace_root()
            if str(ws_root) not in sys.path:
                sys.path.insert(0, str(ws_root))

            artifact_path, metadata_path = self._resolve_paths_and_identity()
            logger.info("Loading model artifact from: %s", artifact_path)
            try:
                self._pipeline = joblib.load(artifact_path)
            except Exception as e:
                logger.error("Failed to load model artifact at %s: %s", artifact_path, e)
                raise RuntimeError(f"Failed to load model artifact at {artifact_path}: {e}") from e

            # Load metadata
            if metadata_path and metadata_path.is_file():
                try:
                    self._metadata = load_reference_metadata(metadata_path)
                    if not self._model_name:
                        self._model_name = self._metadata.get("model_name", "SpamSMS-LogisticRegression")
                    if not self._model_version:
                        self._model_version = self._metadata.get("model_version", "1.0.0")
                except Exception as meta_err:
                    logger.warning("Could not load reference metadata: %s", meta_err)

            if not self._model_name:
                self._model_name = "SpamSMS-LogisticRegression"
            if not self._model_version:
                self._model_version = "1.0.0"

        return self._pipeline

    @property
    def model_name(self) -> str:
        if not self._model_name:
            self.get_pipeline()
        return self._model_name or "SpamSMS-LogisticRegression"

    @property
    def model_version(self) -> str:
        if not self._model_version:
            self.get_pipeline()
        return self._model_version or "1.0.0"

    def predict_single(self, text: str) -> PredictionResult:
        """Classify a single SMS text message."""
        results = self.predict_batch([text])
        return results[0]

    def predict_batch(self, texts: Sequence[str]) -> List[PredictionResult]:
        """
        Classify a sequence of SMS text messages.
        
        Guarantees deterministic output and probability outputs bounded [0.0, 1.0].
        """
        if not texts:
            return []

        pipeline = self.get_pipeline()
        input_list = list(texts)

        # Pipeline returns 2D probabilities: [P(ham), P(spam)]
        probabilities = pipeline.predict_proba(input_list)

        results: List[PredictionResult] = []
        for text, prob in zip(input_list, probabilities):
            ham_prob = float(prob[0])
            spam_prob = float(prob[1])
            is_spam = spam_prob >= 0.5
            predicted_label = "spam" if is_spam else "ham"
            label_id = 1 if is_spam else 0
            confidence = float(max(ham_prob, spam_prob))

            results.append(
                PredictionResult(
                    text=text,
                    predicted_label=predicted_label,
                    label_id=label_id,
                    is_spam=is_spam,
                    spam_probability=round(spam_prob, 4),
                    ham_probability=round(ham_prob, 4),
                    confidence=round(confidence, 4),
                    model_name=self.model_name,
                    model_version=self.model_version,
                )
            )

        return results

    def get_reference_test_data(
        self,
        sample_limit: Optional[int] = None,
        random_state: int = 42,
    ) -> Tuple[List[str], List[int]]:
        """
        Load the deterministic stratified holdout test split (test_size=0.20)
        from the UCI SMS Spam Collection dataset.
        """
        from ml_pipeline.data_loader import load_sms_spam_data

        ws_root = get_workspace_root()
        data_file = ws_root / "ml_pipeline" / "data" / "SMSSpamCollection"
        texts, labels = load_sms_spam_data(data_path=data_file)

        _, X_test, _, y_test = train_test_split(
            texts,
            labels,
            test_size=0.20,
            random_state=random_state,
            stratify=labels,
        )

        if sample_limit is not None and sample_limit > 0:
            return X_test[:sample_limit], y_test[:sample_limit]

        return X_test, y_test

    def evaluate_labeled_data(
        self,
        texts: Sequence[str],
        y_true: Sequence[int],
    ) -> EvaluationMetricsResult:
        """
        Evaluate actual model predictions against provided ground-truth labels.
        
        Calculates genuine evaluation metrics:
        - accuracy
        - precision
        - recall
        - f1-score
        - confusion matrix breakdown (TP, FP, TN, FN)
        - prediction counts (positive=spam, negative=ham)
        """
        if len(texts) != len(y_true):
            raise ValueError(f"Length mismatch: {len(texts)} texts vs {len(y_true)} labels")

        if not texts:
            raise ValueError("Cannot evaluate an empty dataset")

        predictions = self.predict_batch(texts)
        y_pred = [p.label_id for p in predictions]
        y_true_list = list(y_true)

        acc = float(accuracy_score(y_true_list, y_pred))
        prec = float(precision_score(y_true_list, y_pred, zero_division=0))
        rec = float(recall_score(y_true_list, y_pred, zero_division=0))
        f1 = float(f1_score(y_true_list, y_pred, zero_division=0))

        pos_count = sum(y_pred)
        neg_count = len(y_pred) - pos_count

        # Compute confusion matrix elements
        tn = sum(1 for yt, yp in zip(y_true_list, y_pred) if yt == 0 and yp == 0)
        fp = sum(1 for yt, yp in zip(y_true_list, y_pred) if yt == 0 and yp == 1)
        fn = sum(1 for yt, yp in zip(y_true_list, y_pred) if yt == 1 and yp == 0)
        tp = sum(1 for yt, yp in zip(y_true_list, y_pred) if yt == 1 and yp == 1)

        return EvaluationMetricsResult(
            accuracy=round(acc, 4),
            precision=round(prec, 4),
            recall=round(rec, 4),
            f1_score=round(f1, 4),
            prediction_count=len(y_pred),
            positive_prediction_count=pos_count,
            negative_prediction_count=neg_count,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
        )

    def create_observation_payload(
        self,
        metrics: EvaluationMetricsResult,
        model_id: uuid.UUID,
        observed_at: Optional[datetime] = None,
    ) -> MonitoringObservationCreate:
        """
        Construct a valid PhoenixML MonitoringObservationCreate schema payload
        from calculated performance metrics.
        """
        obs_time = observed_at or datetime.now(timezone.utc)
        if obs_time.tzinfo is None:
            obs_time = obs_time.replace(tzinfo=timezone.utc)

        return MonitoringObservationCreate(
            model_id=model_id,
            observed_at=obs_time,
            prediction_count=metrics.prediction_count,
            positive_prediction_count=metrics.positive_prediction_count,
            negative_prediction_count=metrics.negative_prediction_count,
            accuracy=metrics.accuracy,
            precision=metrics.precision,
            recall=metrics.recall,
            f1_score=metrics.f1_score,
        )

    def record_monitoring_observation(
        self,
        metrics: EvaluationMetricsResult,
        model_id: uuid.UUID,
        owner_id: uuid.UUID,
        observed_at: Optional[datetime] = None,
    ) -> MonitoringObservation:
        """
        Persist a new monitoring observation into PhoenixML's monitoring repository.
        """
        if self.obs_repo is None:
            raise RuntimeError("Database session / MonitoringObservationRepository not configured")

        payload = self.create_observation_payload(
            metrics=metrics,
            model_id=model_id,
            observed_at=observed_at,
        )

        return self.obs_repo.create(payload)

    def create_labeled_window(
        self,
        texts: Sequence[str],
        y_true: Sequence[int],
        observed_at: Optional[datetime] = None,
    ) -> LabeledWindow:
        """
        Construct a genuine LabeledWindow domain object for Concept Drift analysis
        containing ground-truth labels and real model predictions.
        """
        predictions = self.predict_batch(texts)
        y_pred = [p.label_id for p in predictions]

        obs_time = observed_at or datetime.now(timezone.utc)
        return LabeledWindow(
            y_true=list(y_true),
            y_pred=y_pred,
            observed_at=obs_time,
        )

    def evaluate_and_record_telemetry(
        self,
        model_id: uuid.UUID,
        owner_id: uuid.UUID,
        texts: Optional[Sequence[str]] = None,
        y_true: Optional[Sequence[int]] = None,
        use_reference_test_set: bool = False,
        sample_limit: Optional[int] = None,
        record_observation: bool = True,
        observed_at: Optional[datetime] = None,
    ) -> TelemetryEvaluationResponse:
        """
        End-to-end evaluation flow:
        1. Resolve evaluation dataset (provided samples or deterministic reference test set)
        2. Execute real inference with SpamSMS-LogisticRegression
        3. Calculate actual performance metrics
        4. If requested, persist MonitoringObservation in PhoenixML
        5. Return structured telemetry response
        """
        eval_texts: List[str]
        eval_labels: List[int]

        if use_reference_test_set:
            eval_texts, eval_labels = self.get_reference_test_data(sample_limit=sample_limit)
        elif texts is not None and y_true is not None:
            eval_texts = list(texts)
            eval_labels = list(y_true)
            if sample_limit is not None and sample_limit > 0:
                eval_texts = eval_texts[:sample_limit]
                eval_labels = eval_labels[:sample_limit]
        else:
            raise ValueError("Must provide (texts, y_true) or specify use_reference_test_set=True")

        metrics = self.evaluate_labeled_data(eval_texts, eval_labels)

        obs_record: Optional[MonitoringObservation] = None
        if record_observation and self.obs_repo is not None:
            obs_record = self.record_monitoring_observation(
                metrics=metrics,
                model_id=model_id,
                owner_id=owner_id,
                observed_at=observed_at,
            )

        return TelemetryEvaluationResponse(
            model_id=model_id,
            model_name=self.model_name,
            model_version=self.model_version,
            evaluated_at=observed_at or datetime.now(timezone.utc),
            metrics=metrics,
            observation_id=obs_record.id if obs_record else None,
            observation_recorded=obs_record is not None,
            notes=(
                f"Evaluated {metrics.prediction_count} real predictions using genuine {self.model_name} "
                f"v{self.model_version} artifact. Metrics derived directly from predictions."
            ),
        )
