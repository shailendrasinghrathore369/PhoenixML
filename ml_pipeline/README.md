# Reference SMS Spam Classification Pipeline

A reproducible reference machine learning pipeline for binary SMS spam classification (`ham` vs. `spam`), trained on the real public UCI SMS Spam Collection dataset.

This pipeline produces serialized model artifacts and metadata descriptors designed for registration, evaluation, and monitoring within the **PhoenixML** decision-support platform.

> [!IMPORTANT]
> **PhoenixML Decision-Support Boundary**:
> This pipeline is a standalone demonstration tool. PhoenixML is an MLOps decision-support platform requiring mandatory Human-in-the-Loop (HITL) approval. PhoenixML did **not** train this model autonomously and does **not** perform autonomous retraining, deployment, or self-healing rollbacks.

---

## 1. Model Architecture & Pipeline Specification

The classifier is constructed as a unified scikit-learn `Pipeline` encapsulating text preprocessing, feature extraction, and probabilistic classification:

| Component | Implementation | Parameters / Details |
| :--- | :--- | :--- |
| **Task** | Binary Text Classification | Classes: `0 = ham`, `1 = spam` |
| **Preprocessing** | Regex Normalization (`clean_text`) | URL (`httpaddr`), Email (`emailaddr`), Currency (`moneysymb`), Phone (`phonenumber`), Whitespace collapsing, Lowercasing |
| **Feature Extraction** | `TfidfVectorizer` | Unigrams + Bigrams (`ngram_range=(1, 2)`), `min_df=2`, `sublinear_tf=True`, English stop words, 7,173 features |
| **Classification** | `LogisticRegression` | `C=10.0`, `class_weight='balanced'`, `max_iter=1000`, `solver='lbfgs'`, `random_state=42` |
| **Serialization** | `joblib` | Single `.joblib` pipeline artifact containing vectorizer + classifier |

---

## 2. Dataset Information & Provenance

- **Dataset**: [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection)
- **Citation**: Almeida, T.A., Gómez Hidalgo, J.M., Yamakami, A. (2011). *Contributions to the Study of SMS Spam Filtering: New Collection and Results*. ACM DocEng'11.
- **Total Samples**: 5,574 messages
- **Class Distribution**:
  - `ham`: 4,827 samples (86.60%)
  - `spam`: 747 samples (13.40%)
- **Data Split**: Stratified 80% Train / 20% Holdout Test (`random_state=42`)
  - **Training Set**: 4,459 samples (3,861 ham, 598 spam)
  - **Holdout Test Set**: 1,115 samples (966 ham, 149 spam)

---

## 3. Evaluation Metrics

Evaluated on the 1,115 holdout test samples:

| Metric | Score | Percentage |
| :--- | :--- | :--- |
| **Accuracy** | 0.9901 | 99.01% |
| **Precision (Spam)** | 0.9600 | 96.00% |
| **Recall (Spam)** | 0.9664 | 96.64% |
| **F1 Score (Spam)** | 0.9632 | 96.32% |

### Confusion Matrix
```
                  Predicted HAM    Predicted SPAM
Actual HAM:            960               6      (TN=960, FP=6)
Actual SPAM:             5             144      (FN=5,  TP=144)
```

---

## 4. Usage & Training Instructions

### Training the Reference Model
To re-train the model deterministically and update artifacts:
```bash
python -m ml_pipeline.train
```

Artifacts produced:
- **Model Pipeline**: `ml_pipeline/artifacts/spam_classifier_v1.joblib`
- **Metadata Descriptor**: `ml_pipeline/artifacts/model_metadata.json`

### Running Inference via CLI
Run verification examples:
```bash
python -m ml_pipeline.predict
```

Classify a single custom message:
```bash
python -m ml_pipeline.predict "Free entry in a weekly competition! Text WIN to 87121."
```

JSON output:
```bash
python -m ml_pipeline.predict "Hey are you coming over tonight?" --json
```

### Python API Integration
```python
from ml_pipeline import SpamPredictor

predictor = SpamPredictor()

# Single prediction
result = predictor.predict_single("Urgent! You have won $1000 cash. Call now!")
print(result["predicted_label"])  # "spam"
print(result["confidence"])       # 0.999...

# Batch predictions
batch_results = predictor.predict([
    "Are we still on for lunch tomorrow?",
    "Claim your £500 gift card today at http://claim-prize.com"
])
```
