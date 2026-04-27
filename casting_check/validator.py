"""Validation logic for casting and rounding checks."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data_cleaner import TOTAL_KEYWORDS


@dataclass
class ValidationRecord:
    table_name: str
    column_name: str
    reported_total: float
    computed_total: float
    difference: float
    status: str
    row_index: int


def detect_numeric_columns(df: pd.DataFrame) -> list[str]:
    """Return likely numeric columns in a mixed dataframe."""
    numeric_cols: list[str] = []
    for col in df.columns:
        series = pd.to_numeric(df[col], errors="coerce")
        ratio = series.notna().mean() if len(series) else 0.0
        if ratio >= 0.5:
            numeric_cols.append(col)
    return numeric_cols


def detect_total_rows(df: pd.DataFrame) -> pd.Series:
    """Detect rows that look like totals/subtotals based on keyword match."""
    text_df = df.astype(str).apply(lambda s: s.str.lower())
    pattern = "|".join(k.replace(" ", r"\\s+") for k in TOTAL_KEYWORDS)
    return text_df.apply(lambda row: row.str.contains(pattern, regex=True, na=False).any(), axis=1)


def compute_totals(df: pd.DataFrame) -> dict[str, float]:
    """Compute totals from non-total (line-item) rows for numeric columns."""
    numeric_cols = detect_numeric_columns(df)
    total_rows = detect_total_rows(df)
    line_items = df.loc[~total_rows, numeric_cols]
    return {col: float(pd.to_numeric(line_items[col], errors="coerce").sum(skipna=True)) for col in numeric_cols}


def classify_difference(diff: float, tolerance: float = 0.01) -> str:
    """Classify validation difference."""
    if np.isnan(diff):
        return "OK"
    if abs(diff) <= tolerance:
        return "OK"
    if abs(diff) <= max(0.05, tolerance * 5):
        return "Decimal Rounding Difference"
    return "Casting Error"


def validate_totals(df: pd.DataFrame, table_name: str, tolerance: float = 0.01) -> tuple[pd.DataFrame, list[ValidationRecord]]:
    """Validate totals against computed sums for each numeric column.

    Returns augmented dataframe and summary records.
    """
    out = df.copy()
    total_rows_mask = detect_total_rows(out)
    numeric_cols = detect_numeric_columns(out)

    out["computed_total"] = np.nan
    out["difference"] = np.nan
    out["status"] = ""

    records: list[ValidationRecord] = []

    for col in numeric_cols:
        computed = float(pd.to_numeric(out.loc[~total_rows_mask, col], errors="coerce").sum(skipna=True))
        total_indices = out.index[total_rows_mask].tolist()

        if not total_indices:
            records.append(
                ValidationRecord(table_name, col, np.nan, computed, np.nan, "Missing Total", -1)
            )
            continue

        for idx in total_indices:
            reported = pd.to_numeric(pd.Series([out.at[idx, col]]), errors="coerce").iloc[0]
            if pd.isna(reported):
                continue

            diff = float(reported - computed)
            status = classify_difference(diff, tolerance)

            out.at[idx, "computed_total"] = computed
            out.at[idx, "difference"] = diff
            out.at[idx, "status"] = status

            records.append(
                ValidationRecord(
                    table_name=table_name,
                    column_name=col,
                    reported_total=float(reported),
                    computed_total=computed,
                    difference=diff,
                    status=status,
                    row_index=int(idx),
                )
            )

    return out, records
