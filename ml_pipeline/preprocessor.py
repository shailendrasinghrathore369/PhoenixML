"""
Text Preprocessing for Spam SMS Classification.

Provides deterministic, reproducible text normalization:
- Lowercases text
- Normalizes URLs to a canonical token 'httpaddr'
- Normalizes email addresses to 'emailaddr'
- Normalizes currency symbols to 'moneysymb'
- Normalizes phone numbers / numeric sequences to 'phonenumber'
- Strips excessive whitespace
"""

import re
from typing import Optional


def clean_text(text: Optional[str]) -> str:
    """
    Clean and normalize raw SMS message text.

    Args:
        text: Raw SMS message string.

    Returns:
        Cleaned, normalized string.
    """
    if text is None or not isinstance(text, str):
        return ""

    # Strip surrounding whitespace
    cleaned = text.strip()

    # Normalize URLs
    cleaned = re.sub(r"https?://\S+|www\.\S+", " httpaddr ", cleaned, flags=re.IGNORECASE)

    # Normalize email addresses
    cleaned = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", " emailaddr ", cleaned)

    # Normalize currency symbols ($ £ € ¥)
    cleaned = re.sub(r"[$£€¥]", " moneysymb ", cleaned)

    # Normalize phone numbers or digit sequences commonly used in spam texts (7-14 digits)
    cleaned = re.sub(r"\b\d{7,14}\b", " phonenumber ", cleaned)

    # Collapse multiple whitespace characters into a single space and lowercase
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()

    return cleaned
