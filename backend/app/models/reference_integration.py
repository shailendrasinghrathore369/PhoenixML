"""
Reference ML Model Integration for PhoenixML Model Registry.

This module bridges the offline-trained reference Spam ML pipeline
(ml_pipeline/artifacts/spam_classifier_v1.joblib) and PhoenixML's
existing Model Registry without requiring architectural database redesign.

Scope & Architecture:
- PhoenixML is a decision-support MLOps platform with mandatory Human-in-the-Loop.
- It does NOT perform autonomous retraining, deployment, or rollbacks.
- This integration registers the genuine trained reference model metadata and
  its artifact path into the existing `registered_models` schema.
- Because the existing `registered_models` table does not feature dedicated
  columns for artifact URIs or semantic versions, structured metadata is
  cleanly encoded in the `description` field while maintaining strict compatibility.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from app.models.models import ModelStatus, RegisteredModel
from app.models.repository import RegisteredModelRepository
from app.models.schemas import ModelCreate

logger = logging.getLogger(__name__)

# Canonical metadata and artifact filenames
DEFAULT_METADATA_FILENAME = "model_metadata.json"
DEFAULT_ARTIFACT_FILENAME = "spam_classifier_v1.joblib"


def get_workspace_root() -> Path:
    """Resolve the root directory of the PhoenixML workspace."""
    current = Path(__file__).resolve()
    # Path(__file__) is backend/app/models/reference_integration.py
    # .parent -> app/models
    # .parent.parent -> app
    # .parent.parent.parent -> backend
    # .parent.parent.parent.parent -> PhoenixML root
    workspace_root = current.parent.parent.parent.parent
    if (workspace_root / "ml_pipeline").exists():
        return workspace_root
    
    # Fallback to current working directory or its parent
    cwd = Path.cwd().resolve()
    if (cwd / "ml_pipeline").exists():
        return cwd
    if (cwd.parent / "ml_pipeline").exists():
        return cwd.parent

    return workspace_root


def find_reference_metadata_file(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Locate the reference model metadata JSON file.
    
    Searches custom_path first, then default locations in ml_pipeline.
    """
    if custom_path:
        p = Path(custom_path).resolve()
        if p.is_file():
            return p
        raise FileNotFoundError(f"Custom model metadata file not found: {custom_path}")

    ws_root = get_workspace_root()
    candidates: List[Path] = [
        ws_root / "ml_pipeline" / "artifacts" / DEFAULT_METADATA_FILENAME,
        ws_root / "ml_pipeline" / DEFAULT_METADATA_FILENAME,
        Path.cwd().resolve() / "ml_pipeline" / "artifacts" / DEFAULT_METADATA_FILENAME,
        Path.cwd().resolve() / "ml_pipeline" / DEFAULT_METADATA_FILENAME,
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        f"Reference model metadata file '{DEFAULT_METADATA_FILENAME}' not found in candidates: "
        f"{[str(c) for c in candidates]}"
    )


def find_reference_artifact_file(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Locate the reference model serialized artifact file (.joblib).
    
    Searches custom_path first, then default locations in ml_pipeline.
    """
    if custom_path:
        p = Path(custom_path).resolve()
        if p.is_file():
            return p
        raise FileNotFoundError(f"Custom model artifact file not found: {custom_path}")

    ws_root = get_workspace_root()
    candidates: List[Path] = [
        ws_root / "ml_pipeline" / "artifacts" / DEFAULT_ARTIFACT_FILENAME,
        ws_root / "ml_pipeline" / DEFAULT_ARTIFACT_FILENAME,
        Path.cwd().resolve() / "ml_pipeline" / "artifacts" / DEFAULT_ARTIFACT_FILENAME,
        Path.cwd().resolve() / "ml_pipeline" / DEFAULT_ARTIFACT_FILENAME,
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        f"Reference model artifact file '{DEFAULT_ARTIFACT_FILENAME}' not found in candidates: "
        f"{[str(c) for c in candidates]}"
    )


def load_reference_metadata(custom_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load and parse the reference model metadata JSON."""
    meta_path = find_reference_metadata_file(custom_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_reference_model_description(
    metadata: Dict[str, Any],
    artifact_path: Union[str, Path],
    relative_to_workspace: bool = True,
) -> str:
    """
    Format a structured description string encoding version, artifact reference,
    dataset summary, and metrics within the 1000-character column limit.
    """
    version = metadata.get("model_version", "1.0.0")
    
    art_path = Path(artifact_path)
    if relative_to_workspace:
        ws_root = get_workspace_root()
        try:
            display_art = art_path.relative_to(ws_root).as_posix()
        except ValueError:
            display_art = art_path.as_posix()
    else:
        display_art = art_path.as_posix()

    dataset_info = metadata.get("dataset", {})
    dataset_name = dataset_info.get("name", "UCI SMS Spam Collection")
    total_samples = dataset_info.get("total_samples", 5574)

    metrics = metadata.get("evaluation_metrics", {})
    acc = metrics.get("accuracy", 0.0)
    prec = metrics.get("precision", 0.0)
    rec = metrics.get("recall", 0.0)
    f1 = metrics.get("f1_score", 0.0)

    desc = (
        f"v{version} | "
        f"Artifact: {display_art} | "
        f"Dataset: {dataset_name} ({total_samples} samples) | "
        f"Metrics: acc={acc:.4f}, prec={prec:.4f}, rec={rec:.4f}, f1={f1:.4f} | "
        f"Local reference deployment"
    )

    # Ensure strict adherence to String(1000) max length
    return desc[:1000]


def parse_reference_model_description(description: Optional[str]) -> Dict[str, Any]:
    """
    Parse back structured metadata embedded within the model description.
    """
    result: Dict[str, Any] = {
        "version": None,
        "artifact_path": None,
        "dataset": None,
        "metrics": {},
        "raw": description or "",
    }
    if not description:
        return result

    # Extract version: v1.0.0
    v_match = re.search(r"\bv(\d+\.\d+(?:\.\d+)?)\b", description)
    if v_match:
        result["version"] = v_match.group(1)

    # Extract artifact path: Artifact: ... |
    art_match = re.search(r"Artifact:\s*([^|]+)", description)
    if art_match:
        result["artifact_path"] = art_match.group(1).strip()

    # Extract dataset: Dataset: ... |
    ds_match = re.search(r"Dataset:\s*([^|]+)", description)
    if ds_match:
        result["dataset"] = ds_match.group(1).strip()

    # Extract metrics: acc=0.9901, prec=0.9600, ...
    metric_matches = re.findall(r"(acc|prec|rec|f1)=([0-9\.]+)", description)
    for k, v in metric_matches:
        try:
            result["metrics"][k] = float(v)
        except ValueError:
            pass

    return result


def build_reference_model_payload(
    metadata_path: Optional[Union[str, Path]] = None,
    artifact_path: Optional[Union[str, Path]] = None,
    name: Optional[str] = None,
    include_version_in_name: bool = False,
    status: ModelStatus = ModelStatus.ACTIVE,
) -> ModelCreate:
    """
    Construct the ModelCreate Pydantic schema for the reference Spam model.
    """
    meta = load_reference_metadata(metadata_path)
    real_artifact = find_reference_artifact_file(artifact_path)

    base_name = name or meta.get("model_name", "SpamSMS-LogisticRegression")
    version = meta.get("model_version", "1.0.0")
    if include_version_in_name and not base_name.endswith(f":v{version}"):
        model_name = f"{base_name}:v{version}"
    else:
        model_name = base_name

    framework = meta.get("framework", "scikit-learn")
    # Clean framework casing to conform to common standards
    if framework.lower() == "scikit-learn":
        framework = "scikit-learn"

    algorithm = "TF-IDF + Logistic Regression"

    description = format_reference_model_description(
        metadata=meta,
        artifact_path=real_artifact,
        relative_to_workspace=True,
    )

    return ModelCreate(
        name=model_name,
        description=description,
        framework=framework,
        algorithm=algorithm,
        status=status,
    )


def register_reference_spam_model(
    db: Session,
    owner_id: uuid.UUID,
    metadata_path: Optional[Union[str, Path]] = None,
    artifact_path: Optional[Union[str, Path]] = None,
    name: Optional[str] = None,
    include_version_in_name: bool = False,
    allow_duplicate: bool = False,
    status: ModelStatus = ModelStatus.ACTIVE,
) -> RegisteredModel:
    """
    Register the real trained Spam model into PhoenixML's Model Registry.
    
    If allow_duplicate is False and a model with the same name already exists
    for this owner, returns the existing RegisteredModel (idempotent registration).
    Otherwise creates and commits a new record.
    """
    repo = RegisteredModelRepository(db)
    payload = build_reference_model_payload(
        metadata_path=metadata_path,
        artifact_path=artifact_path,
        name=name,
        include_version_in_name=include_version_in_name,
        status=status,
    )

    if not allow_duplicate:
        existing = repo.get_by_name(payload.name, owner_id=owner_id)
        if existing:
            logger.info("Reference model '%s' already registered (ID: %s)", existing.name, existing.id)
            return existing

    created = repo.create(payload, owner_id=owner_id)
    logger.info(
        "Successfully registered reference spam model '%s' (ID: %s, Status: %s)",
        created.name,
        created.id,
        created.status,
    )
    return created


def run_standalone_registration() -> None:
    """
    CLI/Standalone runner to register the reference model into the local database.
    """
    from app.db.database import SessionLocal
    from app.users.models import User, UserRole

    db = SessionLocal()
    try:
        # Locate or pick an admin / active user
        user = db.query(User).filter(User.role.in_([UserRole.ADMIN, UserRole.ML_ENGINEER])).first()
        if not user:
            user = db.query(User).first()
        if not user:
            print("Error: No existing user found in database to assign as model owner.")
            return

        print(f"Using owner: {user.email} (ID: {user.id})")
        model = register_reference_spam_model(db, owner_id=user.id)
        print("Registration complete:")
        print(f"  Model ID:   {model.id}")
        print(f"  Name:       {model.name}")
        print(f"  Framework:  {model.framework}")
        print(f"  Algorithm:  {model.algorithm}")
        print(f"  Status:     {model.status}")
        print(f"  Description:{model.description}")
    finally:
        db.close()


if __name__ == "__main__":
    run_standalone_registration()
