"""
Reference Training Pipeline for SMS Spam Classification.

Trains a reproducible reference binary classifier using TF-IDF feature extraction
and Logistic Regression with a stratified train/test split on the UCI SMS Spam Collection.

Produces:
    - Serialized sklearn Pipeline artifact (.joblib)
    - Comprehensive metadata descriptor (.json)

DISCLAIMER:
    This is an offline reference training pipeline for PhoenixML demonstration.
    PhoenixML is an MLOps decision-support platform with mandatory human approval
    and does not autonomously train, deploy, or rollback models.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from ml_pipeline.data_loader import (
    DEFAULT_DATA_FILE,
    get_data_summary,
    load_sms_spam_data,
)
from ml_pipeline.preprocessor import clean_text

DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
DEFAULT_MODEL_FILE = DEFAULT_ARTIFACTS_DIR / "spam_classifier_v1.joblib"
DEFAULT_METADATA_FILE = DEFAULT_ARTIFACTS_DIR / "model_metadata.json"

DETERMINISTIC_EXAMPLES = [
    "Hey, are you free for lunch tomorrow at 12?",
    "Can you pick up some groceries on your way home from work?",
    "WINNER! You have been selected for a £1000 cash prize! Text CLAIM to 88888 to collect.",
    "URGENT! Your mobile number won guaranteed $5000 cash. Call 09061701461 now to claim your award.",
]


def train_spam_model(
    data_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    model_filename: str = "spam_classifier_v1.joblib",
    metadata_filename: str = "model_metadata.json",
    random_state: int = 42,
    test_size: float = 0.20,
    c_param: float = 10.0,
    max_iter: int = 1000,
    verbose: bool = True,
) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Trains a reference SMS Spam classifier and saves the serialized Pipeline and metadata.

    Args:
        data_path: Path to dataset file (defaults to ml_pipeline/data/SMSSpamCollection).
        output_dir: Directory to save serialized artifacts.
        model_filename: Name of the joblib model artifact.
        metadata_filename: Name of the metadata json file.
        random_state: Seed for reproducibility.
        test_size: Proportion of dataset allocated to the holdout test set.
        c_param: Inverse regularization strength for Logistic Regression.
        max_iter: Maximum iterations for Logistic Regression solver.
        verbose: If True, prints training metrics and example predictions.

    Returns:
        Tuple of (fitted_pipeline, metadata_dictionary)
    """
    out_dir = output_dir or DEFAULT_ARTIFACTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / model_filename
    metadata_path = out_dir / metadata_filename

    # 1. Load dataset
    if verbose:
        print("[1/5] Loading SMS Spam Collection dataset...")
    texts, labels = load_sms_spam_data(data_path=data_path)
    full_summary = get_data_summary(texts, labels)

    if verbose:
        print(f"      Total samples: {full_summary['total_samples']} "
              f"({full_summary['ham_count']} ham, {full_summary['spam_count']} spam)")

    # 2. Stratified train/test split
    if verbose:
        print(f"[2/5] Creating stratified train/test split (test_size={test_size}, seed={random_state})...")
    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )
    train_summary = get_data_summary(X_train, y_train)
    test_summary = get_data_summary(X_test, y_test)

    # 3. Build & fit pipeline
    if verbose:
        print("[3/5] Fitting TF-IDF + Logistic Regression pipeline...")
    pipeline = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                preprocessor=clean_text,
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=2,
                sublinear_tf=True,
            ),
        ),
        (
            "clf",
            LogisticRegression(
                C=c_param,
                class_weight="balanced",
                max_iter=max_iter,
                random_state=random_state,
                solver="lbfgs",
            ),
        ),
    ])

    pipeline.fit(X_train, y_train)

    # 4. Evaluate on holdout test set
    if verbose:
        print("[4/5] Evaluating model on holdout test set...")
    y_pred = pipeline.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    cm = confusion_matrix(y_test, y_pred)
    cm_dict = {
        "true_negatives": int(cm[0, 0]),
        "false_positives": int(cm[0, 1]),
        "false_negatives": int(cm[1, 0]),
        "true_positives": int(cm[1, 1]),
    }

    vocab_size = len(pipeline.named_steps["tfidf"].vocabulary_)

    # 5. Assemble metadata
    metadata = {
        "model_name": "SpamSMS-LogisticRegression",
        "model_version": "1.0.0",
        "algorithm": "Logistic Regression",
        "classifier_type": "Binary Classifier",
        "framework": "Scikit-Learn",
        "framework_version": sklearn.__version__,
        "target_classes": {
            "0": "ham",
            "1": "spam",
        },
        "positive_class": "spam",
        "dataset": {
            "name": "SMS Spam Collection Dataset",
            "source": "UCI Machine Learning Repository (https://archive.ics.uci.edu/dataset/228/sms+spam+collection)",
            "total_samples": full_summary["total_samples"],
            "class_distribution": full_summary,
        },
        "data_split": {
            "test_size": test_size,
            "random_state": random_state,
            "stratified": True,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "train_class_distribution": train_summary,
            "test_class_distribution": test_summary,
        },
        "feature_extraction": {
            "method": "TF-IDF",
            "ngram_range": [1, 2],
            "stop_words": "english",
            "min_df": 2,
            "sublinear_tf": True,
            "vocabulary_size": vocab_size,
        },
        "hyperparameters": {
            "C": c_param,
            "class_weight": "balanced",
            "max_iter": max_iter,
            "random_state": random_state,
            "solver": "lbfgs",
        },
        "evaluation_metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": cm_dict,
        },
        "artifact": {
            "filename": model_filename,
            "format": "joblib",
            "pipeline_steps": ["tfidf", "clf"],
        },
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "notes": (
            "Reference ML model artifact trained for PhoenixML demonstration and decision-support "
            "monitoring. PhoenixML is a decision-support platform with mandatory human approval "
            "and does not perform autonomous training, deployment, or rollbacks."
        ),
    }

    # Save artifact
    if verbose:
        print(f"[5/5] Saving model artifact to {model_path}...")
    joblib.dump(pipeline, model_path)

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    if verbose:
        print("\n" + "=" * 50)
        print("MODEL TRAINING COMPLETE")
        print("=" * 50)
        print(f"Accuracy:         {acc:.4f} ({acc * 100:.2f}%)")
        print(f"Precision (Spam): {prec:.4f} ({prec * 100:.2f}%)")
        print(f"Recall (Spam):    {rec:.4f} ({rec * 100:.2f}%)")
        print(f"F1 Score:         {f1:.4f} ({f1 * 100:.2f}%)")
        print(f"Confusion Matrix: TN={cm_dict['true_negatives']}, FP={cm_dict['false_positives']}, "
              f"FN={cm_dict['false_negatives']}, TP={cm_dict['true_positives']}")
        print(f"Vocabulary Size:  {vocab_size} n-grams")
        print(f"Model Artifact:   {model_path}")
        print(f"Metadata File:    {metadata_path}")
        print("\nVerification Examples:")
        probs = pipeline.predict_proba(DETERMINISTIC_EXAMPLES)
        for text, prob in zip(DETERMINISTIC_EXAMPLES, probs):
            pred_lbl = "SPAM" if prob[1] >= 0.5 else "HAM"
            conf = max(prob)
            print(f"  [{pred_lbl}] (conf: {conf:.4f}, spam_p: {prob[1]:.4f}) -> \"{text}\"")
        print("=" * 50)

    return pipeline, metadata


if __name__ == "__main__":
    train_spam_model()
