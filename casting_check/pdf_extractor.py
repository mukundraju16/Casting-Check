"""PDF extraction utilities using Camelot, pdfplumber, and OCR fallback."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pdfplumber

from .data_cleaner import clean_dataframe
from .excel_processor import ExtractedTable


def _camelot_extract(file_path: str) -> list[pd.DataFrame]:
    try:
        import camelot
    except Exception:
        return []

    try:
        tables = camelot.read_pdf(file_path, pages="all", flavor="stream")
    except Exception:
        return []

    return [t.df for t in tables if not t.df.empty]


def _pdfplumber_extract(file_path: str) -> list[pd.DataFrame]:
    outputs: list[pd.DataFrame] = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables() or []
                for table in page_tables:
                    if not table:
                        continue
                    df = pd.DataFrame(table)
                    if not df.empty:
                        outputs.append(df)
    except Exception:
        return []

    return outputs


def _ocr_extract(file_path: str) -> list[pd.DataFrame]:
    """OCR fallback for scanned PDFs.

    Uses pdf2image + pytesseract if installed; returns empty list otherwise.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except Exception:
        return []

    frames: list[pd.DataFrame] = []
    with TemporaryDirectory() as tmpdir:
        try:
            images = convert_from_path(file_path, output_folder=tmpdir)
        except Exception:
            return []

        for img in images:
            text = pytesseract.image_to_string(img)
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            if not lines:
                continue
            split_rows = [ln.split() for ln in lines]
            max_len = max(len(r) for r in split_rows)
            rows = [r + [""] * (max_len - len(r)) for r in split_rows]
            frames.append(pd.DataFrame(rows))

    return frames


def process_pdf(file_path: str) -> list[ExtractedTable]:
    """Extract candidate tables from PDF with layered fallback strategy."""
    frames = _camelot_extract(file_path)
    if not frames:
        frames = _pdfplumber_extract(file_path)
    if not frames:
        frames = _ocr_extract(file_path)

    source = Path(file_path).name
    tables: list[ExtractedTable] = []
    for idx, frame in enumerate(frames, start=1):
        clean = clean_dataframe(frame)
        if clean.empty:
            continue
        tables.append(
            ExtractedTable(
                source_name=source,
                table_name=f"{source}_table_{idx}",
                dataframe=clean,
            )
        )
    return tables
