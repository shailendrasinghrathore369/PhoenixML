"""
Dataset Loader for the UCI SMS Spam Collection.

Provides reproducible data acquisition and ingestion for the SMS Spam Collection dataset.
Dataset source:
    UCI Machine Learning Repository: SMS Spam Collection
    Almeida, T.A., Gómez Hidalgo, J.M., Yamakami, A. (2011)
    https://archive.ics.uci.edu/dataset/228/sms+spam+collection
"""

import io
import os
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

UCI_SPAM_ZIP_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
FALLBACK_RAW_URL = "https://raw.githubusercontent.com/al-one/SMS-Spam-Classification/master/SMSSpamCollection"

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_DATA_FILE = DEFAULT_DATA_DIR / "SMSSpamCollection"


def download_sms_spam_data(target_path: Optional[Path] = None) -> Path:
    """
    Downloads and extracts the UCI SMS Spam Collection dataset if not already present.

    Args:
        target_path: Destination file path for the extracted SMSSpamCollection file.

    Returns:
        Path to the saved SMSSpamCollection file.
    """
    dest = target_path or DEFAULT_DATA_FILE
    dest.parent.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PhoenixML/1.0"}

    # Attempt primary UCI URL
    try:
        req = urllib.request.Request(UCI_SPAM_ZIP_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            zip_bytes = io.BytesIO(response.read())
            with zipfile.ZipFile(zip_bytes) as z:
                raw_bytes = z.read("SMSSpamCollection")
                with open(dest, "wb") as f:
                    f.write(raw_bytes)
                return dest
    except Exception as uci_err:
        # Attempt fallback mirror
        try:
            req = urllib.request.Request(FALLBACK_RAW_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as response:
                content = response.read()
                with open(dest, "wb") as f:
                    f.write(content)
                return dest
        except Exception as fallback_err:
            raise RuntimeError(
                f"Failed to acquire SMS Spam Collection dataset from both primary ({uci_err}) "
                f"and fallback ({fallback_err}) sources. Please ensure internet connectivity "
                f"or manually place 'SMSSpamCollection' at: {dest}"
            ) from fallback_err


def load_sms_spam_data(
    data_path: Optional[Path] = None, force_download: bool = False
) -> Tuple[List[str], List[int]]:
    """
    Loads raw SMS messages and binary classification labels from disk or remote source.

    Labels:
        0 = ham (legitimate)
        1 = spam (unsolicited commercial/phishing)

    Args:
        data_path: Optional custom path to SMSSpamCollection file.
        force_download: If True, re-downloads the dataset even if present locally.

    Returns:
        Tuple of (texts: List[str], labels: List[int])
    """
    path = data_path or DEFAULT_DATA_FILE
    if force_download or not path.exists():
        path = download_sms_spam_data(path)

    texts: List[str] = []
    labels: List[int] = []

    # Read tab-delimited file with latin-1 encoding per dataset specification
    with open(path, "r", encoding="latin-1") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue

            raw_label, text = parts[0].strip().lower(), parts[1].strip()
            if raw_label == "spam":
                label_id = 1
            elif raw_label == "ham":
                label_id = 0
            else:
                continue

            texts.append(text)
            labels.append(label_id)

    if not texts:
        raise ValueError(f"No valid records found in dataset at {path}")

    return texts, labels


def get_data_summary(texts: List[str], labels: List[int]) -> Dict[str, Any]:
    """
    Generates summary statistics for a dataset split.
    """
    total = len(labels)
    if total == 0:
        return {
            "total_samples": 0,
            "ham_count": 0,
            "spam_count": 0,
            "ham_ratio": 0.0,
            "spam_ratio": 0.0,
        }

    spam_count = sum(labels)
    ham_count = total - spam_count

    return {
        "total_samples": total,
        "ham_count": ham_count,
        "spam_count": spam_count,
        "ham_ratio": round(ham_count / total, 4),
        "spam_ratio": round(spam_count / total, 4),
    }
