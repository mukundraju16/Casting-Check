"""Utilities for cleaning and normalizing extracted financial table data."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

import numpy as np
import pandas as pd

TOTAL_KEYWORDS = (
    "total",
    "subtotal",
    "grand total",
    "net total",
)


def clean_number(value: Any) -> float | np.nan:
    """Convert a financial value to float.

    Handles:
    - commas: "1,000" -> 1000
    - bracket negatives: "(1,000)" -> -1000
    - currency symbols and stray whitespace
    - OCR minus variants (–, —)

    Returns np.nan when conversion is not possible.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan

    if isinstance(value, (int, float, np.number)):
        return float(value)

    text = str(value).strip()
    if not text:
        return np.nan

    lowered = text.lower()
    if lowered in {"na", "n/a", "none", "null", "-"}:
        return np.nan

    # Normalize OCR artifacts and symbols.
    text = (
        text.replace("—", "-")
        .replace("–", "-")
        .replace("−", "-")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .replace("₹", "")
    )

    is_bracket_negative = bool(re.match(r"^\(.*\)$", text))
    text = text.strip("()")
    text = text.replace(",", "").replace(" ", "")

    # Keep only digits, decimal point and minus.
    text = re.sub(r"[^0-9.\-]", "", text)

    if text in {"", "-", ".", "-."}:
        return np.nan

    try:
        number = Decimal(text)
    except InvalidOperation:
        return np.nan

    if is_bracket_negative and number > 0:
        number = -number

    return float(number)


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize headers to lowercase snake-like names while preserving uniqueness."""
    seen: dict[str, int] = {}
    new_cols: list[str] = []

    for idx, col in enumerate(df.columns):
        col_text = str(col).strip().lower()
        col_text = re.sub(r"\s+", "_", col_text)
        col_text = re.sub(r"[^a-z0-9_]", "", col_text)
        if not col_text:
            col_text = f"column_{idx + 1}"

        seen[col_text] = seen.get(col_text, 0) + 1
        if seen[col_text] > 1:
            col_text = f"{col_text}_{seen[col_text]}"
        new_cols.append(col_text)

    out = df.copy()
    out.columns = new_cols
    return out


def remove_empty(df: pd.DataFrame) -> pd.DataFrame:
    """Remove fully empty rows and columns."""
    out = df.dropna(how="all").copy()
    out = out.dropna(axis=1, how="all")
    return out


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply standard cleaning pipeline."""
    out = remove_empty(df)
    out = normalize_headers(out)

    for col in out.columns:
        cleaned = out[col].apply(clean_number)
        # Convert to numeric only if majority looks numeric.
        numeric_ratio = cleaned.notna().mean() if len(cleaned) else 0.0
        if numeric_ratio >= 0.5:
            out[col] = cleaned

    return out
