"""
Reference ML Pipeline for SMS Spam Classification.

Demonstration pipeline producing trained model artifacts and evaluation metadata
for subsequent registration and monitoring in PhoenixML.

NOTE:
PhoenixML is an MLOps decision-support platform with mandatory human approval.
PhoenixML does not perform autonomous training, deployment, or rollback.
"""

from ml_pipeline.preprocessor import clean_text
from ml_pipeline.data_loader import load_sms_spam_data, get_data_summary
from ml_pipeline.train import train_spam_model
from ml_pipeline.predict import SpamPredictor

__all__ = [
    "clean_text",
    "load_sms_spam_data",
    "get_data_summary",
    "train_spam_model",
    "SpamPredictor",
]
