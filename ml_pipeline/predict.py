"""
Inference Utility for the Reference SMS Spam Classifier.

Loads the serialized sklearn Pipeline artifact and executes binary classification
inference (ham vs. spam) on raw SMS text messages.

DISCLAIMER:
    This utility provides standalone inference demonstration for reference models.
    PhoenixML is an MLOps decision-support platform with mandatory human approval.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import joblib
from sklearn.pipeline import Pipeline

from ml_pipeline.train import DEFAULT_METADATA_FILE, DEFAULT_MODEL_FILE


class SpamPredictor:
    """
    Inference wrapper for the trained SMS spam classification pipeline.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        metadata_path: Optional[Union[str, Path]] = None,
    ):
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_FILE
        self.metadata_path = Path(metadata_path) if metadata_path else DEFAULT_METADATA_FILE

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Trained model artifact not found at {self.model_path}. "
                "Please run 'python -m ml_pipeline.train' first."
            )

        # Load serialized pipeline artifact
        self.pipeline: Pipeline = joblib.load(self.model_path)

        # Load metadata if present
        self.metadata: Dict[str, Any] = {}
        if self.metadata_path.exists():
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

    @property
    def model_name(self) -> str:
        return self.metadata.get("model_name", "SpamSMS-LogisticRegression")

    @property
    def model_version(self) -> str:
        return self.metadata.get("model_version", "1.0.0")

    def predict_single(self, text: str) -> Dict[str, Any]:
        """
        Predicts class and probability for a single SMS message.

        Args:
            text: Raw SMS message string.

        Returns:
            Dictionary containing prediction outcome, probabilities, and confidence.
        """
        results = self.predict([text])
        return results[0]

    def predict(self, texts: Union[str, Sequence[str]]) -> List[Dict[str, Any]]:
        """
        Predicts classes and probabilities for one or multiple SMS messages.

        Args:
            texts: A single text message string or a sequence of message strings.

        Returns:
            List of prediction dictionaries.
        """
        if isinstance(texts, str):
            input_list = [texts]
        else:
            input_list = list(texts)

        if not input_list:
            return []

        # Predict class probabilities via pipeline [P(ham), P(spam)]
        probabilities = self.pipeline.predict_proba(input_list)

        results: List[Dict[str, Any]] = []
        for text, prob in zip(input_list, probabilities):
            ham_prob = float(prob[0])
            spam_prob = float(prob[1])
            is_spam = spam_prob >= 0.5
            predicted_label = "spam" if is_spam else "ham"
            confidence = float(max(ham_prob, spam_prob))

            results.append({
                "text": text,
                "predicted_label": predicted_label,
                "label_id": 1 if is_spam else 0,
                "is_spam": is_spam,
                "spam_probability": round(spam_prob, 4),
                "ham_probability": round(ham_prob, 4),
                "confidence": round(confidence, 4),
                "model_name": self.model_name,
                "model_version": self.model_version,
            })

        return results


def main():
    parser = argparse.ArgumentParser(description="SMS Spam Classification Inference Utility")
    parser.add_argument("text", nargs="?", help="SMS text to classify")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--model-path", help="Path to custom model joblib file")
    args = parser.parse_args()

    predictor = SpamPredictor(model_path=args.model_path)

    if not args.text:
        # Default verification examples
        sample_messages = [
            "Hey, are you free for lunch tomorrow at 12?",
            "Can you pick up some groceries on your way home?",
            "WINNER! You have won a 1000 dollar prize! Text CLAIM to 88888 now to collect.",
            "URGENT! Your mobile number was awarded £5000 cash. Call 09061701461 to claim your reward.",
        ]
        results = predictor.predict(sample_messages)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"Model: {predictor.model_name} (v{predictor.model_version})\n")
            for res in results:
                status = "SPAM" if res["is_spam"] else "HAM"
                print(f"[{status:<4}] (Confidence: {res['confidence'] * 100:5.1f}%, Spam Prob: {res['spam_probability']:.4f})")
                print(f"       Text: \"{res['text']}\"\n")
        return

    result = predictor.predict_single(args.text)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "SPAM" if result["is_spam"] else "HAM"
        print(f"Prediction: {status}")
        print(f"Confidence: {result['confidence'] * 100:.2f}%")
        print(f"Spam Prob:  {result['spam_probability']:.4f}")
        print(f"Ham Prob:   {result['ham_probability']:.4f}")
        print(f"Model:      {result['model_name']} (v{result['model_version']})")


if __name__ == "__main__":
    main()
