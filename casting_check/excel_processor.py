"""Excel ingestion and table detection logic."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .data_cleaner import clean_dataframe


@dataclass
class ExtractedTable:
    source_name: str
    table_name: str
    dataframe: pd.DataFrame


def detect_tables_in_sheet(df: pd.DataFrame, sheet_name: str) -> list[ExtractedTable]:
    """Detect one or more tables in a sheet by splitting around blank rows.

    This heuristic supports irregular spreadsheets containing multiple table blocks.
    """
    tables: list[ExtractedTable] = []
    working = df.copy()

    # Normalize empty strings so blank-row detection works consistently.
    working = working.replace(r"^\s*$", pd.NA, regex=True)

    start = 0
    table_idx = 1
    blank_rows = working.isna().all(axis=1)

    for i, is_blank in enumerate(blank_rows.tolist() + [True]):
        if is_blank:
            block = working.iloc[start:i].dropna(how="all")
            if not block.empty and block.shape[1] > 1:
                # Use first row as header when likely header-like.
                block = block.reset_index(drop=True)
                header = block.iloc[0].astype(str).str.strip()
                if header.nunique() == len(header):
                    block = block[1:].reset_index(drop=True)
                    block.columns = header
                block = clean_dataframe(block)
                if not block.empty:
                    tables.append(
                        ExtractedTable(
                            source_name=sheet_name,
                            table_name=f"{sheet_name}_table_{table_idx}",
                            dataframe=block,
                        )
                    )
                    table_idx += 1
            start = i + 1

    # Fallback: if no blocks identified, treat whole sheet as a single table.
    if not tables and not working.dropna(how="all").empty:
        clean = clean_dataframe(working)
        tables.append(ExtractedTable(sheet_name, f"{sheet_name}_table_1", clean))

    return tables


def process_excel(file_path: str) -> list[ExtractedTable]:
    """Read all sheets and extract table candidates."""
    sheets = pd.read_excel(file_path, sheet_name=None, header=None)
    results: list[ExtractedTable] = []
    for sheet_name, df in sheets.items():
        results.extend(detect_tables_in_sheet(df, sheet_name))
    return results
