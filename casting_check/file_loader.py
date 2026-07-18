"""File loader dispatching to Excel/PDF processors."""

from __future__ import annotations

from pathlib import Path

from .excel_processor import ExtractedTable, process_excel
from .pdf_extractor import process_pdf


SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".pdf"}


def load_tables(file_path: str) -> list[ExtractedTable]:
    ext = Path(file_path).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    if ext in {".xlsx", ".xls"}:
        return process_excel(file_path)
    return process_pdf(file_path)
