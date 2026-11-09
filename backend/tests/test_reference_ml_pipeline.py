"""
Tests for Reference SMS Spam Classification Pipeline.

Validates:
1. Dataset loading and preprocessing normalization.
2. Pipeline training, evaluation metrics, and metadata generation.
3. Saved model artifact loading and integrity.
4. Inference output validity, probability constraints, and schema conformance.
5. Deterministic and reproducible classification behavior.
"""

import math
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure repository root is on sys.path for importing ml_pipeline
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import joblib
from sklearn.pipeline import Pipeline

from ml_pipeline.preprocessor import clean_text
from ml_pipeline.data_loader import load_sms_spam_data, get_data_summary, DEFAULT_DATA_FILE
from ml_pipeline.train import train_spam_model, DEFAULT_MODEL_FILE, DEFAULT_METADATA_FILE
from ml_pipeline.predict import SpamPredictor


# ---------------------------------------------------------------------------
# 1. Dataset Loading and Preprocessing Tests
# ---------------------------------------------------------------------------

def test_clean_text_normalizes_urls_and_emails():
    raw = "Visit http://example.com/promo or www.spam.co.uk and email us at win@prizes.org now!"
    cleaned = clean_text(raw)
    assert "httpaddr" in cleaned
    assert "http://example.com/promo" not in cleaned
    assert "www.spam.co.uk" not in cleaned
    assert "emailaddr" in cleaned
    assert "win@prizes.org" not in cleaned


def test_clean_text_normalizes_currency_and_numbers():
    raw = "You won $1000 or £500 cash! Call 09061701461 to claim your €100 bonus."
    cleaned = clean_text(raw)
    assert "moneysymb" in cleaned
    assert "$" not in cleaned
    assert "£" not in cleaned
    assert "€" not in cleaned
    assert "phonenumber" in cleaned
    assert "09061701461" not in cleaned


def test_clean_text_handles_null_empty_and_whitespace():
    assert clean_text(None) == ""
    assert clean_text("") == ""
    assert clean_text("   \t  \n  ") == ""
    # Collapses multiple whitespace and lowercases
    assert clean_text("  HELLO   WORLD  ") == "hello world"


def test_data_loader_returns_valid_dataset():
    texts, labels = load_sms_spam_data()
    assert len(texts) == 5574
    assert len(labels) == 5574
    # Binary labels only (0 for ham, 1 for spam)
    assert set(labels) == {0, 1}
    # Expected UCI class distribution
    assert sum(labels) == 747  # spam count
    assert (len(labels) - sum(labels)) == 4827  # ham count


def test_data_summary_distribution():
    texts = ["msg1", "msg2", "msg3", "msg4"]
    labels = [0, 0, 1, 0]
    summary = get_data_summary(texts, labels)
    assert summary["total_samples"] == 4
    assert summary["ham_count"] == 3
    assert summary["spam_count"] == 1
    assert math.isclose(summary["ham_ratio"], 0.75)
    assert math.isclose(summary["spam_ratio"], 0.25)


# ---------------------------------------------------------------------------
# 2. Pipeline Training and Evaluation Tests
# ---------------------------------------------------------------------------

def test_pipeline_training_and_metrics():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pipeline, metadata = train_spam_model(
            output_dir=tmp_path,
            random_state=42,
            test_size=0.20,
            verbose=False,
        )

        metrics = metadata["evaluation_metrics"]
        assert metrics["accuracy"] >= 0.95
        assert metrics["precision"] >= 0.90
        assert metrics["recall"] >= 0.90
        assert metrics["f1_score"] >= 0.90

        cm = metrics["confusion_matrix"]
        assert cm["true_negatives"] > 0
        assert cm["true_positives"] > 0
        # Sum of confusion matrix equals test sample count (1115)
        total_test = cm["true_negatives"] + cm["false_positives"] + cm["false_negatives"] + cm["true_positives"]
        assert total_test == metadata["data_split"]["test_samples"]
        assert total_test == 1115


def test_training_metadata_completeness():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        _, metadata = train_spam_model(
            output_dir=tmp_path,
            random_state=42,
            verbose=False,
        )

        # Validate mandatory metadata fields
        assert metadata["model_name"] == "SpamSMS-LogisticRegression"
        assert metadata["model_version"] == "1.0.0"
        assert metadata["algorithm"] == "Logistic Regression"
        assert metadata["framework"] == "Scikit-Learn"
        assert "dataset" in metadata
        assert metadata["dataset"]["total_samples"] == 5574
        assert "data_split" in metadata
        assert metadata["data_split"]["training_samples"] == 4459
        assert metadata["data_split"]["test_samples"] == 1115
        assert "feature_extraction" in metadata
        assert metadata["feature_extraction"]["method"] == "TF-IDF"
        assert "training_timestamp" in metadata
        assert (tmp_path / "model_metadata.json").exists()


# ---------------------------------------------------------------------------
# 3. Saved Model Loading Tests
# ---------------------------------------------------------------------------

def test_saved_model_artifact_loading():
    assert DEFAULT_MODEL_FILE.exists(), "Default model artifact should exist before loading test"
    loaded_pipe = joblib.load(DEFAULT_MODEL_FILE)
    assert isinstance(loaded_pipe, Pipeline)
    assert "tfidf" in loaded_pipe.named_steps
    assert "clf" in loaded_pipe.named_steps


def test_predictor_missing_model_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        SpamPredictor(model_path=Path("nonexistent_path/model.joblib"))


# ---------------------------------------------------------------------------
# 4. Inference Output Validity Tests
# ---------------------------------------------------------------------------

def test_predictor_single_output_structure():
    predictor = SpamPredictor()
    res = predictor.predict_single("Hey are you coming to lunch today?")

    assert isinstance(res, dict)
    assert "text" in res
    assert "predicted_label" in res
    assert res["predicted_label"] in ("ham", "spam")
    assert "label_id" in res
    assert res["label_id"] in (0, 1)
    assert "is_spam" in res
    assert isinstance(res["is_spam"], bool)
    assert "spam_probability" in res
    assert "ham_probability" in res
    assert "confidence" in res
    assert 0.0 <= res["spam_probability"] <= 1.0
    assert 0.0 <= res["ham_probability"] <= 1.0
    assert 0.5 <= res["confidence"] <= 1.0
    # Probabilities sum to 1.0
    assert math.isclose(res["spam_probability"] + res["ham_probability"], 1.0, abs_tol=1e-3)


def test_predictor_batch_inference():
    predictor = SpamPredictor()
    messages = [
        "Hey, call me later when you are free.",
        "URGENT: You won a £2000 cash prize! Call 09061701461 to claim.",
        "Can we reschedule our meeting to 3pm?",
    ]
    results = predictor.predict(messages)
    assert len(results) == 3
    assert results[0]["predicted_label"] == "ham"
    assert results[1]["predicted_label"] == "spam"
    assert results[2]["predicted_label"] == "ham"


def test_predictor_empty_input():
    predictor = SpamPredictor()
    assert predictor.predict([]) == []


# ---------------------------------------------------------------------------
# 5. Deterministic and Reproducible Behavior Tests
# ---------------------------------------------------------------------------

def test_deterministic_ham_predictions():
    predictor = SpamPredictor()
    ham_samples = [
        "Hey, are you free for lunch tomorrow at 12?",
        "Can you pick up some groceries on your way home?",
        "See you at the office later today.",
        "Thanks for helping with the project earlier!",
    ]
    for text in ham_samples:
        res = predictor.predict_single(text)
        assert res["predicted_label"] == "ham", f"Expected ham for: {text}"
        assert res["is_spam"] is False
        assert res["ham_probability"] > 0.80


def test_deterministic_spam_predictions():
    predictor = SpamPredictor()
    spam_samples = [
        "WINNER! You have been selected for a £1000 cash prize! Text CLAIM to 88888 to collect.",
        "URGENT! Your mobile number won guaranteed $5000 cash. Call 09061701461 now to claim your award.",
        "Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121.",
        "Congratulations! You have won a free vacation to Hawaii. Call 0800123456 to receive your tickets.",
    ]
    for text in spam_samples:
        res = predictor.predict_single(text)
        assert res["predicted_label"] == "spam", f"Expected spam for: {text}"
        assert res["is_spam"] is True
        assert res["spam_probability"] > 0.70


def test_prediction_reproducibility():
    predictor = SpamPredictor()
    test_message = "Urgent: call now to claim your cash bonus of $500."
    pred1 = predictor.predict_single(test_message)
    pred2 = predictor.predict_single(test_message)

    assert pred1["predicted_label"] == pred2["predicted_label"]
    assert pred1["spam_probability"] == pred2["spam_probability"]
    assert pred1["confidence"] == pred2["confidence"]
